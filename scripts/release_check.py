#!/usr/bin/env python3
"""Pre-release gate for a Connect IQ watch face (run before exporting the .iq for the store).

  python3 scripts/release_check.py <face_dir> [--json]

Automated checks (FAIL blocks the release, WARN needs a look):
  lint        ciq_lint (manifest, resources, MIP palette) with no errors
  location    Lat/Lon defaults reset to 0/0 (no personal location shipped)
  settings    every setting -> existing property; every @Strings.X -> defined string
  naming      app name set, no "Garmin" in it
  products    manifest products known in mcp/devices.json
  permissions none, or a privacy policy is needed
  icon        launcher icon exists and is square
  debug       no System.println / TODO left in source
  store       store/listing.md (repo URL, "Not affiliated"), screenshots, 500px icon
  secrets     no developer keys / private keys / personal emails in tracked files
  git         working tree clean

Then prints the manual checklist (simulator, memory, real watch, beta).
Exit code 1 if any FAIL.
"""
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from ciq_lint import lint  # noqa: E402

try:
    from PIL import Image
except ImportError:  # optional
    Image = None

NS = {"iq": "http://www.garmin.com/xml/connectiq"}
MANUAL = [
    "Build for Device with no errors (warnings reviewed)",
    "Simulator: every theme, Low Power Mode, 12h and 24h, °C and °F",
    "Simulator: weather missing (no phone) → no crash, shows --",
    "Simulator: no position → 'no gps fix'; position set → sunrise/sunset shown",
    "Simulator: battery <20%, notifications, step goal, rain → bot emotions",
    "Simulator: bot language EN/PL/UA/JA + own phrase; typing animation after wake; holiday look (change the date)",
    "Simulator: File → View Memory, peak well below the watch-face limit",
    "Real watch: sideload, run at least a few hours, no IQ! crash (check GARMIN/APPS/LOGS)",
    "Export Project → .iq signed with YOUR developer key (backed up in a password manager)",
    "Store: upload as beta first, install from the store, change settings from the phone",
    "Store listing: title, 4 languages, screenshots, devices, category, 'free'",
    "After approval: git tag v<version> && git push --tags; add the store link to README",
]


def add(results, check, status, msg):
    results.append({"check": check, "status": status, "msg": msg})


def read_xml(path):
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, FileNotFoundError):
        return None


def check_settings(face, results):
    res = os.path.join(face, "resources")
    strings, props, used_strings = set(), set(), set()
    for dirpath, _, files in os.walk(res):
        for fn in files:
            if not fn.endswith(".xml"):
                continue
            root = read_xml(os.path.join(dirpath, fn))
            if root is None:
                continue
            for el in root.iter():
                if el.tag == "string" and el.get("id"):
                    strings.add(el.get("id"))
                if el.tag == "property" and el.get("id"):
                    props.add(el.get("id"))
                for attr in ("title", "prompt", "propertyKey"):
                    v = el.get(attr) or ""
                    if v.startswith("@Strings."):
                        used_strings.add(v.split(".", 1)[1])
                if el.text and el.text.strip().startswith("@Strings."):
                    used_strings.add(el.text.strip().split(".", 1)[1])
    keys = set()
    sroot = read_xml(os.path.join(res, "settings", "settings.xml"))
    if sroot is not None:
        for s in sroot.iter("setting"):
            k = (s.get("propertyKey") or "").replace("@Properties.", "")
            keys.add(k)
    man = read_xml(os.path.join(face, "manifest.xml"))
    if man is not None:
        app = man.find("iq:application", NS)
        if app is not None and (app.get("name") or "").startswith("@Strings."):
            used_strings.add(app.get("name").split(".", 1)[1])
    missing_props = sorted(keys - props)
    missing_strings = sorted(used_strings - strings)
    orphan_props = sorted(props - keys)
    if missing_props or missing_strings:
        add(results, "settings", "FAIL",
            f"settings without property: {missing_props or '-'}; undefined strings: {missing_strings or '-'}")
    else:
        add(results, "settings", "PASS", f"{len(keys)} settings, {len(props)} properties, strings OK")
    if orphan_props:
        add(results, "settings", "WARN", f"properties not exposed as settings: {orphan_props}")
    return strings


def string_value(face, sid):
    root = read_xml(os.path.join(face, "resources", "strings", "strings.xml"))
    if root is None:
        return None
    for el in root.iter("string"):
        if el.get("id") == sid:
            return (el.text or "").strip()
    return None


def tracked_files():
    try:
        out = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True, check=True).stdout
        return [l for l in out.splitlines() if l]
    except (OSError, subprocess.CalledProcessError):
        return []


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    face = os.path.abspath(args[0])
    results = []

    # lint + location
    lr = lint(face, mip=True)
    errs = [i["msg"] for i in lr["issues"] if i["level"] == "error"]
    loc = [i["msg"] for i in lr["issues"] if i["check"] == "location"]
    other_w = [i["msg"] for i in lr["issues"] if i["level"] == "warning" and i["check"] != "location"]
    add(results, "lint", "FAIL" if errs else "PASS", "; ".join(errs) or "manifest, resources, palette OK")
    if other_w:
        add(results, "lint", "WARN", "; ".join(other_w))
    add(results, "location", "FAIL" if loc else "PASS", loc[0] if loc else "Lat/Lon defaults are 0/0 (automatic)")

    check_settings(face, results)

    # naming
    man = lr.get("manifest") or {}
    mroot = read_xml(os.path.join(face, "manifest.xml"))
    app = mroot.find("iq:application", NS) if mroot is not None else None
    name_ref = app.get("name", "") if app is not None else ""
    name = string_value(face, name_ref.split(".", 1)[1]) if name_ref.startswith("@Strings.") else name_ref
    if not name:
        add(results, "naming", "FAIL", "app name not set")
    elif "garmin" in name.lower():
        add(results, "naming", "FAIL", f"'{name}' contains 'Garmin' (trademark)")
    else:
        add(results, "naming", "PASS", f"app name: {name}")

    # products
    try:
        with open(os.path.join(ROOT, "mcp", "devices.json"), encoding="utf-8") as f:
            data = json.load(f)
        devs = data.get("devices", data) if isinstance(data, dict) else data
        known = set(devs.keys()) if isinstance(devs, dict) else {d["id"] for d in devs}
        known.discard("_note")
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        known = set()
    prods = man.get("products") or []
    unknown = [p for p in prods if known and p not in known]
    add(results, "products", "WARN" if unknown else "PASS",
        f"products: {prods}" + (f"; not in devices.json (verify in SDK Manager): {unknown}" if unknown else ""))

    perms = man.get("permissions") or []
    add(results, "permissions", "WARN" if perms else "PASS",
        f"uses {perms}: you need a privacy policy and must describe the data use" if perms else "no permissions")

    # icon
    icon_ok = False
    for dirpath, _, files in os.walk(os.path.join(face, "resources")):
        for fn in files:
            if fn.lower().startswith("launcher") and fn.lower().endswith(".png"):
                icon_ok = True
                if Image:
                    w, h = Image.open(os.path.join(dirpath, fn)).size
                    if w != h:
                        add(results, "icon", "WARN", f"{fn} is {w}x{h}, expected square")
    add(results, "icon", "PASS" if icon_ok else "FAIL", "launcher icon found" if icon_ok else "no launcher_icon.png")

    # debug leftovers
    hits = []
    for dirpath, _, files in os.walk(os.path.join(face, "source")):
        for fn in files:
            if fn.endswith(".mc"):
                with open(os.path.join(dirpath, fn), encoding="utf-8") as f:
                    for n, line in enumerate(f, 1):
                        if re.search(r"System\.println|\bTODO\b|\bFIXME\b", line):
                            hits.append(f"{fn}:{n}")
    add(results, "debug", "WARN" if hits else "PASS", f"leftovers at {hits[:5]}" if hits else "no println/TODO")

    # store assets
    store = os.path.join(face, "store")
    lp = os.path.join(store, "listing.md")
    if not os.path.isfile(lp):
        add(results, "store", "FAIL", "store/listing.md missing (run /wf-store)")
    else:
        txt = open(lp, encoding="utf-8").read()
        miss = [k for k in ("Not affiliated", "github.com/") if k not in txt]
        add(results, "store", "WARN" if miss else "PASS",
            f"listing.md missing: {miss}" if miss else "listing.md OK (disclaimer, repo link)")
        shots = os.path.join(store, "screenshots")
        n = len([f for f in os.listdir(shots) if f.endswith(".png")]) if os.path.isdir(shots) else 0
        add(results, "store", "PASS" if n else "FAIL", f"{n} screenshots" if n else "no screenshots")
        add(results, "store", "PASS" if os.path.isfile(os.path.join(store, "icon-500.png")) else "WARN",
            "icon-500.png present" if os.path.isfile(os.path.join(store, "icon-500.png")) else "no store icon")

    # secrets in tracked files
    bad = []
    email_re = re.compile(r"[A-Za-z0-9._%+-]+@(?!users\.noreply\.github\.com|anthropic\.com|example\.com)[A-Za-z0-9.-]+\.[a-z]{2,}")
    for rel in tracked_files():
        base = os.path.basename(rel).lower()
        if base.startswith("developer_key") or base.endswith((".der", ".pem", ".p12")):
            bad.append(f"{rel} (key file)")
            continue
        if rel.endswith((".png", ".jpg", ".gif", ".prg", ".iq")) or "/tests/" in rel:
            continue
        try:
            txt = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        if "PRIVATE KEY-----" in txt and "release_check.py" not in rel and "log_fix.py" not in rel:
            bad.append(f"{rel} (private key)")
        for m in email_re.findall(txt):
            if not m.endswith(("@gnome", "@users.sourceforge.net")) and "fonts at gnome" not in m:
                bad.append(f"{rel} ({m})")
    add(results, "secrets", "FAIL" if bad else "PASS", f"found: {bad[:5]}" if bad else "no keys or personal emails tracked")

    # git
    try:
        st = subprocess.run(["git", "-C", ROOT, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        add(results, "git", "WARN" if st else "PASS", "uncommitted changes" if st else "working tree clean")
    except OSError:
        add(results, "git", "WARN", "git not available")

    ok = not any(r["status"] == "FAIL" for r in results)
    if "--json" in sys.argv:
        print(json.dumps({"face": face, "ok": ok, "results": results, "manual": MANUAL}, indent=2))
    else:
        icons = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}
        for r in results:
            print(f"{icons[r['status']]} {r['check']:<11} {r['msg']}")
        print("\nManual checklist:")
        for m in MANUAL:
            print(f"  [ ] {m}")
        print("\nREADY FOR RELEASE (after the manual checklist)" if ok else "\nNOT READY: fix the ❌ items first")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
