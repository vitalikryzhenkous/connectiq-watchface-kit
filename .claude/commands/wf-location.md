---
description: Set the sunrise/sunset location for local testing (asks for a city, offline lookup), or reset it
argument-hint: [city | reset] [face dir, default templates/n3on-terminal]
---
Use the `connectiq-watchface` skill.

Input: $ARGUMENTS

Why this exists: sideloaded faces can't get settings from the phone, and a fresh watch may have no GPS fix. That leaves sunrise and sunset showing `no gps fix`.

1. Privacy first. Ask only for a **city** (and the country if the name is ambiguous), never a street address. Tell the user in one line: the lookup is offline, coordinates are rounded to city level (~1 km), and nothing leaves their machine.
2. If the input is `reset`: run `python3 scripts/set_location.py --reset --project <dir>` and stop.
3. Otherwise run `python3 scripts/set_location.py --city "<city>" [--country XX] --project <dir>`.
   - If `geonamescache` is missing, offer `pip install geonamescache`. If the user declines, ask them to confirm approximate coordinates for the city, then use `--lat/--lon`.
   - If there are several matches, show the top ones and ask which one.
4. Tell the user to rebuild (Build for Device → fr945) and copy the `.prg` to `GARMIN/APPS`.
5. Always end with this reminder: the location is now in `properties.xml`, a git-tracked file. Before committing, pushing, or exporting for the store, run `/wf-location reset`. `ciq_lint.py` warns while a location is set.
