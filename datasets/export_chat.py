#!/usr/bin/env python3
"""Convert datasets/local/fixes.jsonl to a chat "messages" JSONL for fine-tuning.

  python3 datasets/export_chat.py [--input F] [--output F] [--outcomes fixed,partial] [--no-system]

Each output line: {"messages": [system?, user, assistant]}
  user      = kind/device/sdk header + error log (+ relevant code context if the record has one)
  assistant = the unified diff of the fix
Records with an empty diff or an outcome not in --outcomes (default: fixed) are skipped.
Text is passed through the redactor again as a safety net. Review the file before sharing it.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from log_fix import redact  # noqa: E402

SYSTEM_PROMPT = ("You fix Garmin Connect IQ (Monkey C) watch face build errors and crashes. "
                 "Reply with a minimal unified diff only.")


def user_message(rec):
    head = [f"kind: {rec.get('kind', 'unknown')}", f"device: {rec.get('device', 'unknown')}"]
    if rec.get("sdk"):
        head.append(f"sdk: {rec['sdk']}")
    parts = ["\n".join(head), "Log:\n" + (rec.get("input") or "").rstrip()]
    if rec.get("context"):
        parts.append("Code context:\n" + rec["context"].rstrip())
    return redact("\n\n".join(parts))


def convert(records, outcomes=("fixed",), system=True):
    for rec in records:
        diff = (rec.get("diff") or "").strip("\n")
        if not diff or rec.get("outcome") not in outcomes:
            continue
        msgs = []
        if system:
            msgs.append({"role": "system", "content": SYSTEM_PROMPT})
        msgs.append({"role": "user", "content": user_message(rec)})
        msgs.append({"role": "assistant", "content": redact(diff) + "\n"})
        yield {"messages": msgs}


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"warning: {path}:{n}: skipped ({e})", file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(HERE, "local", "fixes.jsonl"))
    ap.add_argument("--output", default=os.path.join(HERE, "local", "fixes.chat.jsonl"))
    ap.add_argument("--outcomes", default="fixed", help="comma list of outcomes to include")
    ap.add_argument("--no-system", action="store_true", help="omit the system message")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.input):
        print(f"nothing to export: {args.input} not found (see datasets/README.md)")
        return 0
    outcomes = tuple(o.strip() for o in args.outcomes.split(",") if o.strip())
    rows = list(convert(read_jsonl(args.input), outcomes, system=not args.no_system))
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"exported {len(rows)} example(s) -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
