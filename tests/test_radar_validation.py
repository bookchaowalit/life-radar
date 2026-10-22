"""What the radar API refuses and keeps for opportunities, profiles and per-profile statuses (cell.yaml rules)."""

import uuid

import pytest

OPPORTUNITIES = "/v1/opportunities"
PROFILES = "/v1/profiles"
STATUSES = "/v1/opportunity-statuses"


def slug(prefix="opp"):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def create_opportunity(client, owner, **fields):
    body = {"slug": slug(), "name": "Working holiday", "category": "abroad", **fields}
    return client.post(OPPORTUNITIES, headers=owner, json=body)


def create_profile(client, owner, **fields):
    body = {
        "display_name": "Book",
        "birthdate": "1997-03-01",
        "nationality": "TH",
        **fields,
    }
    return client.post(PROFILES, headers=owner, json=body)


def ids_for(client, owner):
    opportunity = create_opportunity(client, owner).json()["id"]
    profile = create_profile(client, owner).json()["id"]
    return profile, opportunity


# --- opportunity -------------------------------------------------------------------------------


@pytest.mark.parametrize("missing", ["slug", "name", "category"])
def test_an_opportunity_needs_a_slug_a_name_and_a_category(client, owner, missing):
    body = {"slug": slug(), "name": "Grant", "category": "business/grant"}
    del body[missing]
    assert client.post(OPPORTUNITIES, headers=owner, json=body).status_code == 422


def test_opportunity_text_limits(client, owner):
    assert create_opportunity(client, owner, slug="s" * 121).status_code == 422
    assert create_opportunity(client, owner, slug="s" * 120).status_code == 201
    assert create_opportunity(client, owner, name="n" * 301).status_code == 422
    assert create_opportunity(client, owner, category="c" * 201).status_code == 422
    assert create_opportunity(client, owner, country="ABCDEFGHI").status_code == 422
    assert create_opportunity(client, owner, country="AU").status_code == 201


@pytest.mark.parametrize(
    ("field", "bad", "good"),
    [
        ("thai_eligible", "maybe", "partial"),
        ("age_basis", "at_birth", "calendar_year"),
        ("gender", "other", "female"),
        ("min_education", "phd", "master"),
        ("recurrence", "monthly", "cohort"),
        ("urgency", "urgent", "preparation_critical"),
        ("verification_status", "checked", "stale"),
        ("status", "closed", "discontinued"),
    ],
)
def test_opportunity_enums_refuse_unknown_values(client, owner, field, bad, good):
    assert create_opportunity(client, owner, **{field: bad}).status_code == 422
    assert create_opportunity(client, owner, **{field: good}).status_code == 201


def test_ages_are_between_0_and_120(client, owner):
    assert create_opportunity(client, owner, min_age=-1).status_code == 422
    assert create_opportunity(client, owner, max_age=121).status_code == 422
    fits = create_opportunity(client, owner, min_age=0, max_age=120)
    assert fits.status_code == 201, fits.text


def test_preparation_lead_time_is_0_to_240_months(client, owner):
    assert (
        create_opportunity(client, owner, prep_lead_time_months=-1).status_code == 422
    )
    assert (
        create_opportunity(client, owner, prep_lead_time_months=241).status_code == 422
    )
    assert (
        create_opportunity(client, owner, prep_lead_time_months=240).status_code == 201
    )


def test_attempts_limit_is_at_least_one(client, owner):
    assert create_opportunity(client, owner, attempts_limit=0).status_code == 422
    assert create_opportunity(client, owner, attempts_limit=1).status_code == 201


@pytest.mark.parametrize(
    "field",
    ["nationalities", "enrollment_required", "window_months", "prerequisites", "tags"],
)
def test_list_fields_must_be_json_arrays(client, owner, field):
    assert create_opportunity(client, owner, **{field: {"TH": True}}).status_code == 422
    assert create_opportunity(client, owner, **{field: []}).status_code == 201


def test_conditions_must_be_a_json_object(client, owner):
    assert create_opportunity(client, owner, conditions=["ielts"]).status_code == 422
    good = create_opportunity(client, owner, conditions={"ielts": 6.5})
    assert good.status_code == 201, good.text
    assert good.json()["conditions"] == {"ielts": 6.5}


def test_dates_must_be_calendar_dates(client, owner):
    assert create_opportunity(client, owner, close_date="31/01/2027").status_code == 422
    assert (
        create_opportunity(client, owner, last_verified_at="2026-02-30").status_code
        == 422
    )


# The next rules are CHECK constraints in migrations/0001_radar.sql, not cell.yaml: the API answers
# 422 invalid_value without naming the fields.


def test_min_age_cannot_be_above_max_age(client, owner):
    refused = create_opportunity(client, owner, min_age=30, max_age=18)
    assert refused.status_code == 422, refused.text
    assert refused.json()["detail"] == {"error": "invalid_value"}
    assert create_opportunity(client, owner, min_age=18, max_age=18).status_code == 201


def test_a_window_cannot_close_before_it_opens(client, owner):
    refused = create_opportunity(
        client, owner, open_date="2027-03-01", close_date="2027-01-31"
    )
    assert refused.status_code == 422, refused.text
    same_day = create_opportunity(
        client, owner, open_date="2027-03-01", close_date="2027-03-01"
    )
    assert same_day.status_code == 201, same_day.text


def test_moving_the_close_date_before_the_open_date_is_refused_on_update(client, owner):
    item = create_opportunity(client, owner, open_date="2027-03-01").json()
    path = f"{OPPORTUNITIES}/{item['id']}"
    refused = client.patch(path, headers=owner, json={"close_date": "2027-02-01"})
    assert refused.status_code == 422, refused.text
    stored = client.get(path, headers=owner).json()
    assert stored["close_date"] is None
    assert stored["version"] == 1


@pytest.mark.parametrize("bad", ["Has Caps", "under_score", "-leading", "double--dash"])
def test_slug_is_lowercase_words_joined_by_dashes(client, owner, bad):
    assert create_opportunity(client, owner, slug=bad).status_code == 422


@pytest.mark.parametrize("bad", ["Abroad", "abroad/", "/abroad", "abroad//visa", "a b"])
def test_category_is_a_lowercase_slash_path(client, owner, bad):
    assert create_opportunity(client, owner, category=bad).status_code == 422
    good = create_opportunity(client, owner, category="education/scholarship/master")
    assert good.status_code == 201, good.text


def test_new_opportunity_defaults(client, owner):
    response = create_opportunity(client, owner)
    assert response.status_code == 201, response.text
    item = response.json()
    assert item["thai_eligible"] == "unknown"
    assert item["age_basis"] == "unspecified"
    assert item["gender"] == "any"
    assert item["min_education"] == "none"
    assert item["recurrence"] == "annual"
    assert item["prep_lead_time_months"] == 0
    assert item["urgency"] == "evergreen"
    assert item["verification_status"] == "unverified"
    assert item["status"] == "active"
    assert item["version"] == 1


def test_slug_is_unique(client, owner):
    assert create_opportunity(client, owner, slug="wh-australia").status_code == 201
    again = create_opportunity(client, owner, slug="wh-australia", name="Copy")
    assert again.status_code == 409, again.text


def test_opportunities_are_listed_by_slug(client, owner):
    for name in ("zeta", "alpha", "mid"):
        create_opportunity(client, owner, slug=name)
    listed = client.get(OPPORTUNITIES, headers=owner)
    assert [i["slug"] for i in listed.json()["items"]] == ["alpha", "mid", "zeta"]
    reverse = client.get(OPPORTUNITIES, headers=owner, params={"order": "desc"})
    assert [i["slug"] for i in reverse.json()["items"]] == ["zeta", "mid", "alpha"]


def test_opportunities_filter_and_group_by_their_filters(client, owner):
    create_opportunity(client, owner, category="abroad", thai_eligible="yes")
    create_opportunity(client, owner, category="abroad", thai_eligible="no")
    create_opportunity(client, owner, category="education/scholarship")
    eligible = client.get(OPPORTUNITIES, headers=owner, params={"thai_eligible": "yes"})
    assert [i["thai_eligible"] for i in eligible.json()["items"]] == ["yes"]
    stats = client.get(
        f"{OPPORTUNITIES}/stats", headers=owner, params={"group_by": "category"}
    )
    assert stats.json()["groups"] == {"abroad": 2, "education/scholarship": 1}
    refused = client.get(
        f"{OPPORTUNITIES}/stats", headers=owner, params={"group_by": "gender"}
    )
    assert refused.status_code == 422


# --- profile ----------------------------------------------------------------------------------


@pytest.mark.parametrize("missing", ["display_name", "birthdate", "nationality"])
def test_a_profile_needs_a_name_a_birthdate_and_a_nationality(client, owner, missing):
    body = {"display_name": "P", "birthdate": "2000-01-01", "nationality": "TH"}
    del body[missing]
    assert client.post(PROFILES, headers=owner, json=body).status_code == 422


def test_nationality_and_residence_are_two_letter_codes(client, owner):
    assert create_profile(client, owner, nationality="THA").status_code == 422
    assert create_profile(client, owner, country_of_residence="AUS").status_code == 422
    assert create_profile(client, owner, country_of_residence="AU").status_code == 201


def test_profile_enums_refuse_unknown_values(client, owner):
    assert create_profile(client, owner, gender="x").status_code == 422
    assert create_profile(client, owner, education_level="phd").status_code == 422
    assert create_profile(client, owner, enrolled_in="kindergarten").status_code == 422


def test_profile_lists_must_be_json_arrays(client, owner):
    assert create_profile(client, owner, other_nationalities="AU").status_code == 422
    assert create_profile(client, owner, interests={"a": 1}).status_code == 422


def test_new_profile_defaults(client, owner):
    profile = create_profile(client, owner).json()
    assert profile["gender"] == "unspecified"
    assert profile["education_level"] == "none"
    assert profile["enrolled_in"] == "none"


# --- opportunity-status -----------------------------------------------------------------------


def test_a_status_needs_a_profile_and_an_opportunity(client, owner):
    profile, opportunity = ids_for(client, owner)
    no_profile = client.post(
        STATUSES, headers=owner, json={"opportunity_id": opportunity}
    )
    assert no_profile.status_code == 422
    no_opportunity = client.post(STATUSES, headers=owner, json={"profile_id": profile})
    assert no_opportunity.status_code == 422


def test_a_status_cannot_point_at_missing_records(client, owner):
    profile, opportunity = ids_for(client, owner)
    for body in (
        {"profile_id": 999_999_999, "opportunity_id": opportunity},
        {"profile_id": profile, "opportunity_id": 999_999_999},
    ):
        response = client.post(STATUSES, headers=owner, json=body)
        assert response.status_code == 422, response.text
        assert response.json()["detail"] == {"error": "reference_not_found"}


def test_status_values_and_limits(client, owner):
    profile, opportunity = ids_for(client, owner)
    base = {"profile_id": profile, "opportunity_id": opportunity}
    bad = client.post(STATUSES, headers=owner, json={**base, "status": "won"})
    assert bad.status_code == 422
    long = client.post(STATUSES, headers=owner, json={**base, "target_cycle": "c" * 51})
    assert long.status_code == 422
    created = client.post(STATUSES, headers=owner, json=base)
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "interested"


def test_one_status_per_profile_and_opportunity(client, owner):
    profile, opportunity = ids_for(client, owner)
    base = {"profile_id": profile, "opportunity_id": opportunity}
    assert client.post(STATUSES, headers=owner, json=base).status_code == 201
    again = client.post(STATUSES, headers=owner, json={**base, "status": "applied"})
    assert again.status_code == 409, again.text
    other = create_opportunity(client, owner).json()["id"]
    second = client.post(
        STATUSES, headers=owner, json={"profile_id": profile, "opportunity_id": other}
    )
    assert second.status_code == 201, second.text


def test_moving_a_status_forward_bumps_the_version(client, owner):
    profile, opportunity = ids_for(client, owner)
    created = client.post(
        STATUSES,
        headers=owner,
        json={"profile_id": profile, "opportunity_id": opportunity},
    ).json()
    path = f"{STATUSES}/{created['id']}"
    applied = client.patch(
        path, headers=owner, json={"status": "applied", "next_action_on": "2026-11-01"}
    )
    assert applied.status_code == 200, applied.text
    assert applied.json()["version"] == 2
    same = client.patch(path, headers=owner, json={"status": "applied"})
    assert same.json()["version"] == 2
    listed = client.get(STATUSES, headers=owner, params={"status": "applied"})
    assert [i["id"] for i in listed.json()["items"]] == [created["id"]]


def test_a_tracked_profile_or_opportunity_cannot_be_deleted(client, owner):
    profile, opportunity = ids_for(client, owner)
    status = client.post(
        STATUSES,
        headers=owner,
        json={"profile_id": profile, "opportunity_id": opportunity},
    ).json()
    assert client.delete(f"{PROFILES}/{profile}", headers=owner).status_code == 409
    assert (
        client.delete(f"{OPPORTUNITIES}/{opportunity}", headers=owner).status_code
        == 409
    )
    assert client.delete(f"{STATUSES}/{status['id']}", headers=owner).status_code == 204
    assert client.delete(f"{PROFILES}/{profile}", headers=owner).status_code == 204
