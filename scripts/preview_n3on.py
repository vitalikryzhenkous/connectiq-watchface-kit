"""Pixel-accurate PNG preview of the N3on Terminal face (3 themes side by side).

Usage: python3 scripts/preview_n3on.py <project_dir> <out.png>

It re-implements the N3onView.mc layout in Python using the project's real
BMFont files, so you can iterate on layout without the simulator.
For a new face: copy this file and mirror that face's onUpdate() drawing calls.
"""
import re
import sys
from PIL import Image, ImageDraw

ROOT = sys.argv[1]
OUT = sys.argv[2]
FD = ROOT + "/resources/fonts/"

PALS = [
    [0x00FFFF, 0xFF00AA, 0xFFFF00, 0x555555, 0x00FF55, 0xAA00AA, 0x000055],
    [0xFFAA00, 0xFF5500, 0xFFFF55, 0x555555, 0xFFAA00, 0xAA5500, 0x550000],
    [0x00FF00, 0x00AA55, 0xAAFF55, 0x555555, 0x55FF55, 0x00AA00, 0x005500],
]
P, A, H, DM, OK, BT, SC = range(7)


def rgb(c):
    return ((c >> 16) & 255, (c >> 8) & 255, c & 255)


class Font:
    def __init__(self, name):
        txt = open(FD + name + ".fnt").read()
        self.atlas = Image.open(FD + name + ".png").split()[3]
        self.chars = {}
        for m in re.finditer(r"char id=(\d+) x=(\d+) y=(\d+) width=(\d+) height=(\d+) xoffset=(-?\d+) yoffset=(-?\d+) xadvance=(\d+)", txt):
            v = list(map(int, m.groups()))
            self.chars[v[0]] = v[1:]

    def width(self, s):
        return sum(self.chars[ord(c)][6] for c in s)

    def draw(self, img, x, y, s, color, just="l"):
        if just == "c":
            x -= self.width(s) // 2
        for c in s:
            gx, gy, w, h, xo, yo, adv = self.chars[ord(c)]
            if w and h:
                mask = self.atlas.crop((gx, gy, gx + w, gy + h))
                img.paste(Image.new("RGB", (w, h), rgb(color)), (x + xo, y + yo), mask)
            x += adv
        return x


small, big = Font("term_small"), Font("term_big")


def bot(d, x, y, pal, mood, img):
    dim = mood in ("low", "night")
    r = lambda x0, y0, w, h, c: d.rectangle([x0, y0, x0 + w - 1, y0 + h - 1], fill=rgb(c))
    r(x + 16, y, 6, 6, pal[DM] if dim else pal[H]); r(x + 18, y + 6, 2, 10, pal[DM] if dim else pal[H])
    d.rectangle([x, y + 16, x + 37, y + 43], outline=rgb(pal[A]), width=2)
    r(x + 5, y + 22, 28, 12, pal[DM] if mood == "night" else pal[P])
    if mood == "happy":
        for ex in (x + 10, x + 23):
            r(ex + 1, y + 25, 3, 2, 0); r(ex, y + 27, 2, 3, 0); r(ex + 3, y + 27, 2, 3, 0)
    elif mood == "night":
        r(x + 10, y + 28, 5, 2, 0); r(x + 23, y + 28, 5, 2, 0)
    else:
        r(x + 10, y + 25, 5, 6, 0); r(x + 23, y + 25, 5, 6, 0)
    if mood == "happy":
        r(x + 8, y + 37, 22, 2, pal[A]); r(x + 10, y + 39, 18, 2, pal[A])
    elif dim:
        r(x + 14, y + 38, 10, 2, pal[DM])
    else:
        r(x + 11, y + 37, 16, 3, pal[A])
    r(x + 6, y + 48, 26, 14, pal[BT])
    if mood == "happy":
        r(x - 2, y + 42, 3, 10, pal[P]); r(x + 37, y + 42, 3, 10, pal[P]); r(x + 1, y + 49, 5, 3, pal[P]); r(x + 32, y + 49, 5, 3, pal[P])
    else:
        r(x - 2, y + 50, 8, 3, pal[P]); r(x + 32, y + 50, 8, 3, pal[P])
    r(x + 8, y + 63, 6, 5, pal[P]); r(x + 24, y + 63, 6, 5, pal[P])
    if mood == "night":
        small.draw(img, x + 27, y - 4, "z", pal[DM])


def face(pal, time="21:24", mood="night", wx=("+8°", "cloudy")):
    img = Image.new("RGB", (240, 240), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(6, 240, 8):
        d.line([0, y, 240, y], fill=rgb(pal[SC]))
    small.draw(img, 120, 18, "[ sys://n3on-0x1 ]", pal[A], "c")
    d.line([42, 37, 198, 37], fill=rgb(pal[A]))
    small.draw(img, 26, 42, "> uptime", pal[P])
    big.draw(img, 21, 59, time, pal[A])
    d.rectangle([8, 90, 25, 92], fill=rgb(pal[A]))
    d.rectangle([140, 70, 153, 71], fill=rgb(pal[H]))
    big.draw(img, 24, 57, time, pal[P])
    small.draw(img, 24, 114, "> mon 26.10.26", pal[H])
    x = small.draw(img, 16, 134, "> wx ", pal[P])
    x = small.draw(img, x, 134, wx[0], pal[A])
    x = small.draw(img, x, 134, " " + wx[1], pal[P])
    cx, cy = x + 8, 136
    d.rectangle([cx + 4, cy + 2, cx + 9, cy + 5], fill=(170, 170, 170))
    d.rectangle([cx + 9, cy, cx + 14, cy + 5], fill=(170, 170, 170))
    d.rectangle([cx, cy + 5, cx + 17, cy + 9], fill=(170, 170, 170))
    x = small.draw(img, 12, 154, "> sun ", pal[P])
    x = small.draw(img, x, 154, "▲06:41", pal[H])
    small.draw(img, x, 154, " ▼16:22", pal[A])
    x = small.draw(img, 20, 174, "> stp ", pal[P])
    x = small.draw(img, x, 174, "8.4k", pal[A])
    x = small.draw(img, x, 174, "  bat ", pal[P])
    small.draw(img, x, 174, "78%", pal[H])
    d.line([46, 196, 194, 196], fill=rgb(pal[A]))
    d.ellipse([74, 206, 82, 214], fill=rgb(pal[OK]))
    x = small.draw(img, 88, 201, "online", pal[OK])
    small.draw(img, x, 201, "_", pal[H])
    bot(d, 178, 46, pal, mood, img)
    # round display mask + bezel
    mask = Image.new("L", (240, 240), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 239, 239], fill=255)
    out = Image.new("RGB", (260, 260), (26, 26, 26))
    out.paste(img, (10, 10), mask)
    return out.resize((520, 520), Image.NEAREST)


tiles = [face(PALS[0], mood="night"), face(PALS[1], "07:58", "normal"), face(PALS[2], "18:30", "happy")]
sheet = Image.new("RGB", (520 * 3 + 40, 560), (12, 12, 12))
for i, t in enumerate(tiles):
    sheet.paste(t, (10 + i * 530, 20))
sheet.save(OUT)
print("saved", OUT)
