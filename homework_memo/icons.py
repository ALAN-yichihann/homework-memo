"""加载统一尺寸的透明 PNG 图标。"""
from pathlib import Path
import sys
import tkinter as tk

FILES = {"book":"icon.png", "edit":"input.png", "display":"display.png", "export":"generate.png", "power":"activate.png", "power-off":"deactivate.png"}

def draw(canvas, kind: str, color: str = "#305d50") -> None:
    canvas.delete("all")
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    path = base / "icon" / FILES[kind]
    if path.exists():
        image = canvas._icon_image = tk.PhotoImage(file=str(path))
        canvas.create_image(int(canvas.cget("width")) // 2, int(canvas.cget("height")) // 2, image=image)
