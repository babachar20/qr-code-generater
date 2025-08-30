from dataclasses import dataclass
from typing import Protocol, Callable, Optional
from .events import EventBus
from .domain.spec import QRSpec
from .services.qr_service import QRService

class PreviewOut(Protocol):
    def show(self, pil_image, qr_obj) -> None: ...

@dataclass
class GenerateQRCommand:
    spec: QRSpec
    service: QRService
    preview: PreviewOut
    bus: EventBus

    def execute(self) -> None:
        if not self.spec.data.strip():
            self.bus.publish("No input: please enter text/URL.")
            raise ValueError("Empty data")
        img, qr = self.service.render_preview(self.spec)
        self.preview.show(img, qr)
        self.bus.publish(
            f"Generated: EC={self.spec.ec}, box={self.spec.box_size}, "
            f"border={self.spec.border}, bg={self.spec.background}"
        )

@dataclass
class SaveQRCommand:
    spec_provider: Callable[[], QRSpec]
    path_provider: Callable[[], Optional[str]]
    service: QRService
    bus: EventBus

    def execute(self) -> None:
        path = self.path_provider()
        if not path:
            return
        self.service.save(self.spec_provider(), path)
        self.bus.publish(f"Saved to {path}")
