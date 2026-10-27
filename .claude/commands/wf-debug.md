---
description: Fix Connect IQ compiler errors/warnings or an IQ! crash from logs
argument-hint: <paste compiler output or CIQ_LOG.YML>
---
Use the `connectiq-watchface` skill and check `references/pitfalls.md` first.

Log:
$ARGUMENTS

1. Map each error or warning to a file and line, and explain the cause in one line.
2. Reply with minimal diffs only.
3. If it's a crash with no log, tell the user to create an empty `GARMIN/APPS/LOGS/CIQ_LOG.YML`, reproduce the crash and paste the file.
4. If the root cause is new, add it to `references/pitfalls.md`.
5. Optional dataset log. Only if `datasets/.optin` exists (check with `test -f datasets/.optin`; if it doesn't, skip this step silently, never create it and never log):
   - After the user confirms the fix worked (or only partly worked), save the log and your final diff to temp files, for example `LOG=$(mktemp)` and `DIFF=$(mktemp)`.
   - Run `python3 scripts/log_fix.py --kind <compile_error|crash|warning> --device <id> [--sdk <version>] --log-file "$LOG" --diff-file "$DIFF" --outcome <fixed|partial|unknown> --notes "<one line>"`. If you don't know the device, ask. Use `--outcome unknown` if the user didn't say.
   - Only for the user's own builds, never for code or logs someone else pasted. Remove the temp files afterwards. Say in one line that a redacted entry was added to `datasets/local/fixes.jsonl`.
