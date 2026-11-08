# Company research and commercial scope continuation

Company/scope research reviewed **7–8 November 2026 UTC** (8 November in Auckland); the seven Ubisoft office/branch investigations were reviewed **8 November UTC**. Starting
checkpoint: `d5583994cda4dd3c99aa28508666057e5e0e96fa`. This continues draft
PR #18 on `codex/global-discovery-visibility`, stacked on unchanged draft PR #15.
Neither PR is merged or deployed by this work.

The [dashboard](reports/dashboard.html) contains the individual evidence,
country progress, source-policy limitations, identity holds and actual proposed
record payloads. It works in the downloaded Actions bundle over localhost HTTP.

## What is prepared, rather than published

- 70 individual company reviews across 35 recorded countries, including seven
  existing city-association reviews. These are not national censuses.
- 30 schema-valid Class C company-reference proposals. Each has a stable research
  identity, source evidence and date, null coordinates and no confirmed facility
  capabilities or ownership. Company self-report and historical directory/event
  corroboration do not independently establish present operation.
- Ten existing-identity matches; these are source/software matches, not ten new
  verified businesses. Two identity holds include Digitoonz's foreign source
  observation and the composite Makia Creative / Mamoncillo exhibitor identity.
- Two out-of-scope leads: FSTVS is a jobs/community service, not its
  employers' production facilities; Inside Track reconciles to the retained
  audio-only record. 26 investigated company cases remain unresolved.
- Five geographic review proposals for existing IDs: four separate approximate
  city-reference payloads (Bad Clay, Scrawl Animation, Robot Playground Media,
  ModelFarm), plus a Tumblehead Copenhagen/Viborg correction question. Points
  cite existing licensed GeoNames city references, including the Singapore
  gazetteer citation already in the baseline; no other studio's facility point
  or parent geography is inherited. None is applied to the map by this release.
- Every starting pending observation is retained: 753 observations / 725 queue
  keys. Sixty-nine keys have individual company/branch continuation reviews; 656 are explicitly
  **not yet individually investigated**. Additional reviews are separately
  identified. Queue keys are not proven distinct companies.

Useful identity findings include Studio Bolland / Studio Bo, Malaysian versus
French Spacesheep, historical Woodblock Hamburg versus current company-listed
Berlin/Ludwigsburg/Los Angeles, and Digitoonz's marketed Los Angeles versus
Glendale address. Office lists, productions and remote teams are not automatic
physical-facility proposals. Eallin's Stockholm is explicitly in development.

Seven Ubisoft office/department leads now have separate structured reviews and matching evidence. Los Angeles identifies the already-listed Film & Television operation. Generic regional-office pages do not establish game-development facilities. Three dated change alerts distinguish the 2024 San Francisco production closure announcement, the Sydney production ramp-down announcement and corroborated March 2026 Red Storm development-to-support reports. They do not close global organisations or change canonical records. [Read the branch/change audit](reports/branch-reviews.json). Company and branch reviews cover 36 countries in total; this is not complete geographic enumeration.

## Public-directory scope change

The canonical storage baseline remains **42,296 references**. All source
records, evidence and IDs remain unchanged, including the 243 root locations.
The root database SHA remains
`ae9930e0ec522812c6bc189efc4b5beac48e781e6e60f8164172755e1259b4f4`.

Only the reversible display policy changes. The Inside Track, Native Audio,
Evoke Audio and The Sound Room demonstrate audio-only services and are excluded
from normal directory results. Their direct profiles, evidence and full CSV
exports remain available in explicit audit mode. Envy remains because visual
post-production is documented. Audio contributions to films, games or animation
do not establish visual-production or game-development services.

| Result set | Before | Normal view after | Audit view |
|---|---:|---:|---:|
| All references | 42,296 | 42,292 | 42,296 |
| Company-only references | 1,677 | 1,673 | 1,677 |
| Game Development sector | 1,141 | 1,141 | 1,141 |
| Audio Post-production sector | 5 | 1 | 5 |
| New Zealand country filter | 149 | 145 | 149 |
| Records with original coordinates | 40,619 | 40,619 | 40,619 |

Search, audience/country/sector filters, organisation results, map markers and
CSV export use the same selected scope. No map coordinate is changed or removed.
Floating Rock's separate Wellington reference and Frame Machine's original
Santa Monica source observation retain their regression checks. The 603 broad
audio/sound/name signals are only a further research queue, **not exclusions**;
names alone cannot establish an audio-only service offering.

Audience rules distinguish potential clients, providers, both, adjacent/uncertain
and out-of-scope records. Most derive from existing sector assertions and are
labeled accordingly. A game developer qualifies as a potential client without
capture services. Only existing site-specific evidence can satisfy confirmed
capability filters. No classification establishes purchasing intent, budget,
outsourcing need or technical problems. Numerical service-alignment scores are
removed from public controls, ranking, badges and exports; historical research
files and scoring tests remain intact.

## Rights and review boundaries

This is bounded individual company research using public official pages,
government/industry evidence and already preserved research history. Some web
tool responses are indexed/cached. A review date records when the evidence was
examined, not the date of a fresh independent operational inspection. Failed,
image-only, ambiguous and inaccessible pages stay documented. No screenshots,
OCR, hidden APIs, alternate hosts or recursive crawling are used as workarounds.
No previously restricted source is enabled. EA remains disabled.

Minimal factual references and evidence links are retained; no source-wide
commercial dataset permission is inferred. No authored descriptions, media or
personal contacts are reproduced. Directory enumeration and new bulk collection
still require their own reviewed access/reuse decision. Historical source rights
and every old research artifact remain in place.

The prepared records are in `reports/proposed-companies.json`, **outside the
canonical public shards**. Human review must resolve identity/city questions,
rights and publication scope before a separate authorised canonical change.
There is no apply command, approval file, fabricated reviewer or automatic merge.
The original 14-candidate worksheet still lacks independent human labels;
precision and recall remain null. Draft status and successful tests do not enforce
human review by themselves; repository protection remains unconfirmed.

## Reproduce and continue

```sh
python tools/global_continuation.py prepare
python tools/global_continuation.py check
python tools/global_visibility.py check
python tools/global_programme.py check
python tools/global_programme.py maintenance-check
python tools/check_bulk_release.py
python tools/validate.py studios.json
python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.js
python tests/commercial_browser.py
```

The continuation validator binds the frozen full-record hashes, root database,
starting compressed report and every pending observation/hint. All generated
continuation artifacts and the public scope sidecar reproduce offline. The
existing workflow also runs the complete HTTP suites, slow-mobile real-data
scenario, synthetic 50,000-location checks and standalone artifact packaging.

Resume from `reports/backlog.csv` / `report.json`, selecting the explicitly
uninvestigated keys rather than repeating worldwide URL searches. Append factual
individual reviews to `inputs/company-reviews.json`, retaining original queue
keys, dates, rights and evidence; run `prepare` and `check` before committing.
Review `reports/audio-scope-research-queue.json` individually; do not exclude by
name. The remaining geographic associations are in the unchanged parent
`../reports/unpinned-companies.json`. Continue independent branches and distinct
physical facilities separately from company proposals. Preserve all source
policy states and frozen history. Save subsequent milestones on this branch;
leave PR #15, its branch, production and Pages settings unchanged.
