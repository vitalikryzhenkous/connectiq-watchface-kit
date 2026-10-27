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
