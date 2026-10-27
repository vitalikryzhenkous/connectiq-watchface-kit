import json
import os
import stat
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.dirname(HERE)
ROOT = os.path.dirname(BENCH)
sys.path.insert(0, BENCH)

import run  # noqa: E402

TEMPLATE = os.path.join(ROOT, "templates", "n3on-terminal")
TASKS = run.list_tasks()
TASK_BY_ID = {run.load_task(p)["id"]: p for p in TASKS}

# tasks the n3on-terminal template must solve completely (reference solution)
REFERENCE_PERFECT = ["t01_digital_time", "t02_time_date_12_24", "t03_steps_battery",
                     "t04_weather_null_safe", "t05_sun_offline", "t06_theme_setting", "t07_mip_palette"]


def score(task_id, project=TEMPLATE, **kw):
    return run.score_project(run.load_task(TASK_BY_ID[task_id]), project, **kw)


# ---- task loading ------------------------------------------------------------

def test_ten_seed_tasks_with_unique_ids():
    assert len(TASKS) == 10
    ids = [run.load_task(p)["id"] for p in TASKS]
    assert len(set(ids)) == 10


@pytest.mark.parametrize("path", TASKS, ids=os.path.basename)
def test_task_schema(path):
    t = run.load_task(path)
    assert t["title"] and t["prompt"].strip()
    assert isinstance(t["devices"], list) and t["devices"]
    assert all(isinstance(d, str) for d in t["devices"])
    assert len(t["required"]) >= 5
    assert all(c["check"] in run.CHECK_TYPES for c in t["required"])


@pytest.mark.parametrize("path", TASKS, ids=os.path.basename)
def test_fallback_parser_matches_pyyaml(path):
    yaml = pytest.importorskip("yaml")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    a = run.validate_task(yaml.safe_load(text))
    b = run.validate_task(run.mini_yaml(text))
    assert a == b


def test_tasks_get_harder():
    diffs = [run.load_task(p)["difficulty"] for p in TASKS]
    assert diffs == sorted(diffs) and diffs[0] == 1 and diffs[-1] == 10


def test_mini_yaml_subset():
    d = run.mini_yaml("""\
# comment
id: x
n: 3
flag: true
devices: [fr945, 'fenix7']
prompt: |
  line one
    indented
  line three
required:
  - manifest_valid
  - {check: pattern, pattern: 'a, b: c\\s+''q''', label: "x, y"}
""")
    assert d["id"] == "x" and d["n"] == 3 and d["flag"] is True
    assert d["devices"] == ["fr945", "fenix7"]
    assert d["prompt"] == "line one\n  indented\nline three\n"
    assert d["required"][0] == "manifest_valid"
    assert d["required"][1] == {"check": "pattern", "pattern": "a, b: c\\s+'q'", "label": "x, y"}


def test_validate_rejects_bad_tasks():
    base = {"id": "a", "title": "t", "prompt": "p", "devices": ["fr945"], "required": ["manifest_valid"]}
    run.validate_task(dict(base))
    with pytest.raises(ValueError):
        run.validate_task({**base, "required": ["nope"]})
    with pytest.raises(ValueError):
        run.validate_task({**base, "required": [{"check": "pattern"}]})
    with pytest.raises(ValueError):
        run.validate_task({**base, "required": [{"check": "pattern", "pattern": "("}]})
    with pytest.raises(ValueError):
        run.validate_task({k: v for k, v in base.items() if k != "prompt"})


def test_json_tasks_supported(tmp_path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"id": "j", "title": "t", "prompt": "p", "devices": ["fr945"],
                             "required": ["manifest_valid", {"check": "uses_api", "pattern": "X"}]}))
    assert run.load_task(str(p))["required"][0] == {"check": "manifest_valid"}


def test_strip_comments_keeps_strings():
    src = 'var a = "http://x"; // Weather.getCurrentConditions()\n/* onEnterSleep */ var b = 1;'
    out = run.strip_comments(src)
    assert '"http://x"' in out and "Weather" not in out and "onEnterSleep" not in out and "var b" in out


# ---- scoring against the reference template -------------------------------------

@pytest.mark.parametrize("task_id", REFERENCE_PERFECT)
def test_template_is_reference_solution(task_id):
    r = score(task_id)
    failed = [c for c in r["checks"] if c["status"] != "pass"]
    assert not failed, failed
    assert r["score"] == 1.0 and r["passed"] == r["total"] > 0
    assert r["compile"] == "skipped"


def test_template_fails_what_it_should():
    r = score("t09_multi_device")
    failed = {c["check"] for c in r["checks"] if c["status"] == "fail"}
    assert failed == {"devices_in_manifest"}
    assert r["passed"] == r["total"] - 1 and r["score"] < 1.0
    r = score("t10_amoled_low_power")
    failed = {c["check"] for c in r["checks"] if c["status"] == "fail"}
    assert "devices_in_manifest" in failed
    assert r["score"] < 1.0


# ---- scoring edge cases ----------------------------------------------------------

def test_missing_project_scores_zero():
    r = score("t01_digital_time", project="/nonexistent/project")
    assert r["score"] == 0.0 and r["passed"] == 0 and r["total"] == len(run.load_task(TASK_BY_ID["t01_digital_time"])["required"])


def make_project(tmp_path, source, devices=("fr945",), permissions=(), extra_resources=None, name="proj"):
    p = tmp_path / name
    (p / "source").mkdir(parents=True)
    (p / "resources" / "drawables").mkdir(parents=True)
    (p / "resources" / "strings").mkdir(parents=True)
    prods = "".join(f'<iq:product id="{d}"/>' for d in devices)
    perms = "".join(f'<iq:uses-permission id="{x}"/>' for x in permissions)
    (p / "manifest.xml").write_text(
        '<?xml version="1.0"?><iq:manifest version="3" xmlns:iq="http://www.garmin.com/xml/connectiq">'
        '<iq:application id="0123456789abcdef0123456789abcdef" type="watchface" name="@Strings.AppName" '
        f'entry="App" launcherIcon="@Drawables.LauncherIcon" minApiLevel="3.2.0"><iq:products>{prods}</iq:products>'
        f'<iq:permissions>{perms}</iq:permissions></iq:application></iq:manifest>')
    (p / "monkey.jungle").write_text("project.manifest = manifest.xml\n")
    (p / "resources" / "drawables" / "drawables.xml").write_text(
        '<drawables><bitmap id="LauncherIcon" filename="launcher_icon.png"/></drawables>')
    (p / "resources" / "drawables" / "launcher_icon.png").write_bytes(b"x")
    (p / "resources" / "strings" / "strings.xml").write_text('<strings><string id="AppName">T</string></strings>')
    for name, text in (extra_resources or {}).items():
        f = p / "resources" / name
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)
    (p / "source" / "A.mc").write_text(source)
    return str(p)


def statuses(r):
    return {(c["check"], c["label"]): c["status"] for c in r["checks"]}


def test_minimal_project_passes_t01(tmp_path):
    src = """import Toybox.WatchUi;
import Toybox.System;
class App extends Application.AppBase { function getInitialView() { return [ new V() ]; } }
class V extends WatchUi.WatchFace {
    function onUpdate(dc) { var t = System.getClockTime(); dc.drawText(1, 1, 0, t.hour.format("%02d"), 0); }
}"""
    r = score("t01_digital_time", project=make_project(tmp_path, src))
    assert r["score"] == 1.0, r["checks"]


def test_comment_only_mentions_do_not_count(tmp_path):
    src = "// System.getClockTime()\nclass V extends WatchUi.WatchFace { function onUpdate(dc) {} }"
    r = score("t01_digital_time", project=make_project(tmp_path, src))
    assert statuses(r)[("uses_api", "System\\.getClockTime\\(\\)")] == "fail"
    assert r["score"] < 1.0


def test_non_mip_color_and_permissions_fail(tmp_path):
    src = "class V extends WatchUi.WatchFace { function onUpdate(dc) { dc.setColor(0x123456, 0); } }"
    r = score("t07_mip_palette", project=make_project(tmp_path, src, permissions=["Positioning"]))
    st = statuses(r)
    assert st[("mip_palette", "")] == "fail"
    assert st[("no_permissions", "")] == "fail"
    assert any(c["check"] == "mip_palette" and "0x123456" in c["detail"] for c in r["checks"])


def test_weather_without_null_guards_fails(tmp_path):
    src = ("class V extends WatchUi.WatchFace { function onUpdate(dc) {"
           " var t = Weather.getCurrentConditions().temperature; } }")
    r = score("t04_weather_null_safe", project=make_project(tmp_path, src))
    st = statuses(r)
    assert st[("forbid", "no unguarded chained access")] == "fail"
    assert st[("null_guard", "module guard")] == "fail"
    assert st[("null_guard", "temperature null guard")] == "fail"
    assert r["score"] < 0.6


def test_setting_property_requires_all_three_parts(tmp_path):
    src = 'var v = Application.Properties.getValue("Theme");'
    props = '<properties><property id="Theme" type="number">0</property></properties>'
    sets = ('<settings><setting propertyKey="@Properties.Theme" title="@Strings.T"><settingConfig type="list">'
            '<listEntry value="0">a</listEntry><listEntry value="1">b</listEntry><listEntry value="2">c</listEntry>'
            '</settingConfig></setting></settings>')
    full = make_project(tmp_path, src, extra_resources={"settings/properties.xml": props, "settings/settings.xml": sets})
    r = score("t06_theme_setting", project=full)
    assert statuses(r)[("setting_property", "Theme")] == "pass"

    only_props = make_project(tmp_path, src, extra_resources={"settings/properties.xml": props}, name="b")
    r = score("t06_theme_setting", project=only_props)
    c = [c for c in r["checks"] if c["check"] == "setting_property"][0]
    assert c["status"] == "fail" and "<setting propertyKey>" in c["detail"]


def test_min_colors_counts_distinct_literals(tmp_path):
    t = {"id": "a", "title": "t", "prompt": "p", "devices": ["fr945"],
         "required": [{"check": "min_colors", "n": 3}]}
    t = run.validate_task(t)
    p2 = make_project(tmp_path, "var a = 0xFF0000; var b = 0xff0000; var c = 0x00FF00;")
    assert run.score_project(t, p2)["score"] == 0.0
    (tmp_path / "proj" / "source" / "A.mc").write_text("var a = 0xFF0000; var c = 0x00FF00; var d = 0x0000FF;")
    assert run.score_project(t, p2)["score"] == 1.0


# ---- compile step ---------------------------------------------------------------------

def fake_monkeyc(dirpath, fail_on=None):
    exe = dirpath / "monkeyc"
    exe.write_text(f"""#!{sys.executable}
import sys
a = sys.argv[1:]
dev = a[a.index('-d') + 1]
if dev == {fail_on!r}:
    print('ERROR: boom on ' + dev); sys.exit(1)
open(a[a.index('-o') + 1], 'wb').write(b'prg')
""")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    return str(dirpath)


def test_compile_skipped_without_monkeyc(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setenv("CIQ_DEV_KEY", "k")
    r = score("t01_digital_time", compile_=True)
    assert r["compile"] == "skipped"
    c = [c for c in r["checks"] if c["check"] == "compile"][0]
    assert c["status"] == "skipped" and "PATH" in c["detail"]
    assert r["score"] == 1.0 and r["total"] == len(run.load_task(TASK_BY_ID["t01_digital_time"])["required"])


def test_compile_skipped_without_key(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", fake_monkeyc(tmp_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.delenv("CIQ_DEV_KEY", raising=False)
    r = score("t01_digital_time", compile_=True)
    assert r["compile"] == "skipped"
    assert "CIQ_DEV_KEY" in [c for c in r["checks"] if c["check"] == "compile"][0]["detail"]


def test_compile_not_run_without_flag(monkeypatch, tmp_path):
    monkeypatch.setenv("PATH", fake_monkeyc(tmp_path) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("CIQ_DEV_KEY", "k")
    r = score("t01_digital_time")
    assert not [c for c in r["checks"] if c["check"] == "compile"]


def test_compile_pass_and_fail_with_fake_monkeyc(monkeypatch, tmp_path):
    monkeypatch.setenv("CIQ_DEV_KEY", "k")
    monkeypatch.setenv("PATH", fake_monkeyc(tmp_path) + os.pathsep + os.environ["PATH"])
    r = score("t01_digital_time", compile_=True)
    assert r["compile"] == "pass" and r["score"] == 1.0
    assert r["total"] == len(run.load_task(TASK_BY_ID["t01_digital_time"])["required"]) + 1

    d2 = tmp_path / "f"
    d2.mkdir()
    monkeypatch.setenv("PATH", fake_monkeyc(d2, fail_on="fenix7") + os.pathsep + os.environ["PATH"])
    t = run.load_task(TASK_BY_ID["t09_multi_device"])
    proj = make_project(tmp_path, "", name="p")
    r = run.score_project(t, proj, compile_=True)
    assert r["compile"] == "fail"
    assert "fenix7" in [c for c in r["checks"] if c["check"] == "compile"][0]["detail"]


# ---- cli ----------------------------------------------------------------------------------

def test_cli_single_task(capsys):
    assert run.main(["--task", TASK_BY_ID["t01_digital_time"], "--project", TEMPLATE]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["task"] == "t01_digital_time" and rep["score"] == 1.0


def test_cli_all_with_projects_dir(tmp_path, capsys):
    out = tmp_path / "report.json"
    assert run.main(["--all", "--projects-dir", str(tmp_path / "empty"), "--out", str(out)]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["task_count"] == 10 and rep["mean_score"] == 0.0 and rep["tasks_perfect"] == 0
    assert json.loads(out.read_text())["task_count"] == 10


def test_cli_all_with_shared_reference_project(capsys):
    run.main(["--all", "--project", TEMPLATE])
    rep = json.loads(capsys.readouterr().out)
    perfect = {t["task"] for t in rep["tasks"] if t["passed"] == t["total"]}
    assert set(REFERENCE_PERFECT) <= perfect
    assert 0.8 < rep["mean_score"] < 1.0


def test_cli_all_requires_dir():
    with pytest.raises(SystemExit):
        run.main(["--all"])


def test_print_prompt(capsys):
    run.main(["--print-prompt", TASK_BY_ID["t09_multi_device"]])
    out = capsys.readouterr().out
    assert "Monkey C" in out and "Devices: fr945, fenix7" in out and "fenix 7" in out
