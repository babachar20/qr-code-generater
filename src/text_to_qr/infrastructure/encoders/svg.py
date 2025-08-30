from io import BytesIO
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from qrcode.image.svg import SvgImage
from ...domain.models import QRCodeSpec
from ...domain.ports import Encoder

_ERR_MAP = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M, "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}

class SvgEncoder(Encoder):
    key = "svg"

    def encode(self, spec: QRCodeSpec) -> bytes:
        # Use SVG factory and omit background (typical for vector workflows)
        qr = qrcode.QRCode(
            version=None,
            error_correction=_ERR_MAP.get(spec.error, ERROR_CORRECT_M),
            box_size=spec.box_size,
            border=spec.border,
            image_factory=SvgImage,
        )
        qr.add_data(spec.data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=spec.fill_color, back_color=None)

        buf = BytesIO()
        img.save(buf)
        return buf.getvalue()
