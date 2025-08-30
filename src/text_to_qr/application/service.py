from dataclasses import dataclass
from typing import Dict, Optional
from ..domain.models import QRCodeSpec
from ..domain.ports import Encoder, StoragePort
from ..domain.errors import UnsupportedFormatError

@dataclass(frozen=True)
class QRCodeServiceConfig:
    default_filename: str = "qr"

class QRCodeService:
    """
    Application service: orchestrates format strategy and optional storage.
    Returns bytes by default (library-first), so UIs decide what to do.
    """
    def __init__(self, encoders: Dict[str, Encoder], storage: Optional[StoragePort] = None,
                 config: QRCodeServiceConfig = QRCodeServiceConfig()):
        self._encoders = encoders
        self._storage = storage
        self._config = config

    def generate_bytes(self, spec: QRCodeSpec) -> bytes:
        encoder = self._encoders.get(spec.fmt.lower())
        if not encoder:
            raise UnsupportedFormatError(f"Unsupported format: {spec.fmt}")
        return encoder.encode(spec)

    def generate_and_save(self, spec: QRCodeSpec, filename: Optional[str] = None) -> str:
        data = self.generate_bytes(spec)
        if not self._storage:
            raise RuntimeError("No storage configured on QRCodeService.")
        fname = filename or f"{self._config.default_filename}.{spec.fmt}"
        return self._storage.save(data, fname)
