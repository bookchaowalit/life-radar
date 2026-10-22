"""The radar rules: given a person and the opportunity catalog, what closes, what to prepare, what is open.

Pure functions over plain dicts (rows as the API returns them), so they are tested without a
database. Every opportunity lands in exactly one bucket, the first that applies in this order:

    prepare_now      the last chance is so close that preparation has to start now
                     (start_prep_by is on or before today + PREP_SLACK_DAYS)
    closing_by_age   the age cap closes it for good within the horizon (default 3 years)
    open_now         a window is open today
    evergreen        no age cap and it recurs (or is rolling): it will still be there
    watch            eligible, nothing urgent yet (the next window is later)
    opens_later      not yet: too young, or a student-only opportunity for a later level
    missed           gone for this person: aged out, or no window left before the age cap,
                     or a one-off that has closed
    not_eligible     nationality, gender or enrollment rules exclude this person

``flags`` lists every condition that holds (an item in prepare_now can also be open_now and
closing_by_age); ``caveats`` lists what the rules could not decide (unknown window, age measured
at programme start, unverified source...).
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

EDUCATION = ("none", "secondary", "vocational", "bachelor", "master", "doctorate")
BUCKETS = (
    "prepare_now",
    "closing_by_age",
    "open_now",
    "evergreen",
    "watch",
    "opens_later",
    "missed",
    "not_eligible",
)
PREP_SLACK_DAYS = 90  # "start now" means within the next three months
LOOKAHEAD_YEARS = (
    12  # how far windows are projected when there is no age cap to stop them
)
STALE_AFTER_DAYS = 365  # a source older than this is flagged for re-verification


@dataclass(frozen=True)
class Person:
    birthdate: date
    nationalities: frozenset[str]
    gender: str = "unspecified"
    education_level: str = "none"
    enrolled_in: str = "none"

    @classmethod
    def of(cls, row: dict[str, Any]) -> Person:
        """From a profile row (or a POST /v1/radar body)."""
        birth = row["birthdate"]
        if isinstance(birth, str):
            birth = date.fromisoformat(birth)
        codes = {
            str(row["nationality"]).upper(),
            *(str(c).upper() for c in row.get("other_nationalities") or []),
        }
        return cls(
            birthdate=birth,
            nationalities=frozenset(codes),
            gender=row.get("gender") or "unspecified",
            education_level=row.get("education_level") or "none",
            enrolled_in=row.get("enrolled_in") or "none",
        )


def add_years(day: date, years: int) -> date:
    """The same calendar day ``years`` later; 29 February becomes 28 February in a common year."""
    try:
        return day.replace(year=day.year + years)
    except ValueError:
        return day.replace(year=day.year + years, day=28)


def age_on(birth: date, day: date) -> int:
    return day.year - birth.year - ((day.month, day.day) < (birth.month, birth.day))


def age_limits(opp: dict[str, Any], birth: date) -> tuple[date | None, date | None]:
    """(first eligible day, first day no longer eligible) from min_age/max_age and the age basis."""
    basis = opp.get("age_basis") or "unspecified"
    opens = closes = None
    if opp.get("min_age") is not None:
        opens = (
            date(birth.year + opp["min_age"], 1, 1)
            if basis == "calendar_year"
            else add_years(birth, opp["min_age"])
        )
    if opp.get("max_age") is not None:
        closes = (
            date(birth.year + opp["max_age"] + 1, 1, 1)
            if basis == "calendar_year"
            else add_years(birth, opp["max_age"] + 1)
        )
    return opens, closes


def _date(value: Any) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def month_runs(months: list[int]) -> list[tuple[int, int]]:
    """Contiguous runs of months, wrapping over the year end: [11, 12, 1] -> [(11, 1)]."""
    chosen = {m for m in months if 1 <= m <= 12}
    if len(chosen) == 12:
        return [(1, 12)]
    runs = []
    for m in sorted(chosen):
        if (m - 2) % 12 + 1 in chosen:  # previous month is in the set: not a run start
            continue
        end = m
        while end % 12 + 1 in chosen:
            end = end % 12 + 1
        runs.append((m, end))
    return runs


def windows(
    opp: dict[str, Any], today: date, until: date
) -> tuple[list[tuple[date, date]], bool]:
    """Application windows that end on or after ``today`` and start before ``until``.

    Returns (windows, known): ``known`` is False when the opportunity says nothing about its window
    (no dates, no months), in which case the windows are a guess (the whole period, flagged).
    """
    recurrence = opp.get("recurrence") or "annual"
    open_date, close_date = _date(opp.get("open_date")), _date(opp.get("close_date"))
    months = list(opp.get("window_months") or [])
    out: list[tuple[date, date]] = []
    if recurrence == "rolling":
        start = max(open_date or today, today)
        end = min(close_date or until, until)
        return ([(start, end)] if start <= end else []), True
    if recurrence == "one_off":
        if close_date is None:
            return [(today, until)], False
        return (
            [(open_date or close_date - timedelta(days=30), close_date)]
            if close_date >= today
            else []
        ), True
    # annual and cohort
    if close_date is not None and close_date >= today:
        out.append((open_date or close_date - timedelta(days=30), close_date))
    after = close_date if close_date is not None else date.min
    if months:
        for year in range(today.year - 1, until.year + 1):
            for first, last in month_runs(months):
                start = date(year, first, 1)
                end_year = year if last >= first else year + 1
                end = date(end_year, last, calendar.monthrange(end_year, last)[1])
                if end >= today and start < until and start > after:
                    out.append((start, end))
    elif (cycle := open_date or close_date) is not None:
        # Known dates of one cycle, no months: assume the same dates every year (a missing
        # end of the cycle is the date that is known).
        first_open, first_close = open_date or cycle, close_date or cycle
        for shift in range(1, until.year - first_close.year + 2):
            start, end = add_years(first_open, shift), add_years(first_close, shift)
            if end >= today and start < until:
                out.append((start, end))
    else:
        return [(today, until)], False
    out.sort()
    return out, True


def classify(
    opp: dict[str, Any], person: Person, today: date, horizon_years: int = 3
) -> dict[str, Any]:
    """Where one opportunity stands for one person on ``today``."""
    flags: list[str] = []
    caveats: list[str] = []
    reasons: list[str] = []
    item: dict[str, Any] = {
        "id": opp.get("id"),
        "slug": opp.get("slug"),
        "name": opp.get("name"),
        "name_th": opp.get("name_th"),
        "category": opp.get("category"),
        "country": opp.get("country"),
        "urgency": opp.get("urgency"),
        "official_url": opp.get("official_url"),
        "source_url": opp.get("source_url"),
        "verification_status": opp.get("verification_status"),
        "last_verified_at": opp.get("last_verified_at"),
        "prep_lead_time_months": opp.get("prep_lead_time_months") or 0,
        "attempts_limit": opp.get("attempts_limit"),
        "age_now": age_on(person.birthdate, today),
        "age_opens_on": None,
        "age_closes_on": None,
        "years_left": None,
        "next_window": None,
        "windows_left": None,
        "latest_chance": None,
        "start_prep_by": None,
    }

    def done(bucket: str) -> dict[str, Any]:
        item.update(bucket=bucket, flags=flags, caveats=caveats, reasons=reasons)
        return item

    if opp.get("verification_status") != "verified":
        caveats.append(f"source_{opp.get('verification_status') or 'unverified'}")
    verified = _date(opp.get("last_verified_at"))
    if verified is None or (today - verified).days > STALE_AFTER_DAYS:
        caveats.append("verify_again")
    if (opp.get("attempts_limit") or 0) == 1:
        flags.append("once_in_a_lifetime")

    # Hard eligibility: who you are, not what you can still do.
    allowed = [str(c).upper() for c in opp.get("nationalities") or []]
    if (allowed and "*" not in allowed and not person.nationalities & set(allowed)) or (
        not allowed
        and "TH" in person.nationalities
        and opp.get("thai_eligible") == "no"
    ):
        reasons.append("nationality")
    elif not allowed and opp.get("thai_eligible") in (None, "unknown"):
        caveats.append("nationality_unknown")
    if opp.get("thai_eligible") == "partial" and "TH" in person.nationalities:
        caveats.append("thai_eligibility_partial")
    wanted_gender = opp.get("gender") or "any"
    if wanted_gender != "any":
        if person.gender in ("male", "female") and person.gender != wanted_gender:
            reasons.append("gender")
        elif person.gender not in ("male", "female"):
            caveats.append(f"only_{wanted_gender}")
    enrollment = [
        level for level in opp.get("enrollment_required") or [] if level in EDUCATION
    ]
    if enrollment and person.enrolled_in not in enrollment:
        lowest = min(EDUCATION.index(level) for level in enrollment)
        if (
            person.enrolled_in != "none"
            and EDUCATION.index(person.enrolled_in) < lowest
        ):
            flags.append("student_only_later")
        else:
            reasons.append("student_only")
    if reasons:
        return done("not_eligible")

    if EDUCATION.index(person.education_level) < EDUCATION.index(
        opp.get("min_education") or "none"
    ):
        caveats.append(f"needs_{opp.get('min_education')}")

    opens_on, closes_on = age_limits(opp, person.birthdate)
    item["age_opens_on"], item["age_closes_on"] = opens_on, closes_on
    if (opp.get("age_basis") or "unspecified") in (
        "at_start",
        "unspecified",
    ) and closes_on is not None:
        caveats.append(f"age_basis_{opp.get('age_basis') or 'unspecified'}")
    if closes_on is not None and closes_on <= today:
        reasons.append("aged_out")
        return done("missed")
    if closes_on is not None:
        item["years_left"] = round((closes_on - today).days / 365.25, 1)

    until = closes_on or add_years(today, LOOKAHEAD_YEARS)
    found, known = windows(opp, today, until)
    if not known:
        caveats.append("window_unknown")
    usable = [
        (start, end) for start, end in found if opens_on is None or end >= opens_on
    ]
    if closes_on is not None:
        usable = [
            (start, min(end, closes_on - timedelta(days=1)))
            for start, end in usable
            if start < closes_on
        ]
        item["windows_left"] = len(usable) if known else None
    if not usable:
        reasons.append(
            "no_window_before_age_cap" if closes_on is not None else "closed"
        )
        return done("missed")
    start, end = usable[0]
    item["next_window"] = {"start": start, "end": end}
    if start <= today <= end and (opens_on is None or opens_on <= today):
        flags.append("open_now")

    if closes_on is not None:
        item["latest_chance"] = usable[-1][1]
    elif (opp.get("recurrence") or "annual") == "one_off":
        item["latest_chance"] = end
    if item["latest_chance"] is not None:
        prep = timedelta(days=round(30.44 * (opp.get("prep_lead_time_months") or 0)))
        start_by = item["latest_chance"] - prep
        item["start_prep_by"] = start_by
        if prep and start_by <= today + timedelta(days=PREP_SLACK_DAYS):
            flags.append("prepare_now")
            if start_by < today:
                caveats.append("preparation_behind_schedule")
    if closes_on is not None and closes_on <= add_years(today, horizon_years):
        flags.append("closing_by_age")
    if closes_on is None and (opp.get("recurrence") or "annual") != "one_off":
        flags.append("evergreen")
    if opens_on is not None and opens_on > today:
        flags.append("too_young")

    if "too_young" in flags or "student_only_later" in flags:
        return done("opens_later")
    for bucket in ("prepare_now", "closing_by_age", "open_now", "evergreen"):
        if bucket in flags:
            return done(bucket)
    return done("watch")


def radar(
    opportunities: list[dict[str, Any]],
    person: Person,
    today: date,
    horizon_years: int = 3,
    statuses: dict[int, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """All active opportunities, bucketed for one person and sorted by what runs out first."""
    buckets: dict[str, list[dict[str, Any]]] = {name: [] for name in BUCKETS}
    for opp in opportunities:
        if (opp.get("status") or "active") != "active":
            continue
        item = classify(opp, person, today, horizon_years)
        if statuses is not None:
            opp_id = opp.get("id")
            mine = statuses.get(opp_id) if opp_id is not None else None
            item["my_status"] = mine["status"] if mine else None
        buckets[item["bucket"]].append(item)

    far = date.max

    def soonest(item: dict[str, Any]) -> tuple[date, date, date, date, str]:
        return (
            item["start_prep_by"] or far,
            item["latest_chance"] or far,
            item["age_closes_on"] or far,
            (item["next_window"] or {}).get("end") or far,
            item["slug"] or "",
        )

    for items in buckets.values():
        items.sort(key=soonest)
    return {
        "as_of": today,
        "horizon_years": horizon_years,
        "age": age_on(person.birthdate, today),
        "counts": {name: len(items) for name, items in buckets.items()},
        "buckets": buckets,
    }
