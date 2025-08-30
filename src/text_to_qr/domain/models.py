from dataclasses import dataclass
from typing import Literal

ECLevel = Literal["L", "M", "Q", "H"]
BG = Literal["white", "transparent"]
Fmt = Literal["png", "svg"]

@dataclass(frozen=True)
class QRCodeSpec:
    data: str
    error: ECLevel = "M"
    box_size: int = 10
    border: int = 4
    fill_color: str = "black"
    background: BG = "white"
    fmt: Fmt = "png"  # output format (encoder key)
