# SPEC-001 — L2 baseline: locked dependencies, strict types, domain rules under test

Standard: ADR-0004 — TDD + SDD (architecture-docs, `docs/architecture/decisions/ADR-0004-tdd-sdd-standard.md`).
Big Loop Plan Wave 2 (solo-empire `repository-catalog/roadmaps/BIG-LOOP-PLAN-2026-10-21.md`).

## Document control

| Field | Value |
|---|---|
| Spec ID / version | SPEC-001 / 1.0 |
| Status | in review (implemented; owner approval pending) |
| Repository / path | bookchaowalit/life-radar / `specs/001-l2-baseline/spec.md` |
| Owner (maker) | Claude Code (Wave 2 cells session) |
| Reviewer (checker) | Fresh Claude reviewer session (no maker context) |
| Approver | Owner (bookchaowalit): pending, see the Wave 2 report owner actions |
| Requirement links | Big Loop DoD L2: `PRODUCT.md`, ≥ 3 test files, Sentry, type check; L1 lockfile |
| Main-only | yes: committed straight to `main`, so the red run is local (ADR-0004 rule 2, v1.1) |
| Created / approved | 2026-10-22 / pending owner |

## 1. Problem and intent

- **Problem:** Dependencies were installed unpinned, the cell's own code (`src/life_radar/`) failed the strict type check with 14 errors and the tests failed the lint rules (PT018, C420), and the cell.yaml and migration rules of the catalog (slug and category formats, age and window order, one status per profile and opportunity) had no tests of their own.
- **Outcome:** the image installs exactly `uv.lock` (`uv sync --frozen`), CI runs Ruff, mypy
  (strict on `src/`) and a coverage gate on shared CI v1.1.1, and the cell's own rules have
  tests of their own beyond the generic contract suite.
- **Why now:** Wave 2 of the Big Loop Plan; milestone M1 is 2026-11-15.

## 2. Scope

| In scope | Out of scope (non-goals) |
|---|---|
| `uv.lock`, Dockerfile, CI caller bump, Ruff/mypy config and fixes, domain tests, `PRODUCT.md` | New endpoints or fields; database migrations; a shared cellkit package (owner decision 2026-10-21: each service owns its code) |

## 3. Behaviour — scenarios

### AC-01 — Minimum age cannot be above maximum age

- **Given** an owner with write permission
- **When** they create an opportunity with `min_age` 30 and `max_age` 18
- **Then** the API answers 422 `invalid_value`; equal ages are accepted
- **Test:** `tests/test_radar_validation.py::test_min_age_cannot_be_above_max_age` · level: integration (API + throwaway PostgreSQL)

### AC-02 — A window cannot close before it opens

- **Given** an opportunity opening 2027-03-01
- **When** it is created with `close_date` 2027-01-31, or patched to close on 2027-02-01
- **Then** both are refused with 422 and the stored row is unchanged (version 1); the same day for both is accepted
- **Test:** `tests/test_radar_validation.py::test_moving_the_close_date_before_the_open_date_is_refused_on_update` · level: integration (API + throwaway PostgreSQL)

### AC-03 — Slugs and categories follow their formats

- **Given** an owner with write permission
- **When** they create an opportunity with slug `Has Caps` or category `abroad//visa`
- **Then** the API answers 422; `education/scholarship/master` is accepted
- **Test:** `tests/test_radar_validation.py::test_category_is_a_lowercase_slash_path` · level: integration (API + throwaway PostgreSQL)

### AC-04 — One status per profile and opportunity

- **Given** a profile with a status for one opportunity
- **When** a second status for the same pair is created, then one for another opportunity
- **Then** the first is refused with 409, the second is created
- **Test:** `tests/test_radar_validation.py::test_one_status_per_profile_and_opportunity` · level: integration (API + throwaway PostgreSQL)

### AC-05 — A tracked profile or opportunity cannot be deleted

- **Given** a status linking a profile and an opportunity
- **When** the owner deletes the profile or the opportunity, then the status, then the profile
- **Then** the first two are refused with 409; after the status is gone the profile is deleted
- **Test:** `tests/test_radar_validation.py::test_a_tracked_profile_or_opportunity_cannot_be_deleted` · level: integration (API + throwaway PostgreSQL)

### AC-06 — New opportunities get the catalog defaults

- **Given** an opportunity with only slug, name and category
- **When** it is created
- **Then** `thai_eligible` unknown, `recurrence` annual, `urgency` evergreen, `verification_status` unverified, `status` active, `prep_lead_time_months` 0
- **Test:** `tests/test_radar_validation.py::test_new_opportunity_defaults` · level: integration (API + throwaway PostgreSQL)

### AC-07 — Opportunities are listed by slug

- **Given** opportunities zeta, alpha and mid
- **When** the owner lists them, then with `order=desc`
- **Then** they come back alpha, mid, zeta and reversed
- **Test:** `tests/test_radar_validation.py::test_opportunities_are_listed_by_slug` · level: integration (API + throwaway PostgreSQL)

### AC-08 — One known date of a cycle repeats each year

- **Given** an annual opportunity with only a close date (or only an open date) and no months
- **When** the radar projects its windows
- **Then** that date is a one-day window in each later year (behaviour kept through the type-check refactor)
- **Test:** `tests/test_rules.py::test_one_known_date_repeats_as_a_one_day_window_each_year` · level: integration (API + throwaway PostgreSQL)

### AC-09 — Numbers fit their columns

- **Given** an int field (PostgreSQL integer) or a real field
- **When** a client sends 2**31, or NaN / Infinity / 1e400 as raw JSON
- **Then** the API answers 422 naming the field (before: a 500 from PostgreSQL, or the value silently stored as null)
- **Test:** `tests/test_contract.py::test_numbers_fit_their_columns` · level: integration (API + throwaway PostgreSQL)

## 4. Interfaces and data

| Interface | Change | Contract |
|---|---|---|
| `/v1/*` (all resources) | unchanged | same routes and payloads; see README |

- **Data model / migration:** N/A — no schema change. Range rules are checked by the API on
  create and update; rows already stored are not rewritten.
- **Backward compatibility:** clients keep the same routes. A write that would store a range
  ending before it starts now gets `422 invalid_value` instead of `201/200`.

## 5. Non-functional requirements

| NFR | Target | How it is tested |
|---|---|---|
| Performance | N/A — no hot-path change beyond one comparison per declared range | — |
| Security / privacy | Same authorization, RLS and Sentry scrubbing as before | contract suite (`tests/test_contract.py`), `tests/test_sentry.py` |
| Reliability / observability | Reproducible image from `uv.lock`; failed inline publishes reach Sentry | image rehearsal before push; `test_inline_publish_failure_is_reported` |
| Accessibility / UX | N/A — API only | — |

## 6. Test plan (TDD)

- **Test levels:** integration tests against the FastAPI app with a throwaway local PostgreSQL
  (pgserver) and a fake platform; no hosted database or platform.
- **Test data:** generated in each test; no production data.
- **Coverage:** CI gate `coverage-threshold: "60"` (measured 62.43% on 2026-10-22, minus 2 points).
- **Not test-first (exceptions):** tests that pin behaviour the service already had
  (characterization tests, marked below) were written after the code by nature; tooling and
  config changes are covered by CI itself.

### Red / green log

| Scenario | Test | Red: commit / run + failure message | Green: commit / run | Refactor note |
|---|---|---|---|---|
| AC-01 | `tests/test_radar_validation.py::test_min_age_cannot_be_above_max_age` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-02 | `tests/test_radar_validation.py::test_moving_the_close_date_before_the_open_date_is_refused_on_update` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-03 | `tests/test_radar_validation.py::test_category_is_a_lowercase_slash_path` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-04 | `tests/test_radar_validation.py::test_one_status_per_profile_and_opportunity` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-05 | `tests/test_radar_validation.py::test_a_tracked_profile_or_opportunity_cannot_be_deleted` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-06 | `tests/test_radar_validation.py::test_new_opportunity_defaults` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-07 | `tests/test_radar_validation.py::test_opportunities_are_listed_by_slug` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-08 | `tests/test_rules.py::test_one_known_date_repeats_as_a_one_day_window_each_year` | characterization (behaviour already present; passed on first run) | CI run of the pushed tip | none |
| AC-09 | `tests/test_contract.py::test_numbers_fit_their_columns` | 5ac199b · `.venv/bin/pytest -q -k numbers_fit` · `psycopg.errors.NumericValueOutOfRange: integer out of range` | CI run of the pushed tip | none |

## 7. Risks and open questions

| # | Risk or question | Impact | Owner | Resolution / date |
|---|---|---|---|---|
| 1 | Stored rows written before a range rule existed may already be inverted | a patch touching one of those dates is refused until both are fixed | owner | patches that do not touch the range still work |

## 8. Change log

| Version | Date | Change | Scenarios affected | Approved by |
|---|---|---|---|---|
| 1.0 | 2026-10-22 | Implemented with the Wave 2 baseline | all | pending owner |

## Approval

| Gate | Role | Name / date | Decision | Evidence |
|---|---|---|---|---|
| Implemented (DoD) | Reviewer (checker) | Fresh Claude reviewer / 2026-10-22 | see Wave 2 report | CI run of the pushed tip |
| Implemented (DoD) | Approver | Owner | pending | Wave 2 report |
