"""The profile radar: which opportunities close by age, need preparation now, are open, or are evergreen.

    GET  /v1/profiles/{id}/radar   a stored profile, with that profile's status per opportunity
                                   (read on profile, opportunity and opportunity-status)
    POST /v1/radar                 an ad-hoc profile in the body, nothing stored (read on opportunity)

Both take ``as_of`` (default today), ``horizon_years`` (1-10, default 3) and ``category`` (a path
prefix: ``abroad`` matches ``abroad`` and ``abroad/working-holiday``). The rules are in ``rules.py``.
"""

from datetime import date
from typing import Annotated, Any, Literal

from fastapi import HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field

from life_radar.rules import EDUCATION, Person, radar

MAX_ROWS = 20_000  # catalog rows per workspace; a bigger one gets 413 instead of an unbounded scan
OPPORTUNITY_COLUMNS = (
    "id, slug, name, name_th, category, country, official_url, nationalities, thai_eligible, min_age, max_age,"
    " age_basis, gender, min_education, enrollment_required, recurrence, open_date, close_date, window_months,"
    " attempts_limit, prep_lead_time_months, urgency, source_url, last_verified_at, verification_status, status"
)
Level = Literal[EDUCATION]  # type: ignore[valid-type]


class AdHocProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    birthdate: date
    nationality: str = Field(min_length=2, max_length=2)
    other_nationalities: list[Annotated[str, Field(min_length=2, max_length=2)]] = []
    gender: Literal["unspecified", "male", "female", "other"] = "unspecified"
    education_level: Level = "none"
    enrolled_in: Level = "none"


def category_filter(category: str | None) -> tuple[str, list[Any]]:
    if not category:
        return "", []
    prefix = category.strip("/")
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return " AND (category = %s OR category LIKE %s)", [prefix, escaped + "/%"]


def register(ctx) -> None:
    schema, cell = ctx.cell.schema, ctx.cell.name
    opportunities = f"{schema}.{ctx.cell.resource('opportunity').table}"
    statuses = f"{schema}.{ctx.cell.resource('opportunity-status').table}"
    Caller = (
        ctx.caller
    )  # a real annotation object: FastAPI must see the dependency, not a string

    def catalog(conn, category: str | None) -> list[dict[str, Any]]:
        extra, params = category_filter(category)
        rows = conn.execute(
            f"SELECT {OPPORTUNITY_COLUMNS} FROM {opportunities} WHERE status = 'active'{extra}"
            " ORDER BY slug LIMIT %s",
            [*params, MAX_ROWS + 1],
        ).fetchall()
        if len(rows) > MAX_ROWS:
            raise HTTPException(
                status_code=413,
                detail={"error": "catalog_too_large", "limit": MAX_ROWS},
            )
        return rows

    def answer(result: dict[str, Any], **extra: Any) -> dict[str, Any]:
        return jsonable_encoder({**extra, **result})

    @ctx.app.get("/v1/profiles/{profile_id}/radar", tags=["radar"])
    def profile_radar(
        profile_id: int,
        caller: Caller,
        as_of: date | None = None,
        horizon_years: Annotated[int, Query(ge=1, le=10)] = 3,
        category: Annotated[str | None, Query(max_length=200)] = None,
    ) -> dict[str, Any]:
        ctx.allow(
            caller, f"{cell}.profile:read", "profile", str(profile_id), not_found=True
        )
        ctx.allow(caller, f"{cell}.opportunity:read", "opportunity")
        ctx.allow(caller, f"{cell}.opportunity-status:read", "opportunity-status")
        with ctx.bound(caller) as conn:
            profile = ctx.load(conn, ctx.cell.resource("profile"), profile_id)
            rows = catalog(conn, category)
            mine = {
                row["opportunity_id"]: row
                # nosemgrep: python.sqlalchemy.security.sqlalchemy-execute-raw-query.sqlalchemy-execute-raw-query -- the table name comes from the cell spec (validated snake_case identifiers); values are bound as %s parameters
                for row in conn.execute(
                    f"SELECT opportunity_id, status FROM {statuses} WHERE profile_id = %s",
                    (profile_id,),
                ).fetchall()
            }
        result = radar(
            rows,
            Person.of(profile),
            as_of or date.today(),
            horizon_years,
            statuses=mine,
        )
        return answer(result, profile_id=profile_id)

    @ctx.app.post("/v1/radar", tags=["radar"])
    def adhoc_radar(
        body: AdHocProfile,
        caller: Caller,
        as_of: date | None = None,
        horizon_years: Annotated[int, Query(ge=1, le=10)] = 3,
        category: Annotated[str | None, Query(max_length=200)] = None,
    ) -> dict[str, Any]:
        ctx.allow(caller, f"{cell}.opportunity:read", "opportunity")
        with ctx.bound(caller) as conn:
            rows = catalog(conn, category)
        return answer(
            radar(
                rows, Person.of(body.model_dump()), as_of or date.today(), horizon_years
            )
        )
