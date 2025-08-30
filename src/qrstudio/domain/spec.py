from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ErrorCorrection(str, Enum):
    L = "L"
    M = "M"
    Q = "Q"
    H = "H"

@dataclass
class QRSpec:
    data: str
    ec: ErrorCorrection
    box_size: int
    border: int
    fill_color: str
    background: str  # "white" | "transparent"

    def normalized_background(self) -> str:
        return "transparent" if self.background.lower().startswith("trans") else "white"
