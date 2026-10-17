"""Load the curated opportunity catalog (``seeds/opportunities.v<N>.yaml``) into a workspace.

    radar-seed check  [--file PATH]                                  validate only
    radar-seed db     --workspace UUID [--file PATH]                 local database, upsert by slug
    radar-seed api    --api URL --token-file PATH [--file PATH]      through the cell API (hosted)

Every row must cite ``source_url`` and ``last_verified_at`` and carry a ``verification_status``;
the loader refuses the file otherwise. Rows are matched by ``slug``: new slugs are inserted,
changed rows updated (version + 1), identical rows left alone, so a rerun is a no-op.

The ``db`` mode writes rows directly as the API role inside the workspace (row-level security
still applies) and skips the platform's execution records, so it refuses the hosted database;
use the ``api`` mode there. The token is read from a file and never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml
from fastapi.encoders import jsonable_encoder
from psycopg.types.json import Jsonb
from pydantic import ValidationError

from cellkit.app import models
from cellkit.spec import Cell, Resource

REQUIRED_PROVENANCE = ("source_url", "last_verified_at", "verification_status")


class SeedError(ValueError):
    pass


def default_file(root: Path) -> Path:
    """The newest versioned seed file (opportunities.v<N>.yaml with the highest N)."""
    files = sorted(
        root.glob("seeds/opportunities.v*.yaml"),
        key=lambda p: int(p.stem.rsplit(".v", 1)[1]),
    )
    if not files:
        raise SeedError(f"no seeds/opportunities.v*.yaml under {root}")
    return files[-1]


def read(path: Path, resource: Resource) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """(header, rows): rows validated against the opportunity model of cell.yaml (Python values)."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise SeedError(f"{path.name}: expected a mapping with an 'items' list")
    header = {k: v for k, v in data.items() if k != "items"}
    if not isinstance(header.get("version"), int):
        raise SeedError(f"{path.name}: 'version' must be an integer")
    create, _ = models(resource)
    rows, seen, problems = [], set(), []
    for n, raw in enumerate(data["items"]):
        label = raw.get("slug", f"#{n}") if isinstance(raw, dict) else f"#{n}"
        if not isinstance(raw, dict):
            problems.append(f"{label}: not a mapping")
            continue
        missing = [k for k in REQUIRED_PROVENANCE if not raw.get(k)]
        if missing:
            problems.append(f"{label}: missing {', '.join(missing)}")
        if raw.get("slug") in seen:
            problems.append(f"{label}: duplicate slug")
        seen.add(raw.get("slug"))
        if (
            raw.get("min_age") is not None
            and raw.get("max_age") is not None
            and raw["min_age"] > raw["max_age"]
        ):
            problems.append(f"{label}: min_age > max_age")
        try:
            row = create(**raw)
        except ValidationError as exc:
            problems.append(
                f"{label}: "
                + "; ".join(
                    f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()
                )
            )
            continue
        rows.append({k: v for k, v in row.model_dump().items() if k in raw})
    if problems:
        raise SeedError(
            f"{path.name}: {len(problems)} invalid rows\n  " + "\n  ".join(problems)
        )
    return header, rows


def upsert_db(
    conn, cell: Cell, workspace: uuid.UUID, rows: list[dict[str, Any]]
) -> dict[str, int]:
    """Insert or update by slug inside one workspace; returns counts. The caller commits."""
    r = cell.resource("opportunity")
    table = f"{cell.schema}.{r.table}"
    conn.execute("SELECT set_config('app.workspace_id', %s, true)", (str(workspace),))
    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    for row in rows:
        # Every column of the resource, so a field removed from the seed is cleared, not kept stale.
        values = {f.name: row.get(f.name, f.default) for f in r.fields}
        values = {
            k: (Jsonb(v) if r.field(k).type == "json" and v is not None else v)
            for k, v in values.items()
        }
        columns = list(values)
        changed = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns if c != "slug")
        distinct = (
            f"({', '.join(f'{r.table}.{c}' for c in columns)})"
            f" IS DISTINCT FROM ({', '.join(f'EXCLUDED.{c}' for c in columns)})"
        )
        result = conn.execute(
            f"INSERT INTO {table} (workspace_id, {', '.join(columns)}) VALUES (%s, {', '.join(['%s'] * len(columns))})"
            f" ON CONFLICT (workspace_id, slug) DO UPDATE SET {changed}, version = {r.table}.version + 1,"
            f" updated_at = now() WHERE {distinct} RETURNING (xmax = 0) AS inserted",
            [workspace, *values.values()],
        ).fetchone()
        if result is None:
            counts["unchanged"] += 1
        elif result["inserted"] if isinstance(result, dict) else result[0]:
            counts["inserted"] += 1
        else:
            counts["updated"] += 1
    return counts


def upsert_api(
    client, headers: dict[str, str], version: int, rows: list[dict[str, Any]]
) -> dict[str, int]:
    """The same upsert through the cell API (platform executions and audit included)."""
    existing: dict[str, dict[str, Any]] = {}
    after = None
    while True:
        params = {"limit": 1000, **({"after_id": after} if after else {})}
        page = client.get("/v1/opportunities", headers=headers, params=params)
        page.raise_for_status()
        items = page.json()["items"]
        existing.update({item["slug"]: item for item in items})
        if len(items) < 1000:
            break
        after = items[-1]["id"]
    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    for row in jsonable_encoder(rows):
        current = existing.get(row["slug"])
        if current is None:
            response = client.post(
                "/v1/opportunities",
                json=row,
                headers={
                    **headers,
                    "Idempotency-Key": f"seed-v{version}-{row['slug']}"[:200],
                },
            )
            response.raise_for_status()
            counts["inserted"] += 1
            continue
        diff = {
            k: v
            for k, v in row.items()
            if json.dumps(current.get(k), sort_keys=True)
            != json.dumps(v, sort_keys=True)
        }
        if not diff:
            counts["unchanged"] += 1
            continue
        response = client.patch(
            f"/v1/opportunities/{current['id']}",
            headers=headers,
            json={**diff, "expected_version": current["version"]},
        )
        response.raise_for_status()
        counts["updated"] += 1
    return counts


def main(argv: list[str] | None = None) -> int:
    from cellkit.server import cell as load_cell

    spec = load_cell()
    parser = argparse.ArgumentParser(
        prog="radar-seed", description="load the curated opportunity catalog"
    )
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("check", "db", "api"):
        p = sub.add_parser(name)
        p.add_argument("--file", type=Path)
        if name == "db":
            p.add_argument("--workspace", type=uuid.UUID, required=True)
        if name == "api":
            p.add_argument("--api", required=True)
            p.add_argument("--token-file", type=Path, required=True)
    args = parser.parse_args(argv)
    path = args.file or default_file(spec.root)
    try:
        header, rows = read(path, spec.resource("opportunity"))
    except SeedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    summary: dict[str, Any] = {
        "event": "radar.seed",
        "file": path.name,
        "version": header["version"],
        "rows": len(rows),
    }
    if args.mode == "db":
        if os.environ.get(f"{spec.env}_DB_MODE") == "hosted":
            print(
                "db mode refuses the hosted database; use: radar-seed api --api URL --token-file PATH",
                file=sys.stderr,
            )
            return 2
        from psycopg.rows import dict_row

        from cellkit.db import default_cluster

        with default_cluster(spec).connect(spec.role("api")) as conn:
            conn.row_factory = dict_row
            summary.update(upsert_db(conn, spec, args.workspace, rows))
            conn.commit()
    elif args.mode == "api":
        import httpx

        token = args.token_file.read_text(encoding="utf-8").strip()
        with httpx.Client(base_url=args.api.rstrip("/"), timeout=30) as client:
            summary.update(
                upsert_api(
                    client,
                    {"Authorization": f"Bearer {token}"},
                    header["version"],
                    rows,
                )
            )
    print(json.dumps(summary))
    return 0


def run() -> None:
    sys.exit(main())


if __name__ == "__main__":
    run()
