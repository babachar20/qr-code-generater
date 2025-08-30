# QR Studio — Text → QR (GUI)

A small, production-quality desktop app for generating QR codes from any text/URL.  
Preview instantly and save as **PNG** (white or transparent background) or **SVG**.

- Keyboard shortcuts: **Ctrl+G** Generate, **Ctrl+S** Save, **Esc** Clear
- Error correction: L / M / Q / H
- Backgrounds: White or Transparent (PNG)

---

## Folder Structure

text-to-qr/
├─ pyproject.toml
├─ README.md
├─ .gitignore
└─ src/
└─ qrstudio/
├─ init.py
├─ main.py # Allows python -m qrstudio
├─ config.py # App configuration (dataclass)
├─ events.py # Minimal event bus (Observer)
├─ commands.py # Generate/Save commands (Command pattern)
├─ domain/
│ ├─ init.py
│ ├─ spec.py # QRSpec + ErrorCorrection (domain model)
│ └─ backgrounds.py # Background strategies (Strategy)
├─ encoding/
│ ├─ init.py
│ └─ encoders.py # PNG/SVG encoders (Factory)
├─ services/
│ ├─ init.py
│ └─ qr_service.py # Pure service: build/render/save QR
└─ ui/
├─ init.py
└─ tk_app.py # Tkinter GUI (thin layer over commands)


**Why this architecture?**
- **Domain → Services → UI** layering keeps logic testable and UI swappable.
- **Command** pattern isolates actions; UI only wires callbacks.
- **Strategy** for background (white/transparent); **Factory** for encoders (PNG/SVG).
- **EventBus (Observer)** decouples logging/console from actions.

---

## Requirements

- **Python ≥ 3.9**
- Platforms: Windows, macOS, Linux (Tkinter included in python.org installers)
- Dependencies: `qrcode[pil]`, `Pillow` (installed via `pyproject.toml`)

---

## Quick Start

From the project root (the folder containing `pyproject.toml`):

### 1) Create & activate a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

macOS / Linux (bash/zsh)

python3 -m venv .venv
source .venv/bin/activate

2) Install in editable mode

python -m pip install --upgrade pip
python -m pip install -e .

3) Run the app

# Option A: module entry
python -m qrstudio

# Option B: console script defined in pyproject
qrstudio

The window opens. Enter your text/URL, choose White or Transparent (PNG), click Generate, then Save… to export PNG or SVG.
    Want to launch without an attached console on Windows?

    pythonw -m qrstudio

Usage Notes
    - Transparent PNG: choose “Transparent (PNG)” before generating. Saving as SVG always uses a transparent canvas (vector).
    - Error correction:
    - L (7%), M (15%), Q (25%), H (30%) — higher = more robust, larger codes.
    - Box size & border control pixel density and quiet zone.

Troubleshooting
    - ModuleNotFoundError: qrcode or PIL Re-run python -m pip install -e .
    - Tkinter errors (e.g., _tkinter / init.tcl)
      Install Python from python.org (includes Tcl/Tk).
      On Linux, you may need your distro’s Tk package (e.g., sudo apt-get install python3-tk).

Nothing happens on Save
Generate first, then use Save…. Ensure the path has .png or .svg.