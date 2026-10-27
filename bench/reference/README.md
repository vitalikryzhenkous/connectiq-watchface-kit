# Reference solution

`templates/n3on-terminal` (the kit's N3on Terminal face, verified on a real Forerunner 945) is the reference
solution for ConnectIQ-Bench. It scores 100% on the static checks of tasks t01 to t08 (t01-t07 are real fits for
the template's feature set; t08 passes because the face already tracks `onEnterSleep`/`onExitSleep`), and
fails t09/t10 on purpose-built checks (fr945 only, no AMOLED mode).

Reproduce:
```bash
python3 bench/run.py --all --project templates/n3on-terminal            # static
CIQ_DEV_KEY=/path/to/developer_key.der python3 bench/run.py --all --project templates/n3on-terminal --compile
```
The pytest suite (`bench/tests/test_bench.py`) asserts t01-t07 stay perfect, so a change to a task regex that
breaks the reference is caught. Only the template is a reference: the bench does not ship other solutions,
so there is nothing to leak into training data besides the task prompts.

For per-task reference projects (`<dir>/<task_id>/`), copy the template and trim or extend it; each project needs
its own app id (`python3 -c "import uuid;print(uuid.uuid4().hex)"`).
