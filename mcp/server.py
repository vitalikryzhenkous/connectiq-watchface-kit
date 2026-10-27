#!/usr/bin/env python3
"""connectiq-watchface-kit MCP server (v0.1, stdio, local only).

Exposes the kit's scripts as MCP tools: scaffold_face, gen_font, render_preview,
lint, device_info. No network access, no subprocesses; every write stays inside
the repo root or the current working directory.
"""
import contextlib
import importlib.util
import io
import json
import re
import shutil
import sys
import threading
import uuid
from pathlib import Path
from xml.sax.saxutils import escape

try:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP, Image
    from mcp.server.fastmcp.exceptions import ToolError
except ImportError:  # mcp 2.x renamed FastMCP to MCPServer
    from mcp.server.mcpserver import Image
    from mcp.server.mcpserver import MCPServer as FastMCP
    from mcp.server.mcpserver.exceptions import ToolError


class KitError(ToolError, ValueError):
    """Validation/usage error. As a ToolError its message is shown to the client."""

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
TEMPLATE_DIR = REPO_ROOT / "templates" / "n3on-terminal"
DEVICES_FILE = Path(__file__).resolve().parent / "devices.json"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import ciq_lint as _ciq_lint  # noqa: E402
import gen_font as _gen_font  # noqa: E402

SLUG_RE = re.compile(r"^[a-z0-9-]{2,40}$")
PRODUCT_RE = re.compile(r"^[a-z0-9_]{2,40}$")
FONT_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
_PREVIEW_LOCK = threading.Lock()

mcp = FastMCP(
    "connectiq",
    instructions=(
        "Tools for building Garmin Connect IQ watch faces from the connectiq-watchface-kit: "
        "scaffold a project, generate bitmap fonts, preview, lint, look up device specs. "
        "Local only; writes stay inside the repo or the current working directory."
    ),
)


# --------------------------------------------------------------------------- paths
def _allowed_roots():
    roots = [REPO_ROOT]
    cwd = Path.cwd().resolve()
    if cwd != Path(cwd.anchor) and cwd not in roots:  # never treat "/" as a root
        roots.append(cwd)
    return roots


def _inside(path, roots):
    return any(path == r or r in path.parents for r in roots)


def _check_text(value, what):
    if not isinstance(value, str) or not value.strip():
        raise KitError(f"{what} must be a non-empty string")
    if "\0" in value:
        raise KitError(f"{what} contains a null byte")
    if ".." in Path(value).parts:
        raise KitError(f"{what} must not contain '..': {value!r}")


def _resolve(value, what, must_exist=False):
    """Resolve a user path. Relative paths try cwd first, then the repo root."""
    _check_text(value, what)
    raw = Path(value)
    if raw.is_absolute():
        candidates = [raw]
    else:
        bases = _allowed_roots()[::-1]  # cwd (if usable) first, repo root last
        candidates = [b / raw for b in bases]
    if must_exist:
        existing = [c for c in candidates if c.exists()]
        if not existing:
            raise KitError(f"{what} not found: {value!r}")
        candidates = existing
    return candidates[0].resolve()


def _safe_dir(value, what, must_exist=False):
    """Like _resolve, but the result must lie inside the repo root or cwd."""
    p = _resolve(value, what, must_exist)
    if not _inside(p, _allowed_roots()):
        raise KitError(
            f"{what} {value!r} resolves outside the repo root and the current working directory"
        )
    if must_exist and not p.is_dir():
        raise KitError(f"{what} is not a directory: {value!r}")
    return p


# --------------------------------------------------------------------------- tools
@mcp.tool()
def scaffold_face(slug: str, app_name: str, products: list[str], out_dir: str = "faces") -> dict:
    """Copy the N3on Terminal template to <out_dir>/<slug> with a fresh app id,
    your product list and your app name. Never overwrites an existing directory.
    slug: ^[a-z0-9-]{2,40}$. products: Connect IQ device ids such as fr945, fenix7."""
    if not isinstance(slug, str) or not SLUG_RE.match(slug):
        raise KitError("slug must match ^[a-z0-9-]{2,40}$")
    if not isinstance(app_name, str) or not app_name.strip() or len(app_name) > 60:
        raise KitError("app_name must be 1-60 characters")
    if any(ord(c) < 32 for c in app_name):
        raise KitError("app_name must not contain control characters")
    if not isinstance(products, list) or not products:
        raise KitError("products must be a non-empty list of device ids")
    clean, warnings = [], []
    known = _load_devices()
    for p in products:
        if not isinstance(p, str) or not PRODUCT_RE.match(p):
            raise KitError(f"invalid product id {p!r}: expected ^[a-z0-9_]{{2,40}}$ (e.g. fr945)")
        if p not in clean:
            clean.append(p)
        if p not in known:
            warnings.append(f"product '{p}' is not in the bundled device list; verify it in SDK Manager")
    if len(clean) > 60:
        raise KitError("too many products (max 60)")
    if "garmin" in app_name.lower():
        warnings.append("app_name contains 'Garmin'; the Connect IQ Store rules advise against it")
    if not TEMPLATE_DIR.is_dir():
        raise KitError(f"template not found: {TEMPLATE_DIR}")

    out = _safe_dir(out_dir, "out_dir")
    target = out / slug
    if target.exists() or target.is_symlink():
        raise KitError(f"refusing to overwrite existing path: {target}")
    out.mkdir(parents=True, exist_ok=True)

    app_id = uuid.uuid4().hex
    try:
        shutil.copytree(TEMPLATE_DIR, target, ignore=shutil.ignore_patterns("__pycache__", "store"))

        mf = target / "manifest.xml"
        text = mf.read_bytes().decode("utf-8")
        text, n_id = re.subn(
            r'(<iq:application\b[^>]*?\bid=")[0-9a-fA-F]{32}(")',
            lambda m: m.group(1) + app_id + m.group(2), text, count=1)
        block = "<iq:products>\n" + "".join(
            f'            <iq:product id="{p}"/>\n' for p in clean) + "        </iq:products>"
        text, n_pr = re.subn(r"<iq:products>.*?</iq:products>", lambda m: block, text, count=1, flags=re.S)
        if n_id != 1 or n_pr != 1:
            raise KitError("template manifest.xml has an unexpected layout")
        mf.write_bytes(text.encode("utf-8"))

        sf = target / "resources" / "strings" / "strings.xml"
        text = sf.read_bytes().decode("utf-8")
        text, n_name = re.subn(
            r'(<string id="AppName">).*?(</string>)',
            lambda m: m.group(1) + escape(app_name.strip()) + m.group(2), text, count=1, flags=re.S)
        if n_name != 1:
            raise KitError("template strings.xml has no AppName string")
        sf.write_bytes(text.encode("utf-8"))

        result = _ciq_lint.lint(str(target), mip=False)
        if not result["ok"]:
            raise KitError(f"scaffolded project failed lint: {result['issues']}")
    except Exception:
        shutil.rmtree(target, ignore_errors=True)  # we created it just now
        raise
    return {"path": str(target), "app_id": app_id, "app_name": app_name.strip(),
            "products": clean, "warnings": warnings}


@mcp.tool()
def gen_font(ttf_path: str, size: int, name: str, out_dir: str, chars: str | None = None) -> str:
    """Convert a TTF/OTF into a crisp (non-antialiased) Connect IQ bitmap font
    (<name>.fnt + <name>.png) in out_dir. Refuses to overwrite existing files.
    chars defaults to ASCII plus the degree sign and triangles. Returns an info line."""
    ttf = _resolve(ttf_path, "ttf_path", must_exist=True)  # read-only, may live anywhere
    if not ttf.is_file() or ttf.suffix.lower() not in (".ttf", ".otf"):
        raise KitError("ttf_path must be an existing .ttf or .otf file")
    if not isinstance(size, int) or isinstance(size, bool) or not 4 <= size <= 512:
        raise KitError("size must be an integer between 4 and 512")
    if not isinstance(name, str) or not FONT_NAME_RE.match(name):
        raise KitError("name must match ^[A-Za-z0-9_-]{1,40}$")
    if chars is None:
        chars = _gen_font.DEFAULT_CHARS
    elif not isinstance(chars, str) or not chars or len(chars) > 5000:
        raise KitError("chars must be a non-empty string of at most 5000 characters")
    out = _safe_dir(out_dir, "out_dir")
    for ext in (".fnt", ".png"):
        if (out / f"{name}{ext}").exists() or (out / f"{name}{ext}").is_symlink():
            raise KitError(f"refusing to overwrite existing file: {out / (name + ext)}")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):  # make_font prints its info line; keep stdio clean
        _gen_font.make_font(name, str(ttf), size, chars, str(out))
    return buf.getvalue().strip()


def _load_preview_module(project):
    """Import scripts/preview_n3on.py for this project. It reads sys.argv and loads
    fonts at import time, so argv is swapped temporarily and a fresh module is built per call."""
    path = SCRIPTS_DIR / "preview_n3on.py"
    saved = sys.argv
    sys.argv = [str(path), str(project), str(project / "preview.png")]
    try:
        spec = importlib.util.spec_from_file_location("_preview_n3on_run", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.argv = saved
    return mod


@mcp.tool()
def render_preview(project_dir: str) -> Image:
    """Render the 3-theme (neon / amber / green) preview of an N3on-based project as a
    PNG, save it to <project_dir>/preview.png and return it. Needs resources/fonts/term_small
    and term_big. The preview mirrors the N3on layout using the project's fonts, not its source code."""
    from PIL import Image as PILImage

    project = _safe_dir(project_dir, "project_dir", must_exist=True)
    fonts = project / "resources" / "fonts"
    missing = [f"{n}.{e}" for n in ("term_small", "term_big") for e in ("fnt", "png")
               if not (fonts / f"{n}.{e}").is_file()]
    if missing:
        raise KitError(
            "render_preview only supports N3on-based projects; missing in resources/fonts: "
            + ", ".join(missing))
    out_png = project / "preview.png"
    if out_png.is_symlink():
        raise KitError("preview.png is a symlink; refusing to write through it")
    with _PREVIEW_LOCK:
        try:
            mod = _load_preview_module(project)
            tiles = [mod.face(mod.PALS[0], mood="night"),
                     mod.face(mod.PALS[1], "07:58", "normal"),
                     mod.face(mod.PALS[2], "18:30", "happy")]
        except KeyError as e:
            raise KitError(f"project font is missing a glyph needed by the preview (char id {e})") from e
    sheet = PILImage.new("RGB", (520 * 3 + 40, 560), (12, 12, 12))
    for i, t in enumerate(tiles):
        sheet.paste(t, (10 + i * 530, 20))
    buf = io.BytesIO()
    sheet.save(buf, format="PNG")
    data = buf.getvalue()
    out_png.write_bytes(data)
    return Image(data=data, format="png")


@mcp.tool()
def lint(project_dir: str, mip: bool = True) -> dict:
    """Static checks for a watch face project: manifest, referenced resources and,
    with mip=True, MIP palette (channels must be 00/55/AA/FF). Returns {project, manifest, issues, ok}."""
    project = _safe_dir(project_dir, "project_dir", must_exist=True)
    return _ciq_lint.lint(str(project), mip=bool(mip))


def _load_devices():
    with open(DEVICES_FILE, encoding="utf-8") as f:
        return json.load(f)["devices"]


@mcp.tool()
def device_info(product_id: str) -> dict:
    """Look up a Connect IQ device from the bundled list (fr945, fr955, fr255, fr265,
    fr965, fenix7, fenix7x, venu2): name, id, screen_px, display (MIP/AMOLED), notes."""
    devices = _load_devices()
    key = product_id.strip().lower() if isinstance(product_id, str) else ""
    if key not in devices:
        raise KitError(
            f"unknown product id {product_id!r}. Known ids: {', '.join(sorted(devices))}. "
            "The list is bundled and not exhaustive; check SDK Manager -> Devices for other ids.")
    info = dict(devices[key])
    info["verify"] = "Bundled reference data: verify in SDK Manager before relying on it."
    return info


if __name__ == "__main__":
    mcp.run()
