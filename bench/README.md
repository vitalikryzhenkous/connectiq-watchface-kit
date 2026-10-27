# ConnectIQ-Bench

A small eval for LLMs that write Garmin Connect IQ watch faces in Monkey C.

## Goal
Monkey C is a low-resource language: few public repos, a niche API (Toybox), and device quirks that models
get wrong (MIP 64-color palette, AMOLED burn-in, null weather data, missing modules on old devices).
ConnectIQ-Bench measures whether a model can turn a short spec into a project that
1. passes static checks (valid manifest and resources, MIP palette, required APIs, null guards, settings wiring), and
2. optionally **compiles** with the real Garmin toolchain.

10 seed tasks in `bench/tasks/`, from "digital time on fr945" to "AMOLED always-on mode on fr965".

## How tasks are scored
Each task lists `required` checks. `score = passed / total` (0..1). A task with a missing project dir scores 0.
Check types:

| Check | Passes when |
|---|---|
| `manifest_valid` | `scripts/ciq_lint.py` finds no manifest error or warning (32-hex id, `watchface`, products, launcher icon) |
| `resources_valid` | resource XML parses and every referenced file exists |
| `devices_in_manifest` | every device in the task's `devices` is a `<iq:product>` |
| `no_permissions` | manifest requests no permissions |
| `mip_palette` | every `0xRRGGBB` literal uses channels 00/55/AA/FF (ciq_lint `--mip`) |
| `uses_api` / `pattern` / `null_guard` | `pattern` (regex) matches `source/**/*.mc` after comments are stripped |
| `forbid` | `pattern` does **not** match |
| `min_colors` | at least `n` distinct `0xRRGGBB` literals |
| `setting_property` | `id` exists as `<property>` and as `<setting propertyKey="@Properties.id">` in resources, source reads it via `Properties.getValue`; optional `min_entries` counts `<listEntry>` |
| `compile` | only with `--compile` and `compile: true`: `monkeyc` succeeds for every task device |

`uses_api`, `pattern` and `null_guard` behave identically; the names document intent in the task file.
Compile is `pass`/`fail` when run and counts as one more check. When it is skipped (no `monkeyc`, no
`CIQ_DEV_KEY`, or no `--compile`) it is reported as `"skipped"` and does **not** count in the score.

## Run
```bash
pip install pyyaml          # optional: without it a built-in parser reads the task files
# 1. give the model the prompt
python3 bench/run.py --print-prompt bench/tasks/04_weather_null_safe.yaml
# 2. save its files as <dir>/<task_id>/ (manifest.xml, monkey.jungle, source/, resources/)
#    and add the placeholder icon the models are told not to create:
cp bench/assets/launcher_icon.png <dir>/<task_id>/resources/drawables/
# 3. score
python3 bench/run.py --task bench/tasks/04_weather_null_safe.yaml --project <dir>/t04_weather_null_safe
python3 bench/run.py --all --projects-dir <dir> [--compile] [--out report.json]
```
Output is JSON: per-check `pass`/`fail` with a `detail`, `score`, and for `--all` also `mean_score`.
`--all --project <dir>` scores one project against every task (used for reference runs).

Compile step: `monkeyc -d <device> -f monkey.jungle -o <tmp>/<device>.prg -y $CIQ_DEV_KEY`, run in the project
directory. Needs the Garmin SDK (`monkeyc` on `PATH`) and a developer key (`export CIQ_DEV_KEY=/path/to/developer_key.der`).

## Add a task
Create `bench/tasks/NN_name.yaml` (or `.json`):
```yaml
id: t11_my_task            # unique
title: Short title
difficulty: 5
devices: [fr945]           # manifest product ids
compile: true              # compile when --compile is given
prompt: |                  # the spec shown to the model
  Build ...
required:
  - manifest_valid
  - {check: pattern, pattern: 'onEnterSleep', label: sleep hook}   # single-quote regexes, no escaping needed
  - {check: forbid, pattern: 'Timer\.Timer'}
```
The built-in parser supports this subset only: top-level `key: value`, `|` blocks, `- item` lists with scalars or
`{a: b}` / `[a, b]` flow items, no nesting. `pytest bench/tests` checks that it agrees with PyYAML on every task.
Validate your regexes against `templates/n3on-terminal` or a hand-written solution before adding the task.

## Limitations
- Static checks are regexes. They show that required constructs exist, not that the face works or looks right.
  A model can satisfy them with dead code, and a valid solution written in an unusual style can miss them.
  Treat the static score as necessary, not sufficient.
- Checks are not device-aware beyond the manifest: `fr945` code that is valid on one device passes on any.
- `mip_palette` only sees `0xRRGGBB` literals (and the `forbid` check catches long decimal literals).
  Colors computed at runtime are not checked.
- Compile needs a local Garmin SDK and a developer key. **The SDK can't be redistributed**, so it is not
  bundled and CI without it only runs the static part. Compiling still doesn't prove runtime behavior (use the
  simulator or a watch for that).
- Models can't write binary files: the harness copies `bench/assets/launcher_icon.png` (the kit's own icon).
- 10 tasks and one reference face is a seed set, not a statistically solid benchmark. Don't train on it if you want to
  evaluate with it.

## Reference solution
`templates/n3on-terminal` is the reference; see [reference/README.md](reference/README.md).
Results of `python3 bench/run.py --all --project templates/n3on-terminal` (static only, compile skipped):

| Task | Passed | Score | Failed checks |
|---|---|---|---|
| t01_digital_time | 10/10 | 1.00 | |
| t02_time_date_12_24 | 12/12 | 1.00 | |
| t03_steps_battery | 11/11 | 1.00 | |
| t04_weather_null_safe | 13/13 | 1.00 | |
| t05_sun_offline | 13/13 | 1.00 | |
| t06_theme_setting | 11/11 | 1.00 | |
| t07_mip_palette | 12/12 | 1.00 | |
| t08_sleep_animation | 11/11 | 1.00 | |
| t09_multi_device | 10/11 | 0.91 | `devices_in_manifest` (only fr945 listed) |
| t10_amoled_low_power | 11/13 | 0.85 | `devices_in_manifest`, burn-in API |

Mean 0.976, 8 of 10 perfect. The template is a complete solution for t01-t08 as far as the static checks go; it was
not compiled in this run (no SDK in the environment), though the face has been built and run on a real fr945.
t09 and t10 need real changes (more products, AMOLED layout), and the near-perfect scores there show how weak
a static-only score is, which is why `--compile` matters.

---
Part of [connectiq-watchface-kit](../README.md). Like it? [Buy me a coffee](https://buymeacoffee.com/vitaliiryzhenko) ☕
