"""Tests for mcp/server.py. Run: python3 -m pytest mcp/tests -q"""
import asyncio
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

SERVER = Path(__file__).resolve().parents[1] / "server.py"
REPO = SERVER.parent.parent
TTF = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

spec = importlib.util.spec_from_file_location("ciq_mcp_server", SERVER)
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


@pytest.fixture
def work(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---- scaffold_face
def test_scaffold_face(work):
    r = server.scaffold_face("my-face", "My <Face> & Co", ["fr945", "fenix7", "fr945"])
    target = Path(r["path"])
    assert target == work / "faces" / "my-face"
    assert re.fullmatch(r"[0-9a-f]{32}", r["app_id"])
    assert r["products"] == ["fr945", "fenix7"]
    manifest = (target / "manifest.xml").read_text()
    assert r["app_id"] in manifest
    assert "304e5cd6a370442d97317e23bbed64c7" not in manifest
    assert manifest.count("<iq:product ") == 2 and 'id="fenix7"' in manifest
    strings = (target / "resources/strings/strings.xml").read_text()
    assert "<string id=\"AppName\">My &lt;Face&gt; &amp; Co</string>" in strings
    assert (target / "source" / "N3onView.mc").is_file()
    assert server.lint(str(target))["ok"] is True


def test_scaffold_ids_are_unique(work):
    a = server.scaffold_face("aa", "A", ["fr945"], out_dir="x")
    b = server.scaffold_face("bb", "B", ["fr945"], out_dir="x")
    assert a["app_id"] != b["app_id"]


def test_scaffold_warns_on_unknown_product(work):
    r = server.scaffold_face("aa", "A", ["edge1050"])
    assert any("edge1050" in w for w in r["warnings"])


@pytest.mark.parametrize("slug", ["A", "a", "Bad_Slug", "has space", "x" * 41, "../up", "a/b", ""])
def test_scaffold_bad_slug(work, slug):
    with pytest.raises(ValueError, match="slug"):
        server.scaffold_face(slug, "A", ["fr945"])


@pytest.mark.parametrize("products", [[], ["FR945"], ["fr945\"/>"], ["x"]])
def test_scaffold_bad_products(work, products):
    with pytest.raises(ValueError):
        server.scaffold_face("aa", "A", products)


def test_scaffold_never_overwrites(work):
    server.scaffold_face("aa", "A", ["fr945"])
    marker = work / "faces" / "aa" / "keep.txt"
    marker.write_text("x")
    with pytest.raises(ValueError, match="overwrite"):
        server.scaffold_face("aa", "A", ["fr945"])
    assert marker.read_text() == "x"


def test_scaffold_rejects_escaping_out_dir(work):
    with pytest.raises(ValueError, match=r"\.\."):
        server.scaffold_face("aa", "A", ["fr945"], out_dir="../evil")
    with pytest.raises(ValueError, match="outside"):
        server.scaffold_face("aa", "A", ["fr945"], out_dir="/etc/connectiq-test")
    assert not Path("/etc/connectiq-test").exists()


# ---- gen_font
def test_gen_font(work):
    line = server.gen_font(TTF, 14, "term_x", "fonts")
    assert line.startswith("term_x: advance(0)=") and "glyphs=" in line
    assert (work / "fonts" / "term_x.fnt").is_file() and (work / "fonts" / "term_x.png").is_file()


def test_gen_font_custom_chars(work):
    line = server.gen_font(TTF, 24, "digits", "fonts", chars="0123456789:")
    assert "glyphs=11" in line


def test_gen_font_validation(work):
    with pytest.raises(ValueError, match="size"):
        server.gen_font(TTF, 1, "n", "fonts")
    with pytest.raises(ValueError, match="name"):
        server.gen_font(TTF, 12, "../n", "fonts")
    with pytest.raises(ValueError, match="not found"):
        server.gen_font(str(work / "missing.ttf"), 12, "n", "fonts")
    with pytest.raises(ValueError, match=r"\.\."):
        server.gen_font("../x.ttf", 12, "n", "fonts")
    with pytest.raises(ValueError, match="outside"):
        server.gen_font(TTF, 12, "n", "/tmp/definitely-elsewhere-xyz")
    not_font = work / "a.txt"
    not_font.write_text("x")
    with pytest.raises(ValueError, match="ttf"):
        server.gen_font(str(not_font), 12, "n", "fonts")


def test_gen_font_no_overwrite(work):
    server.gen_font(TTF, 12, "f", "fonts")
    with pytest.raises(ValueError, match="overwrite"):
        server.gen_font(TTF, 12, "f", "fonts")


# ---- render_preview
def test_render_preview(work):
    server.scaffold_face("pv", "PV", ["fr945"])
    img = server.render_preview("faces/pv")
    assert img._format == "png" and img.data[:8] == b"\x89PNG\r\n\x1a\n"
    saved = work / "faces" / "pv" / "preview.png"
    assert saved.read_bytes() == img.data
    from PIL import Image
    assert Image.open(saved).size == (520 * 3 + 40, 560)


def test_render_preview_restores_argv(work):
    server.scaffold_face("pv", "PV", ["fr945"])
    before = list(sys.argv)
    server.render_preview("faces/pv")
    assert sys.argv == before


def test_render_preview_rejects_non_n3on(work):
    (work / "plain").mkdir()
    with pytest.raises(ValueError, match="N3on-based"):
        server.render_preview("plain")
    with pytest.raises(ValueError, match="not found"):
        server.render_preview("nope")
    with pytest.raises(ValueError, match=r"\.\."):
        server.render_preview("../plain")


# ---- lint
def test_lint_ok_and_mip_violation(work):
    r = server.scaffold_face("lt", "LT", ["fr945"])
    res = server.lint(r["path"])
    assert res["ok"] is True and res["manifest"]["id"] == r["app_id"]
    bad = Path(r["path"]) / "source" / "Bad.mc"
    bad.write_text("var c = 0x123456;\n")
    res = server.lint("faces/lt", mip=True)
    assert res["ok"] is False and any(i["check"] == "palette" for i in res["issues"])
    assert server.lint("faces/lt", mip=False)["ok"] is True


def test_lint_repo_template_and_errors(work):
    # the repo itself is an allowed root, so the shipped template can be linted by absolute path
    res = server.lint(str(REPO / "templates" / "n3on-terminal"))
    assert res["ok"] is True
    with pytest.raises(ValueError, match="outside"):
        server.lint("/usr")
    with pytest.raises(ValueError, match="not found"):
        server.lint("missing-dir")


# ---- device_info
def test_device_info():
    d = server.device_info("fr265")
    assert d["screen_px"] == 416 and d["display"] == "AMOLED" and d["id"] == "fr265"
    assert "SDK Manager" in d["verify"]
    assert server.device_info(" FENIX7X ")["screen_px"] == 280
    data = json.loads((SERVER.parent / "devices.json").read_text())["devices"]
    assert set(data) == {"fr945", "fr955", "fr255", "fr265", "fr965", "fenix7", "fenix7x", "venu2"}
    for k, v in data.items():
        assert set(v) == {"name", "id", "screen_px", "display", "notes"} and v["id"] == k


def test_device_info_unknown():
    with pytest.raises(ValueError) as e:
        server.device_info("nope")
    assert "fr945" in str(e.value) and "venu2" in str(e.value)


# ---- real stdio smoke test
def test_stdio_smoke(work):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], cwd=str(work))

    async def run():
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {t.name for t in tools.tools}
                made = await session.call_tool(
                    "scaffold_face", {"slug": "smoke", "app_name": "Smoke", "products": ["fr945"]})
                lint_res = await session.call_tool("lint", {"project_dir": "faces/smoke"})
                dev = await session.call_tool("device_info", {"product_id": "nope"})
                prev = await session.call_tool("render_preview", {"project_dir": "faces/smoke"})
                return names, made, lint_res, dev, prev

    def is_err(r):  # mcp 1.x: isError, mcp 2.x: is_error
        return getattr(r, "is_error", getattr(r, "isError", None))

    names, made, lint_res, dev, prev = asyncio.run(run())
    assert names == {"scaffold_face", "gen_font", "render_preview", "lint", "device_info"}
    assert not is_err(made) and not is_err(lint_res)
    assert '"ok": true' in lint_res.content[0].text.lower().replace('":true', '": true')
    assert is_err(dev) and "Known ids" in dev.content[0].text
    assert not is_err(prev) and prev.content[0].type == "image"
