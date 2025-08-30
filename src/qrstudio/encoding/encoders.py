from __future__ import annotations
from typing import Protocol
import qrcode
from qrcode.image.svg import SvgImage

class ImageEncoder(Protocol):
    ext: str
    def save(self, qr: qrcode.QRCode, path: str, fill_color: str, back_color: str): ...

class PNGEncoder:
    ext = "png"
    def save(self, qr, path, fill_color, back_color):
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        if back_color == "transparent":
            img = img.convert("RGBA")
        img.save(path, format="PNG")

class SVGEncoder:
    ext = "svg"
    def save(self, qr, path, fill_color, back_color):
        # Recreate with SVG image factory (keeps vector crisp, no fixed bg)
        svg_qr = qrcode.QRCode(
            version=qr.version, error_correction=qr.error_correction,
            box_size=qr.box_size, border=qr.border, image_factory=SvgImage
        )
        # qr.data_list is prepared segments
        svg_qr.add_data(qr.data_list)
        svg_qr.make(fit=True)
        with open(path, "wb") as f:
            svg_qr.make_image(fill_color=fill_color, back_color=None).save(f)

def encoder_for_ext(ext: str) -> ImageEncoder:
    e = ext.lower().lstrip(".")
    return PNGEncoder() if e not in ("svg",) else SVGEncoder()
