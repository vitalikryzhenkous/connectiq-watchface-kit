# Security

## Reporting
Please report vulnerabilities privately through GitHub **Security → Report a vulnerability** on this repository. Don't open a public issue.

## Scope and design
- The watch face requests **no permissions**. It makes no network calls, collects no data and contains no analytics. The last known position is stored only on the watch, so it can compute sunrise and sunset.
- The Python scripts run locally, have no network access and depend only on Pillow.
- The `.claude/` folder holds only Markdown instructions: a skill and slash commands. There are **no hooks and no `settings.json`**. Changes that add hooks, MCP servers or executable automation under `.claude/` get extra review before they're merged.

## For contributors
- Never commit developer keys, tokens, or personal emails. Use the GitHub noreply address.
- Fonts and assets must be original or carry a redistribution-compatible license.
