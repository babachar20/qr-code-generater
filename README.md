# text-to-qr

Library QR generator

## Install (dev)
pip install -e .

## Library usage
```python
from text_to_qr import QRCodeSpec, QRCodeService
from text_to_qr.infrastructure.factory import default_encoders

svc = QRCodeService(encoders=default_encoders())
spec = QRCodeSpec(data="your-text-right-here", background="transparent", fmt="png")
png_bytes = svc.generate_bytes(spec)
