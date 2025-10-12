from __future__ import annotations
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from typing import Optional
from ..config import AppConfig
from ..events import EventBus
from ..domain.spec import QRSpec, ErrorCorrection
from ..services.qr_service import QRService
from ..commands import GenerateQRCommand, SaveQRCommand

class _GuiLogger:
    def __init__(self, text: tk.Text) -> None:
        self._t = text
    def write(self, msg: str) -> None:
        self._t.configure(state="normal")
        self._t.insert("end", msg + "\n")
        self._t.see("end")
        self._t.configure(state="disabled")

class _Preview( object ):
    def __init__(self, app: "App"):
        self.app = app
        self.photo: Optional[ImageTk.PhotoImage] = None
    def show(self, pil_image: Image.Image, qr_obj) -> None:
        self.app._current_qr = qr_obj
        self.app._current_img = pil_image
        # Fit for preview
        max_side = self.app.cfg.preview_max
        w, h = pil_image.size
        scale = min(max_side / max(w, h), 1.0)
        resized = pil_image.resize((max(1,int(w*scale)), max(1,int(h*scale))), Image.NEAREST)
        self.photo = ImageTk.PhotoImage(resized)
        self.app.preview.configure(image=self.photo)
        self.app.preview.image = self.photo
        self.app.status.set(f"Preview {resized.size[0]}×{resized.size[1]}")

class App:
    def __init__(self, root: tk.Tk):
        self.cfg = AppConfig()
        self.root = root
        self.root.title(self.cfg.title)
        self.root.minsize(self.cfg.min_width, self.cfg.min_height)
        self.bus = EventBus()
        self.service = QRService()
        self._current_img = None
        self._current_qr = None

        self._build_ui()
        self.preview_out = _Preview(self)
        self.logger.write("Ready. Enter text/URL and press Generate.")

        # Shortcuts
        self.root.bind("<Control-g>", lambda e: self.on_generate())
        self.root.bind("<Control-s>", lambda e: self.on_save())
        self.root.bind("<Escape>", lambda e: self.on_clear())

    # UI
    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Text / URL").grid(row=0, column=0, sticky="w")
        self.var_text = tk.StringVar()
        self.input = ttk.Entry(top, textvariable=self.var_text, width=80)
        self.input.grid(row=1, column=0, columnspan=8, sticky="ew", pady=(4, 10))
        self.input.focus()

        ttk.Label(top, text="Error correction").grid(row=2, column=0, sticky="w")
        self.var_ec = tk.StringVar(value="M")
        ttk.Combobox(top, textvariable=self.var_ec, values=["L","M","Q","H"], width=5,
                     state="readonly").grid(row=3, column=0, sticky="w")

        ttk.Label(top, text="Box size").grid(row=2, column=1, sticky="w", padx=(10,0))
        self.var_box = tk.IntVar(value=self.cfg.default_box_size)
        ttk.Spinbox(top, from_=2, to=40, textvariable=self.var_box, width=6)\
            .grid(row=3, column=1, sticky="w", padx=(10,0))

        ttk.Label(top, text="Border").grid(row=2, column=2, sticky="w", padx=(10,0))
        self.var_border = tk.IntVar(value=self.cfg.default_border)
        ttk.Spinbox(top, from_=1, to=16, textvariable=self.var_border, width=6)\
            .grid(row=3, column=2, sticky="w", padx=(10,0))

        ttk.Label(top, text="Fill color").grid(row=2, column=3, sticky="w", padx=(10,0))
        self.var_fill = tk.StringVar(value=self.cfg.default_fill)
        ttk.Entry(top, textvariable=self.var_fill, width=10)\
            .grid(row=3, column=3, sticky="w", padx=(10,0))

        ttk.Label(top, text="Background").grid(row=2, column=4, sticky="w", padx=(10,0))
        self.var_bg = tk.StringVar(value="white")
        bg_frame = ttk.Frame(top); bg_frame.grid(row=3, column=4, sticky="w", padx=(10,0))
        ttk.Radiobutton(bg_frame, text="White", value="white", variable=self.var_bg).pack(side="left")
        ttk.Radiobutton(bg_frame, text="Transparent (PNG)", value="transparent", variable=self.var_bg).pack(side="left")

        actions = ttk.Frame(top); actions.grid(row=3, column=7, sticky="e")
        ttk.Button(actions, text="Generate (Ctrl+G)", command=self.on_generate).pack(side="left", padx=4)
        ttk.Button(actions, text="Save… (Ctrl+S)", command=self.on_save).pack(side="left", padx=4)
        ttk.Button(actions, text="Clear (Esc)", command=self.on_clear).pack(side="left", padx=4)

        top.columnconfigure(0, weight=1)

        mid = ttk.Frame(self.root, padding=(10,0,10,10)); mid.pack(fill="both", expand=True)
        left = ttk.Frame(mid); left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Preview").pack(anchor="w")
        self.preview = ttk.Label(left, relief="groove"); self.preview.pack(fill="both", expand=True, pady=(4,0))

        right = ttk.Frame(mid, width=280); right.pack(side="right", fill="y")
        ttk.Label(right, text="Console").pack(anchor="w")
        self.console = tk.Text(right, height=12, wrap="word", state="disabled")
        self.console.pack(fill="both", expand=True, pady=(4,0))
        self.logger = _GuiLogger(self.console)
        self.bus.subscribe(self.logger.write)
        self.status = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.status, anchor="w", relief="sunken").pack(fill="x", side="bottom")

    # Helpers
    def _spec(self) -> QRSpec:
        return QRSpec(
            data=self.var_text.get(),
            ec=ErrorCorrection(self.var_ec.get()),
            box_size=int(self.var_box.get()),
            border=int(self.var_border.get()),
            fill_color=self.var_fill.get() or "black",
            background=self.var_bg.get(),
        )

    # Actions
    def on_generate(self):
        cmd = GenerateQRCommand(self._spec(), self.service, self.preview_out, self.bus)
        try:
            cmd.execute()
        except ValueError:
            messagebox.showwarning("No input", "Please enter some text/URL to encode.")

    def on_save(self):
        if self._current_img is None:
            messagebox.showinfo("Nothing to save", "Generate a QR code first.")
            return
        def _ask_path():
            return filedialog.asksaveasfilename(
                title="Save QR code",
                defaultextension=".png",
                filetypes=[
                    ("PNG Image", "*.png"),
                    ("JPEG Image", "*.jpg;*.jpeg"),
                    ("SVG Vector", "*.svg"),
                    ("All Files", "*.*")
                ],
            )
        cmd = SaveQRCommand(self._spec, _ask_path, self.service, self.bus)
        try:
            cmd.execute()
            messagebox.showinfo("Saved", "QR code saved successfully.")
        except Exception as e:
            self.bus.publish(f"ERROR saving: {e}")
            messagebox.showerror("Save failed", str(e))

    def on_clear(self):
        self.var_text.set("")
        self.preview.configure(image="", text="No preview")
        self._current_img = None
        self._current_qr = None
        self.bus.publish("Cleared.")
        self.status.set("Cleared")

def main():
    root = tk.Tk()
    # Simple scaling tweak for macOS HiDPI
    try:
        if sys.platform == "darwin":
            root.tk.call("tk", "scaling", 1.2)
    except Exception:
        pass
    App(root)
    root.mainloop()
