#!/usr/bin/env python3
"""
QR Code Studio (single file)

Features
- Input any text/URL
- Preview QR
- Choose background: White or Transparent (PNG); SVG also supported
- Save dialog (PNG/SVG)
- Console log pane
- Keyboard shortcuts: Ctrl+G (Generate), Ctrl+S (Save), Esc (Clear)
"""

from __future__ import annotations

import io
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import dataclass
from typing import Callable, List, Optional, Protocol, Tuple, Union

# Import core external library (Pillow + qrcode)
from PIL import Image, ImageTk
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
from qrcode.image.svg import SvgImage


# --------------------------- App Config (Singleton) ---------------------------

class _Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class AppConfig(metaclass=_Singleton):
    title: str = "QR Code Studio"
    min_size: Tuple[int, int] = (760, 560)
    preview_max: int = 360  # px
    default_box_size: int = 10
    default_border: int = 4


# --------------------------- Observer (Event Bus) -----------------------------

class EventBus:
    def __init__(self) -> None:
        self._subs: List[Callable[[str], None]] = []
    def subscribe(self, fn: Callable[[str], None]) -> None:
        self._subs.append(fn)
    def publish(self, message: str) -> None:
        for fn in self._subs:
            fn(message)

# --------------------------- Strategy: Background ----------------------------

class BackgroundStrategy(Protocol):
    name: str
    def back_color(self) -> Union[str, Tuple[int, int, int, int]]: ...

class WhiteBackground:
    name = "White"
    def back_color(self):
        return "white"

class TransparentBackground:
    name = "Transparent"
    def back_color(self):
        return "transparent"

# --------------------------- Factory: Encoders --------------------------------

class ImageEncoder(Protocol):
    ext: str
    def save(self, qr: qrcode.QRCode, path: str, fill_color, back_color, box_size, border): ...

class PNGEncoder:
    ext = "png"
    def save(self, qr: qrcode.QRCode, path: str, fill_color, back_color, box_size, border):
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        # Ensure alpha if transparent requested
        if back_color == "transparent":
            img = img.convert("RGBA")
        img.save(path, format="PNG")

class SVGEncoder:
    ext = "svg"
    def save(self, qr: qrcode.QRCode, path: str, fill_color, back_color, box_size, border):
        # SVG generation uses a different image factory
        svg_qr = qrcode.QRCode(
            version=qr.version,
            error_correction=qr.error_correction,
            box_size=box_size,
            border=border,
            image_factory=SvgImage,
        )
        svg_qr.add_data(qr.data_list)
        svg_qr.make(fit=True)
        img = svg_qr.make_image(fill_color=fill_color, back_color=None)  # SVG typically no bg
        with open(path, "wb") as f:
            img.save(f)

class ImageEncoderFactory:
    @staticmethod
    def for_extension(ext: str) -> ImageEncoder:
        e = ext.lower().lstrip(".")
        if e == "png":
            return PNGEncoder()
        if e == "svg":
            return SVGEncoder()
        # default to PNG if unknown
        return PNGEncoder()

# --------------------------- Commands ----------------------------------------

class Command(Protocol):
    def execute(self) -> None: ...

@dataclass
class QRSpec:
    data: str
    error_level: str
    box_size: int
    border: int
    fill_color: str
    background: BackgroundStrategy

class GenerateQRCommand:
    def __init__(self, app: "QRApp", spec: QRSpec, bus: EventBus):
        self.app = app
        self.spec = spec
        self.bus = bus

    def execute(self) -> None:
        if not self.spec.data.strip():
            messagebox.showwarning("No input", "Please enter some text/URL to encode.")
            return
        err_map = {
            "L": ERROR_CORRECT_L,
            "M": ERROR_CORRECT_M,
            "Q": ERROR_CORRECT_Q,
            "H": ERROR_CORRECT_H,
        }
        qr = qrcode.QRCode(
            version=None,  # auto
            error_correction=err_map.get(self.spec.error_level, ERROR_CORRECT_M),
            box_size=self.spec.box_size,
            border=self.spec.border,
        )
        qr.add_data(self.spec.data)
        qr.make(fit=True)
        img = qr.make_image(fill_color=self.spec.fill_color, back_color=self.spec.background.back_color())

        # Make sure that it's displayable format for Tk (RGB or RGBA)
        try:
            img = img.convert("RGBA")
        except Exception:
            img = img.convert("RGB")

        self.app.set_preview(img, qr)
        self.bus.publish(f"Generated QR (EC={self.spec.error_level}, box={self.spec.box_size}, border={self.spec.border}, bg={self.spec.background.name}).")

class SaveQRCommand:
    def __init__(self, app: "QRApp", bus: EventBus):
        self.app = app
        self.bus = bus

    def execute(self) -> None:
        if self.app.current_qr is None:
            messagebox.showinfo("Nothing to save", "Generate a QR code first.")
            return
        # Open Dialig
        path = filedialog.asksaveasfilename(
            title="Save QR code",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("SVG Vector", "*.svg"), ("All Files", "*.*")],
        )
        if not path:
            return

        # Resolve encoder by extension
        encoder = ImageEncoderFactory.for_extension(path.split(".")[-1])
        try:
            # Rebuild QR from current spec to avoid display scaling issues
            spec = self.app.current_spec
            err_map = {
                "L": ERROR_CORRECT_L,
                "M": ERROR_CORRECT_M,
                "Q": ERROR_CORRECT_Q,
                "H": ERROR_CORRECT_H,
            }
            qr = qrcode.QRCode(
                version=None,
                error_correction=err_map.get(spec.error_level, ERROR_CORRECT_M),
                box_size=spec.box_size,
                border=spec.border,
            )
            qr.add_data(spec.data)
            qr.make(fit=True)
            encoder.save(
                qr=qr,
                path=path,
                fill_color=spec.fill_color,
                back_color=spec.background.back_color(),
                box_size=spec.box_size,
                border=spec.border,
            )
            self.bus.publish(f"Saved QR to {path}")
            messagebox.showinfo("Saved", f"QR code saved:\n{path}")
        except Exception as e:
            self.bus.publish(f"ERROR saving: {e}")
            messagebox.showerror("Save failed", f"Could not save file:\n{e}")

# --------------------------- GUI Application ---------------------------------

class GuiLogger:
    def __init__(self, text_widget: tk.Text):
        self.text_widget = text_widget
    def write(self, msg: str) -> None:
        self.text_widget.configure(state="normal")
        self.text_widget.insert("end", msg + "\n")
        self.text_widget.see("end")
        self.text_widget.configure(state="disabled")

class QRApp:
    def __init__(self, root: tk.Tk):
        self.cfg = AppConfig()
        self.root = root
        self.root.title(self.cfg.title)
        self.root.minsize(*self.cfg.min_size)

        # state
        self.current_image: Optional[Image.Image] = None
        self.current_qr: Optional[qrcode.QRCode] = None
        self.current_spec: Optional[QRSpec] = None
        self.preview_photo: Optional[ImageTk.PhotoImage] = None

        # event bus + console logger
        self.bus = EventBus()

        self._build_ui()
        self.bus.subscribe(self.console.write)

        self.bus.publish("Ready. Enter your text (e.g., https://github.com/your-username) and press Generate.")

        # shortcuts
        self.root.bind("<Control-g>", lambda e: self.on_generate())
        self.root.bind("<Control-s>", lambda e: self.on_save())
        self.root.bind("<Escape>", lambda e: self.on_clear())

    # ---------------- UI layout ----------------
    def _build_ui(self) -> None:
        # top frame: input + options
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        # TODO: Setting class Option
        # Input row
        ttk.Label(top, text="Text / URL").grid(row=0, column=0, sticky="w")
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(top, textvariable=self.input_var, width=80)
        self.input_entry.grid(row=1, column=0, columnspan=8, sticky="ew", pady=(4, 10))
        self.input_entry.focus()

        # Options: error correction, box, border, fill, background
        ttk.Label(top, text="Error correction").grid(row=2, column=0, sticky="w")
        self.ec_var = tk.StringVar(value="M")
        ec_menu = ttk.Combobox(top, textvariable=self.ec_var, values=["L","M","Q","H"], width=5, state="readonly")
        ec_menu.grid(row=3, column=0, sticky="w")

        ttk.Label(top, text="Box size").grid(row=2, column=1, sticky="w", padx=(10,0))
        self.box_var = tk.IntVar(value=self.cfg.default_box_size)
        box_spin = ttk.Spinbox(top, from_=2, to=40, textvariable=self.box_var, width=6)
        box_spin.grid(row=3, column=1, sticky="w", padx=(10,0))

        ttk.Label(top, text="Border").grid(row=2, column=2, sticky="w", padx=(10,0))
        self.border_var = tk.IntVar(value=self.cfg.default_border)
        border_spin = ttk.Spinbox(top, from_=1, to=16, textvariable=self.border_var, width=6)
        border_spin.grid(row=3, column=2, sticky="w", padx=(10,0))

        ttk.Label(top, text="Fill color").grid(row=2, column=3, sticky="w", padx=(10,0))
        self.fill_var = tk.StringVar(value="black")
        fill_entry = ttk.Entry(top, textvariable=self.fill_var, width=10)
        fill_entry.grid(row=3, column=3, sticky="w", padx=(10,0))

        ttk.Label(top, text="Background").grid(row=2, column=4, sticky="w", padx=(10,0))
        self.bg_var = tk.StringVar(value="white")
        bg_frame = ttk.Frame(top)
        bg_frame.grid(row=3, column=4, sticky="w", padx=(10,0))
        ttk.Radiobutton(bg_frame, text="White", value="white", variable=self.bg_var).pack(side="left")
        ttk.Radiobutton(bg_frame, text="Transparent (PNG)", value="transparent", variable=self.bg_var).pack(side="left")

        # Actions
        actions = ttk.Frame(top)
        actions.grid(row=3, column=7, sticky="e")
        gen_btn = ttk.Button(actions, text="Generate (Ctrl+G)", command=self.on_generate)
        gen_btn.pack(side="left", padx=4)
        save_btn = ttk.Button(actions, text="Save… (Ctrl+S)", command=self.on_save)
        save_btn.pack(side="left", padx=4)
        clear_btn = ttk.Button(actions, text="Clear (Esc)", command=self.on_clear)
        clear_btn.pack(side="left", padx=4)

        top.columnconfigure(0, weight=1)
        for c in range(1,7):
            top.columnconfigure(c, weight=0)

        # Middle: preview
        mid = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        mid.pack(fill="both", expand=True)
        left = ttk.Frame(mid)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Preview").pack(anchor="w")
        self.preview_label = ttk.Label(left, relief="groove")
        self.preview_label.pack(fill="both", expand=True, pady=(4, 0))

        # Right: console
        right = ttk.Frame(mid, width=280)
        right.pack(side="right", fill="y")
        ttk.Label(right, text="Console").pack(anchor="w")
        self.console_text = tk.Text(right, height=12, wrap="word", state="disabled")
        self.console_text.pack(fill="both", expand=True, pady=(4,0))
        self.console = GuiLogger(self.console_text)

        # Status
        self.status_var = tk.StringVar(value="Ready")
        status = ttk.Label(self.root, textvariable=self.status_var, anchor="w", relief="sunken")
        status.pack(fill="x", side="bottom")

    # --------------- Actions ----------------
    def _build_spec(self) -> QRSpec:
        bg_strategy = WhiteBackground() if self.bg_var.get() == "white" else TransparentBackground()
        return QRSpec(
            data=self.input_var.get(),
            error_level=self.ec_var.get(),
            box_size=int(self.box_var.get()),
            border=int(self.border_var.get()),
            fill_color=self.fill_var.get() or "black",
            background=bg_strategy,
        )

    def on_generate(self) -> None:
        spec = self._build_spec()
        cmd = GenerateQRCommand(self, spec, self.bus)
        cmd.execute()

    def on_save(self) -> None:
        cmd = SaveQRCommand(self, self.bus)
        cmd.execute()

    def on_clear(self) -> None:
        self.input_var.set("")
        self.set_preview(None, None)
        self.bus.publish("Cleared.")
        self.status_var.set("Cleared")

    # --------------- Preview handling ----------------
    def set_preview(self, img: Optional[Image.Image], qr: Optional[qrcode.QRCode]) -> None:
        self.current_image = img
        self.current_qr = qr
        self.current_spec = self._build_spec() if img is not None else None

        if img is None:
            self.preview_label.configure(image="", text="No preview")
            self.preview_photo = None
            return

        # Fit to preview area preserving aspect
        max_side = self.cfg.preview_max
        w, h = img.size
        scale = min(max_side / max(w, h), 1.0)
        new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        display_img = img.resize(new_size, Image.NEAREST)

        self.preview_photo = ImageTk.PhotoImage(display_img)
        self.preview_label.configure(image=self.preview_photo)
        self.preview_label.image = self.preview_photo  # prevent GC
        self.status_var.set(f"Preview {new_size[0]}×{new_size[1]}")

# --------------------------- Entrypoint --------------------------------------

def main():
    root = tk.Tk()

    # Native-like theming for ttk if available
    try:
        if sys.platform == "darwin":
            root.tk.call("tk", "scaling", 1.2)
        style = ttk.Style(root)
        # Use default OS theme; fallback to 'clam'
        if style.theme_use() not in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    app = QRApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
