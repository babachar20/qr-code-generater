from typing import Callable, List

class EventBus:
    """Minimal observer bus for string messages."""
    def __init__(self) -> None:
        self._subs: List[Callable[[str], None]] = []
    def subscribe(self, fn: Callable[[str], None]) -> None:
        self._subs.append(fn)
    def publish(self, message: str) -> None:
        for fn in self._subs:
            fn(message)
