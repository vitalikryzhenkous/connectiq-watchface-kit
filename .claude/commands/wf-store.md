---
description: Prepare a Connect IQ Store release — export, screenshots, localized listing
argument-hint: <face dir>
---
Use the `connectiq-watchface` skill and `references/store-listing.md`.

Face: $ARGUMENTS

1. Reset any personal location: `python3 scripts/set_location.py --reset --project <face>`. Then run `python3 scripts/ciq_lint.py <face> --mip`. It must show no `location` warning.
2. Check the manifest: name, products, and permissions (minimal).
3. Render 4–5 store screenshots: themes and states.
4. Write the listing: name, short hook, feature bullets. Write it in EN, PL, DE and UK, and save it to `<face>/store/listing.md`.
5. Give the export and upload steps: `.iq` → private beta → verify settings from the phone → public.
