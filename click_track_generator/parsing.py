import re


def parse_duration(duration_str: str) -> float:
    """Parses a duration string like '5min 30s', '5min', '10s', '5' (minutes), or '04:30' into seconds."""
    if not duration_str:
        return 0.0

    mm_ss_match = re.match(r'^(\d+):(\d{2})$', duration_str.strip())
    if mm_ss_match:
        minutes = int(mm_ss_match.group(1))
        seconds = int(mm_ss_match.group(2))
        return float(minutes * 60 + seconds)

    try:
        return float(duration_str) * 60.0
    except ValueError:
        pass

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


def parse_section_duration(s: str, bpm: float, beats_per_measure: int, beat_unit: int) -> float:
    """Parse a duration that may include a bars specifier (e.g. '8bars') in addition to standard formats."""
    match = re.match(r'^(\d+(?:\.\d+)?)\s*bars?$', s.strip(), re.IGNORECASE)
    if match:
        n_bars = float(match.group(1))
        seconds_per_bar = beats_per_measure * (60.0 / bpm) * (4.0 / beat_unit)
        return n_bars * seconds_per_bar
    return parse_duration(s)


def parse_measure(measure: str) -> tuple[int, int]:
    """Parse a time signature string like '4/4' into (beats_per_measure, beat_unit)."""
    try:
        parts = measure.split('/')
        beats_per_measure = int(parts[0])
        beat_unit = int(parts[1])
        if beat_unit not in [1, 2, 4, 8, 16]:
            raise ValueError(f"Unsupported beat unit: {beat_unit}")
        return beats_per_measure, beat_unit
    except (ValueError, IndexError):
        raise ValueError(
            f"Invalid measure format: {measure}. Expected 'n/m' (e.g., 4/4) with denominator in [1, 2, 4, 8, 16].")
