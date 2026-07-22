from typing import Optional

import click

from .generator import generate_click_track_core
from .models import ClickTrackSpec, TempoSection
from .parsing import parse_duration


def _parse_section(s: str) -> TempoSection:
    parts = s.split('|')
    if len(parts) < 2:
        raise click.BadParameter(
            f"Section must be 'BPM|DURATION[|TRANSITION[|TRANSITION_DURATION]]', got: '{s}'"
        )
    try:
        bpm = float(parts[0])
    except ValueError:
        raise click.BadParameter(f"Invalid BPM in section: '{parts[0]}'")
    duration = parts[1]
    transition = parts[2] if len(parts) > 2 else 'immediate'
    if transition not in ('immediate', 'gradual'):
        raise click.BadParameter(f"Transition must be 'immediate' or 'gradual', got: '{transition}'")
    transition_duration = parts[3] if len(parts) > 3 else '0s'
    return TempoSection(bpm=bpm, duration=duration, transition=transition, transition_duration=transition_duration)


@click.command()
@click.option('--bpm', default=120, help='Beats per minute (ignored when --section is used).')
@click.option('--duration', 'duration_str', default='5.0',
              help='Duration of the main track (e.g. "5min 30s", "5min", "10s", or "5" for minutes). '
                   'Ignored when --section is used.')
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
              help='Output filename. Defaults to click-track-<bpm>bpm.wav (or click-track-variable.wav with --section).')
@click.option('--fs', default=44100, help='Sampling rate.')
@click.option('--measure', default='4/4', help='Time signature (e.g., 4/4, 3/4, 6/8).')
@click.option('--section', 'section_strs', multiple=True, metavar='SECTION',
              help='Tempo section: "BPM|DURATION[|TRANSITION[|TRANSITION_DURATION]]". '
                   'DURATION accepts bars (e.g. 8bars), MM:SS, seconds (e.g. 30s), or minutes float. '
                   'TRANSITION is "immediate" (default) or "gradual". '
                   'Repeat the flag for multiple sections. '
                   'Example: --section "120|8bars" --section "140|8bars|gradual|2bars"')
def generate_click_track(
    bpm: int, duration_str: str, main_track_beats: Optional[int], pre_roll_sec: float,
    count_in_beats: int, count_in_type: str, click_type: str, use_accent_click: bool,
    custom_high: Optional[str], custom_low: Optional[str], output_file: Optional[str],
    fs: int, measure: str, section_strs: tuple[str, ...],
) -> None:
    """Generates a click track WAV with pre-roll and count-in."""
    try:
        tempo_sections = [_parse_section(s) for s in section_strs] if section_strs else None
    except click.BadParameter as e:
        raise click.ClickException(click.style(str(e), fg="red"))

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
        tempo_sections=tempo_sections,
    )

    try:
        generate_click_track_core(spec)
    except ValueError as e:
        raise click.ClickException(click.style(str(e), fg="red"))

    resolved_output = output_file or (
        'click-track-variable.wav' if tempo_sections else f"click-track-{bpm}bpm.wav"
    )

    click.echo(click.style("\nClick Track Generated Successfully!", fg="green", bold=True))
    click.echo("-" * 40)
    click.echo(f"{'Output File:':<20} {resolved_output}")
    click.echo(f"{'Measure:':<20} {measure}")
    click.echo(f"{'Pre-roll (sec):':<20} {pre_roll_sec}")
    click.echo(f"{'Count-in Beats:':<20} {count_in_beats}")
    click.echo(f"{'Count-in Type:':<20} {count_in_type}")
    click.echo(f"{'Click Type:':<20} {click_type}")
    if custom_high:
        click.echo(f"{'Custom High:':<20} {custom_high}")
    if custom_low:
        click.echo(f"{'Custom Low:':<20} {custom_low}")
    click.echo(f"{'Sampling Rate:':<20} {fs} Hz")

    if tempo_sections:
        click.echo(f"{'Sections:':<20}")
        for i, sec in enumerate(tempo_sections):
            is_last = i == len(tempo_sections) - 1
            line = f"  [{i + 1}] {sec.bpm:.0f} BPM  {sec.duration}"
            if not is_last and sec.transition == 'gradual':
                line += click.style(f"  → gradual over {sec.transition_duration}", fg="cyan")
            click.echo(line)
    else:
        click.echo(f"{'BPM:':<20} {bpm}")
        click.echo(f"{'Duration:':<20} {duration_str}")
        if main_track_beats is None:
            duration_sec = parse_duration(duration_str)
            main_track_beats = int((duration_sec * bpm / 60.0))
        click.echo(f"{'Duration (beats):':<20} {main_track_beats}")

    click.echo("-" * 40)
