"""The radar rules on hand-made opportunities: age caps, windows, preparation and eligibility."""

from datetime import date

import pytest

from life_radar.rules import (
    Person,
    add_years,
    age_limits,
    age_on,
    classify,
    month_runs,
    radar,
    windows,
)

TODAY = date(2026, 10, 17)
THAI_29 = Person(
    birthdate=date(1997, 3, 1),
    nationalities=frozenset({"TH"}),
    gender="male",
    education_level="bachelor",
)


def opp(**fields):
    base = {
        "id": 1,
        "slug": "x",
        "name": "X",
        "category": "abroad/working-holiday",
        "nationalities": ["TH"],
        "thai_eligible": "yes",
        "recurrence": "rolling",
        "urgency": "time_critical",
        "status": "active",
        "verification_status": "verified",
        "last_verified_at": "2026-10-17",
        "prep_lead_time_months": 0,
        "age_basis": "at_application",
        "gender": "any",
        "min_education": "none",
    }
    return {**base, **fields}


def test_ages_and_leap_days():
    assert age_on(date(1997, 3, 1), TODAY) == 29
    assert age_on(date(1997, 10, 18), TODAY) == 28
    assert add_years(date(2000, 2, 29), 1) == date(2001, 2, 28)


def test_age_limits_by_basis():
    birth = date(1997, 3, 1)
    assert age_limits(
        {"min_age": 18, "max_age": 30, "age_basis": "at_application"}, birth
    ) == (date(2015, 3, 1), date(2028, 3, 1))
    # calendar_year: eligible through the whole year in which you turn 30
    assert age_limits({"max_age": 30, "age_basis": "calendar_year"}, birth) == (
        None,
        date(2028, 1, 1),
    )


def test_month_runs_wrap_over_the_year_end():
    assert month_runs([11, 12, 1]) == [(11, 1)]
    assert month_runs([3, 4, 9]) == [(3, 4), (9, 9)]
    assert month_runs(list(range(1, 13))) == [(1, 12)]


def test_annual_windows_from_months():
    found, known = windows(
        {"recurrence": "annual", "window_months": [9, 10]}, TODAY, date(2028, 12, 31)
    )
    assert known and found[0] == (date(2026, 9, 1), date(2026, 10, 31))
    assert (date(2027, 9, 1), date(2027, 10, 31)) in found


def test_annual_windows_repeat_known_dates():
    found, known = windows(
        {"recurrence": "annual", "open_date": "2026-02-01", "close_date": "2026-03-31"},
        TODAY,
        date(2028, 12, 31),
    )
    assert known and found == [
        (date(2027, 2, 1), date(2027, 3, 31)),
        (date(2028, 2, 1), date(2028, 3, 31)),
    ]


def test_working_holiday_closing_by_age():
    item = classify(opp(min_age=18, max_age=30), THAI_29, TODAY)
    assert item["bucket"] == "closing_by_age"
    assert item["age_closes_on"] == date(2028, 3, 1) and item["years_left"] == 1.4
    assert "open_now" in item["flags"]


def test_long_preparation_moves_it_to_prepare_now():
    # 30 cap closes 2028-03-01; with 16 months of prep the start date is 2026-10-30: within 90 days
    item = classify(
        opp(min_age=18, max_age=30, prep_lead_time_months=16), THAI_29, TODAY
    )
    assert item["bucket"] == "prepare_now"
    assert {"closing_by_age", "prepare_now"} <= set(item["flags"])
    assert item["start_prep_by"] <= date(2026, 11, 1)


def test_last_annual_window_before_the_cap_is_the_latest_chance():
    item = classify(
        opp(max_age=30, recurrence="annual", window_months=[5, 6]), THAI_29, TODAY
    )
    assert item["windows_left"] == 1 and item["latest_chance"] == date(2027, 6, 30)
    assert item["bucket"] == "closing_by_age"


def test_no_window_left_before_the_cap_is_missed():
    # a 29 cap closes on 2027-03-01; this year's June window has passed and next June is too late
    person = Person(birthdate=date(1997, 3, 1), nationalities=frozenset({"TH"}))
    item = classify(
        opp(max_age=29, recurrence="annual", window_months=[6]), person, TODAY
    )
    assert item["bucket"] == "missed" and "no_window_before_age_cap" in item["reasons"]


def test_aged_out_and_too_young():
    assert classify(opp(max_age=25), THAI_29, TODAY)["bucket"] == "missed"
    teen = Person(birthdate=date(2010, 1, 1), nationalities=frozenset({"TH"}))
    item = classify(opp(min_age=18, max_age=30), teen, TODAY)
    assert item["bucket"] == "opens_later" and item["age_opens_on"] == date(2028, 1, 1)


def test_nationality_gender_and_student_rules():
    assert classify(opp(nationalities=["JP", "KR"]), THAI_29, TODAY)["reasons"] == [
        "nationality"
    ]
    assert (
        classify(opp(nationalities=["*"]), THAI_29, TODAY)["bucket"] != "not_eligible"
    )
    assert (
        classify(opp(nationalities=[], thai_eligible="no"), THAI_29, TODAY)["bucket"]
        == "not_eligible"
    )
    assert classify(opp(gender="female"), THAI_29, TODAY)["reasons"] == ["gender"]
    assert classify(opp(enrollment_required=["bachelor"]), THAI_29, TODAY)[
        "reasons"
    ] == ["student_only"]
    pupil = Person(
        birthdate=date(2010, 1, 1),
        nationalities=frozenset({"TH"}),
        enrolled_in="secondary",
    )
    assert (
        classify(opp(enrollment_required=["bachelor"]), pupil, TODAY)["bucket"]
        == "opens_later"
    )


def test_evergreen_and_watch():
    licence = opp(
        recurrence="annual",
        window_months=[3],
        urgency="evergreen",
        prep_lead_time_months=36,
    )
    assert classify(licence, THAI_29, TODAY)["bucket"] == "evergreen"
    far_cap = opp(max_age=40, recurrence="annual", window_months=[3])
    assert classify(far_cap, THAI_29, TODAY)["bucket"] == "watch"


def test_one_off_deadline_and_closed_one_off():
    upcoming = opp(
        recurrence="one_off",
        open_date="2026-11-01",
        close_date="2027-01-31",
        prep_lead_time_months=3,
    )
    item = classify(upcoming, THAI_29, TODAY)
    assert item["bucket"] == "prepare_now" and item["latest_chance"] == date(
        2027, 1, 31
    )
    closed = opp(recurrence="one_off", close_date="2026-01-31")
    assert classify(closed, THAI_29, TODAY)["bucket"] == "missed"


def test_caveats_for_unverified_and_stale_sources():
    item = classify(
        opp(verification_status="unverified", last_verified_at="2024-01-01"),
        THAI_29,
        TODAY,
    )
    assert {"source_unverified", "verify_again"} <= set(item["caveats"])


@pytest.mark.parametrize("status", ["suspended", "discontinued"])
def test_radar_skips_inactive_and_sorts(status):
    rows = [
        opp(id=1, slug="late", max_age=31),
        opp(id=2, slug="soon", max_age=30),
        opp(id=3, slug="gone", status=status),
    ]
    out = radar(rows, THAI_29, TODAY, statuses={2: {"status": "preparing"}})
    assert [i["slug"] for i in out["buckets"]["closing_by_age"]] == ["soon", "late"]
    assert out["buckets"]["closing_by_age"][0]["my_status"] == "preparing"
    assert sum(out["counts"].values()) == 2 and out["age"] == 29
