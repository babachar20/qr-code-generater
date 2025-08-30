import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from io import BytesIO

from ...domain.models import QRCodeSpec
from ...application.service import QRCodeService
from ...infrastructure.factory import default_encoders

class QRGui:
    def __init__(self, root: tk.Tk):
        self.svc = QRCodeService(encoders=default_encoders())
        self.root = root
        self.root.title("Text to QR")
        self._build_ui()
        self._img_bytes = b""
        self._photo = None

    def _build_ui(self):
        f = ttk.Frame(self.root, padding=10); f.pack(fill="both", expand=True)
        self.data = tk.StringVar()
        ttk.Label(f, text="Text/URL").grid(row=0, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.data, width=60).grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0,10))
        self.bg = tk.StringVar(value="white")
        ttk.Radiobutton(f, text="White", variable=self.bg, value="white").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(f, text="Transparent", variable=self.bg, value="transparent").grid(row=2, column=1, sticky="w")
        ttk.Button(f, text="Generate", command=self.on_generate).grid(row=2, column=3, sticky="e")
        self.preview = ttk.Label(f, relief="groove"); self.preview.grid(row=3, column=0, columnspan=4, sticky="nsew", pady=8)
        ttk.Button(f, text="Save…", command=self.on_save).grid(row=4, column=3, sticky="e")
        f.columnconfigure(0, weight=1); f.columnconfigure(1, weight=0); f.columnconfigure(2, weight=0); f.columnconfigure(3, weight=0)

    def on_generate(self):
        text = self.data.get().strip()
        if not text:
            messagebox.showwarning("No input", "Enter text/URL.")
            return
        spec = QRCodeSpec(data=text, background=self.bg.get(), fmt="png")
        self._img_bytes = self.svc.generate_bytes(spec)
        img = Image.open(BytesIO(self._img_bytes))
        img.thumbnail((360, 360))
        self._photo = ImageTk.PhotoImage(img)
        self.preview.configure(image=self._photo)

    def on_save(self):
        if not self._img_bytes:
            messagebox.showinfo("Nothing to save", "Generate first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG","*.png"),("All","*.*")])
        if not path: return
        with open(path, "wb") as f:
            f.write(self._img_bytes)
        messagebox.showinfo("Saved", path)

def main():
    root = tk.Tk()
    QRGui(root)
    root.mainloop()

if __name__ == "__main__":
    main()
