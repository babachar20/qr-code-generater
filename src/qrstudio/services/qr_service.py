from __future__ import annotations
from typing import Tuple
from PIL import Image
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from ..domain.spec import QRSpec, ErrorCorrection
from ..domain.backgrounds import get_background
from ..encoding.encoders import encoder_for_ext

_EC_MAP = {
    ErrorCorrection.L: ERROR_CORRECT_L,
    ErrorCorrection.M: ERROR_CORRECT_M,
    ErrorCorrection.Q: ERROR_CORRECT_Q,
    ErrorCorrection.H: ERROR_CORRECT_H,
}

class QRService:
    """Pure service (no UI) for generating/saving QR codes."""

    def build_qr(self, spec: QRSpec) -> qrcode.QRCode:
        qr = qrcode.QRCode(
            version=None,
            error_correction=_EC_MAP[spec.ec],
            box_size=spec.box_size,
            border=spec.border,
        )
        qr.add_data(spec.data)
        qr.make(fit=True)
        return qr

    def render_preview(self, spec: QRSpec) -> Tuple[Image.Image, qrcode.QRCode]:
        qr = self.build_qr(spec)
        bg = get_background(spec.background).back_color()
        img = qr.make_image(fill_color=spec.fill_color, back_color=bg)
        try:
            img = img.convert("RGBA")
        except Exception:
            img = img.convert("RGB")
        return img, qr

    def save(self, spec: QRSpec, path: str) -> None:
        qr = self.build_qr(spec)
        bg = get_background(spec.background).back_color()
        encoder_for_ext(path.split(".")[-1]).save(qr, path, spec.fill_color, bg)
