import re
from typing import Optional

import click
import numpy as np
from scipy.io import wavfile


def parse_duration(duration_str: str) -> float:
    """Parses a duration string like '5min 30s', '5min', '10s', '5' (minutes), or '04:30' into seconds."""
    if not duration_str:
        return 0.0

    # Try to parse as MM:SS
    mm_ss_match = re.match(r'^(\d+):(\d{2})$', duration_str.strip())
    if mm_ss_match:
        minutes = int(mm_ss_match.group(1))
        seconds = int(mm_ss_match.group(2))
        return float(minutes * 60 + seconds)

    # Try to parse as a simple float (default to minutes)
    try:
        return float(duration_str) * 60.0
    except ValueError:
        pass

    # Regex for components
    min_match = re.search(r'(\d+(?:\.\d+)?)\s*min', duration_str)
    sec_match = re.search(r'(\d+(?:\.\d+)?)\s*s', duration_str)

    total_seconds = 0.0
    if min_match:
        total_seconds += float(min_match.group(1)) * 60.0
    if sec_match:
        total_seconds += float(sec_match.group(1))

    if not min_match and not sec_match:
        raise ValueError(f"Invalid duration format: {duration_str}")

    return total_seconds


def create_click(freq: float, fs: int, duration_ms: float = 80) -> np.ndarray:
    """
    Creates a typical digital metronome click sound
    """
    t = np.linspace(0, duration_ms / 1000, int(fs * (duration_ms / 1000)), False)

    sine = np.sin(2 * np.pi * freq * t)
    square = np.sign(sine)
    wave = (sine * 0.7) + (square * 0.3)
    envelope = np.exp(-50 * t)

    return wave * envelope


def create_wood_click(freq: float, fs: int, duration_ms: float = 60) -> np.ndarray:
    """
    Creates a click sound that mimics a wood block click.
    """
    t = np.linspace(0, duration_ms / 1000, int(fs * (duration_ms / 1000)), False)

    wave = np.sin(2 * np.pi * freq * t) * 0.5
    wave += np.sin(2 * np.pi * freq * 2.1 * t) * 0.2
    wave += np.sin(2 * np.pi * freq * 3.5 * t) * 0.1
    noise = np.random.uniform(-1, 1, len(t)) * np.exp(-200 * t) * 0.2
    wave += noise
    envelope = np.exp(-80 * t)

    return wave * envelope


def create_stick_clap(fs: int, duration_ms: float = 50) -> np.ndarray:
    """
    Creates a sound that mimics a drum stick clap using noise and a sharp envelope.
    """
    t = np.linspace(0, duration_ms / 1000, int(fs * (duration_ms / 1000)), False)

    noise = np.random.uniform(-1, 1, len(t))
    noise = np.diff(noise, prepend=0)
    tone = np.sin(2 * np.pi * 3000 * t) * np.exp(-100 * t)
    wave = (noise * 0.8) + (tone * 0.2)
    envelope = np.exp(-150 * t)

    return wave * envelope


def load_custom_click(path: str, target_fs: int) -> np.ndarray:
    """
    Load a custom WAV file to use as click. Make sure that the
    WAV file has the same sampling rate as the output WAV
    """
    try:
        sample_rate, data = wavfile.read(path)

        # Normalize wave
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32767.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483647.0
        elif data.dtype == np.float32:
            pass
        else:
            data = data.astype(np.float32) / np.max(np.abs(data))

        # Handle multi-channel (mono-ize)
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        if sample_rate != target_fs:
            click.echo(click.style(f"Warning: Sample rate mismatch for {path} ({sample_rate} vs {target_fs}).",
                                   fg="yellow"))

        return data
    except Exception as e:
        raise click.ClickException(click.style(f"Error loading custom WAV {path}: {e}", fg="red"))


def generate_click_track_core(bpm: int = 120, duration_str: str = '5.0', main_track_beats: Optional[int] = None,
                              pre_roll_sec: float = 1.0, count_in_beats: int = 4,
                              count_in_type: str = 'stick', click_type: str = 'default',
                              custom_high: Optional[str] = None, custom_low: Optional[str] = None,
                              output_file: Optional[str] = None, fs: int = 44100,
                              measure: str = '4/4') -> None:
    """Core logic to generate a click track."""

    try:
        parts = measure.split('/')
        beats_per_measure = int(parts[0])
        beat_unit = int(parts[1])
        if beat_unit not in [1, 2, 4, 8, 16]:
            raise ValueError(f"Unsupported beat unit: {beat_unit}")
    except (ValueError, IndexError):
        raise ValueError(
            f"Invalid measure format: {measure}. Expected 'n/m' (e.g., 4/4) with denominator in [1, 2, 4, 8, 16].")

    if output_file is None:
        output_file = f"click-track-{bpm}bpm.wav"

    samples_per_beat = (60.0 / bpm) * (4.0 / beat_unit) * fs

    if main_track_beats is None:
        duration_sec = parse_duration(duration_str)
        main_track_beats = int((duration_sec * bpm / 60.0) * (beat_unit / 4.0))

    total_beats = count_in_beats + main_track_beats

    # Count-in
    if count_in_type == 'stick':
        click_count = create_stick_clap(fs)
    elif count_in_type == 'wood':
        click_count = create_wood_click(1800, fs)
    else:
        click_count = create_click(1800, fs)  # High/Sharp

    # High Click
    if custom_high:
        click_high = load_custom_click(custom_high, fs)
    else:
        if click_type == 'wood':
            click_high = create_wood_click(1200, fs)
        else:
            click_high = create_click(1200, fs)

    # Low Click
    if custom_low:
        click_low = load_custom_click(custom_low, fs)
    else:
        if click_type == 'wood':
            click_low = create_wood_click(600, fs)
        else:
            click_low = create_click(600, fs)

    # Assemble click track 
    pre_roll_samples = int(pre_roll_sec * fs)
    total_samples = pre_roll_samples + int(total_beats * samples_per_beat) + fs
    track = np.zeros(total_samples)

    for i in range(total_beats):
        start_idx = pre_roll_samples + int(round(i * samples_per_beat))

        if i < count_in_beats:
            current_sound = click_count
        else:
            relative_i = i - count_in_beats
            current_sound = click_high if (relative_i % beats_per_measure == 0) else click_low

        end_idx = start_idx + len(current_sound)
        if end_idx < len(track):
            track[start_idx:end_idx] = current_sound

    # Peak normalize track. 
    gain_reduction = 1.5  # must be >= 1
    peak = np.max(np.abs(track)) * gain_reduction
    if peak > 0:
        track = track / peak

    # Convert to 16-bit PCM
    output_data = (track * 32767).astype(np.int16)
    wavfile.write(output_file, fs, output_data)


@click.command()
@click.option('--bpm', default=120, help='Beats per minute.')
@click.option('--duration', 'duration_str', default='5.0',
              help='Duration of the main track (e.g. "5min 30s", "5min", "10s", or "5" for minutes).')
@click.option('--beats', 'main_track_beats', type=int, default=None,
              help='Duration in number of beats. If provided, duration is ignored.')
@click.option('--pre-roll', 'pre_roll_sec', default=1.0, help='Pre-roll duration in seconds.')
@click.option('--count-in', 'count_in_beats', default=4, help='Number of count-in beats.')
@click.option('--count-in-type', type=click.Choice(['default', 'stick', 'wood']), default='stick',
              help='Sound type for the count-in.')
@click.option('--click-type', type=click.Choice(['default', 'wood']), default='default',
              help='Sound type for the main click.')
@click.option('--custom-high', type=click.Path(exists=True), default=None,
              help='Custom WAV file for the high click.')
@click.option('--custom-low', type=click.Path(exists=True), default=None,
              help='Custom WAV file for the low click.')
@click.option('--output', 'output_file', default=None,
              help='Output filename. Defaults to click-track-<bpm>bpm.wav')
@click.option('--fs', default=44100, help='Sampling rate.')
@click.option('--measure', default='4/4', help='Measure/Time signature (e.g., 4/4, 3/4, 6/8).')
def generate_click_track(bpm: int, duration_str: str, main_track_beats: Optional[int], pre_roll_sec: float,
                         count_in_beats: int,
                         count_in_type: str, click_type: str, custom_high: Optional[str],
                         custom_low: Optional[str], output_file: Optional[str], fs: int,
                         measure: str) -> None:
    """Generates a click track with pre-roll and count-in."""

    try:
        generate_click_track_core(
            bpm=bpm,
            duration_str=duration_str,
            main_track_beats=main_track_beats,
            pre_roll_sec=pre_roll_sec,
            count_in_beats=count_in_beats,
            count_in_type=count_in_type,
            click_type=click_type,
            custom_high=custom_high,
            custom_low=custom_low,
            output_file=output_file,
            fs=fs,
            measure=measure
        )
    except ValueError as e:
        raise click.ClickException(click.style(str(e), fg="red"))

    click.echo(click.style("\nClick Track Generated Successfully!", fg="green", bold=True))
    click.echo("-" * 40)
    click.echo(f"{'Output File:':<20} {output_file}")
    click.echo(f"{'BPM:':<20} {bpm}")
    click.echo(f"{'Duration:':<20} {duration_str}")
    if main_track_beats is None:
        duration_sec = parse_duration(duration_str)
        main_track_beats = int((duration_sec * bpm / 60.0))
    click.echo(f"{'Duration (beats):':<20} {main_track_beats}")
    click.echo(f"{'Pre-roll (sec):':<20} {pre_roll_sec}")
    click.echo(f"{'Count-in Beats:':<20} {count_in_beats}")
    click.echo(f"{'Count-in Type:':<20} {count_in_type}")
    click.echo(f"{'Measure:':<20} {measure}")
    click.echo(f"{'Click Type:':<20} {click_type}")
    if custom_high:
        click.echo(f"{'Custom High:':<20} {custom_high}")
    if custom_low:
        click.echo(f"{'Custom Low:':<20} {custom_low}")
    click.echo(f"{'Sampling Rate:':<20} {fs} Hz")
    click.echo("-" * 40)


if __name__ == '__main__':
    generate_click_track()
