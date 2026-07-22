# Click Track Generator

A Python tool to generate WAV click tracks with configurable BPM, time signature, duration, count-in, and click sounds.

## Installation

Requires Python >=3.11.

```bash
pip install -e .
```

## Usage

```bash
python -m click_track_generator [OPTIONS]
```

### Options

| Option | Default | Description |
|---|---|---|
| `--bpm` | `120` | Beats per minute |
| `--duration` | `5.0` | Duration of the main track. Accepts `MM:SS`, `"5min 30s"`, `"10s"`, or a plain number (minutes) |
| `--beats` | — | Duration in beats; overrides `--duration` if provided |
| `--measure` | `4/4` | Time signature (e.g. `3/4`, `6/8`). The denominator affects pulse speed — `6/8` at 120 BPM pulses twice as fast as `6/4` |
| `--count-in` | `4` | Number of count-in beats before the main track |
| `--count-in-type` | `default` | Count-in sound: `default`, `stick`, or `wood` |
| `--click-type` | `default` | Main click sound: `default` or `wood` |
| `--use-accent-click` | `true` | Accent beat 1 with a higher-pitched click |
| `--custom-high` | — | Custom WAV file for the accented (beat 1) click |
| `--custom-low` | — | Custom WAV file for the other beats |
| `--pre-roll` | `1.0` | Silence in seconds before the count-in |
| `--output` | `click-track-<bpm>bpm.wav` | Output filename |
| `--fs` | `44100` | Sampling rate in Hz |

### Examples

120 BPM, 4 minutes, wood click sound:
```bash
python -m click_track_generator --bpm 120 --duration 4 --click-type wood
```

140 BPM in 3/4, 2-minute track with an 8-beat count-in:
```bash
python -m click_track_generator --bpm 140 --measure 3/4 --duration 2 --count-in 8 --output waltz.wav
```

Exact length by beat count, no accent on beat 1:
```bash
python -m click_track_generator --bpm 90 --beats 128 --use-accent-click false
```

## Batch generation

To generate click tracks in a batch, you can use Python code as shown
in the example below to generate a click track from a spec.

```python
from click_track_generator import ClickTrackSpec, generate_click_track_core

spec = ClickTrackSpec(bpm=120, duration_str="04:30", measure="4/4", click_type="wood", output_file="my-track.wav")
generate_click_track_core(spec)
```

