from typing import Dict
from .encoders.pil_png import PngEncoder
from .encoders.svg import SvgEncoder
from ..domain.ports import Encoder

def default_encoders() -> Dict[str, Encoder]:
    encs: Dict[str, Encoder] = {}
    for enc in (PngEncoder(), SvgEncoder()):
        encs[enc.key] = enc
    return encs
