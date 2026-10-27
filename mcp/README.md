# connectiq MCP server (v0.1)

A small local [MCP](https://modelcontextprotocol.io) server that exposes the kit's tooling to Claude Code, Claude Desktop or any MCP client: scaffold a watch face project, generate bitmap fonts, render a preview, lint, and look up device specs.

It reuses the scripts in `scripts/` (`gen_font.py`, `ciq_lint.py`, `preview_n3on.py`) without modifying them. Transport is stdio.

## Install
```bash
pip install -r mcp/requirements.txt
```
Works with `mcp` 1.x (`FastMCP`) and 2.x (`MCPServer`); the server picks whichever is installed.

## Connect to Claude Code
```bash
claude mcp add connectiq -- python3 /abs/path/to/connectiq-watchface-kit/mcp/server.py
```

## Connect to Claude Desktop
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "connectiq": {
      "command": "python3",
      "args": ["/abs/path/to/connectiq-watchface-kit/mcp/server.py"]
    }
  }
}
```
Relative paths given to tools resolve against the server's working directory first, then the repo root.

## Tools
| Tool | What it does |
|---|---|
| `scaffold_face(slug, app_name, products, out_dir="faces")` | Copies `templates/n3on-terminal` (without its `store/` assets) to `out_dir/slug`, writes a new app id, sets the product list and `AppName`. Returns path and id. |
| `gen_font(ttf_path, size, name, out_dir, chars=None)` | TTF/OTF to a crisp Connect IQ bitmap font (`.fnt` + `.png`). Returns the info line. |
| `render_preview(project_dir)` | Renders the 3-theme preview of an N3on-based project, saves `project_dir/preview.png`, returns the image. |
| `lint(project_dir, mip=True)` | Runs `ciq_lint`: manifest, resource references, and MIP palette. Returns the result dict. |
| `device_info(product_id)` | Name, id, screen size, display type and notes from the bundled `devices.json`. |

`devices.json` is bundled reference data. Verify ids and screen sizes in SDK Manager before relying on them.

Notes:
- `render_preview` mirrors the N3on layout using the project's fonts (`term_small`, `term_big`). It does not parse your own Monkey C code.
- `scaffold_face` keeps the template's source file names (`N3onApp`, `N3onView`) and does not copy the template's store screenshots or listing.

## Tests
```bash
python3 -m pytest mcp/tests -q
```
Includes a real stdio smoke test that starts the server and calls it through the MCP client.

## Security
- Local only: no network access, no subprocesses. Tools call local Python functions.
- Writes stay inside the repo root or the current working directory. Paths containing `..` are rejected, and absolute paths (or symlinks) resolving outside those roots are rejected. The filesystem root is never treated as an allowed root.
- Existing directories are never overwritten: `scaffold_face` refuses an existing `out_dir/slug`, and `gen_font` refuses to replace existing font files. The only file overwritten is `preview.png`.
- The one read outside those roots is the font file passed to `gen_font` (for example a system TTF). It must be a `.ttf` or `.otf`.
- Inputs are validated: slug `^[a-z0-9-]{2,40}$`, device ids `^[a-z0-9_]{2,40}$`, font names `^[A-Za-z0-9_-]{1,40}$`; the app name is XML-escaped.
