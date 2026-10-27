#!/usr/bin/env python3
"""ConnectIQ-Bench runner: score a generated Monkey C watch face project against a task.

  python3 bench/run.py --task bench/tasks/01_digital_time.yaml --project <dir> [--compile]
  python3 bench/run.py --all --projects-dir <dir> [--compile]     # expects <dir>/<task_id>/
  python3 bench/run.py --all --project <dir>                      # same project for every task (reference runs)
  python3 bench/run.py --print-prompt bench/tasks/01_digital_time.yaml

Prints a JSON report. score = passed / total over the task's checks. Static checks need only Python
(PyYAML optional: `pip install pyyaml`; a minimal built-in parser handles the task files otherwise).
--compile runs `monkeyc` for every task device if `monkeyc` is on PATH and $CIQ_DEV_KEY is set;
otherwise the compile check is reported as "skipped" and does not count towards the score.
"""
import argparse
import glob
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _load_lint():
    spec = importlib.util.spec_from_file_location("ciq_lint", os.path.join(ROOT, "scripts", "ciq_lint.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ciq_lint = _load_lint()

# ------------------------------------------------------------------ task loading

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - exercised via mini_yaml tests
    yaml = None


def _unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] == "'":
        return s[1:-1].replace("''", "'")
    if len(s) >= 2 and s[0] == s[-1] == '"':
        return json.loads(s)
    return s


def _scalar(s):
    s = s.strip()
    if s[:1] in "'\"":
        return _unquote(s)
    low = s.lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "~", ""):
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _split_flow(s):
    """Split on top-level commas, respecting quotes and nested [] {}."""
    parts, buf, depth, quote = [], "", 0, None
    i = 0
    while i < len(s):
        c = s[i]
        if quote:
            buf += c
            if c == quote:
                if quote == "'" and s[i + 1:i + 2] == "'":
                    buf += "'"
                    i += 1
                else:
                    quote = None
            elif c == "\\" and quote == '"':
                buf += s[i + 1:i + 2]
                i += 1
        elif c in "'\"":
            quote = c
            buf += c
        elif c in "[{":
            depth += 1
            buf += c
        elif c in "]}":
            depth -= 1
            buf += c
        elif c == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += c
        i += 1
    if buf.strip():
        parts.append(buf)
    return parts


def _split_key(s):
    """'key: value' -> (key, value), colon outside quotes."""
    quote = None
    for i, c in enumerate(s):
        if quote:
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c == ":" and (i + 1 == len(s) or s[i + 1] == " "):
            return s[:i].strip(), s[i + 1:].strip()
    raise ValueError(f"expected 'key: value', got: {s!r}")


def _flow(s):
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        return [_flow(p) for p in _split_flow(s[1:-1])]
    if s.startswith("{") and s.endswith("}"):
        out = {}
        for p in _split_flow(s[1:-1]):
            k, v = _split_key(p.strip())
            out[_unquote(k)] = _flow(v)
        return out
    return _scalar(s)


def mini_yaml(text):
    """Tiny YAML subset: top-level `key: scalar|flow`, `key: |` block scalars, and `key:` + `- item`
    lists whose items are scalars, flow mappings {a: b} or flow lists [a, b]. No anchors, no nesting."""
    lines = text.splitlines()
    out, i = {}, 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith("#"):
            i += 1
            continue
        if raw[0] in " \t":
            raise ValueError(f"line {i + 1}: unexpected indentation")
        key, val = _split_key(raw)
        i += 1
        if val in ("|", "|-", ">", ">-"):
            block = []
            while i < len(lines) and (not lines[i].strip() or lines[i][0] in " \t"):
                block.append(lines[i])
                i += 1
            ind = min((len(l) - len(l.lstrip()) for l in block if l.strip()), default=0)
            block = [l[ind:] for l in block]
            while block and not block[-1].strip():
                block.pop()
            if val.startswith(">"):
                body = " ".join(l.strip() for l in block)
            else:
                body = "\n".join(block)
            out[key] = body if val.endswith("-") else body + "\n"
        elif val == "":
            items = []
            while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith(("-", "#"))):
                l = lines[i].strip()
                i += 1
                if l.startswith("- ") or l == "-":
                    items.append(_flow(l[2:]))
            out[key] = items
        else:
            out[key] = _flow(val)
    return out


def load_task(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.endswith(".json"):
        task = json.loads(text)
    elif yaml is not None:
        task = yaml.safe_load(text)
    else:
        task = mini_yaml(text)
    return validate_task(task, path)


CHECK_TYPES = {
    # name: required keys
    "manifest_valid": [],
    "resources_valid": [],
    "mip_palette": [],
    "no_permissions": [],
    "devices_in_manifest": [],
    "uses_api": ["pattern"],
    "pattern": ["pattern"],
    "null_guard": ["pattern"],
    "forbid": ["pattern"],
    "setting_property": ["id"],
    "min_colors": ["n"],
}


def normalize_check(c):
    """A check is a bare name ('mip_palette') or a mapping with a `check` key."""
    if isinstance(c, str):
        c = {"check": c}
    if not isinstance(c, dict) or "check" not in c:
        raise ValueError(f"bad check entry: {c!r}")
    return c


def validate_task(task, path="<task>"):
    if not isinstance(task, dict):
        raise ValueError(f"{path}: task must be a mapping")
    for k in ("id", "title", "prompt", "devices", "required"):
        if not task.get(k):
            raise ValueError(f"{path}: missing '{k}'")
    if not isinstance(task["devices"], list) or not isinstance(task["required"], list):
        raise ValueError(f"{path}: 'devices' and 'required' must be lists")
    task["required"] = [normalize_check(c) for c in task["required"]]
    for c in task["required"]:
        t = c["check"]
        if t not in CHECK_TYPES:
            raise ValueError(f"{path}: unknown check '{t}'")
        for k in CHECK_TYPES[t]:
            if k not in c:
                raise ValueError(f"{path}: check '{t}' needs '{k}'")
        if "pattern" in c:
            try:
                re.compile(c["pattern"])
            except re.error as e:
                raise ValueError(f"{path}: bad regex {c['pattern']!r}: {e}")
    task["compile"] = bool(task.get("compile", False))
    return task


def list_tasks(tasks_dir=None):
    d = tasks_dir or os.path.join(HERE, "tasks")
    return sorted(glob.glob(os.path.join(d, "*.yaml")) + glob.glob(os.path.join(d, "*.json")))


# ------------------------------------------------------------------ source helpers

def strip_comments(src):
    """Remove // and /* */ comments, keeping string literals intact."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == '"':
            j = i + 1
            while j < n and src[j] != '"':
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1])
            i = j + 1
        elif src.startswith("//", i):
            while i < n and src[i] != "\n":
                i += 1
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
        else:
            out.append(c)
            i += 1
    return "".join(out)


def read_source(project):
    files = sorted(glob.glob(os.path.join(project, "source", "**", "*.mc"), recursive=True))
    parts = []
    for fp in files:
        with open(fp, encoding="utf-8", errors="replace") as f:
            parts.append(strip_comments(f.read()))
    return "\n".join(parts), files


def resource_xml_text(project):
    parts = []
    for fp in sorted(glob.glob(os.path.join(project, "resources*", "**", "*.xml"), recursive=True)):
        with open(fp, encoding="utf-8", errors="replace") as f:
            parts.append((fp, f.read()))
    return parts


# ------------------------------------------------------------------ checks

def _result(check, ok, detail=""):
    r = {"check": check["check"], "label": check.get("label") or check.get("pattern") or check.get("id") or "", "status": "pass" if ok else "fail"}
    if detail:
        r["detail"] = detail
    return r


def run_check(check, ctx):
    t = check["check"]
    lint, lint_mip, code, manifest = ctx["lint"], ctx["lint_mip"], ctx["code"], ctx["manifest"]
    if t == "manifest_valid":
        bad = [i["msg"] for i in lint["issues"] if i["check"] == "manifest"]
        return _result(check, not bad, "; ".join(bad))
    if t == "resources_valid":
        bad = [i["msg"] for i in lint["issues"] if i["check"] == "resources"]
        return _result(check, not bad, "; ".join(bad))
    if t == "mip_palette":
        if not ctx["files"]:
            return _result(check, False, "no source/*.mc files")
        bad = [i["msg"] for i in lint_mip["issues"] if i["check"] == "palette"]
        return _result(check, not bad, "; ".join(bad[:3]))
    if t == "no_permissions":
        if manifest is None:
            return _result(check, False, "no valid manifest")
        return _result(check, not manifest["permissions"], f"permissions: {manifest['permissions']}" if manifest["permissions"] else "")
    if t == "devices_in_manifest":
        if manifest is None:
            return _result(check, False, "no valid manifest")
        missing = [d for d in ctx["task"]["devices"] if d not in manifest["products"]]
        return _result(check, not missing, f"missing products: {missing}" if missing else "")
    if t in ("uses_api", "pattern", "null_guard"):
        ok = re.search(check["pattern"], code, re.M) is not None
        return _result(check, ok, "" if ok else "pattern not found in source/*.mc")
    if t == "forbid":
        m = re.search(check["pattern"], code, re.M)
        return _result(check, m is None, f"found: {m.group(0)[:60]!r}" if m else "")
    if t == "min_colors":
        colors = {m.group(1).upper() for m in ciq_lint.HEX_RE.finditer(code)}
        ok = len(colors) >= int(check["n"])
        return _result(check, ok, f"{len(colors)} distinct 0xRRGGBB literals, need {check['n']}")
    if t == "setting_property":
        pid = check["id"]
        problems = []
        res = resource_xml_text(ctx["project"])
        prop_ok = any(re.search(r'<property\s[^>]*id="%s"' % re.escape(pid), txt) for _, txt in res)
        set_ok = any(re.search(r'<setting\s[^>]*propertyKey="@Properties\.%s"' % re.escape(pid), txt) for _, txt in res)
        # direct call getValue("Id"), or a helper that calls getValue(key) while "Id" appears as a string literal
        use_ok = (re.search(r"Properties\.getValue\(\s*[\"']%s[\"']\s*\)" % re.escape(pid), code) is not None
                  or (re.search(r"Properties\.getValue\(", code) is not None
                      and re.search(r"[\"']%s[\"']" % re.escape(pid), code) is not None))
        if not prop_ok:
            problems.append("no <property> in resources")
        if not set_ok:
            problems.append("no <setting propertyKey> in resources")
        if not use_ok:
            problems.append("source never calls Properties.getValue")
        if "min_entries" in check:
            n = sum(len(re.findall(r"<listEntry\b", txt)) for _, txt in res)
            if n < int(check["min_entries"]):
                problems.append(f"{n} <listEntry> found, need {check['min_entries']}")
        return _result(check, not problems, "; ".join(problems))
    raise ValueError(f"unknown check {t}")  # validate_task prevents this


def run_compile(task, project):
    """Returns (status, detail). status in pass|fail|skipped."""
    exe = shutil.which("monkeyc")
    key = os.environ.get("CIQ_DEV_KEY")
    if not exe:
        return "skipped", "monkeyc not on PATH"
    if not key:
        return "skipped", "CIQ_DEV_KEY not set"
    if not os.path.isfile(os.path.join(project, "monkey.jungle")):
        return "fail", "monkey.jungle not found"
    outdir = tempfile.mkdtemp(prefix="ciq-bench-")
    try:
        for dev in task["devices"]:
            out = os.path.join(outdir, f"{dev}.prg")
            try:
                p = subprocess.run([exe, "-d", dev, "-f", "monkey.jungle", "-o", out, "-y", key],
                                   cwd=project, capture_output=True, text=True, timeout=300)
            except subprocess.TimeoutExpired:
                return "fail", f"{dev}: monkeyc timed out"
            if p.returncode != 0 or not os.path.isfile(out):
                tail = (p.stdout + p.stderr).strip().splitlines()[-3:]
                return "fail", f"{dev}: " + " | ".join(tail)
        return "pass", ""
    finally:
        shutil.rmtree(outdir, ignore_errors=True)


def score_project(task, project, compile_=False):
    checks, summary = [], {}
    if not os.path.isdir(project):
        for c in task["required"]:
            checks.append({"check": c["check"], "label": c.get("pattern") or c.get("id") or "", "status": "fail",
                           "detail": f"project dir not found: {project}"})
        passed, total = 0, len(checks)
        return {"task": task["id"], "project": project, "passed": passed, "total": total, "score": 0.0,
                "compile": "skipped", "checks": checks, "error": "project dir not found"}
    lint = ciq_lint.lint(project, mip=False)
    lint_mip = ciq_lint.lint(project, mip=True)
    code, files = read_source(project)
    ctx = {"task": task, "project": project, "lint": lint, "lint_mip": lint_mip, "code": code,
           "files": files, "manifest": lint["manifest"]}
    for c in task["required"]:
        checks.append(run_check(c, ctx))
    compile_status = "skipped"
    if compile_ and task["compile"]:
        compile_status, detail = run_compile(task, project)
        entry = {"check": "compile", "label": ",".join(task["devices"]), "status": compile_status}
        if detail:
            entry["detail"] = detail
        checks.append(entry)
    elif compile_:
        compile_status = "not_requested_by_task"
    counted = [c for c in checks if c["status"] in ("pass", "fail")]
    passed = sum(1 for c in counted if c["status"] == "pass")
    total = len(counted)
    return {"task": task["id"], "project": project, "passed": passed, "total": total,
            "score": round(passed / total, 4) if total else 0.0, "compile": compile_status, "checks": checks}


def print_prompt(task):
    pre = os.path.join(HERE, "prompt_preamble.md")
    with open(pre, encoding="utf-8") as f:
        preamble = f.read().rstrip()
    return f"{preamble}\n\nDevices: {', '.join(task['devices'])}\n\n{task['prompt'].rstrip()}\n"


# ------------------------------------------------------------------ cli

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", help="task file (.yaml/.json)")
    ap.add_argument("--project", help="generated project directory")
    ap.add_argument("--all", action="store_true", help="run every task in bench/tasks")
    ap.add_argument("--projects-dir", help="with --all: directory holding <task_id>/ projects")
    ap.add_argument("--tasks-dir", help="override bench/tasks")
    ap.add_argument("--compile", action="store_true", help="also run monkeyc for tasks with compile: true")
    ap.add_argument("--print-prompt", metavar="TASK", help="print the full prompt for a task and exit")
    ap.add_argument("--out", help="also write the JSON report to this file")
    args = ap.parse_args(argv)

    if args.print_prompt:
        sys.stdout.write(print_prompt(load_task(args.print_prompt)))
        return 0

    if args.all:
        if not (args.projects_dir or args.project):
            ap.error("--all needs --projects-dir <dir> (or --project <dir> for a single shared project)")
        results = []
        for tp in list_tasks(args.tasks_dir):
            task = load_task(tp)
            proj = args.project or os.path.join(args.projects_dir, task["id"])
            results.append(score_project(task, proj, args.compile))
        scores = [r["score"] for r in results]
        report = {"tasks": results, "mean_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
                  "tasks_perfect": sum(1 for r in results if r["total"] and r["passed"] == r["total"]),
                  "task_count": len(results)}
    else:
        if not (args.task and args.project):
            ap.error("need --task and --project (or --all)")
        report = score_project(load_task(args.task), args.project, args.compile)

    text = json.dumps(report, indent=2)
    print(text)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
