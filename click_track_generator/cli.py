from typing import Optional

import click

from .generator import generate_click_track_core
from .models import ClickTrackSpec
from .parsing import parse_duration


@click.command()
@click.option('--bpm', default=120, help='Beats per minute.')
@click.option('--duration', 'duration_str', default='5.0',
              help='Duration of the main track (e.g. "5min 30s", "5min", "10s", or "5" for minutes).')
@click.option('--beats', 'main_track_beats', type=int, default=None,
              help='Duration in number of beats. If provided, --duration is ignored.')
@click.option('--pre-roll', 'pre_roll_sec', default=1.0, help='Pre-roll duration in seconds.')
@click.option('--count-in', 'count_in_beats', default=4, help='Number of count-in beats.')
@click.option('--count-in-type', type=click.Choice(['default', 'stick', 'wood']), default='default',
              help='Sound type for the count-in.')
@click.option('--click-type', type=click.Choice(['default', 'wood']), default='default',
              help='Sound type for the main click.')
@click.option('--use-accent-click', type=bool, default=True,
              help='If false, beat 1 is not accented.')
@click.option('--custom-high', type=click.Path(exists=True), default=None,
              help='Custom WAV file for the high (accented) click.')
@click.option('--custom-low', type=click.Path(exists=True), default=None,
              help='Custom WAV file for the low click.')
@click.option('--output', 'output_file', default=None,
              help='Output filename. Defaults to click-track-<bpm>bpm.wav')
@click.option('--fs', default=44100, help='Sampling rate.')
@click.option('--measure', default='4/4', help='Time signature (e.g., 4/4, 3/4, 6/8).')
def generate_click_track(
    bpm: int, duration_str: str, main_track_beats: Optional[int], pre_roll_sec: float,
    count_in_beats: int, count_in_type: str, click_type: str, use_accent_click: bool,
    custom_high: Optional[str], custom_low: Optional[str], output_file: Optional[str],
    fs: int, measure: str,
) -> None:
    """Generates a click track WAV with pre-roll and count-in."""
    spec = ClickTrackSpec(
        bpm=bpm,
        duration_str=duration_str,
        main_track_beats=main_track_beats,
        pre_roll_sec=pre_roll_sec,
        count_in_beats=count_in_beats,
        count_in_type=count_in_type,
        click_type=click_type,
        use_accent_click=use_accent_click,
        custom_high=custom_high,
        custom_low=custom_low,
        output_file=output_file,
        fs=fs,
        measure=measure,
    )

    try:
        generate_click_track_core(spec)
    except ValueError as e:
        raise click.ClickException(click.style(str(e), fg="red"))

    resolved_output = output_file or f"click-track-{bpm}bpm.wav"
    if main_track_beats is None:
        duration_sec = parse_duration(duration_str)
        main_track_beats = int((duration_sec * bpm / 60.0))

    click.echo(click.style("\nClick Track Generated Successfully!", fg="green", bold=True))
    click.echo("-" * 40)
    click.echo(f"{'Output File:':<20} {resolved_output}")
    click.echo(f"{'BPM:':<20} {bpm}")
    click.echo(f"{'Duration:':<20} {duration_str}")
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
