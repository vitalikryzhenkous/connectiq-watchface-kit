"""Pixel-accurate PNG preview of the N3on Terminal face (themes, emotions, holidays, phrases).

Usage: python3 scripts/preview_n3on.py <project_dir> <out.png> [--frames <dir>] [--moods <sheet.png>] [--holidays <sheet.png>] [--phrases <sheet.png>]

--frames also writes store screenshots: native 240x240 PNGs (like simulator
screenshots) plus 2x upscaled round versions.

It re-implements the N3onView.mc layout in Python using the project's real
BMFont files, so you can iterate on layout without the simulator.
For a new face: copy this file and mirror that face's onUpdate() drawing calls.
"""
import re
import sys
from PIL import Image, ImageDraw

ROOT = sys.argv[1]
OUT = sys.argv[2]
FRAMES = sys.argv[sys.argv.index("--frames") + 1] if "--frames" in sys.argv else None
FD = ROOT + "/resources/fonts/"

# mirror of source/Theme.mc (index 3 = High contrast)
PALS = [
    [0x00FFFF, 0xFF55AA, 0xFFFF00, 0x555555, 0x00FF55, 0xAA00AA, 0x000055, 0xAAAAAA],
    [0xFFAA00, 0xFF5500, 0xFFFF55, 0x555555, 0xFFAA00, 0xAA5500, 0x550000, 0xAAAAAA],
    [0x00FF00, 0x55AA55, 0xAAFF55, 0x555555, 0x55FF55, 0x00AA00, 0x005500, 0xAAAAAA],
    [0xFFFFFF, 0xFFFF00, 0x00FFFF, 0x555555, 0x55FF55, 0xAA00AA, 0x000000, 0xAAAAAA],
]
P, A, H, DM, OK, BT, SC, MU = range(8)


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


small, big, ja = Font("term_small"), Font("term_big"), Font("term_ja")


def bot(d, x, y, pal, mood, img, phase=True):
    """Mirror of source/Bot.mc. mood: normal, low, night, happy, rain, notify, run, morning."""
    dim = mood in ("low", "night")
    WH, RD = 0xFFFFFF, 0xFF0000
    r = lambda x0, y0, w, h, c: d.rectangle([x + x0, y + y0, x + x0 + w - 1, y + y0 + h - 1], fill=rgb(c))
    if mood == "rain":
        r(18, 6, 2, 12, pal[DM]); r(8, -2, 22, 4, pal[A]); r(0, 2, 38, 4, pal[A]); r(-2, 6, 42, 3, pal[A])
        for a, b in ((-3, 13), (41, 15), (-5, 22), (42, 26)):
            r(a, b, 1, 4, pal[P])
    elif mood == "low":
        r(18, 8, 2, 8, pal[DM]); r(20, 4, 6, 6, pal[DM])
    else:
        ant = pal[DM] if mood == "night" else (pal[A] if (mood == "notify" and phase) else pal[H])
        r(16, 0, 6, 6, ant); r(18, 6, 2, 10, ant)
    if mood == "notify":
        for a, b in ((12, -3), (24, -3), (10, 2), (26, 2)):
            r(a, b, 2, 2, pal[H])
        r(-18, -2, 12, 13, WH); r(-8, 11, 3, 3, WH); r(-13, 0, 2, 6, pal[A]); r(-13, 8, 2, 2, pal[A])
    d.rectangle([x, y + 16, x + 37, y + 43], outline=rgb(pal[A]), width=2)
    r(5, 22, 28, 12, pal[DM] if mood == "night" else pal[P])
    if mood == "happy":
        for ex in (10, 23):
            r(ex + 1, 25, 3, 2, 0); r(ex, 27, 2, 3, 0); r(ex + 3, 27, 2, 3, 0)
    elif mood == "night":
        r(10, 28, 5, 2, 0); r(23, 28, 5, 2, 0)
    elif mood in ("low", "morning"):
        r(10, 28, 5, 3, 0); r(23, 28, 5, 3, 0)
    elif mood == "notify":
        r(8, 25, 5, 6, 0); r(21, 25, 5, 6, 0)
    else:
        r(10, 25, 5, 6, 0); r(23, 25, 5, 6, 0)
    if mood in ("happy", "run"):
        r(8, 37, 22, 2, pal[A]); r(10, 39, 18, 2, pal[A])
    elif mood == "morning":
        r(15, 36, 8, 6, pal[A]); r(17, 38, 4, 2, 0)
    elif dim:
        r(14, 38, 10, 2, pal[DM])
    else:
        r(11, 37, 16, 3, pal[A])
    r(6, 48, 26, 14, pal[BT])
    if mood == "low":
        r(12, 52, 13, 6, 0); d.rectangle([x + 12, y + 52, x + 24, y + 57], outline=rgb(pal[A]))
        r(25, 54, 2, 2, pal[A]); r(13, 53, 3, 4, RD)
    if mood == "happy":
        r(-2, 40, 3, 12, pal[P]); r(37, 40, 3, 12, pal[P]); r(1, 49, 5, 3, pal[P]); r(32, 49, 5, 3, pal[P])
    elif mood == "run":
        r(-4, 46, 8, 3, pal[P]); r(32, 54, 8, 3, pal[P])
    elif mood == "morning":
        r(-2, 50, 8, 3, pal[P]); r(32, 50, 9, 3, pal[P])
    else:
        r(-2, 50, 8, 3, pal[P]); r(32, 50, 8, 3, pal[P])
    if mood == "run":
        r(2, 63, 6, 5, pal[P]); r(30, 61, 6, 5, pal[P])
        for a, b in ((-14, 58), (-18, 62), (-12, 66)):
            r(a, b, 8, 1, pal[DM])
    else:
        r(8, 63, 6, 5, pal[P]); r(24, 63, 6, 5, pal[P])
    if mood == "happy":
        for a, b in ((-8, -2), (42, 2), (44, 30)):
            r(a + 2, b, 2, 6, pal[H]); r(a, b + 2, 6, 2, pal[H])
    elif mood == "morning":
        r(40, 45, 8, 8, WH); r(48, 47, 2, 4, WH); r(42, 39, 1, 4, pal[DM]); r(45, 37, 1, 5, pal[DM])
    elif mood == "night":
        small.draw(img, x + 27, y - 4, "z", pal[DM])


def holiday_overlay(d, x, y, pal, holiday, mood):
    """Mirror of source/Holiday.mc draw(). holiday: halloween, christmas, newyear, valentine, easter, winter."""
    OR, RD, GN, PK, WH = 0xFF5500, 0xFF0000, 0x00AA00, 0xFF55AA, 0xFFFFFF
    r = lambda x0, y0, w, h, c: d.rectangle([x + x0, y + y0, x + x0 + w - 1, y + y0 + h - 1], fill=rgb(c))
    hat_ok = mood != "rain"
    left_free = mood not in ("notify", "happy")

    def heart(a, b, c):
        r(a, b + 1, 5, 2, c); r(a + 1, b, 1, 1, c); r(a + 3, b, 1, 1, c); r(a + 1, b + 3, 3, 1, c); r(a + 2, b + 4, 1, 1, c)

    if holiday == "halloween":
        r(37, 58, 13, 9, OR); r(39, 56, 9, 2, OR); r(43, 53, 2, 3, GN)
        r(40, 60, 2, 2, 0); r(45, 60, 2, 2, 0); r(41, 64, 6, 1, 0)
        if left_free:
            r(-16, 6, 10, 2, pal[DM]); r(-13, 4, 4, 6, pal[DM]); r(-18, 4, 2, 2, pal[DM]); r(-6, 4, 2, 2, pal[DM])
    elif holiday == "christmas" and hat_ok:
        r(4, 9, 30, 5, RD); r(8, 5, 22, 4, RD); r(12, 1, 16, 4, RD); r(18, -2, 14, 3, RD)
        r(1, 13, 36, 3, WH); r(31, -5, 5, 5, WH)
    elif holiday == "newyear":
        if hat_ok:
            r(12, 9, 14, 5, pal[A]); r(16, 1, 6, 4, pal[A]); r(14, 5, 10, 4, pal[H]); r(18, -2, 2, 3, pal[H]); r(12, 14, 14, 2, pal[A])
        for a, b, c in ((-6, 4, P), (44, 20, P), (-10, 14, H), (40, 6, H), (2, -2, A), (42, 34, A)):
            r(a, b, 2, 2, pal[c])
    elif holiday == "valentine":
        if mood == "normal":
            r(8, 24, 22, 8, pal[P]); heart(10, 25, RD); heart(23, 25, RD)
        if left_free:
            heart(-12, 2, PK); heart(-6, 10, RD)
    elif holiday == "easter" and mood != "morning":
        r(41, 43, 6, 9, WH); r(42, 42, 4, 1, WH); r(42, 52, 4, 1, WH); r(41, 45, 6, 1, pal[A]); r(41, 48, 6, 1, pal[P])
    elif holiday == "winter":
        r(4, 44, 30, 4, RD); r(24, 48, 5, 9, RD); r(4, 45, 30, 1, WH); r(24, 53, 5, 1, WH)


def face(pal, time="21:24", mood="night", wx=("+8°", "cloudy"), raw=False, holiday=None,
         phrase="hi there", glitch=True, online=True):
    img = Image.new("RGB", (240, 240), (0, 0, 0))
    d = ImageDraw.Draw(img)
    hc = pal is PALS[3]
    if not hc:
        for y in range(6, 240, 8):
            d.line([0, y, 240, y], fill=rgb(pal[SC]))
    small.draw(img, 120, 18, "[ sys://n3on-0x1 ]", pal[A], "c")
    d.line([42, 37, 198, 37], fill=rgb(pal[A]))
    # first line: bot phrase + cursor (Japanese uses the term_ja font)
    px = small.draw(img, 26, 42, "> ", pal[P])
    if any(ord(c) >= 0x3000 for c in phrase):
        px = ja.draw(img, px, 44, phrase, pal[P])
    else:
        px = small.draw(img, px, 42, phrase, pal[P])
    small.draw(img, px, 42, "_", pal[H])
    if glitch and not hc:
        big.draw(img, 21, 59, time, pal[A])
        d.rectangle([8, 90, 25, 92], fill=rgb(pal[A]))
        d.rectangle([140, 70, 153, 71], fill=rgb(pal[H]))
    big.draw(img, 24, 57, time, pal[P])
    small.draw(img, 12, 114, "> mon 26.10.26", pal[H])
    x = small.draw(img, 14, 134, "> wx ", pal[P])
    x = small.draw(img, x, 134, wx[0], pal[A])
    x = small.draw(img, x, 134, " " + wx[1], pal[P])
    cx, cy = x + 8, 136
    d.rectangle([cx + 4, cy + 2, cx + 9, cy + 5], fill=(170, 170, 170))
    d.rectangle([cx + 9, cy, cx + 14, cy + 5], fill=(170, 170, 170))
    d.rectangle([cx, cy + 5, cx + 17, cy + 9], fill=(170, 170, 170))
    x = small.draw(img, 20, 154, "> sun ", pal[P])
    x = small.draw(img, x, 154, "▲06:41", pal[H])
    small.draw(img, x, 154, " ▼16:22", pal[A])
    x = small.draw(img, 30, 174, "> stp ", pal[P])
    x = small.draw(img, x, 174, "8.4k", pal[A])
    x = small.draw(img, x, 174, "  bat ", pal[P])
    small.draw(img, x, 174, "78%", pal[H])
    d.line([46, 196, 194, 196], fill=rgb(pal[A]))
    st = pal[OK] if online else pal[MU]
    d.ellipse([74, 206, 82, 214], fill=rgb(st))
    small.draw(img, 88, 201, "online" if online else "offline", st)
    bot(d, 178, 46, pal, mood, img)
    if holiday:
        holiday_overlay(d, 178, 46, pal, holiday, mood)
    if raw:
        return img
    # round display mask + bezel
    mask = Image.new("L", (240, 240), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 239, 239], fill=255)
    out = Image.new("RGB", (260, 260), (26, 26, 26))
    out.paste(img, (10, 10), mask)
    return out.resize((520, 520), Image.NEAREST)


if __name__ == "__main__":
    import os
    tiles = [face(PALS[0], mood="night"), face(PALS[1], "07:58", "normal"), face(PALS[2], "18:30", "happy")]
    sheet = Image.new("RGB", (520 * 3 + 40, 560), (12, 12, 12))
    for i, t in enumerate(tiles):
        sheet.paste(t, (10 + i * 530, 20))
    sheet.save(OUT)
    print("saved", OUT)

    if FRAMES:
        os.makedirs(FRAMES, exist_ok=True)
        shots = [
            ("01-neon-day", PALS[0], "10:08", "normal", "hi there", True),
            ("02-neon-night", PALS[0], "21:24", "night", "sleep tight", False),
            ("03-amber", PALS[1], "07:58", "morning", "good morning", False),
            ("04-green-goal", PALS[2], "18:30", "happy", "goal smashed!", False),
            ("05-neon-rain", PALS[0], "13:15", "rain", "take umbrella", False),
            ("06-neon-notify", PALS[0], "09:42", "notify", "3 new msg", False),
            ("07-high-contrast", PALS[3], "16:05", "normal", "hejka!", False),
        ]
        for name, pal, t, mood, ph, gl in shots:
            face(pal, t, mood, raw=True, phrase=ph, glitch=gl).save(os.path.join(FRAMES, f"{name}-240.png"))
            face(pal, t, mood, phrase=ph, glitch=gl).save(os.path.join(FRAMES, f"{name}-round.png"))
        print("frames in", FRAMES)

    if "--moods" in sys.argv:
        moods_out = sys.argv[sys.argv.index("--moods") + 1]
        names = ["normal", "night", "low", "happy", "rain", "notify", "run", "morning"]
        says = ["hi there", "sleep tight", "charge me pls", "goal smashed!", "take umbrella", "3 new msg", "go go go!", "good morning"]
        cells = [face(PALS[0], "10:08", m, phrase=t) for m, t in zip(names, says)]
        cw, ch = cells[0].size
        grid = Image.new("RGB", (cw * 4 + 50, ch * 2 + 30), (12, 12, 12))
        for k, cimg in enumerate(cells):
            grid.paste(cimg, (10 + (k % 4) * (cw + 10), 10 + (k // 4) * (ch + 10)))
        grid.save(moods_out)
        print("moods sheet:", moods_out)

    if "--holidays" in sys.argv:
        hol_out = sys.argv[sys.argv.index("--holidays") + 1]
        items = [("halloween", "normal", "boo!"), ("christmas", "normal", "merry xmas!"),
                 ("newyear", "happy", "happy new year"), ("valentine", "normal", "love you <3"),
                 ("easter", "normal", "happy easter"), ("winter", "normal", "hejka!")]
        cells = [face(PALS[0], "10:08", m, holiday=h, phrase=t) for h, m, t in items]
        cw, ch = cells[0].size
        grid = Image.new("RGB", (cw * 3 + 40, ch * 2 + 30), (12, 12, 12))
        for k, cimg in enumerate(cells):
            grid.paste(cimg, (10 + (k % 3) * (cw + 10), 10 + (k // 3) * (ch + 10)))
        grid.save(hol_out)
        print("holidays sheet:", hol_out)

    if "--phrases" in sys.argv:
        ph_out = sys.argv[sys.argv.index("--phrases") + 1]
        items = [(PALS[0], "hi there"), (PALS[0], "dzień dobry"), (PALS[0], "привіт!"),
                 (PALS[0], "おはよう"), (PALS[0], "ハッピーハロウィン"), (PALS[3], "hejka Vitalii")]
        cells = [face(p, "10:08", "normal", phrase=t) for p, t in items]
        cw, ch = cells[0].size
        grid = Image.new("RGB", (cw * 3 + 40, ch * 2 + 30), (12, 12, 12))
        for k, cimg in enumerate(cells):
            grid.paste(cimg, (10 + (k % 3) * (cw + 10), 10 + (k // 3) * (ch + 10)))
        grid.save(ph_out)
        print("phrases sheet:", ph_out)
