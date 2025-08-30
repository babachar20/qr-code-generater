from dataclasses import dataclass

@dataclass(frozen=True)
class AppConfig:
    title: str = "QR Code Studio"
    min_width: int = 760
    min_height: int = 560
    preview_max: int = 360
    default_box_size: int = 10
    default_border: int = 4
    default_fill: str = "black"
