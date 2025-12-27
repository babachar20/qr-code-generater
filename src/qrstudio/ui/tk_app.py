from __future__ import annotations
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from customtkinter import CTkImage

from typing import Optional
from ..config import AppConfig
from ..events import EventBus
from ..domain.spec import QRSpec, ErrorCorrection
from ..services.qr_service import QRService
from ..commands import GenerateQRCommand, SaveQRCommand

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class _GuiLogger:
    def __init__(self, text: ctk.CTkTextbox) -> None:
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
        self.photo = CTkImage(light_image=resized, dark_image=resized, size=resized.size)
        self.app.preview.configure(image=self.photo)
        # self.app.preview.image = self.photo

        self.app.status.set(f"Preview {resized.size[0]}×{resized.size[1]}")

class App:
    def __init__(self, root: ctk.CTk):
        self.cfg = AppConfig()
        self.root = root
        self.root.title(self.cfg.title)
        self.root.minsize(self.cfg.min_width, self.cfg.min_height)
        self.bus = EventBus()
        self.service = QRService()
        self._current_img = None
        self._current_qr = None

        #workaround for removing image when cleared, used in on_clear()
        self.blank_image = CTkImage(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))

        self._build_ui()
        self.preview_out = _Preview(self)
        self.logger.write("Ready. Enter text/URL and press Generate.")

        # Shortcuts
        self.root.bind("<Control-g>", lambda e: self.on_generate())
        self.root.bind("<Control-s>", lambda e: self.on_save())
        self.root.bind("<Escape>", lambda e: self.on_clear())

    # UI
    def _build_ui(self):
        top = ctk.CTkFrame(self.root)
        top.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(top, text="Text / URL").grid(row=0, column=0, sticky="w")
        self.var_text = ctk.StringVar()
        self.input = ctk.CTkEntry(top, textvariable=self.var_text, width=80)
        self.input.grid(row=1, column=0, columnspan=8, sticky="ew", pady=(4, 10))
        self.input.focus()

        self.var_ec = ctk.StringVar(value="M")
        ctk.CTkLabel(top, text="Error correction").grid(row=2, column=0, sticky="w")
        ctk.CTkComboBox(top, variable=self.var_ec, values=["L","M","Q","H"], width=80, state="readonly")\
            .grid(row=3, column=0, sticky="w")

        self.var_box = ctk.StringVar(value=self.cfg.default_box_size) #used StringVar, as IntVar was throwing error whenever the value was cleared and re-entered in the entry box
        ctk.CTkLabel(top, text="Box size").grid(row=2, column=1, sticky="w", padx=10)
        ctk.CTkEntry(top, textvariable=self.var_box, width=60)\
            .grid(row=3, column=1, sticky="w", padx=10)

        self.var_border = ctk.StringVar(value=self.cfg.default_border) #used StringVar, as IntVar was throwing error whenever the value was cleared and re-entered in the entry box
        ctk.CTkLabel(top, text="Border").grid(row=2, column=2, sticky="w", padx=10)
        ctk.CTkEntry(top, textvariable=self.var_border, width=60)\
            .grid(row=3, column=2, sticky="w", padx=10)

        self.var_fill = ctk.StringVar(value=self.cfg.default_fill)
        ctk.CTkLabel(top, text="Fill color").grid(row=2, column=3, sticky="w", padx=10)
        ctk.CTkEntry(top, textvariable=self.var_fill, width=80)\
            .grid(row=3, column=3, sticky="w", padx=10)

        self.var_bg = ctk.StringVar(value="white")
        ctk.CTkLabel(top, text="Background").grid(row=2, column=4, sticky="w", padx=10)
        bg_frame = ctk.CTkFrame(top)
        bg_frame.grid(row=3, column=4, sticky="w", padx=10)
        ctk.CTkRadioButton(bg_frame, text="White", variable=self.var_bg, value="white").pack(side="left")
        ctk.CTkRadioButton(bg_frame, text="Transparent (PNG)", variable=self.var_bg, value="transparent").pack(side="left")

        actions = ctk.CTkFrame(top)
        actions.grid(row=3, column=5, sticky="e")
        ctk.CTkButton(actions, text="Generate (Ctrl+G)", command=self.on_generate).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Save (Ctrl+S)", command=self.on_save).pack(side="left", padx=4)
        ctk.CTkButton(actions, text="Clear (Esc)", command=self.on_clear).pack(side="left", padx=4)

        mid = ctk.CTkFrame(self.root)
        mid.pack(fill="both", expand=True, padx=10, pady=(0,10))

        left = ctk.CTkFrame(mid)
        left.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(left, text="Preview").pack(anchor="w")
        self.preview = ctk.CTkLabel(left, text="No preview", fg_color="gray20", corner_radius=6)
        self.preview.pack(fill="both", expand=True, pady=4)

        right = ctk.CTkFrame(mid, width=280)
        right.pack(side="right", fill="y")
        ctk.CTkLabel(right, text="Console").pack(anchor="w")
        self.console = ctk.CTkTextbox(right, height=200)
        self.console.pack(fill="both", expand=True, pady=4)
        self.logger = _GuiLogger(self.console)
        self.bus.subscribe(self.logger.write)

        self.status = ctk.StringVar(value="Ready")
        ctk.CTkLabel(self.root, textvariable=self.status, anchor="w").pack(fill="x", side="bottom")

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
            self.preview.configure(text="")
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
                filetypes=[("PNG Image", "*.png"), ("SVG Vector", "*.svg"), ("All Files", "*.*")],
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
        self.preview.configure(image=self.blank_image, text="No preview")
        self._current_img = None
        self._current_qr = None
        self.bus.publish("Cleared.")
        self.status.set("Cleared")

def main():
    root = ctk.CTk()
    # Simple scaling tweak for macOS HiDPI
    try:
        if sys.platform == "darwin":
            root.tk.call("tk", "scaling", 1.2)
    except Exception:
        pass
    App(root)
    root.mainloop()
