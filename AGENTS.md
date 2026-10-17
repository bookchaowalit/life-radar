# Agent Instructions

- Human-facing replies are in Thai by default; keep code, commands and identifiers as-is.
- Never print, commit or copy secrets: database URLs, tokens and keys live in Railway
  variables and `~/.config/solo-radar/` (owner-only).
- Tests use a throwaway local PostgreSQL and a fake platform; they must never reach
  the hosted database or the hosted platform.
- Run `.venv/bin/pytest -q` before committing. Migrations are append-only: never edit
  an applied file, add a new numbered one (`0001_radar.sql` is applied on Neon since 2026-10-17).
- `src/cellkit` is this repository's own copy of the cell kit (taken from `life-opportunities-api`
  on 2026-10-17). Change it here; there is nothing upstream to sync from.
  Cell-specific code lives in `src/life_radar/`: `rules.py` (pure bucket rules), `routes.py`
  (radar endpoints), `seed.py` (catalog loader), `local.py` (local database).
- Seed data (`seeds/opportunities.v<N>.yaml`) is curated by hand. Every row cites an official
  `source_url`, a `last_verified_at` date and a `verification_status`; facts come from the
  official page, never from memory. Anything not confirmed is marked `partially_verified` or
  `unverified` with the reason in `verification_notes`. A new curation round is a new file
  version (`v2`), not an edit of history that was already loaded somewhere.
- `radar-mcp` (stdio, see `.mcp.json`) is this cell's MCP server: tools `radar.<resource>.list|get|create|update|delete`
  call the cell API with the caller's token (`EMPIRE_TOKEN`, `EMPIRE_TOKEN_FILE` or the `owner-mcp` automation token;
  URL from `EMPIRE_RADAR_API`). Set `EMPIRE_MCP_READONLY=1` for list/get only. Never add actor, workspace or token arguments.
- Deploys are manual (`railway up`) and change production; verify `/health` and one
  authorized read afterwards.
- Keep the solo-empire registry entry (`radar` in
  `repository-catalog/registries/online-systems.yaml`) in sync.
