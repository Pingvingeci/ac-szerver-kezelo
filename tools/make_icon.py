"""A program ikonjának (assets/icon.ico) elkészítése: zászló gradiens háttéren."""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
S = 256

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
# Piros-narancs átmenet lekerekített négyzetben
grad = Image.new("RGBA", (S, S))
for y in range(S):
    for x in range(S):
        t = (x + y) / (2 * S)
        grad.putpixel((x, y), (int(255), int(61 + (138 - 61) * t), int(90 + (61 - 90) * t), 255))
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle((8, 8, S - 8, S - 8), radius=60, fill=255)
img.paste(grad, (0, 0), mask)

# Kockás zászló
d = ImageDraw.Draw(img)
pole_x, top = 70, 58
d.rounded_rectangle((pole_x - 8, top, pole_x + 4, 206), radius=6, fill="white")
cols, rows, cell = 4, 3, 26
for r in range(rows):
    for c in range(cols):
        x0 = pole_x + 4 + c * cell
        y0 = top + r * cell + (4 if c % 2 else 0)
        color = (255, 255, 255, 255) if (r + c) % 2 == 0 else (30, 30, 36, 255)
        d.rectangle((x0, y0, x0 + cell, y0 + cell), fill=color)

out = ROOT / "assets" / "icon.ico"
out.parent.mkdir(exist_ok=True)
img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("kész:", out)
