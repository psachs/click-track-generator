import click
import numpy as np
from scipy.io import wavfile


def create_click(freq: float, fs: int, duration_ms: float = 80) -> np.ndarray:
    """Creates a typical digital metronome click sound."""
    t = np.linspace(0, duration_ms / 1000, int(fs * (duration_ms / 1000)), False)
    sine = np.sin(2 * np.pi * freq * t)
    square = np.sign(sine)
    wave = (sine * 0.7) + (square * 0.3)
    envelope = np.exp(-50 * t)
    return wave * envelope


def create_wood_click(freq: float, fs: int, duration_ms: float = 60) -> np.ndarray:
    """Creates a click sound that mimics a wood block click."""
    t = np.linspace(0, duration_ms / 1000, int(fs * (duration_ms / 1000)), False)
    wave = np.sin(2 * np.pi * freq * t) * 0.5
    wave += np.sin(2 * np.pi * freq * 2.1 * t) * 0.2
    wave += np.sin(2 * np.pi * freq * 3.5 * t) * 0.1
    noise = np.random.uniform(-1, 1, len(t)) * np.exp(-200 * t) * 0.2
    wave += noise
    envelope = np.exp(-80 * t)
    return wave * envelope


def create_stick_clap(fs: int, duration_ms: float = 50) -> np.ndarray:
    """Creates a sound that mimics a drum stick clap using noise and a sharp envelope."""
    t = np.linspace(0, duration_ms / 1000, int(fs * (duration_ms / 1000)), False)
    noise = np.random.uniform(-1, 1, len(t))
    noise = np.diff(noise, prepend=0)
    tone = np.sin(2 * np.pi * 3000 * t) * np.exp(-100 * t)
    wave = (noise * 0.8) + (tone * 0.2)
    envelope = np.exp(-150 * t)
    return wave * envelope


def load_custom_click(path: str, target_fs: int) -> np.ndarray:
    """Load a custom WAV file to use as click. The WAV must match the output sampling rate."""
    try:
        sample_rate, data = wavfile.read(path)

        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32767.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483647.0
        elif data.dtype != np.float32:
            data = data.astype(np.float32) / np.max(np.abs(data))

        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        if sample_rate != target_fs:
            click.echo(click.style(
                f"Warning: Sample rate mismatch for {path} ({sample_rate} vs {target_fs}).", fg="yellow"))

        return data
    except Exception as e:
        raise click.ClickException(click.style(f"Error loading custom WAV {path}: {e}", fg="red"))
