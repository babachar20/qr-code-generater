from .spec import QRSpec, ErrorCorrection
from .backgrounds import (
    BackgroundStrategy,
    WhiteBackground,
    TransparentBackground,
    get_background,
)

__all__ = [
    "QRSpec",
    "ErrorCorrection",
    "BackgroundStrategy",
    "WhiteBackground",
    "TransparentBackground",
    "get_background",
]
