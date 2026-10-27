---
description: Render a pixel-accurate PNG preview of a watch face without the simulator
argument-hint: <face folder, e.g. templates/n3on-terminal>
---
Use the `connectiq-watchface` skill.

Target: $ARGUMENTS

1. Find the face's preview script: `scripts/preview_<slug>.py` (for N3on, `scripts/preview_n3on.py`). If there isn't one, create it by mirroring the face's `onUpdate()` draw calls and using its real `.fnt` fonts.
2. Run it: `python3 scripts/preview_<slug>.py <face dir> /tmp/preview.png`. Look at the image yourself and check for overlaps, clipping by the round mask, and off-palette colors.
3. Send the PNG to the user and list any layout problems found as diffs to fix.
