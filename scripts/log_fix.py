#!/usr/bin/env python3
"""Opt-in LOCAL logger for Connect IQ fixes (your own fine-tuning / eval data).

  python3 scripts/log_fix.py --kind compile_error --device fr945 \
      --log-file /tmp/log.txt --diff-file /tmp/fix.diff --outcome fixed --notes "..."

Never telemetry: nothing is sent anywhere. It only appends one JSON line to
datasets/local/fixes.jsonl (gitignored), and only if the file datasets/.optin
exists. Without it the script prints how to opt in and exits 0 without
reading or writing anything.

Everything is redacted before it is written (home paths, emails, tokens/keys,
32-hex app ids). See datasets/README.md.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

SCHEMA_VERSION = 1
KINDS = ("compile_error", "crash", "warning")
OUTCOMES = ("fixed", "partial", "unknown")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------- redaction

PEM_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*KEY-----[\s\S]*?(?:-----END [A-Z0-9 ]*KEY-----|\Z)")
# /Users/<name>/ and /home/<name>/
UNIX_HOME_RE = re.compile(r"/(?:Users|home)/[^/\s\"'<>|:\\]+/")
UNIX_HOME_END_RE = re.compile(r"/(?:Users|home)/[^/\s\"'<>|:\\]+(?=$|[\s\"'])", re.M)
# C:\Users\<name>\  (also C:/Users/<name>/ and JSON-escaped C:\\Users\\<name>\\)
WIN_HOME_RE = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"'<>|:]+[\\/]+", re.I)
WIN_HOME_END_RE = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"'<>|:]+(?=$|[\s\"'])", re.I | re.M)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
HEX_RE = re.compile(r"(?<![0-9A-Za-z])[0-9a-fA-F]{32,}(?![0-9A-Za-z])")
B64_RE = re.compile(r"(?<![A-Za-z0-9+/_=-])[A-Za-z0-9+/_-]{32,}={0,2}(?![A-Za-z0-9+/_-])")
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*")
PREFIXED_RE = re.compile(
    r"\b(?:ghp|gho|ghs|ghu|github_pat|sk|pk|xox[abpr])[-_][A-Za-z0-9_-]{16,}")
BEARER_RE = re.compile(r"\b(Bearer)\s+[A-Za-z0-9._~+/-]{8,}=*", re.I)
KEYVAL_RE = re.compile(
    r"(?i)\b((?:api[_-]?key|secret|token|passw(?:or)?d|authorization)\w*)"
    r"(\s*[:=]\s*)([\"']?)([^\s\"',;]{8,})\3")
# lines where file paths live: skip the "long base64" heuristic so paths survive
DIFF_HEADER_PREFIXES = ("--- ", "+++ ", "diff --git ", "rename ", "index ")

REDACTED = "<REDACTED>"


def _b64_sub(m):
    s = m.group(0)
    # needs a letter and a digit, otherwise it is an ordinary long identifier
    if re.search(r"[A-Za-z]", s) and re.search(r"[0-9]", s):
        return REDACTED
    return s


def _redact_tokens(line):
    line = JWT_RE.sub(REDACTED, line)
    line = PREFIXED_RE.sub(REDACTED, line)
    line = BEARER_RE.sub(lambda m: m.group(1) + " " + REDACTED, line)
    line = KEYVAL_RE.sub(lambda m: m.group(1) + m.group(2) + m.group(3) + REDACTED + m.group(3), line)
    line = HEX_RE.sub(REDACTED, line)
    return B64_RE.sub(_b64_sub, line)


def redact(text):
    """Scrub personal data and secrets from text. Idempotent."""
    if not text:
        return text
    text = PEM_RE.sub(REDACTED, text)
    text = WIN_HOME_RE.sub("<HOME>/", text)
    text = WIN_HOME_END_RE.sub("<HOME>", text)
    text = UNIX_HOME_RE.sub("<HOME>/", text)
    text = UNIX_HOME_END_RE.sub("<HOME>", text)
    text = EMAIL_RE.sub("<EMAIL>", text)
    out = []
    for line in text.split("\n"):
        if line.startswith(DIFF_HEADER_PREFIXES):
            # headers: only hex ids (32 chars) are safe to strip, keep path text
            out.append(HEX_RE.sub(REDACTED, line))
        else:
            out.append(_redact_tokens(line))
    return "\n".join(out)


# ---------------------------------------------------------------- diff parsing

def files_touched(diff):
    """File paths from unified-diff headers, in order, de-duplicated."""
    files = []

    def add(p):
        p = p.split("\t", 1)[0].strip().strip('"')
        if not p or p == "/dev/null":
            return
        if p.startswith(("a/", "b/")):
            p = p[2:]
        if p not in files:
            files.append(p)

    old = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            m = re.match(r"diff --git (\S+) (\S+)", line)
            if m:
                add(m.group(2))
            old = None
        elif line.startswith("--- "):
            old = line[4:]
        elif line.startswith("+++ "):
            new = line[4:].split("\t", 1)[0].strip()
            add(old if (new == "/dev/null" and old) else line[4:])
            old = None
    return files


# ---------------------------------------------------------------- record + io

def build_record(kind, device, sdk, log_text, diff_text, outcome, notes, context=None, now=None):
    diff = redact(diff_text)
    rec = {
        "schema_version": SCHEMA_VERSION,
        "ts": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": kind,
        "device": redact(device),
        "sdk": redact(sdk) if sdk else None,
        "input": redact(log_text),
        "diff": diff,
        "files_touched": files_touched(diff),
        "outcome": outcome,
        "notes": redact(notes or ""),
    }
    if context:
        rec["context"] = redact(context)
    return rec


def optin_path(root):
    return os.path.join(root, "datasets", ".optin")


def out_path(root):
    return os.path.join(root, "datasets", "local", "fixes.jsonl")


def append_record(rec, root):
    path = out_path(root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


OPTIN_HELP = """Fix logging is OFF (opt-in only, local only, never sent anywhere).
To enable it for your own builds:

    touch datasets/.optin

Entries are appended to datasets/local/fixes.jsonl (gitignored) after redaction.
Details: datasets/README.md. Nothing was logged."""


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main(argv=None, root=None):
    root = root or ROOT
    ap = argparse.ArgumentParser(description="Append one redacted fix record to datasets/local/fixes.jsonl (opt-in).")
    ap.add_argument("--kind", required=True, choices=KINDS)
    ap.add_argument("--device", required=True, help="e.g. fr945")
    ap.add_argument("--sdk", help="SDK version, e.g. 8.1.1")
    ap.add_argument("--log-file", required=True, help="raw compiler output or CIQ_LOG.YML")
    ap.add_argument("--diff-file", required=True, help="unified diff of the fix")
    ap.add_argument("--context-file", help="optional: relevant code context (redacted too)")
    ap.add_argument("--outcome", choices=OUTCOMES, default="unknown")
    ap.add_argument("--notes", default="")
    ap.add_argument("--dry-run", action="store_true", help="print the redacted record, write nothing")
    args = ap.parse_args(argv)

    if not os.path.isfile(optin_path(root)):
        print(OPTIN_HELP)
        return 0

    for p in (args.log_file, args.diff_file) + ((args.context_file,) if args.context_file else ()):
        if not os.path.isfile(p):
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2

    rec = build_record(args.kind, args.device, args.sdk, _read(args.log_file), _read(args.diff_file),
                       args.outcome, args.notes,
                       context=_read(args.context_file) if args.context_file else None)
    if args.dry_run:
        print(json.dumps(rec, indent=2, ensure_ascii=False))
        return 0
    path = append_record(rec, root)
    print(f"logged 1 fix ({rec['kind']}, {rec['outcome']}) -> {os.path.relpath(path, root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
