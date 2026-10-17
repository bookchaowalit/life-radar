"""A local PostgreSQL for development: ``radar-local up`` (init, start, roles, migrate) and ``radar-local down``.

The cluster lives in ``.runtime/pgdata`` with a private socket (no TCP), the same layout
``radar-db`` and ``radar-seed db`` use when ``RADAR_DB_MODE`` is not ``hosted``.
"""

from __future__ import annotations

import argparse
import sys

from cellkit.db import LocalCluster, default_cluster, migrate
from cellkit.server import cell


def main(argv: list[str] | None = None) -> int:
    spec = cell()
    parser = argparse.ArgumentParser(prog="radar-local", description="run the local development database")
    parser.add_argument("command", choices=("up", "down"))
    args = parser.parse_args(argv)
    cluster = default_cluster(spec)
    if not isinstance(cluster, LocalCluster):
        print("radar-local only manages the local database (unset RADAR_DB_MODE)", file=sys.stderr)
        return 2
    if args.command == "down":
        cluster.stop()
        print("local database stopped")
        return 0
    if not (cluster.data_dir / "PG_VERSION").exists():
        cluster.data_dir.parent.mkdir(parents=True, exist_ok=True)
        cluster.init()
    if not (cluster.data_dir / "postmaster.pid").exists():
        cluster.start()
    cluster.bootstrap()
    applied = migrate(cluster)
    print(f"local database up at {cluster.socket_dir}; {len(applied)} migrations applied")
    return 0


def run() -> None:
    sys.exit(main())


if __name__ == "__main__":
    run()
