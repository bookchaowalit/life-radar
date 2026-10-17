# Seed catalog

`opportunities.v1.yaml` — curated 2026-10-17: the first set of **age-gated (or deadline-gated) opportunities
relevant to Thai citizens**, 57 rows across 12 top-level categories.

## How it was made

- Every row was researched on the web (search + fetch of the official page) on 2026-10-17, not from memory.
- `source_url` is the page that confirms the eligibility facts; `official_url` is the programme home page.
- `verification_status`:
  - `verified`: the age/eligibility facts were read on the official page that day;
  - `partially_verified`: some facts come from a secondary source (news, university notice, another embassy's copy
    of the same call) because the official page blocked access or did not state them — the reason is in `verification_notes`;
  - `unverified`: no official confirmation found; kept because it is worth knowing, shown with a caveat by the radar.
- `last_verified_at` is the day the row was checked; on partly verified rows it is the check date, not a confirmation date.
- The radar shows every non-`verified` row with a `source_*` caveat, and every row older than 12 months with `verify_again`.
- Append-only by version: the next curation round is `opportunities.v2.yaml`; the loader picks the highest version.

## Counts

| verification_status | rows |
|---|---|
| `partially_verified` | 30 |
| `verified` | 24 |
| `unverified` | 3 |

## Rows

| slug | category | age | thai_eligible | status |
|---|---|---|---|---|
| `au-work-and-holiday-462-th` | abroad/working-holiday | 18–30 | yes | verified |
| `nz-thailand-working-holiday-th` | abroad/working-holiday | 18–30 | yes | verified |
| `young-smart-farmer-th` | business/agriculture | 17–45 | yes | unverified |
| `thai-airways-student-pilot` | career/aviation | 18–32 | yes | verified |
| `th-assistant-judge-exam` | career/government | 25– | yes | partially_verified |
| `google-summer-of-code` | career/open-source | 18– | yes | verified |
| `adb-young-professionals-program` | career/young-professional | –32 | yes | verified |
| `imf-economist-program` | career/young-professional | –33 | yes | verified |
| `un-young-professionals-programme` | career/young-professional | –32 | no | partially_verified |
| `world-bank-young-professionals-program` | career/young-professional | — | yes | verified |
| `yseali-professional-fellows-program-th` | career/young-professional | 25–35 | yes | verified |
| `james-dyson-award-th` | competition/design-engineering | — | yes | partially_verified |
| `icpc-regional-contest` | competition/programming | — | yes | partially_verified |
| `hult-prize` | competition/startup | 18– | yes | partially_verified |
| `microsoft-imagine-cup-2027` | competition/startup | 18– | yes | partially_verified |
| `worldskills-competition-th` | competition/vocational-skills | –22 | yes | partially_verified |
| `afs-thailand-year-program` | education/exchange/secondary | 14–18 | yes | verified |
| `flex-global-usa-high-school-exchange-th` | education/exchange/secondary | 14–16 | yes | verified |
| `rotary-youth-exchange-th` | education/exchange/secondary | 15–18 | yes | partially_verified |
| `th-armed-forces-academies-prep-school` | education/military-academy | 16–18 | yes | partially_verified |
| `cn-csc-chinese-government-scholarship-masters` | education/scholarship/postgraduate | –34 | yes | partially_verified |
| `cn-schwarzman-scholars` | education/scholarship/postgraduate | 18–28 | yes | verified |
| `cn-yenching-academy-pku` | education/scholarship/postgraduate | — | yes | verified |
| `int-adb-japan-scholarship-program` | education/scholarship/postgraduate | –35 | partial | partially_verified |
| `jp-mext-research-student-embassy-th` | education/scholarship/postgraduate | –34 | yes | partially_verified |
| `kr-gks-graduate-th` | education/scholarship/postgraduate | –39 | yes | verified |
| `th-ocsc-government-scholarship-general-degree` | education/scholarship/postgraduate | –35 | yes | partially_verified |
| `uk-chevening-th` | education/scholarship/postgraduate | — | yes | verified |
| `us-fulbright-thai-graduate-scholarship-tgs` | education/scholarship/postgraduate | — | yes | partially_verified |
| `jp-mext-undergraduate-embassy-th` | education/scholarship/undergraduate | –24 | yes | partially_verified |
| `kr-gks-undergraduate-th` | education/scholarship/undergraduate | –24 | yes | partially_verified |
| `th-ocsc-kings-scholarship` | education/scholarship/undergraduate | –20 | yes | partially_verified |
| `jp-mext-kosen-embassy-th` | education/scholarship/vocational | –24 | yes | verified |
| `jp-mext-specialized-training-embassy-th` | education/scholarship/vocational | –24 | yes | verified |
| `th-national-savings-fund-nsf` | finance/savings | 15–60 | yes | partially_verified |
| `th-military-registration-sd9` | government/military | 17–17 | yes | partially_verified |
| `th-rotc-nor-sor-tor` | government/military | 15–22 | yes | partially_verified |
| `th-social-security-section-39` | government/social-security | — | yes | verified |
| `th-social-security-section-40` | government/social-security | 15–65 | yes | verified |
| `th-elderly-living-allowance` | government/welfare | 59– | yes | partially_verified |
| `th-red-cross-blood-donation` | health/blood-donation | 17–70 | yes | verified |
| `th-cpa-licence-tfac` | license/accounting | — | yes | partially_verified |
| `caat-commercial-pilot-licence` | license/aviation | 18– | yes | partially_verified |
| `th-coe-associate-engineer-licence` | license/engineering | 18– | yes | unverified |
| `th-thai-barrister-netibandit` | license/law | — | yes | unverified |
| `one-young-world-leading-scholarship` | networking/fellowship | 18–35 | yes | verified |
| `yseali-academic-fellows-program-th` | networking/fellowship | 18–25 | yes | verified |
| `forbes-30-under-30-asia` | networking/recognition | –29 | yes | partially_verified |
| `humboldt-research-fellowship` | research/fellowship | — | yes | verified |
| `jsps-postdoctoral-fellowship-standard` | research/fellowship | — | yes | verified |
| `lindau-nobel-laureate-meeting` | research/fellowship | –35 | yes | partially_verified |
| `msca-postdoctoral-fellowships` | research/fellowship | — | yes | verified |
| `aiesec-global-volunteer` | volunteering/youth | 18–30 | yes | partially_verified |
| `asean-youth-volunteer-programme-ayvp` | volunteering/youth | 18–30 | yes | partially_verified |
| `sseayp-ship-for-southeast-asian-japanese-youth-th` | volunteering/youth | 18–30 | yes | partially_verified |
| `un-university-volunteers-th` | volunteering/youth | 18–29 | partial | partially_verified |
| `un-youth-volunteers-th` | volunteering/youth | 18–26 | yes | partially_verified |

## Not fully verified (re-check first)

- `young-smart-farmer-th` (unverified): Age range 17-45 comes only from a Matichon news report quoting a government spokesperson (around 2018) and a 2024 BAAC loan scheme ('not over 45'). No current DOAE criteria page was found or fetched; application timing is via provincial agriculture offices and was not confirmed.
- `th-assistant-judge-exam` (partially_verified): Minimum age 25, nationality by birth, Bar requirement and track rules are taken from iLaw's article on the Judicial Service Act. The official COJ home page has no 2026/2027 exam notice; dates vary by year (e.g. a 2024 announcement dated 11 Jun 2024). The act's text was not read directly.
- `un-young-professionals-programme` (partially_verified): Age (32 or younger in exam year), degree and language rules confirmed on un.org Academic Impact page. careers.un.org is JavaScript-only, so the official country list could not be read. Thailand is NOT on the 2025-26 participating list (seen on OpenIGO, which says it is not affiliated with the UN). Partial 2026 lists on Global South Opportunities and Opportunity Desk also omit Thailand. thai_eligib…
- `james-dyson-award-th` (partially_verified): Official jamesdysonaward.org returned HTTP 403 to our fetcher. Eligibility (students or graduates within 4 years, Thailand eligible since 2022) and prize amounts come from search results of Chulalongkorn/KMUTNB announcements and Bangkok Post. 2026 deadline reported as 15 July 2026 (passed); 2027 dates not published.
- `icpc-regional-contest` (partially_verified): Fetched the official ICPC regional rules page (nc.na.icpc.global/rules, labelled 2026-2027 season but text is Regionals 2025/26): born 2005+ or began post-secondary 2021+, 2 World Finals and 5 regional-year limits, half-time enrolment. The 2026/27 cutoffs (likely 2006/2022 by the yearly pattern) are not confirmed. Asia regional dates for Thailand teams vary by host; window_months is an estimate.
- `hult-prize` (partially_verified): Fetched hultprize.org home (confirms student startup competition, USD 1M prize). Age-18-by-2027-02-28, 2-4 member and degree-seeking enrolment rules come from the official register page as shown in search results (not fetched directly). Cycle registration reported to start in September; exact 2026-27 dates not confirmed.
- `microsoft-imagine-cup-2027` (partially_verified): Rules read from Microsoft's Imagine Cup FAQ on the staging host (imaginecup-stg.microsoft.com); the production site only says 'Imagine Cup 2027 - Coming Soon'. Close date 2027-02-28 and the new startup-entity rule should be re-checked on the production Official Rules once published. Open date not confirmed. Thailand is not on the excluded list.
- `worldskills-competition-th` (partially_verified): Age rule and exception list quoted from worldskills.org how-compete page; Thailand listed as a member on worldskills.org/members; next competition Aichi 2028 (15-20 Nov 2028) from worldskills.org/what/competitions. Thai national selection procedure and dates (DSD) not confirmed from an official DSD page. WorldSkills rules generally allow competing only once at a WorldSkills Competition; attempts_l…
- `rotary-youth-exchange-th` (partially_verified): Age 15-18, one-year format and costs from a Rotary club (Chiang Mai International Rotary Club) post; 2026-27 applications were due mid-October 2025. rotary.org could not be fetched (security checkpoint/429). Other Thai districts (3330, 3340, 3350) may have different ages and dates; 2027-28 deadline not confirmed.
- `th-armed-forces-academies-prep-school` (partially_verified): Age 16-18 in the year of entry and the M.4 requirement come from news reports quoting the 2024/2026 recruitment announcements (Thansettakij, PPTV); afaps.ac.th was not fetched, so the official_url is not checked. The 2027 announcement and application dates are not confirmed. attempts_limit=3 is derived from the 3-year age window, not an official rule.
- `cn-csc-chinese-government-scholarship-masters` (partially_verified): Age caps confirmed on an official Shanghai Municipal Government page (2026) and consistent with 2026 university notices. campuschina.org could not be reached (DNS failure). Thai-specific dispatching authority, quota and dates not confirmed; the typical January-April window comes from university notices. The word 'generally' means caps are guidelines that universities enforce.
- `int-adb-japan-scholarship-program` (partially_verified): Age (<=35 at application), work experience and benefits confirmed on official ADB FAQ. Thailand's presence on the eligible-country list is supported by a University of Tokyo application guide and AIT listings but the ADB country list itself was not fetched; institution deadlines vary (no single window).
- `jp-mext-research-student-embassy-th` (partially_verified): Age cap 'under 35' confirmed on JASSO Study in Japan official page (EN and TH). The 1992-04-02 birth-date cutoff for 2027 comes from MEXT 2027 guidance as reproduced by other Embassies of Japan (India, Philippines); the Embassy of Japan in Thailand site (th.emb-japan.go.jp) returned HTTP 403 so the Thailand research-student annex, dates and quota were not seen. Window months are inferred from the …
- `th-ocsc-government-scholarship-general-degree` (partially_verified): Age wording (35 master's / 40 PhD at closing date) appears in an OCSC announcement hosted on the NSTDA scholar site (search snippet), and in an OCSC 2566 summary (Bangkok Biz News: 137 places, 10 Nov-28 Dec 2022). The PDF's Thai text could not be extracted (custom font encoding) and ocsc.go.th returns 403, so the 2570 cycle dates, quota and per-unit GPA were not confirmed. Window months inferred f…
- `us-fulbright-thai-graduate-scholarship-tgs` (partially_verified): 2027 call (deadline 30 April 2026, up to 4 grants, no medicine/nursing) and January-April window seen in fulbrightthai.org search results; direct WebFetch of fulbrightthai.org pages returned 404 (JS-rendered site). GPA/English thresholds from TUSEF Nov-2025 brochure as summarised in search results. No age cap confirmed either way. 2028 call not yet published.
- `jp-mext-undergraduate-embassy-th` (partially_verified): Under-25 cap confirmed on JASSO official page. Thai-specific 2027 undergraduate annex not retrieved (Embassy site 403); birth-date cutoff taken from MEXT 2027 guidance on other embassy/government pages. Stipend mapping in JASSO table was ambiguous. Next (2028) cycle dates not yet published; months inferred from 2027 cycle.
- `kr-gks-undergraduate-th` (partially_verified): Embassy-track dates 15-30 Sep 2026 confirmed on official Korean Embassy (Kenya) notice at mofa.go.kr. Age (born after 2002-03-01), university-track-through-November and quotas taken from Korea JoongAng Daily, as the 2027 GKS-U guideline PDF on studyinkorea.go.kr was not retrieved. Thailand's inclusion in the 2027 embassy-track country list was not confirmed (Thailand was eligible for GKS-G 2026).
- `th-ocsc-kings-scholarship` (partially_verified): Details (age <=20 at 30 Oct 2026, final-year secondary, GPAX 3.50, 9 places, 5-30 Oct 2026 application, fees, timeline) from Eduzones article dated 7 Oct 2026 summarising the OCSC announcement of 2 Oct 2026; the OCSC page linked from that article (used as source_url) returned HTTP 403 to automated fetch so it was not read directly. attempts_limit=1 because only students in their final secondary ye…
- `th-national-savings-fund-nsf` (partially_verified): Fetched nsf.or.th FAQ: confirms exclusions (GPF, SS 33/39/40 options 2-3, provident fund; SS40 option 1 allowed), 50-30,000 baht limits, pension at 60. The 15-60 joining age and the age-banded match rates come from news and gov't summaries in search results, not a fetched NSF page. NSF homepage stats show members in the 15-30 band, which fits a 15 minimum.
- `th-military-registration-sd9` (partially_verified): Rule wording comes from the official Territorial Defence Command PDF (tdc.mi.th) as shown in search results; the PDF itself was not fetched. Men born B.E. 2552 register during B.E. 2569 (2026). This is an obligation, listed so users don't miss the year.
- `th-rotc-nor-sor-tor` (partially_verified): Age 15-22, education and nationality rules from a Srinakharinwirot University 2026 ROTC recruitment announcement (an institutional copy of TDC rules) and Mahidol documents, seen in search results, not fetched. Application windows vary by institution (SWU: July-August). The conscription-exemption benefit is general knowledge, not confirmed on a fetched page.
- `th-elderly-living-allowance` (partially_verified): dop.go.th Q&A (dated 2021) confirms Thai nationality, pension exclusion, amounts by age band and that you must be 59 to register. It names a 1-30 Nov window, which is older. The current Oct-Nov + Jan-Sep windows (FY2570: Oct-Nov 2025 and Jan-Sep 2026) come from bantaksin.dop.go.th and news. The FY2571 birth range (2 Sep 2510 - 1 Sep 2511) is from news reports, not confirmed on an official page.
- `th-cpa-licence-tfac` (partially_verified): The TFAC home page confirms that the CPA exam is run in rounds (a notice dated 9 Oct 2026 covers round 64, 3/2569) and has links to the training and exam systems. The training length, hours and number of subjects come from secondary sources (Jobsdb, Trueplookpanya); TFAC's own rule pages were not reached.
- `caat-commercial-pilot-licence` (partially_verified): Class 1 medical for CPL confirmed in CAAT eAIP GEN 1.7, which lists no Annex 1 difference on CPL age. The minimum age of 18 therefore rests on the ICAO standard, not on Thai text. The CAAT form and Regulation No. 24 PDFs could not be text-extracted. CATC (catc.or.th) lists CPL/IR integrated courses but shows no age or entry criteria. Flight-hour minimums are not recorded here.
- `th-coe-associate-engineer-licence` (unverified): The official coe.or.th home page returned no readable content. The membership age of 18, nationality and test structure come from Trueplookpanya and a Naresuan University handbook (eng.nu.ac.th); the Engineer Act text was not confirmed.
- `th-thai-barrister-netibandit` (unverified): The official site thethaibar.or.th refused the connection (ECONNREFUSED), so no official page was read. That Netibandit is required for the judge exams is confirmed via iLaw's summary of the Judicial Service Act. The course structure and eligibility come from secondary sources only.
- `forbes-30-under-30-asia` (partially_verified): Rules for the Class of 2026 were confirmed from Forbes' own announcement (4 Nov 2025): nominations close 31 Dec 2025, under 30 by that date, prior listees excluded. The 2027 Asia call is not yet announced. Assuming the same pattern, it would open about Nov 2026 with a 31 Dec 2026 cut-off (born on or after 1 Jan 1997). This is an inference.
- `lindau-nobel-laureate-meeting` (partially_verified): NSTDA (Thailand) is confirmed as nominating institution for the 76th meeting (Physiology/Medicine, 27 Jun-2 Jul 2027); the application process has run since Sep 2026. The 35 cap comes from Lindau's Young Economists page and partner calls, not the 2027 criteria. NSTDA's 2027 Thai call and its age rule were not found. attempts_limit 1 assumes the usual no-repeat rule.
- `aiesec-global-volunteer` (partially_verified): 18-30 age range confirmed on AIESEC UK's official Global Volunteer page via search result; the global aiesec.org page fetched today does not state age or fees. AIESEC in Thailand's fee and process not confirmed.
- `asean-youth-volunteer-programme-ayvp` (partially_verified): Eligibility (ASEAN nationals incl. Thailand, 18-30, self-funded travel) read on the UKM-hosted AYVP page today, but the page is headed 'Get ready for AYVP 2025' with no dates; whether a 2026/2027 edition is running and its application window are not confirmed.
- `sseayp-ship-for-southeast-asian-japanese-youth-th` (partially_verified): Programme, Thailand participation and 18-30 age range confirmed via Cabinet Office SSEAYP pages/reports and the Singapore NYC 50th SSEAYP factsheet (3 Jan-5 Feb 2027 voyage). Thai call: DCY announcement for the 49th (2026) programme exists (dcy.go.th, could not be rendered); the Thai age wording/basis and the Thai 50th-programme (2027) call dates are not confirmed. Window [3,4] inferred from past …
- `un-university-volunteers-th` (partially_verified): 18-29 seen in an official UNV brochure (undated, ~2017 data) and live vacancies via search results; the UNV requirements page states 18-26. Most assignments run through partner universities/donor funding; no Thai partner-university scheme was confirmed, hence thai_eligible 'partial'.
- `un-youth-volunteers-th` (partially_verified): 18-26 age range seen on the official unv.org requirements page via search result (direct fetch blocked by Incapsula/403). Thai eligibility for individual assignments depends on the sponsor (many youth posts are donor-country-restricted); not confirmed which assignments are open to Thais.

## Researched and left out

- Working holiday schemes other than Australia (462) and New Zealand: Japan, Korea, Taiwan, Poland, Hungary, Czechia,
  Portugal and Ireland have no scheme with Thailand.
- JENESYS (nomination per programme, no common call or age rule); Ship for World Youth (Thailand not a participant).
- Bangkok Airways / Thai AirAsia cadet programmes (no current official programme found); NIA Startup Thailand League
  (no official eligibility rules found); Swedish Institute, Taiwan Scholarship, Erasmus Mundus, DAAD (no age cap; next round).
- `un-young-professionals-programme` is kept with `thai_eligible: no`: Thailand is not on the latest participating list
  (re-check every year).
