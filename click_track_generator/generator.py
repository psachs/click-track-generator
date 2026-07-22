from typing import Optional

import numpy as np
from scipy.io import wavfile

from .models import ClickTrackSpec, TempoSection
from .parsing import parse_duration, parse_measure, parse_section_duration
from .sounds import create_click, create_wood_click, create_stick_clap, load_custom_click


def _make_count_in_sound(count_in_type: str, fs: int) -> np.ndarray:
    if count_in_type == 'stick':
        return create_stick_clap(fs)
    if count_in_type == 'wood':
        return create_wood_click(1800, fs)
    if count_in_type == 'default':
        return create_click(1800, fs)
    raise ValueError(f'Invalid count_in_type: {count_in_type}')


def _make_click_pair(
    click_type: str,
    custom_high: Optional[str],
    custom_low: Optional[str],
    fs: int,
) -> tuple[np.ndarray, np.ndarray]:
    if custom_high:
        click_high = load_custom_click(custom_high, fs)
    elif click_type == 'wood':
        click_high = create_wood_click(1100, fs)
    else:
        click_high = create_click(1100, fs)

    if custom_low:
        click_low = load_custom_click(custom_low, fs)
    elif click_type == 'wood':
        click_low = create_wood_click(700, fs)
    else:
        click_low = create_click(700, fs)

    return click_high, click_low


def _compute_main_track_beats(spec: ClickTrackSpec, beat_unit: int) -> int:
    duration_sec = parse_duration(spec.duration_str)
    return int((duration_sec * spec.bpm / 60.0) * (beat_unit / 4.0))


def _assemble_samples(
    pre_roll_sec: float,
    fs: int,
    total_beats: int,
    count_in_beats: int,
    beats_per_measure: int,
    samples_per_beat: float,
    count_in_sound: np.ndarray,
    click_high: np.ndarray,
    click_low: np.ndarray,
    use_accent_click: bool,
) -> np.ndarray:
    pre_roll_samples = int(pre_roll_sec * fs)
    total_samples = pre_roll_samples + int(total_beats * samples_per_beat) + fs
    track = np.zeros(total_samples)

    for i in range(total_beats):
        start_idx = pre_roll_samples + int(round(i * samples_per_beat))

        if i < count_in_beats:
            sound = count_in_sound
        else:
            relative_i = i - count_in_beats
            on_beat_one = (relative_i % beats_per_measure == 0) and use_accent_click
            sound = click_high if on_beat_one else click_low

        end_idx = start_idx + len(sound)
        if end_idx < len(track):
            track[start_idx:end_idx] = sound

    return track


def _ramp_beat_times(
    start_time: float,
    bpm_a: float,
    bpm_b: float,
    duration: float,
    beat_unit: int,
) -> list[float]:
    """Compute beat times during a linear BPM ramp from bpm_a to bpm_b over `duration` seconds.

    Integrating the tempo curve gives cumulative beats f(t) = beat_unit/240 * [bpm_a*t + (bpm_b-bpm_a)*t²/(2T)].
    Setting f(t) = n and solving the resulting quadratic yields each beat's timestamp analytically.
    """
    times: list[float] = []
    n = 0
    while True:
        target = n * 240.0 / beat_unit  # = n * 60 * 4 / beat_unit
        if abs(bpm_b - bpm_a) < 1e-6:
            t = n * (60.0 / bpm_a) * (4.0 / beat_unit)
        else:
            a = (bpm_b - bpm_a) / (2.0 * duration)
            b = bpm_a
            disc = b * b - 4 * a * (-target)
            if disc < 0:
                break
            t = (-b + np.sqrt(disc)) / (2 * a)
        if t >= duration:
            break
        times.append(start_time + t)
        n += 1
    return times


def _build_variable_tempo_events(
    sections: list[TempoSection],
    beats_per_measure: int,
    beat_unit: int,
    count_in_beats: int,
    pre_roll_sec: float,
    use_accent_click: bool,
) -> tuple[list[tuple[float, str]], float]:
    """Build the full list of beat events for a variable-tempo track.

    Returns (events, total_duration_sec) where each event is (time_sec, kind)
    and kind is 'count_in', 'high', or 'low'.
    """
    first_spb = (60.0 / sections[0].bpm) * (4.0 / beat_unit)
    events: list[tuple[float, str]] = [
        (pre_roll_sec + i * first_spb, 'count_in') for i in range(count_in_beats)
    ]

    current_time = pre_roll_sec + count_in_beats * first_spb
    main_beat = 0  # running beat index within the main track (for accent detection)

    for idx, section in enumerate(sections):
        next_section = sections[idx + 1] if idx + 1 < len(sections) else None
        section_dur = parse_section_duration(section.duration, section.bpm, beats_per_measure, beat_unit)
        spb = (60.0 / section.bpm) * (4.0 / beat_unit)
        n_beats = int(section_dur / spb)

        for j in range(n_beats):
            on_beat_one = (main_beat % beats_per_measure == 0) and use_accent_click
            events.append((current_time + j * spb, 'high' if on_beat_one else 'low'))
            main_beat += 1
        current_time += n_beats * spb

        if next_section and section.transition == 'gradual':
            trans_dur = parse_section_duration(
                section.transition_duration, section.bpm, beats_per_measure, beat_unit
            )
            if trans_dur > 0:
                for t in _ramp_beat_times(current_time, section.bpm, next_section.bpm, trans_dur, beat_unit):
                    on_beat_one = (main_beat % beats_per_measure == 0) and use_accent_click
                    events.append((t, 'high' if on_beat_one else 'low'))
                    main_beat += 1
                current_time += trans_dur

    return events, current_time + 1.0  # +1 s tail after last beat


def _assemble_from_events(
    events: list[tuple[float, str]],
    count_in_sound: np.ndarray,
    click_high: np.ndarray,
    click_low: np.ndarray,
    total_duration: float,
    fs: int,
) -> np.ndarray:
    sound_map = {'count_in': count_in_sound, 'high': click_high, 'low': click_low}
    total_samples = int(total_duration * fs)
    track = np.zeros(total_samples)
    for time_sec, kind in events:
        sound = sound_map[kind]
        start_idx = int(round(time_sec * fs))
        end_idx = start_idx + len(sound)
        if end_idx <= total_samples:
            track[start_idx:end_idx] += sound
    return track


def _normalize_rms(signal: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
    rms = np.sqrt(np.mean(signal ** 2))
    if rms > 0:
        signal = signal * (target_rms / rms)
    return signal


def _normalize(track: np.ndarray, gain_reduction: float = 1.5) -> np.ndarray:
    peak = np.max(np.abs(track)) * gain_reduction
    if peak > 0:
        track = track / peak
    return track


def generate_click_track_core(spec: ClickTrackSpec) -> None:
    """Generate a click track WAV file from a ClickTrackSpec."""
    beats_per_measure, beat_unit = parse_measure(spec.measure)

    count_in_sound = _normalize_rms(_make_count_in_sound(spec.count_in_type, spec.fs))
    click_high, click_low = _make_click_pair(spec.click_type, spec.custom_high, spec.custom_low, spec.fs)
    click_high = _normalize_rms(click_high)
    click_low = _normalize_rms(click_low)

    if spec.tempo_sections:
        output_file = spec.output_file or 'click-track-variable.wav'
        events, total_duration = _build_variable_tempo_events(
            spec.tempo_sections, beats_per_measure, beat_unit,
            spec.count_in_beats, spec.pre_roll_sec, spec.use_accent_click,
        )
        track = _assemble_from_events(
            events, count_in_sound, click_high, click_low, total_duration, spec.fs,
        )
    else:
        output_file = spec.output_file or f"click-track-{spec.bpm}bpm.wav"
        samples_per_beat = (60.0 / spec.bpm) * (4.0 / beat_unit) * spec.fs
        main_track_beats = (
            spec.main_track_beats
            if spec.main_track_beats is not None
            else _compute_main_track_beats(spec, beat_unit)
        )
        total_beats = spec.count_in_beats + main_track_beats
        track = _assemble_samples(
            pre_roll_sec=spec.pre_roll_sec,
            fs=spec.fs,
            total_beats=total_beats,
            count_in_beats=spec.count_in_beats,
            beats_per_measure=beats_per_measure,
            samples_per_beat=samples_per_beat,
            count_in_sound=count_in_sound,
            click_high=click_high,
            click_low=click_low,
            use_accent_click=spec.use_accent_click,
        )

    track = _normalize(track)
    output_data = (track * 32767).astype(np.int16)
    wavfile.write(output_file, spec.fs, output_data)
