"""生成应用使用的统一 64x64 透明 PNG 图标。"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "icon"
COLOR = (48, 93, 80, 255)
GOLD = (230, 182, 95, 255)

def make(name, painter):
    image = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
    painter(ImageDraw.Draw(image))
    image.save(OUT / name, "PNG", optimize=True)

def book(d):
    d.polygon([(9,20),(20,18),(31,23),(31,48),(20,43),(9,45)], outline=COLOR, width=3)
    d.polygon([(31,23),(43,18),(54,20),(54,45),(43,43),(31,48)], outline=COLOR, width=3)
    d.line((15,28,25,30), fill=COLOR, width=2); d.line((15,34,25,36), fill=COLOR, width=2)
    d.polygon([(33,37),(38,27),(50,10),(55,14),(42,32)], fill=GOLD, outline=COLOR)

def edit(d):
    d.line((25,15,39,15), fill=COLOR, width=3); d.line((32,15,32,49), fill=COLOR, width=3); d.line((25,49,39,49), fill=COLOR, width=3)

def display(d):
    d.rectangle((13,16,51,43), outline=COLOR, width=3); d.line((13,24,51,24), fill=COLOR, width=2); d.line((32,43,32,50), fill=COLOR, width=3); d.line((23,50,41,50), fill=COLOR, width=3)

def generate(d):
    d.polygon([(18,10),(50,10),(50,54),(14,54),(14,18)], outline=COLOR, width=3); d.line((18,10,18,18,14,18), fill=COLOR, width=3); d.line((21,30,37,30), fill=COLOR, width=2); d.line((21,36,38,36), fill=COLOR, width=2)

def power(d):
    d.arc((15,16,49,50), 135, 405, fill=COLOR, width=3); d.line((32,11,32,32), fill=COLOR, width=3)

def power_off(d):
    power(d); d.line((13,53,51,11), fill=COLOR, width=3)

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for filename, painter in {"icon.png":book,"input.png":edit,"display.png":display,"generate.png":generate,"activate.png":power,"deactivate.png":power_off}.items(): make(filename, painter)
