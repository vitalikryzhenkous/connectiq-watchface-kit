#!/usr/bin/env python3
"""Generate a Connect IQ bitmap font (AngelCode BMFont text .fnt + .png atlas) from any TTF.

No antialiasing: glyphs are crisp on MIP (memory-in-pixel) displays.

Examples:
  python3 scripts/gen_font.py --ttf DejaVuSansMono.ttf --size 14 --name term_small \
      --out myface/resources/fonts
  python3 scripts/gen_font.py --ttf DejaVuSansMono-Bold.ttf --size 48 --name term_big \
      --chars "0123456789:- " --out myface/resources/fonts

Then reference it in resources/fonts/fonts.xml:
  <font id="TermSmall" filename="term_small.fnt" antialias="false"/>
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFont

DEFAULT_CHARS = "".join(chr(c) for c in range(32, 127)) + "°▲▼"


def make_font(name, ttf, size, chars, out_dir, atlas_w=256):
    font = ImageFont.truetype(ttf, size)
    ascent, descent = font.getmetrics()
    glyphs = []
    for ch in dict.fromkeys(chars):  # dedupe, keep order
        l, t, r, b = font.getbbox(ch)
        w, h = max(r - l, 0), max(b - t, 0)
        img = None
        if w and h:
            img = Image.new("L", (w, h), 0)
            d = ImageDraw.Draw(img)
            d.fontmode = "1"
            d.text((-l, -t), ch, font=font, fill=255)
        glyphs.append((ch, l, t, w, h, round(font.getlength(ch)), img))

    pad = 1
    x = y = row_h = 0
    pos = []
    for g in glyphs:
        w, h = g[3], g[4]
        if x + w + pad > atlas_w:
            x, y, row_h = 0, y + row_h + pad, 0
        pos.append((x, y))
        x += w + pad
        row_h = max(row_h, h)
    atlas_h = 1
    while atlas_h < y + row_h + pad:
        atlas_h *= 2

    atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    for g, (px, py) in zip(glyphs, pos):
        if g[6] is not None:
            atlas.paste(Image.new("RGBA", g[6].size, (255, 255, 255, 255)), (px, py), g[6])
    os.makedirs(out_dir, exist_ok=True)
    png = f"{name}.png"
    atlas.save(os.path.join(out_dir, png))

    lines = [
        f'info face="{name}" size={size} bold=0 italic=0 charset="" unicode=1 '
        f"stretchH=100 smooth=0 aa=1 padding=0,0,0,0 spacing=1,1",
        f"common lineHeight={ascent + descent} base={ascent} scaleW={atlas_w} "
        f"scaleH={atlas_h} pages=1 packed=0",
        f'page id=0 file="{png}"',
        f"chars count={len(glyphs)}",
    ]
    for g, (px, py) in zip(glyphs, pos):
        ch, l, t, w, h, adv, _ = g
        lines.append(
            f"char id={ord(ch)} x={px} y={py} width={w} height={h} "
            f"xoffset={l} yoffset={t} xadvance={adv} page=0 chnl=15"
        )
    with open(os.path.join(out_dir, f"{name}.fnt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{name}: advance(0)={round(font.getlength('0'))}px lineHeight={ascent + descent}px "
          f"atlas={atlas_w}x{atlas_h} glyphs={len(glyphs)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ttf", required=True, help="path to a .ttf/.otf (monospace recommended)")
    ap.add_argument("--size", type=int, required=True, help="pixel size")
    ap.add_argument("--name", required=True, help="output base name, e.g. term_small")
    ap.add_argument("--out", required=True, help="output dir, usually <project>/resources/fonts")
    ap.add_argument("--chars", default=DEFAULT_CHARS, help="characters to include (default: ASCII + ° ▲ ▼)")
    a = ap.parse_args()
    make_font(a.name, a.ttf, a.size, a.chars, a.out)
