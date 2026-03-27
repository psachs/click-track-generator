# Click Track Generator

A simple Python script to generate a WAV click track with configurable BPM, duration, pre-roll, and count-in beats.

## Features

- Custom BPM.
- Configurable measure/time signature (e.g., 4/4, 3/4, 6/8). The denominator affects the pulse speed (e.g., 8/8 is twice as fast as 4/4 at the same BPM).
- Configurable duration (e.g., "5min 30s", "10s", or "5" for minutes) or number of beats.
- Optional pre-roll (silence at the start) in seconds.
- Configurable count-in beats.
- Choice of count-in sound: standard click, "drum stick clap", or "wood block".
- Choice of main click sound: standard or "wood block".
- Option to use custom WAV files for high and low clicks.
- Sharp, audible click sound (sine + square mix with sharp attack).
- Peak normalized output.

## Installation

Ensure you have Python installed. This project uses `numpy`, `scipy`, and `click`.

If you have `uv` installed, you can run it directly:

```bash
uv run click_track_generator.py [OPTIONS]
```

Or install dependencies manually:

```bash
pip install numpy scipy click
```

## Usage

You can run the script with various options:

```bash
python click_track_generator.py --bpm 120 --duration 5 --output my-track.wav
```

### Options

| Option            | Description                                         | Default                    |
|-------------------|-----------------------------------------------------|----------------------------|
| `--bpm`           | Beats per minute                                    | `120`                      |
| `--duration`      | Duration (e.g., "5min 30s", "10s", or "5")          | `5.0`                      |
| `--beats`         | Duration in number of beats (overrides --duration)  | -                          |
| `--pre-roll`      | Pre-roll duration in seconds                        | `1.0`                      |
| `--count-in`      | Number of count-in beats                            | `4`                        |
| `--count-in-type` | Count-in sound type (`default`, `stick`, or `wood`) | `stick`                    |
| `--click-type`    | Main click sound type (`default` or `wood`)         | `default`                  |
| `--custom-high`   | Custom WAV file for the high click                  | -                          |
| `--custom-low`    | Custom WAV file for the low click                   | -                          |
| `--output`        | Output filename                                     | `click-track-<bpm>bpm.wav` |
| `--measure`       | Measure/Time signature (e.g., 4/4, 3/4, 6/8)        | `4/4`                      |
| `--fs`            | Sampling rate in Hz                                 | `44100`                    |
| `--help`          | Show the help message and exit                      | -                          |

## Example

Generate a 140 BPM click track in 3/4 time, 2 minutes long, with an 8-beat count-in:

```bash
python click_track_generator.py --bpm 140 --measure 3/4 --duration 2 --count-in 8 --output my-click.wav
```
