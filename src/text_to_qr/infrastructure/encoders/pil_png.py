from io import BytesIO
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from PIL import Image
from ...domain.models import QRCodeSpec
from ...domain.ports import Encoder

_ERR_MAP = {"L": ERROR_CORRECT_L, "M": ERROR_CORRECT_M, "Q": ERROR_CORRECT_Q, "H": ERROR_CORRECT_H}

class PngEncoder(Encoder):
    key = "png"

    def encode(self, spec: QRCodeSpec) -> bytes:
        qr = qrcode.QRCode(
            version=None,
            error_correction=_ERR_MAP.get(spec.error, ERROR_CORRECT_M),
            box_size=spec.box_size,
            border=spec.border,
        )
        qr.add_data(spec.data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=spec.fill_color,
                            back_color="transparent" if spec.background == "transparent" else "white")
        # Ensure alpha when transparent
        img = img.convert("RGBA") if spec.background == "transparent" else img.convert("RGB")

        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
