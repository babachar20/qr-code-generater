from typing import Protocol, Union, Tuple

class BackgroundStrategy(Protocol):
    name: str
    def back_color(self) -> Union[str, Tuple[int,int,int,int]]: ...

class WhiteBackground:
    name = "White"
    def back_color(self): return "white"

class TransparentBackground:
    name = "Transparent"
    def back_color(self): return "transparent"

def get_background(name: str) -> BackgroundStrategy:
    return TransparentBackground() if str(name).lower().startswith("trans") else WhiteBackground()
