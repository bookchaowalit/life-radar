# life-radar — Product brief

**Slug:** `bookchaowalit/life-radar`
**Written:** 2026-10-17
**Status:** v0.1 — cell scaffolded, tested locally; not provisioned, not deployed, no repository remote

## Problem

The opportunities that matter most in a life are easy to miss, and most of them are missed not
because you said no but because you never knew they existed, or found out after the door closed:

- **Age caps close doors for good.** A Thai citizen can get an Australian Work and Holiday visa only
  before turning 31; many government scholarships, young-professional programmes and youth exchanges
  stop at 25, 28, 32 or 35. Nothing tells you "this closes in 14 months".
- **Preparation takes longer than the window.** A scholarship that needs IELTS 6.5, two years of work
  experience and references has to be started a year or more before its deadline; a pilot cadet
  programme needs medical and English tests before the age cap.
- **Information is scattered** across embassies, ministries, universities and programme sites, in
  Thai and English, with no single place that knows your age and nationality.

## Users

1. The owner (a Thai solopreneur) — first and only user in v0.1.
2. Later: anyone (start with Thai citizens, then other nationalities) who wants a timeline of what
   their age, nationality and education still open up — the product could be public (web app,
   LINE bot, newsletter "what closes for you this year").

## What it does (v0.1)

- **Universal catalog** of every kind of life opportunity in one shape: eligibility (age range and how
  age is measured, nationality, gender, education, enrollment), window (rolling / annual / one-off /
  cohort, dates or typical months, quota, lifetime attempts), preparation (lead time, prerequisites),
  urgency tier (`time_critical`, `preparation_critical`, `evergreen`) and provenance (official source,
  last verified, verification status). Categories are an open path (`abroad/working-holiday`,
  `education/scholarship/postgraduate`, `license/accounting`...), so new kinds need no migration.
- **Profile radar**: given birthdate, nationality and education, every opportunity lands in one bucket —
  `prepare_now`, `closing_by_age`, `open_now`, `evergreen`, `watch`, `opens_later`, `missed`,
  `not_eligible` — with the date the age cap closes, the latest chance, how many windows remain and
  the date preparation must start.
- **Personal status** per opportunity (interested → preparing → applied → accepted / rejected / missed).
- **Seed catalog v1**: a first curated set of age-gated opportunities for Thai citizens, each citing an
  official source and verification status (`seeds/`).

## Non-goals (v0.1)

- No scraping or automatic updates of the catalog; curation is manual and source-cited.
- No notifications, UI or calendar export yet (see roadmap).
- Not legal, immigration or financial advice: the radar points at the official source, which wins.

## Design decisions

| Decision | Why |
|---|---|
| One `opportunity` shape for all categories, extras in `conditions` (JSON) | "every kind of opportunity" without a table per category; the radar rules only need the common fields |
| Hierarchical text `category` with a format check | extensible without migrations; prefix queries (`category=abroad`) |
| Age as `min_age`/`max_age` (inclusive) + `age_basis` | official rules are written "under 31", "not yet 31", "born on or after"; the basis keeps the date arithmetic honest and flags the cases it cannot decide |
| Buckets computed per profile at query time, not stored | the answer changes every day and with every profile; storing it would go stale |
| Every row cites `source_url` + `last_verified_at` + `verification_status`; the loader refuses rows without them | a radar that is wrong about a deadline is worse than none; unverified facts are visible as caveats |
| Cell kit pattern (own API, own Neon DB, platform for auth/audit), workspace-scoped rows | same operations model as the other life cells; multi-user later without a rewrite |

## Roadmap

1. **Approve and go live (owner):** create the GitHub repository, `radar-db provision` (Neon),
   first Railway deploy, register `radar` in the solo-empire registry, load the seed via the API.
2. **Catalog depth:** more categories (networking, health and sport, government rights by age),
   other nationalities, re-verification routine (rows older than 12 months get `verify_again`).
3. **Delivery:** weekly digest "what changed in your radar", calendar export of `start_prep_by` and
   `latest_chance`, MCP tools for the radar query.
4. **Public product:** a shared read-only catalog workspace, sign-up profiles, web UI / LINE bot,
   community submissions with source review.

## Limits

- Rule caveats are real: age measured "at programme start" or "in the calendar year", unknown windows
  and partial verification are flagged, not resolved.
- The seed set is a starting point, not complete coverage; programmes change every cycle.

## Runnable path

See `README.md` (`pytest`, `radar-local up`, `radar-seed db`).
