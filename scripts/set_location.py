#!/usr/bin/env python3
"""Set (or reset) the default sunrise/sunset location of a watch face, offline.

  python3 scripts/set_location.py --city "Poznań" [--country PL] [--project templates/n3on-terminal]
  python3 scripts/set_location.py --lat 52.41 --lon 16.93
  python3 scripts/set_location.py --reset        # back to 0/0 = automatic (do this before publishing!)

Why: sideloaded faces can't receive settings from the phone, and a fresh watch
may have no GPS fix yet. This writes the Lat/Lon defaults into
resources/settings/properties.xml so sunrise/sunset works right away.

Privacy:
- The city lookup is offline (geonamescache, bundled data). No network calls are made.
- Coordinates are rounded to 2 decimals (~1 km), which is city level, not your address.
- properties.xml is tracked by git: don't commit or publish your city. Run --reset before
  you commit or export for the store (ciq_lint warns if a location is baked in).

The city lookup needs `pip install geonamescache` (optional). --lat/--lon works without it.
"""
import argparse
import os
import re
import sys

PROP_RE = r'(<property id="{key}" type="float">)([^<]*)(</property>)'


def lookup_city(name, country=None):
    try:
        import geonamescache
    except ImportError:
        sys.exit("City lookup needs: pip install geonamescache  (or pass --lat/--lon)")
    gc = geonamescache.GeonamesCache(min_city_population=15000)
    hits = gc.search_cities(name, case_sensitive=False)
    if country:
        hits = [h for h in hits if h["countrycode"].upper() == country.upper()]
    if not hits:
        sys.exit(f"City '{name}' not found offline. Try the English name, add --country, or pass --lat/--lon.")
    hits.sort(key=lambda h: -h["population"])
    best = hits[0]
    if len(hits) > 1:
        others = ", ".join(f"{h['name']} ({h['countrycode']})" for h in hits[1:5])
        print(f"Several matches, using the largest. Others: {others}. Use --country to pick.")
    return best["name"], best["countrycode"], float(best["latitude"]), float(best["longitude"])


def write_location(project, lat, lon):
    path = os.path.join(project, "resources", "settings", "properties.xml")
    if not os.path.isfile(path):
        sys.exit(f"Not found: {path}")
    with open(path, encoding="utf-8") as f:
        xml = f.read()
    for key, val in (("Lat", lat), ("Lon", lon)):
        pattern = PROP_RE.format(key=key)
        if not re.search(pattern, xml):
            sys.exit(f'{path} has no <property id="{key}" type="float">. Add Lat/Lon properties first '
                     f"(see templates/n3on-terminal).")
        xml = re.sub(pattern, lambda m: f"{m.group(1)}{val:.2f}{m.group(3)}", xml)
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default="templates/n3on-terminal")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--city")
    g.add_argument("--lat", type=float)
    g.add_argument("--reset", action="store_true")
    ap.add_argument("--lon", type=float)
    ap.add_argument("--country", help="ISO country code to disambiguate, e.g. PL")
    a = ap.parse_args()

    if a.reset:
        lat = lon = 0.0
        label = "automatic (0/0)"
    elif a.city:
        name, cc, lat, lon = lookup_city(a.city, a.country)
        label = f"{name}, {cc}"
    else:
        if a.lon is None:
            ap.error("--lat needs --lon")
        lat, lon = a.lat, a.lon
        label = "manual"
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        sys.exit("Latitude must be -90..90 and longitude -180..180.")

    path = write_location(a.project, round(lat, 2), round(lon, 2))
    print(f"Location set to {label}: Lat {lat:.2f}, Lon {lon:.2f}, in {path}")
    if not a.reset:
        print("Rebuild and sideload the .prg. Before committing or exporting for the store, run:\n"
              f"  python3 scripts/set_location.py --reset --project {a.project}")


if __name__ == "__main__":
    main()
