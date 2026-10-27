#!/usr/bin/env python3
"""Static checks for a Connect IQ watch face project (no SDK needed).

  python3 scripts/ciq_lint.py <project_dir> [--mip] [--json]

Checks:
  manifest  - XML parses, 32-hex app id, type=watchface, products listed, launcher icon set
  palette   - with --mip: every 0xRRGGBB literal in source/*.mc uses only 00/55/AA/FF channels
  resources - fonts/drawables referenced in XML exist on disk
Exit code 1 if any error.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

MIP_LEVELS = {0x00, 0x55, 0xAA, 0xFF}
NS = {"iq": "http://www.garmin.com/xml/connectiq"}
HEX_RE = re.compile(r"\b0x([0-9A-Fa-f]{6})\b")


def is_mip_color(value):
    return all(((value >> s) & 0xFF) in MIP_LEVELS for s in (16, 8, 0))


def nearest_mip(value):
    def snap(c):
        return min(MIP_LEVELS, key=lambda m: abs(m - c))
    r, g, b = (value >> 16) & 255, (value >> 8) & 255, value & 255
    return (snap(r) << 16) | (snap(g) << 8) | snap(b)


def check_manifest(project):
    issues = []
    path = os.path.join(project, "manifest.xml")
    if not os.path.isfile(path):
        return [{"level": "error", "check": "manifest", "msg": "manifest.xml not found"}], None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return [{"level": "error", "check": "manifest", "msg": f"XML parse error: {e}"}], None
    app = root.find("iq:application", NS)
    if app is None:
        return [{"level": "error", "check": "manifest", "msg": "no <iq:application>"}], None
    app_id = app.get("id", "")
    if not re.fullmatch(r"[0-9a-fA-F]{32}", app_id):
        issues.append({"level": "error", "check": "manifest", "msg": f"app id must be 32 hex chars, got '{app_id}'"})
    if app.get("type") != "watchface":
        issues.append({"level": "warning", "check": "manifest", "msg": f"type is '{app.get('type')}', expected 'watchface'"})
    products = [p.get("id") for p in app.findall("iq:products/iq:product", NS)]
    if not products:
        issues.append({"level": "error", "check": "manifest", "msg": "no products listed"})
    if not app.get("launcherIcon"):
        issues.append({"level": "warning", "check": "manifest", "msg": "launcherIcon not set"})
    perms = [p.get("id") for p in app.findall("iq:permissions/iq:uses-permission", NS)]
    return issues, {"id": app_id, "products": products, "permissions": perms,
                    "minApiLevel": app.get("minApiLevel")}


def check_palette(project):
    issues = []
    src = os.path.join(project, "source")
    for dirpath, _, files in os.walk(src):
        for fn in sorted(files):
            if not fn.endswith(".mc"):
                continue
            fp = os.path.join(dirpath, fn)
            with open(fp, encoding="utf-8") as f:
                for n, line in enumerate(f, 1):
                    code = line.split("//", 1)[0]
                    for m in HEX_RE.finditer(code):
                        v = int(m.group(1), 16)
                        if not is_mip_color(v):
                            issues.append({
                                "level": "error", "check": "palette",
                                "msg": f"{os.path.relpath(fp, project)}:{n}: 0x{m.group(1).upper()} is not a MIP color, "
                                       f"nearest is 0x{nearest_mip(v):06X}",
                            })
    return issues


def check_resources(project):
    issues = []
    res = os.path.join(project, "resources")
    for dirpath, _, files in os.walk(res):
        for fn in files:
            if not fn.endswith(".xml"):
                continue
            fp = os.path.join(dirpath, fn)
            try:
                root = ET.parse(fp).getroot()
            except ET.ParseError as e:
                issues.append({"level": "error", "check": "resources", "msg": f"{os.path.relpath(fp, project)}: {e}"})
                continue
            for el in root.iter():
                ref = el.get("filename")
                if ref and not os.path.isfile(os.path.join(dirpath, ref)):
                    issues.append({"level": "error", "check": "resources",
                                   "msg": f"{os.path.relpath(fp, project)}: missing file '{ref}'"})
    return issues


def lint(project, mip=False):
    issues, manifest = check_manifest(project)
    issues += check_resources(project)
    if mip:
        issues += check_palette(project)
    return {"project": project, "manifest": manifest, "issues": issues,
            "ok": not any(i["level"] == "error" for i in issues)}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    result = lint(args[0], mip="--mip" in sys.argv)
    if "--json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        for i in result["issues"]:
            print(f"[{i['level']}] {i['check']}: {i['msg']}")
        print("OK" if result["ok"] else "FAILED")
    sys.exit(0 if result["ok"] else 1)
