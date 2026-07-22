from typing import Optional

import numpy as np
from scipy.io import wavfile

from .models import ClickTrackSpec
from .parsing import parse_duration, parse_measure
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


def _normalize(track: np.ndarray, gain_reduction: float = 1.5) -> np.ndarray:
    peak = np.max(np.abs(track)) * gain_reduction
    if peak > 0:
        track = track / peak
    return track


def generate_click_track_core(spec: ClickTrackSpec) -> None:
    """Generate a click track WAV file from a ClickTrackSpec."""
    beats_per_measure, beat_unit = parse_measure(spec.measure)

    output_file = spec.output_file or f"click-track-{spec.bpm}bpm.wav"
    samples_per_beat = (60.0 / spec.bpm) * (4.0 / beat_unit) * spec.fs

    main_track_beats = (
        spec.main_track_beats
        if spec.main_track_beats is not None
        else _compute_main_track_beats(spec, beat_unit)
    )
    total_beats = spec.count_in_beats + main_track_beats

    count_in_sound = _make_count_in_sound(spec.count_in_type, spec.fs)
    click_high, click_low = _make_click_pair(spec.click_type, spec.custom_high, spec.custom_low, spec.fs)

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
