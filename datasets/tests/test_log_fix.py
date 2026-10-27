import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "datasets"))

import log_fix  # noqa: E402
import export_chat  # noqa: E402

DIFF = """\
diff --git a/source/View.mc b/source/View.mc
index 111..222 100644
--- a/source/View.mc
+++ b/source/View.mc
@@ -1,3 +1,3 @@
-var pal = [1, 2];
+var pal as Array<Number> = [1, 2];
--- /dev/null
+++ b/resources/new.xml
@@ -0,0 +1 @@
+<x/>
"""


# ---- redaction -------------------------------------------------------------

@pytest.mark.parametrize("src,expected", [
    ("/Users/alice/dev/face/source/A.mc:3", "<HOME>/dev/face/source/A.mc:3"),
    ("at /home/bob/work/x.mc", "at <HOME>/work/x.mc"),
    ("C:\\Users\\Carol\\Documents\\face\\A.mc", "<HOME>/Documents\\face\\A.mc"),
    ("C:\\\\Users\\\\Carol\\\\face", "<HOME>/face"),
    ("C:/Users/Dave/face", "<HOME>/face"),
    ("cwd=/Users/erin", "cwd=<HOME>"),
])
def test_home_paths(src, expected):
    out = log_fix.redact(src)
    assert out == expected
    for name in ("alice", "bob", "Carol", "Dave", "erin"):
        assert name not in out


def test_emails():
    out = log_fix.redact("author: jane.doe+kit@example.co.uk, cc a_b@x.io")
    assert out == "author: <EMAIL>, cc <EMAIL>"


def test_monkeyc_resource_refs_are_not_emails():
    s = 'name="@Strings.AppName" launcherIcon="@Drawables.LauncherIcon"'
    assert log_fix.redact(s) == s


def test_pem_block():
    s = "before\n-----BEGIN PRIVATE KEY-----\nAAAA\nBBBB\n-----END PRIVATE KEY-----\nafter"
    out = log_fix.redact(s)
    assert out == "before\n<REDACTED>\nafter"
    assert "AAAA" not in out


def test_truncated_pem_block_redacted_to_end():
    out = log_fix.redact("x\n-----BEGIN RSA PRIVATE KEY-----\nMIIEow\nstill secret")
    assert "secret" not in out and "MIIEow" not in out


def test_hex_and_app_uuid():
    app_id = "304e5cd6a370442d97317e23bbed64c7"
    assert len(app_id) == 32
    out = log_fix.redact(f'<iq:application id="{app_id}" type="watchface">')
    assert app_id not in out
    assert out == '<iq:application id="<REDACTED>" type="watchface">'
    assert log_fix.redact("a" * 64) == "<REDACTED>"


def test_short_hex_colors_survive():
    s = "dc.setColor(0x00FFFF, 0x000055); deadbeef1234"
    assert log_fix.redact(s) == s


def test_base64_token():
    tok = "Zm9vYmFyMTIzNDU2Nzg5MGFiY2RlZmdoaWprbG1ub3A="
    out = log_fix.redact(f"Authorization header was {tok} ok")
    assert tok not in out and "<REDACTED>" in out


def test_long_identifier_without_digits_survives():
    s = "ThisIsAVeryLongCamelCaseIdentifierWithoutDigitsAtAll"
    assert len(s) > 32
    assert log_fix.redact(s) == s


def test_key_value_and_prefixed_tokens():
    out = log_fix.redact("api_key=abcd1234efgh and password: 'hunter2hunter2' and ghp_" + "x" * 30)
    assert "abcd1234efgh" not in out
    assert "hunter2hunter2" not in out
    assert "ghp_x" not in out
    assert "api_key=<REDACTED>" in out


def test_jwt():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijk"
    assert log_fix.redact("t " + jwt) == "t <REDACTED>"


def test_redaction_idempotent_and_empty():
    s = "/Users/zed/a.mc mail me@x.org " + "f" * 40
    once = log_fix.redact(s)
    assert log_fix.redact(once) == once
    assert log_fix.redact("") == ""
    assert log_fix.redact(None) is None


def test_diff_header_paths_not_mangled_by_token_heuristic():
    path = "faces/my_face_v2/resources-fenix7/layouts/layout_main_screen_ab12"
    assert len(path) > 32
    line = f"+++ b/{path}"
    assert log_fix.redact(line) == line


# ---- diff parsing ------------------------------------------------------------

def test_files_touched():
    assert log_fix.files_touched(DIFF) == ["source/View.mc", "resources/new.xml"]


def test_files_touched_deleted_file_and_plain_headers():
    d = "--- a/old.mc\t2026-01-01\n+++ /dev/null\n@@ -1 +0,0 @@\n-x\n--- src/a.mc\n+++ src/a.mc\n"
    assert log_fix.files_touched(d) == ["old.mc", "src/a.mc"]


def test_files_touched_empty():
    assert log_fix.files_touched("") == []


# ---- opt-in gating + end-to-end ------------------------------------------------

@pytest.fixture
def repo(tmp_path):
    (tmp_path / "datasets").mkdir()
    log = tmp_path / "log.txt"
    log.write_text("ERROR: /Users/alice/face/source/View.mc:12: boom, mail alice@example.com\n")
    diff = tmp_path / "fix.diff"
    diff.write_text(DIFF)
    return tmp_path, log, diff


def _args(log, diff, *extra):
    return ["--kind", "compile_error", "--device", "fr945", "--log-file", str(log),
            "--diff-file", str(diff), *extra]


def test_no_optin_prints_help_and_writes_nothing(repo, capsys):
    root, log, diff = repo
    assert log_fix.main(_args(log, diff), root=str(root)) == 0
    assert "touch datasets/.optin" in capsys.readouterr().out
    assert not (root / "datasets" / "local").exists()


def test_no_optin_does_not_even_read_files(repo, capsys):
    root, _, _ = repo
    assert log_fix.main(_args("/nonexistent/a", "/nonexistent/b"), root=str(root)) == 0
    assert "touch datasets/.optin" in capsys.readouterr().out


def test_optin_must_be_a_file(repo):
    root, log, diff = repo
    (root / "datasets" / ".optin").mkdir()
    log_fix.main(_args(log, diff), root=str(root))
    assert not (root / "datasets" / "local").exists()


def test_logs_redacted_record(repo):
    root, log, diff = repo
    (root / "datasets" / ".optin").touch()
    rc = log_fix.main(_args(log, diff, "--sdk", "8.1.1", "--outcome", "fixed",
                            "--notes", "ping me at bob@example.org"), root=str(root))
    assert rc == 0
    lines = (root / "datasets" / "local" / "fixes.jsonl").read_text().splitlines()
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert set(rec) == {"schema_version", "ts", "kind", "device", "sdk", "input", "diff",
                        "files_touched", "outcome", "notes"}
    assert rec["schema_version"] == 1
    assert rec["ts"].endswith("Z") and len(rec["ts"]) == 20
    assert (rec["kind"], rec["device"], rec["sdk"], rec["outcome"]) == ("compile_error", "fr945", "8.1.1", "fixed")
    assert "alice" not in rec["input"] and "<HOME>/face/source/View.mc:12" in rec["input"]
    assert "<EMAIL>" in rec["input"] and "example.com" not in rec["input"]
    assert rec["notes"] == "ping me at <EMAIL>"
    assert rec["files_touched"] == ["source/View.mc", "resources/new.xml"]

    # appends, does not overwrite
    log_fix.main(_args(log, diff), root=str(root))
    assert len((root / "datasets" / "local" / "fixes.jsonl").read_text().splitlines()) == 2


def test_defaults_and_optional_context(repo):
    root, log, diff = repo
    (root / "datasets" / ".optin").touch()
    ctx = root / "ctx.mc"
    ctx.write_text("// /home/zed/x\nvar a = 1;\n")
    log_fix.main(_args(log, diff, "--context-file", str(ctx)), root=str(root))
    rec = json.loads((root / "datasets" / "local" / "fixes.jsonl").read_text())
    assert rec["sdk"] is None and rec["outcome"] == "unknown" and rec["notes"] == ""
    assert rec["context"].startswith("// <HOME>/x")


def test_dry_run_writes_nothing(repo, capsys):
    root, log, diff = repo
    (root / "datasets" / ".optin").touch()
    log_fix.main(_args(log, diff, "--dry-run"), root=str(root))
    assert json.loads(capsys.readouterr().out)["kind"] == "compile_error"
    assert not (root / "datasets" / "local").exists()


def test_missing_file_errors(repo, capsys):
    root, log, _ = repo
    (root / "datasets" / ".optin").touch()
    assert log_fix.main(_args(log, root / "nope.diff"), root=str(root)) == 2


def test_invalid_kind_rejected(repo):
    root, log, diff = repo
    with pytest.raises(SystemExit):
        log_fix.main(["--kind", "bogus", "--device", "x", "--log-file", str(log),
                      "--diff-file", str(diff)], root=str(root))


# ---- export_chat ---------------------------------------------------------------

def _rec(**kw):
    base = {"schema_version": 1, "ts": "2026-01-01T00:00:00Z", "kind": "compile_error", "device": "fr945",
            "sdk": "8.1.1", "input": "ERROR: x", "diff": DIFF, "files_touched": [], "outcome": "fixed", "notes": ""}
    base.update(kw)
    return base


def test_export_messages_format():
    rows = list(export_chat.convert([_rec(context="var a = 1;")]))
    assert len(rows) == 1
    m = rows[0]["messages"]
    assert [x["role"] for x in m] == ["system", "user", "assistant"]
    assert "ERROR: x" in m[1]["content"] and "device: fr945" in m[1]["content"]
    assert "Code context:\nvar a = 1;" in m[1]["content"]
    assert m[2]["content"].startswith("diff --git a/source/View.mc")


def test_export_without_context_or_system():
    m = list(export_chat.convert([_rec()], system=False))[0]["messages"]
    assert [x["role"] for x in m] == ["user", "assistant"]
    assert "Code context" not in m[0]["content"]


def test_export_filters_outcome_and_empty_diff():
    recs = [_rec(outcome="partial"), _rec(diff=""), _rec(outcome="unknown"), _rec()]
    assert len(list(export_chat.convert(recs))) == 1
    assert len(list(export_chat.convert(recs, outcomes=("fixed", "partial")))) == 2


def test_export_redacts_again():
    rows = list(export_chat.convert([_rec(input="/Users/mallory/x.mc mallory@evil.test")]))
    u = rows[0]["messages"][1]["content"]
    assert "mallory" not in u


def test_export_cli_roundtrip(tmp_path, capsys):
    src = tmp_path / "in.jsonl"
    src.write_text(json.dumps(_rec()) + "\n\n" + "not json\n" + json.dumps(_rec(outcome="unknown")) + "\n")
    out = tmp_path / "sub" / "out.jsonl"
    assert export_chat.main(["--input", str(src), "--output", str(out)]) == 0
    lines = out.read_text().splitlines()
    assert len(lines) == 1 and "messages" in json.loads(lines[0])


def test_export_missing_input_is_ok(tmp_path, capsys):
    assert export_chat.main(["--input", str(tmp_path / "none.jsonl"), "--output", str(tmp_path / "o")]) == 0
    assert not (tmp_path / "o").exists()
