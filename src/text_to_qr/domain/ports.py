from typing import Protocol
from .models import QRCodeSpec

class Encoder(Protocol):
    """Strategy for encoding a QR into bytes in a specific format."""
    key: str  # "png" or "svg"
    def encode(self, spec: QRCodeSpec) -> bytes: ...

class StoragePort(Protocol):
    """Abstracts output persistence (disk, S3, DB, …)."""
    def save(self, data: bytes, filename: str) -> str: ...
