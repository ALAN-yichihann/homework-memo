"""用 Canvas 绘制清晰的简约图标，不加载图标库。"""


def draw(canvas, kind: str, color: str = "#305d50") -> None:
    canvas.delete("all")
    size = int(canvas.cget("width"))
    scale = size / 64

    def line(*points, width=2.6, **kwargs):
        return canvas.create_line(*(p * scale for p in points), fill=color,
                                  width=width * scale, capstyle="round", joinstyle="round", **kwargs)

    def polygon(*points, fill="", width=2.6):
        return canvas.create_polygon(*(p * scale for p in points), fill=fill,
                                     outline=color, width=width * scale, joinstyle="round")

    if kind == "book":
        polygon(9, 20, 20, 18, 31, 23, 31, 48, 20, 43, 9, 45)
        polygon(31, 23, 43, 18, 54, 20, 54, 45, 43, 43, 31, 48)
        line(15, 28, 25, 30, width=1.5)
        line(15, 34, 25, 36, width=1.5)
        polygon(33, 37, 38, 27, 50, 10, 55, 14, 42, 32, fill="#e6b65f")
    elif kind == "edit":
        line(25, 15, 39, 15)
        line(32, 15, 32, 49)
        line(25, 49, 39, 49)
    elif kind == "display":
        polygon(13, 16, 51, 16, 51, 43, 13, 43)
        line(13, 24, 51, 24, width=1.5)
        line(32, 43, 32, 50)
        line(23, 50, 41, 50)
    elif kind == "export":
        polygon(23, 10, 46, 10, 46, 33, 52, 33, 52, 51, 12, 51, 12, 21, 23, 10)
        line(23, 10, 23, 21, 12, 21)
        line(21, 30, 37, 30, width=1.5)
        line(21, 36, 32, 36, width=1.5)
        line(33, 52, 32, 47, 36, 42, 43, 41, width=1.2, smooth=True)
        line(36, 42, 43, 41, 54, 41, width=3.5, smooth=True)
        line(48, 35, 55, 41, 48, 47, width=3.5)
    elif kind in ("power", "power-off"):
        canvas.create_arc(15 * scale, 16 * scale, 49 * scale, 50 * scale,
                          start=135, extent=270, style="arc", outline=color, width=2.6 * scale)
        line(32, 11, 32, 32)
        if kind == "power-off":
            line(13, 53, 51, 11)

