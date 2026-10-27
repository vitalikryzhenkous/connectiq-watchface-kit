---
description: Add support for more Garmin devices to an existing watch face
argument-hint: <face dir> <device ids, e.g. fr955 fenix7 fr965>
---
Use the `connectiq-watchface` skill and `references/project-structure.md`.

Input: $ARGUMENTS

1. For each device, note the screen size and type (MIP or AMOLED) and whether it supports the APIs used (Weather needs 3.2+).
2. Add the product ids to `manifest.xml`.
3. Layout: replace fixed 240px coordinates with scaling from `dc.getWidth()`, or add `resources-<device>/` with bigger fonts (`gen_font.py`) and register them in `monkey.jungle`.
4. AMOLED: add an always-on low-power layout (time only, ~10% lit pixels, shift by 1–2 px each minute, no scanlines or bot).
5. Output the changes as diffs. Then tell the user which devices to download in SDK Manager and to run the simulator for each.
