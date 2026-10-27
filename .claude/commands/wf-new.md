---
description: Start a new Connect IQ watch face from the kit (design → mockup → project)
argument-hint: <style idea, e.g. "minimal amber analog for fenix7">
---
Use the `connectiq-watchface` skill.

Request: $ARGUMENTS

1. Reply with a short analysis and a work plan. Ask only the questions that still matter: target devices, data fields, settings, 12/24h handling.
2. Show an inline SVG mockup at the target resolution. Use original art only, no brand characters, and keep to the MIP 64-color palette when the device is MIP.
3. After approval, create `faces/<slug>/` from the `templates/n3on-terminal` structure:
   - new UUID in the manifest, products list, strings, settings
   - fonts via `scripts/gen_font.py`, icon via `scripts/gen_icon.py` or a new original icon
   - copy `scripts/preview_n3on.py` → `scripts/preview_<slug>.py`, adapt it, and render a PNG preview
4. Finish with build steps from `docs/build-and-run-mac.md`, and ask the user to paste the compiler output.
