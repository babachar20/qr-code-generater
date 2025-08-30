from text_to_qr.domain.models import QRCodeSpec
from text_to_qr.application.service import QRCodeService
from text_to_qr.infrastructure.factory import default_encoders

def test_png_bytes():
    svc = QRCodeService(encoders=default_encoders())
    data = svc.generate_bytes(QRCodeSpec(data="hello", fmt="png", background="transparent"))
    assert isinstance(data, (bytes, bytearray)) and len(data) > 100

def test_svg_bytes():
    svc = QRCodeService(encoders=default_encoders())
    data = svc.generate_bytes(QRCodeSpec(data="hello", fmt="svg"))
    assert data.startswith(b"<?xml") or b"<svg" in data[:200]
