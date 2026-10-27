# Connect IQ Store listing

## Release flow
1. VS Code: `Monkey C: Export Project`. This produces a `.iq` signed with the developer key. Keep the key forever: every update must use the same key.
2. developer.garmin.com → Connect IQ → Developer Dashboard → upload the `.iq`.
3. First upload: set it to **beta** (private). Install it from the store on your own watch and verify the phone settings.
4. Submit it publicly. Review usually takes a few days.
5. Updates: bump `version` in manifest (if set) → export → upload a new version.

## Listing checklist
- Name that's unique and searchable, e.g. "N3on Terminal - cyberpunk".
- Short description that leads with the hook: "Terminal-style cyberpunk face with a pixel bot that reacts to your day."
- Feature bullets: weather, sunrise/sunset, steps, battery, themes, battery-friendly.
- 4–5 screenshots: each theme, night bot, happy bot, low battery. Render them with `scripts/preview_n3on.py` or take them in the simulator (File → Save Screenshot).
- Hero image and an animated GIF if possible.
- Localize the description: EN, PL, DE, UK.
- List the supported devices. More devices means more installs.
- Mention the permissions only if they're used. This face needs none.

## Growth ideas
- User-selectable data per line: steps, calories, Body Battery, floors, HR, notifications.
- More themes, plus seasonal easter eggs for the bot.
- Reply to store reviews and ship small updates often (updates resurface the app).
- Paid apps: check the current terms and supported countries in the dashboard.
