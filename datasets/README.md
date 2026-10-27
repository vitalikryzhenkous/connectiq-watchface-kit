# datasets/ — opt-in local fix log

Purpose: keep **your own** compiler-error / crash fixes as (log, diff) pairs, so you can later
fine-tune a small model or build eval cases for Monkey C. This is **not telemetry**: nothing is sent
anywhere, the scripts have no network code, and the data stays on your disk.

## Opt in
```bash
touch datasets/.optin
```
Without `datasets/.optin`, `scripts/log_fix.py` prints this hint and exits 0 without reading or writing anything.
Opt out: `rm datasets/.optin` (delete `datasets/local/` to remove collected data).

`/wf-debug` calls the logger only if the opt-in file exists and only after you confirm the fix worked.

## Manual use
```bash
python3 scripts/log_fix.py --kind compile_error --device fr945 --sdk 8.1.1 \
  --log-file build.log --diff-file fix.diff --outcome fixed --notes "typed the palette array"
# --dry-run prints the redacted record without writing it
```
Entries are appended to `datasets/local/fixes.jsonl` (one JSON object per line).

## Schema (version 1)
| Field | Type | Notes |
|---|---|---|
| `schema_version` | int | `1` |
| `ts` | string | UTC, `YYYY-MM-DDTHH:MM:SSZ` |
| `kind` | string | `compile_error`, `crash` or `warning` |
| `device` | string | product id, e.g. `fr945` |
| `sdk` | string or null | SDK version if known |
| `input` | string | redacted compiler output or `CIQ_LOG.YML` |
| `diff` | string | redacted unified diff of the fix |
| `files_touched` | string[] | paths parsed from the diff headers |
| `outcome` | string | `fixed`, `partial` or `unknown` |
| `notes` | string | free text, redacted |
| `context` | string, optional | only with `--context-file`: relevant code, redacted |

## Redaction (applied before writing, and again on export)
| What | Becomes |
|---|---|
| `/Users/<name>/`, `/home/<name>/`, `C:\Users\<name>\` | `<HOME>/` |
| email addresses | `<EMAIL>` |
| `-----BEGIN ... KEY-----` blocks | `<REDACTED>` |
| hex runs of 32+ chars (also app UUIDs from manifests) | `<REDACTED>` |
| base64-like runs of 32+ chars containing letters and digits, JWTs, `ghp_`/`sk-` style tokens, `Bearer ...`, `api_key=...`/`token=...`/`password=...` values | `<REDACTED>` |

Redaction is heuristic and errs on the side of over-redacting. It does not remove names in source
code, comments, or strings. **Always read the data yourself before you share it.**

## Privacy rules
- Local only. `datasets/local/` and `datasets/.optin` are gitignored; never force-add them.
- Log only fixes to **your own** builds. Never log other people's code, logs or data (a friend's face,
  a client project, a pasted issue from someone else).
- Review `datasets/local/*.jsonl` before sharing or publishing anything derived from it.
- Respect licenses. If a diff or its context contains third-party code (the bundled DejaVu-derived fonts,
  Garmin sample code, other open-source faces), check that license allows the intended use, or drop the record.
  Garmin SDK files and the developer key must never be included.
- Delete anything you are unsure about; an empty dataset is better than a leaky one.

## Export to a fine-tuning chat format
```bash
python3 datasets/export_chat.py                      # fixes.jsonl -> datasets/local/fixes.chat.jsonl
python3 datasets/export_chat.py --outcomes fixed,partial --no-system --output my.jsonl
```
Each line is `{"messages": [...]}` in the common chat format:
- `system` (optional): short instruction to reply with a minimal diff
- `user`: kind/device/sdk, the error log, plus `Code context:` if the record has `context`
- `assistant`: the unified diff

By default only `outcome == "fixed"` records with a non-empty diff are exported.

## Tests
```bash
python3 -m pytest datasets/tests
```
