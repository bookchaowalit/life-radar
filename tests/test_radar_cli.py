"""The radar-local and radar-seed command lines (argument handling, mode guards, what they print).

The database and HTTP calls they make are covered in test_radar_api.py; here they are faked.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from cellkit.db import HostedCluster, LocalCluster, Names
from cellkit.server import cell

from life_radar import local, seed

FIXTURE = Path(__file__).parent / "fixtures" / "opportunities.v1.yaml"


class FakeLocal(LocalCluster):
    """A LocalCluster that records calls instead of running pg_ctl."""

    def __init__(self, data_dir: Path) -> None:
        super().__init__(Names(cell()), data_dir, data_dir.parent / "sock")
        self.calls: list[str] = []

    def init(self) -> None:
        self.calls.append("init")
        self.data_dir.mkdir(parents=True)
        (self.data_dir / "PG_VERSION").write_text("17")

    def start(self) -> None:
        self.calls.append("start")

    def stop(self) -> None:
        self.calls.append("stop")

    def bootstrap(self) -> None:
        self.calls.append("bootstrap")


@pytest.fixture
def fake_local(tmp_path, monkeypatch):
    cluster = FakeLocal(tmp_path / "rt" / "pgdata")
    monkeypatch.setattr(local, "default_cluster", lambda spec: cluster)
    monkeypatch.setattr(local, "migrate", lambda c: ["0001", "0002"])
    return cluster


def test_local_up_initialises_starts_bootstraps_and_migrates(fake_local, capsys):
    assert local.main(["up"]) == 0
    assert fake_local.calls == ["init", "start", "bootstrap"]
    assert "2 migrations applied" in capsys.readouterr().out


def test_local_up_reuses_a_running_cluster(fake_local):
    fake_local.data_dir.mkdir(parents=True)
    (fake_local.data_dir / "PG_VERSION").write_text("17")
    (fake_local.data_dir / "postmaster.pid").write_text("1")
    assert local.main(["up"]) == 0
    assert fake_local.calls == ["bootstrap"]


def test_local_down_stops(fake_local, capsys):
    assert local.main(["down"]) == 0
    assert fake_local.calls == ["stop"]
    assert "stopped" in capsys.readouterr().out


def test_local_refuses_the_hosted_database(monkeypatch, capsys):
    hosted = object.__new__(HostedCluster)
    monkeypatch.setattr(local, "default_cluster", lambda spec: hosted)
    assert local.main(["up"]) == 2
    assert "unset RADAR_DB_MODE" in capsys.readouterr().err


def test_local_rejects_an_unknown_command():
    with pytest.raises(SystemExit):
        local.main(["sideways"])


def test_local_run_exits_with_the_status(monkeypatch):
    monkeypatch.setattr(local, "main", lambda: 3)
    with pytest.raises(SystemExit) as exc:
        local.run()
    assert exc.value.code == 3


def test_seed_check_reads_the_file_and_prints_a_summary(capsys):
    assert seed.main(["check", "--file", str(FIXTURE)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "event": "radar.seed",
        "file": FIXTURE.name,
        "version": 1,
        "rows": 3,
    }


def test_seed_check_defaults_to_the_newest_committed_seed(capsys):
    assert seed.main(["check"]) == 0
    assert json.loads(capsys.readouterr().out)["file"].startswith("opportunities.v")


def test_seed_reports_an_invalid_file(tmp_path, capsys):
    bad = tmp_path / "opportunities.v9.yaml"
    bad.write_text("items: nope\n", encoding="utf-8")
    assert seed.main(["check", "--file", str(bad)]) == 1
    assert "expected a mapping" in capsys.readouterr().err


def test_seed_db_refuses_the_hosted_database(monkeypatch, capsys):
    monkeypatch.setenv("RADAR_DB_MODE", "hosted")
    code = seed.main(
        [
            "db",
            "--file",
            str(FIXTURE),
            "--workspace",
            "00000000-0000-0000-0000-000000000001",
        ]
    )
    assert code == 2
    assert "refuses the hosted database" in capsys.readouterr().err


def test_seed_api_sends_the_token_and_reports_the_counts(tmp_path, monkeypatch, capsys):
    token = tmp_path / "token"
    token.write_text("tok-fake-radar\n", encoding="utf-8")
    seen = {}

    def fake_upsert(client, headers, version, rows):
        seen.update(
            base=str(client.base_url), headers=headers, version=version, rows=len(rows)
        )
        return {"inserted": 3, "updated": 0, "unchanged": 0}

    monkeypatch.setattr(seed, "upsert_api", fake_upsert)
    code = seed.main(
        [
            "api",
            "--file",
            str(FIXTURE),
            "--api",
            "https://radar.example/",
            "--token-file",
            str(token),
        ]
    )
    assert code == 0
    assert seen == {
        "base": "https://radar.example",
        "headers": {"Authorization": "Bearer tok-fake-radar"},
        "version": 1,
        "rows": 3,
    }
    assert json.loads(capsys.readouterr().out)["inserted"] == 3


def test_seed_run_exits_with_the_status(monkeypatch):
    monkeypatch.setattr(seed, "main", lambda: 0)
    with pytest.raises(SystemExit) as exc:
        seed.run()
    assert exc.value.code == 0
