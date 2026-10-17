# life-radar

**Personal Opportunity Radar.** A catalog of every kind of life opportunity — scholarships,
working holidays, career programmes, professional licences, research fellowships, competitions,
business funding, government rights by age, volunteering, networking, health and sport — in one
universal shape, matched against a profile so you see what closes for good, what you must start
preparing now, what is open today and what will always be there.

The Life Radar cell has its own API and its own database, described by `cell.yaml` and served by
the cell kit in `src/cellkit/` (this repository's own copy, taken from `life-opportunities-api`).
It reuses empire-platform for identity, authorization, executions and audit over HTTP with the
caller's token. Cell-specific code is in `src/life_radar/`.

| | |
|---|---|
| API | Railway project `life-radar`, service `radar-api` (Serverless, Singapore): https://radar-api-production-7fe7.up.railway.app |
| Data | Neon project `life-radar` (aws-ap-southeast-1), database `radar` |
| Registry | solo-empire `repository-catalog/registries/online-systems.yaml` (`radar`) |

## Model

One shape for every category (`cell.yaml`, resource `opportunity`):

| Group | Fields |
|---|---|
| What | `slug`, `name`, `name_th`, `description`, `category` (path, e.g. `abroad/working-holiday`), `country`, `region`, `issuer`, `official_url`, `value_benefit`, `cost`, `tags` |
| Who | `nationalities` (ISO codes or `["*"]`), `thai_eligible`, `min_age`, `max_age`, `age_basis` (`at_application`, `at_start`, `at_deadline`, `calendar_year`), `gender`, `min_education`, `enrollment_required`, `education_text`, `profession`, `conditions_text`, `conditions` |
| When | `recurrence` (`rolling`, `annual`, `one_off`, `cohort`), `open_date`, `close_date`, `window_months`, `quota`, `attempts_limit` |
| Preparation | `prep_lead_time_months`, `prerequisites`, `urgency` (`time_critical`, `preparation_critical`, `evergreen`) |
| Provenance | `source_url`, `last_verified_at`, `verification_status` (`verified`, `partially_verified`, `unverified`, `stale`), `verification_notes`, `status` |

`profile` holds a person (birthdate, nationality, education, enrollment); `opportunity-status`
holds that person's status per opportunity (`interested`, `preparing`, `applied`, `accepted`,
`rejected`, `missed`, `not_eligible`, `dismissed`). Every row belongs to a workspace (row-level
security), so the same cell can later serve many users.

## API

Every resource has list, stats, get, get-by-legacy-id, create, patch and delete (see
`cellkit/app.py`). Permissions are `radar.<resource>:read|write|delete`.

| Path | Resource | Filters |
|---|---|---|
| `/v1/opportunities` | opportunity | `category`, `country`, `urgency`, `recurrence`, `thai_eligible`, `verification_status`, `status` |
| `/v1/profiles` | profile | — |
| `/v1/opportunity-statuses` | opportunity-status | `profile_id`, `opportunity_id`, `status` |
| `GET /v1/profiles/{id}/radar` | the radar for a stored profile, with its statuses | `as_of`, `horizon_years` (1-10, default 3), `category` (path prefix) |
| `POST /v1/radar` | the radar for a profile in the body; nothing stored | same |

The radar puts every active opportunity in exactly one bucket, the first that applies
(`src/life_radar/rules.py`):

| Bucket | Meaning |
|---|---|
| `prepare_now` | the last chance (age cap or deadline) minus the preparation time falls within 90 days |
| `closing_by_age` | the age cap closes it for good within the horizon |
| `open_now` | a window is open today |
| `evergreen` | no age cap and it recurs: it will still be there |
| `watch` | eligible, nothing urgent yet |
| `opens_later` | too young, or student-only for a level not reached yet |
| `missed` | aged out, no window left before the cap, or a closed one-off |
| `not_eligible` | nationality, gender or enrollment rules exclude this profile |

Each item carries `flags` (every condition that holds), `caveats` (what the rules could not decide:
`window_unknown`, `age_basis_at_start`, `source_partially_verified`, `verify_again`...), `age_closes_on`,
`years_left`, `next_window`, `windows_left`, `latest_chance` and `start_prep_by`.

```bash
curl -s -X POST "$API/v1/radar?horizon_years=3" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"birthdate": "1997-03-01", "nationality": "TH", "education_level": "bachelor"}'
```

## Seed catalog

`seeds/opportunities.v1.yaml` is the first curated set: age-gated opportunities relevant to Thai
citizens, every row with an official `source_url`, `last_verified_at` and `verification_status`
(see [`seeds/README.md`](seeds/README.md)). Load it with `radar-seed`, which upserts by `slug`
(a rerun changes nothing):

```bash
.venv/bin/radar-seed check                                   # validate only
.venv/bin/radar-seed db --workspace <uuid>                   # local database
.venv/bin/radar-seed api --api "$API" --token-file <path>    # hosted, through the API
```

## Develop and operate

```bash
uv venv .venv && uv pip install --python .venv/bin/python -e ".[dev]"
.venv/bin/pytest -q
.venv/bin/radar-local up                       # local PostgreSQL in .runtime/pgdata (socket in $XDG_RUNTIME_DIR, path < 100 chars)
.venv/bin/radar-seed db --workspace "$(python3 -c 'import uuid; print(uuid.uuid4())')"
.venv/bin/radar-local down
```

Hosted (done 2026-10-17; rerun only to change it):

```bash
NEON_API_KEY=... .venv/bin/radar-db provision
npm install && railway config apply && railway up --ci --service radar-api
railway scale --service radar-api asia-southeast1-eqsg3a=1 us-east4-eqdc4a=0   # next to Neon and the platform
```

Before the hosted API answers anything but `/health`, the owner's workspace needs the radar
permissions and a token with `radar-api` in its audience. Both come from the empire-platform
checkout, on the machine that holds its hosted database URLs and signing key:

```bash
EMPIRE_DB_MODE=hosted .venv/bin/empire-cells grant --workspace owner --cell radar
EMPIRE_DB_MODE=hosted .venv/bin/empire-automations provision --workspace owner \
    --tokens ~/.config/empire-platform/tokens --key-dir ~/.config/empire-platform/signing \
    --issuer empire-platform --ttl-days 30      # owner-mcp now carries radar read/write
.venv/bin/radar-seed api --api https://radar-api-production-7fe7.up.railway.app \
    --token-file ~/.config/empire-platform/tokens/owner-mcp.jwt
```

Railway variables: `RADAR_DB_MODE=hosted`, `RADAR_DB_URL_API`, `RADAR_JWT_PUBLIC_KEY_PEM` (or
`RADAR_JWT_JWKS_URL`), `RADAR_JWT_ISSUER`, `EMPIRE_PLATFORM_URL`.

Docs: [`PRODUCT.md`](PRODUCT.md) (product brief, roadmap) and [`DOCPACK/`](DOCPACK/) (product card).
