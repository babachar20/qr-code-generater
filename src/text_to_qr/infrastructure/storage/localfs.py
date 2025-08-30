from pathlib import Path
from ..domain.ports import StoragePort

class LocalFileStorage(StoragePort):
    def __init__(self, base_dir: str = "."):
        self.base = Path(base_dir)

    def save(self, data: bytes, filename: str) -> str:
        self.base.mkdir(parents=True, exist_ok=True)
        path = (self.base / filename).resolve()
        path.write_bytes(data)
        return str(path)
