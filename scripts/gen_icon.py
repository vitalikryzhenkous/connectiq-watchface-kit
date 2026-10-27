#!/usr/bin/env python3
"""Generate the N3on pixel-bot launcher icon (original design).

Usage: python3 scripts/gen_icon.py --out myface/resources/drawables/launcher_icon.png [--size 40]

Icon size per device: check the device's launcherIcon size in the SDK's
compiler.json (Devices folder) — fr945 uses 40x40. The art is drawn on a
40x40 grid and scaled with nearest-neighbour for other sizes.
"""
import argparse

from PIL import Image, ImageDraw

CY, MG, YL, PU, BK = (0, 255, 255), (255, 0, 170), (255, 255, 0), (170, 0, 170), (0, 0, 0)


def draw_bot(size):
    icon = Image.new("RGB", (40, 40), BK)
    d = ImageDraw.Draw(icon)
    d.rectangle([18, 2, 21, 5], fill=YL)
    d.rectangle([19, 6, 20, 9], fill=YL)
    d.rectangle([8, 10, 31, 25], outline=MG, width=2)
    d.rectangle([11, 13, 28, 19], fill=CY)
    d.rectangle([14, 15, 16, 18], fill=BK)
    d.rectangle([23, 15, 25, 18], fill=BK)
    d.rectangle([15, 21, 24, 22], fill=MG)
    d.rectangle([12, 27, 27, 34], fill=PU)
    d.rectangle([5, 28, 10, 29], fill=CY)
    d.rectangle([29, 28, 34, 29], fill=CY)
    d.rectangle([13, 35, 16, 38], fill=CY)
    d.rectangle([23, 35, 26, 38], fill=CY)
    return icon if size == 40 else icon.resize((size, size), Image.NEAREST)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--size", type=int, default=40)
    a = ap.parse_args()
    draw_bot(a.size).save(a.out)
    print("saved", a.out)
