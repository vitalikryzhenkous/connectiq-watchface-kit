---
name: connectiq-watchface
description: Design, build, test, sideload and publish Garmin Connect IQ watch faces in Monkey C (Forerunner, Fenix, Venu). Use for any Garmin watch face or Connect IQ task — new face, new device support, compiler errors, IQ! crashes, store listing.
---

# Connect IQ watch face workflow

Working kit for Garmin watch faces. Reference project: `templates/n3on-terminal/`
(cyberpunk terminal face, built and verified on a real Forerunner 945).

## Ground rules
- The Garmin SDK can't be downloaded in a cloud container (it needs a Garmin login). Write the code, then the user builds it on their Mac in VS Code. Ask them to paste compiler output and reply with diffs.
- Never use brand characters or logos (Claude, Garmin or others) in the design. Use original art only, like the N3on bot.
- MIP displays (FR945/955/255, Fenix 6/7, Instinct) show 64 colors: every RGB channel must be one of 00, 55, AA, FF. Use only those values. There's no glow and no alpha.
- AMOLED devices (FR265/965, Venu, Epix) need a separate low-power (always-on) layout. No more than ~10% of pixels may be lit, the content must shift every minute to avoid burn-in, and there are no scanlines or big filled areas.
- Battery: draw seconds and animation only while awake (`onExitSleep` / `onEnterSleep`). Cache expensive math (sun times) per day and position. Write to `Application.Storage` only when a value changes.

## Phases
1. **Design.** Agree on style, data fields, 12/24h handling and settings. Show an inline SVG mockup at the real resolution (240 for FR945, 260 for FR955/255/Fenix 7, 280 for Fenix 7X, 416/454 for AMOLED). Then render a pixel preview with `scripts/preview_n3on.py` (copy it and adapt it for a new face).
2. **Project.** Copy the template's structure (see `references/project-structure.md`). Generate a new UUID for the manifest `id`. Make fonts with `scripts/gen_font.py` and the icon with `scripts/gen_icon.py`.
3. **Build and test.** The user follows `docs/build-and-run-mac.md`: build in VS Code, run the simulator, then sideload the `.prg` to `GARMIN/APPS` with OpenMTP.
4. **Debug.** Fix compiler errors with diffs. A crash on the watch shows as `IQ!`: have the user create `GARMIN/APPS/LOGS/CIQ_LOG.YML`, reproduce the crash and paste the file. See `references/pitfalls.md`.
5. **More devices.** Add product ids to the manifest and add `resources-<device>/` folders for fonts or layouts that differ. Layout code should use `_ox/_oy` offsets or scale from `dc.getWidth()`.
6. **Store.** Export the `.iq` and upload it to the Connect IQ developer dashboard. Ship a private beta first: settings from the phone only work on store installs, not sideloads. See `references/store-listing.md`.

## Key APIs (watch face)
- `WatchUi.WatchFace`: `onLayout`, `onUpdate`, `onEnterSleep`, `onExitSleep`, optionally `onPartialUpdate` for seconds on MIP
- Time: `System.getClockTime()`, `Gregorian.info(Time.now(), Time.FORMAT_SHORT)`
- Settings: `System.getDeviceSettings()` (`is24Hour`, `temperatureUnits`, `phoneConnected`)
- Data: `ActivityMonitor.getInfo()` (steps, stepGoal, calories, floors), `System.getSystemStats().battery`
- Weather (API 3.2+): `Weather.getCurrentConditions()` (temperature in °C, condition, observationLocationPosition)
- Position fallback: `Activity.getActivityInfo().currentLocation`
- Properties and settings: `Application.Properties.getValue(key)`, applied in `AppBase.onSettingsChanged()`
- Persisted values: `Application.Storage`

## Tools in this repo
- `python3 scripts/ciq_lint.py <dir> --mip` checks the manifest, resources and palette. Run it before telling the user to build.
- `mcp/server.py` is an MCP server with the same tools for other clients.
- `bench/run.py` runs ConnectIQ-Bench to score a generated face against a task.
- `scripts/log_fix.py` is an opt-in dataset logger. `/wf-debug` calls it only if `datasets/.optin` exists.

## Commands in this repo
`/wf-new`, `/wf-preview`, `/wf-add-device`, `/wf-debug`, `/wf-store`. They live in `.claude/commands/`.
