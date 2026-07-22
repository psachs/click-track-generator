from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TempoSection:
    bpm: float
    duration: str
    transition: str = 'immediate'       # 'immediate' | 'gradual'
    transition_duration: str = '0s'     # only used when transition='gradual'


@dataclass
class ClickTrackSpec:
    bpm: int = 120
    duration_str: str = '5.0'
    main_track_beats: Optional[int] = None
    pre_roll_sec: float = 1.0
    count_in_beats: int = 4
    count_in_type: str = 'default'
    click_type: str = 'default'
    use_accent_click: bool = True
    custom_high: Optional[str] = None
    custom_low: Optional[str] = None
    output_file: Optional[str] = None
    fs: int = 44100
    measure: str = '4/4'
    tempo_sections: Optional[list[TempoSection]] = None
