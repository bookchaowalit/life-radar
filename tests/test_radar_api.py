"""The radar routes and the seed loader against the throwaway database and the fake platform."""

import uuid
from datetime import date
from pathlib import Path

import pytest
import yaml
from psycopg.rows import dict_row

from life_radar.seed import SeedError, default_file, read, upsert_api, upsert_db

FIXTURE = Path(__file__).parent / "fixtures" / "opportunities.v1.yaml"
AS_OF = "2026-10-17"


def workspace_of(headers):
    import jwt

    claims = jwt.decode(
        headers["Authorization"].split()[1], options={"verify_signature": False}
    )
    return uuid.UUID(claims["ws"])


def seed_db(harness, headers, path=FIXTURE):
    _, rows = read(path, harness.cell.resource("opportunity"))
    with harness.cluster.connect(harness.cell.role("api")) as conn:
        conn.row_factory = dict_row
        counts = upsert_db(conn, harness.cell, workspace_of(headers), rows)
        conn.commit()
    return counts


def test_seed_db_is_idempotent_and_updates_changed_rows(
    harness, owner, client, tmp_path
):
    assert seed_db(harness, owner) == {"inserted": 3, "updated": 0, "unchanged": 0}
    assert seed_db(harness, owner) == {"inserted": 0, "updated": 0, "unchanged": 3}
    data = yaml.safe_load(FIXTURE.read_text())
    data["items"][0]["max_age"] = 35
    changed = tmp_path / "opportunities.v2.yaml"
    changed.write_text(yaml.safe_dump(data))
    assert seed_db(harness, owner, changed) == {
        "inserted": 0,
        "updated": 1,
        "unchanged": 2,
    }
    items = client.get("/v1/opportunities", headers=owner).json()["items"]
    row = next(i for i in items if i["slug"] == "test-working-holiday")
    assert row["max_age"] == 35 and row["version"] == 2


def test_seed_rows_stay_inside_their_workspace(harness, owner, client, platform):
    seed_db(harness, owner)
    actor = uuid.uuid4()
    platform.grants[actor] = set(harness.cell.permissions())
    other = harness.token(actor, uuid.uuid4())
    assert client.get("/v1/opportunities", headers=other).json()["items"] == []


def test_seed_api_mode_goes_through_the_api(harness, owner, client, platform):
    _, rows = read(FIXTURE, harness.cell.resource("opportunity"))
    assert upsert_api(client, owner, 1, rows) == {
        "inserted": 3,
        "updated": 0,
        "unchanged": 0,
    }
    assert upsert_api(client, owner, 1, rows) == {
        "inserted": 0,
        "updated": 0,
        "unchanged": 3,
    }
    assert any(
        e["permission"] == "radar.opportunity:write"
        for e in platform.executions.values()
    )


def test_seed_file_is_refused_without_provenance(harness, tmp_path):
    data = yaml.safe_load(FIXTURE.read_text())
    del data["items"][1]["source_url"]
    data["items"][2]["slug"] = data["items"][0]["slug"]
    bad = tmp_path / "opportunities.v1.yaml"
    bad.write_text(yaml.safe_dump(data))
    with pytest.raises(SeedError) as error:
        read(bad, harness.cell.resource("opportunity"))
    assert "missing source_url" in str(error.value) and "duplicate slug" in str(
        error.value
    )


def test_the_curated_seed_file_is_valid(harness, cell_root):
    header, rows = read(default_file(cell_root), harness.cell.resource("opportunity"))
    assert header["version"] >= 1 and 30 <= len(rows) <= 80
    for row in rows:
        assert row["source_url"].startswith("https://") or row["source_url"].startswith(
            "http://"
        )
        assert row["verification_status"] in (
            "verified",
            "partially_verified",
            "unverified",
        )
        assert row["category"].split("/")[0] in {
            "abroad",
            "education",
            "career",
            "business",
            "finance",
            "competition",
            "license",
            "research",
            "volunteering",
            "networking",
            "health",
            "sport",
            "government",
        }


def test_the_curated_seed_loads_and_answers_a_thai_profile(
    harness, owner, client, cell_root
):
    counts = seed_db(harness, owner, default_file(cell_root))
    assert counts["inserted"] >= 30
    out = client.post(
        "/v1/radar",
        headers=owner,
        params={"as_of": AS_OF},
        json={
            "birthdate": "1997-03-01",
            "nationality": "TH",
            "education_level": "bachelor",
        },
    )
    assert out.status_code == 200, out.text
    body = out.json()
    assert body["age"] == 29 and sum(body["counts"].values()) == counts["inserted"]
    urgent = body["buckets"]["prepare_now"] + body["buckets"]["closing_by_age"]
    assert any(i["category"].startswith("abroad/working-holiday") for i in urgent)


def test_profile_radar_buckets_and_statuses(harness, owner, client):
    seed_db(harness, owner)
    profile = client.post(
        "/v1/profiles",
        headers=owner,
        json={
            "display_name": "Book",
            "birthdate": "1997-03-01",
            "nationality": "TH",
            "education_level": "bachelor",
        },
    ).json()
    items = {
        i["slug"]: i
        for i in client.get("/v1/opportunities", headers=owner).json()["items"]
    }
    status = client.post(
        "/v1/opportunity-statuses",
        headers=owner,
        json={
            "profile_id": profile["id"],
            "opportunity_id": items["test-working-holiday"]["id"],
            "status": "preparing",
        },
    )
    assert status.status_code == 201, status.text
    out = client.get(
        f"/v1/profiles/{profile['id']}/radar", headers=owner, params={"as_of": AS_OF}
    )
    assert out.status_code == 200, out.text
    body = out.json()
    where = {
        i["slug"]: (bucket, i) for bucket, rows in body["buckets"].items() for i in rows
    }
    # cap 30 closes 2028-03-01 with 6 months of prep: inside the horizon, no need to start yet
    assert where["test-working-holiday"][0] == "closing_by_age"
    assert where["test-working-holiday"][1]["my_status"] == "preparing"
    assert where["test-working-holiday"][1]["age_closes_on"] == "2028-03-01"
    assert where["test-scholarship"][0] == "watch"  # cap 34: closes 2032
    assert where["test-licence"][0] == "evergreen"
    # four years older: the cap of 34 closes 2028-03-01, so May 2027 is the last chance and
    # 12 months of preparation should have started already
    older = client.post(
        "/v1/radar",
        headers=owner,
        params={"as_of": AS_OF},
        json={"birthdate": "1993-03-01", "nationality": "TH"},
    ).json()
    late = older["buckets"]["prepare_now"]
    assert [i["slug"] for i in late] == ["test-scholarship"] and late[0][
        "latest_chance"
    ] == "2027-05-31"
    assert "preparation_behind_schedule" in late[0]["caveats"]
    assert [i["slug"] for i in older["buckets"]["missed"]] == ["test-working-holiday"]


def test_radar_category_prefix_and_validation(harness, owner, client):
    seed_db(harness, owner)
    body = {"birthdate": "1997-03-01", "nationality": "TH"}
    out = client.post(
        "/v1/radar",
        headers=owner,
        params={"as_of": AS_OF, "category": "abroad"},
        json=body,
    ).json()
    assert sum(out["counts"].values()) == 1
    assert client.post(
        "/v1/radar", headers=owner, params={"category": "abr"}, json=body
    ).json()["counts"] == {k: 0 for k in out["counts"]}
    assert (
        client.post(
            "/v1/radar", headers=owner, json={**body, "nationality": "THA"}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/radar", headers=owner, params={"horizon_years": 0}, json=body
        ).status_code
        == 422
    )


def test_radar_permissions(harness, owner, client, platform):
    profile = client.post(
        "/v1/profiles",
        headers=owner,
        json={"display_name": "P", "birthdate": "2000-01-01", "nationality": "TH"},
    ).json()
    actor = uuid.uuid4()
    platform.grants[actor] = {"radar.opportunity:read"}
    reader = harness.token(actor, workspace_of(owner))
    assert (
        client.post(
            "/v1/radar",
            headers=reader,
            json={"birthdate": "2000-01-01", "nationality": "TH"},
        ).status_code
        == 200
    )
    assert (
        client.get(f"/v1/profiles/{profile['id']}/radar", headers=reader).status_code
        == 404
    )
    stranger = harness.token(uuid.uuid4(), uuid.uuid4())
    assert (
        client.post(
            "/v1/radar",
            headers=stranger,
            json={"birthdate": "2000-01-01", "nationality": "TH"},
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/v1/profiles/{profile['id'] + 999}/radar", headers=owner
        ).status_code
        == 404
    )
    assert (
        date.fromisoformat(
            client.post(
                "/v1/radar",
                headers=owner,
                json={"birthdate": "2000-01-01", "nationality": "TH"},
            ).json()["as_of"]
        )
        == date.today()
    )
