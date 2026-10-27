---
description: Pre-release gate for a watch face — automated checks + manual checklist before Connect IQ Store export
argument-hint: <face dir, e.g. templates/n3on-terminal> [version, e.g. 1.0.0]
---
Use the `connectiq-watchface` skill (`references/store-listing.md`, `references/pitfalls.md`).

Input: $ARGUMENTS

1. Run `python3 scripts/release_check.py <face>`.
2. For every ❌, explain it in one line and fix it, as diffs:
   - `location`: run `scripts/set_location.py --reset`.
   - `settings`/`naming`: edit the resources.
   - `secrets`: stop. Tell the user to remove the file from git history and rotate the key. Never print secret values.
3. For every ⚠️, say whether it blocks this release.
4. Review by reading the code (the script can't check these):
   - null-guards for weather, location, activity info and properties;
   - nothing animates in low power;
   - Storage writes happen only on change;
   - text fits the round screen on every listed device (render `/wf-preview`).
5. Check that the store listing matches reality: features, settings, supported devices, and screenshots made from the current code (re-render with `scripts/preview_n3on.py ... --frames`).
6. Print the manual checklist from the script as the user's to-do list, plus the release steps:
   - export the `.iq`;
   - upload it to the dashboard as beta and verify phone settings;
   - make it public;
   - `git tag v<version>` and update the README with the store link.
7. Re-run the script until the result reads **READY FOR RELEASE**. Then summarize in 3 bullets.
