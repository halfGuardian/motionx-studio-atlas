# v1.1 — One combined global research atlas

This is the preserved acquisition-stage report. The [current optimisation and launch-readiness report](optimisation.md), [licensing dashboard](licensing.html) and updated [validation](validation.json) describe the subsequent work on the same PR. Acquisition counts and evidence classes below are unchanged; the original 3.30 MB transport and 167/43/34 test counts are historical comparison points.

This draft release puts every acquired reference in the same public atlas: **41,735 records = 243 existing locations + 40,376 Overture place observations + 1,116 game-company references**. All classes are visible together by default. Search, filters, profiles, organisation navigation and CSV export use the combined catalogue. Company references have no invented city, physical branch or map point.

## Actual coverage

| Metric | Count |
| --- | ---: |
| Existing location IDs retained unchanged | 243 |
| New source observations | 40,376 |
| New company references | 1,116 |
| Combined searchable records | 41,735 |
| A: retained source-reviewed locations | 230 |
| B: source-listed location observations | 4,626 |
| C: unresolved research references, visible with warnings | 36,879 |
| Records with source coordinates | 40,619 |
| Source countries/territories represented | 178 |
| Retained operating organisations | 119 |
| Provisional/matched identities across new references | 41,234 |
| Existing source-confirmed capture locations retained | 22 |
| New confirmed facility/capture capability claims | 0 |
| Malformed Overture records rejected | 0 |
| Repeated exact Overture source IDs | 0 |
| Potential existing-location duplicate candidates | 117 |

These are **reference counts, not 41,735 verified unique production facilities**. Possible duplicates remain linked and unresolved; physical facilities are never merged merely because their owner or city matches. Provisional source identities are not a verified-company total. All 13 legacy unknown-evidence records remain accessible as C. No legacy evidence issue is claimed resolved by bulk acquisition.

## Sources and audit

- [Successful full acquisition, run 42287663742](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42287663742): the official Overture Places `2026-10-21.0` release was scanned across 16 objects, 88,418,121 places and 2,132 categories. The complete relevant slice contains 5,197 `animation_studio`, 18,621 `movie_television_studio` and 16,558 `video_film_production` records. Extraction took 3,329.658 seconds. No row quota or synthetic locations were used.
- [Successful cache/projection replay, run 42300014355](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42300014355): complete hash-checked snapshots, review outputs and licence copies are retained in the [committed archive](../runs/42300014355/manifest.json). Cache reuse does not advance observation dates. The earlier interrupted 34,000-record attempt and original run receipts remain in history/artifacts; only the complete slice supplies this catalogue.
- Overture provider licences: 39,669 observations under CDLA-Permissive-2.0 and 707 under Apache-2.0, with Foursquare NOTICE. AllThePlaces is supported but absent from this slice. Affected records retain original IDs/hashes while unresolved Overture-signals overlay payloads are withheld; no overlay licence is invented.
- All 1,116 [game-company references](../unified-input/source-receipt.json) are pinned to source commit `2ed3b6c1dbf38085ecc7053bb1ef00c27bb9183d`. The CSV last changed 14 September 2026; observation on 6 November is not corroboration of its business claims. There are 766 Studio, 235 Studio+Publisher and 115 Publisher references. Source statuses are 1,092 Active, four Acquired and 20 Closed, displayed as uncorroborated source assertions. No authored descriptions or social/contact profiles are republished. **The source has no explicit dataset redistribution licence**; factual references carry `UNSPECIFIED` terms and C labels.
- Wikidata and Overpass returned robots denials in [run 42282499526](../access-run-42282499526.json): zero records, sources disabled. No alternate host, user-agent, screenshot/OCR or hidden API was used. Existing restricted sources, including EA, remain disabled. Fifteen bulk sources are evaluated in the registry; evaluation is not permission to collect.

Dates above are actual UTC observation dates; 6 November UTC corresponds to 7 November in New Zealand. Source listings, provider scores and passing tests do not independently verify current operation or services.

## Evidence warnings and 20,000-facility gap

Among Overture observations, 35,750 still require research. Overlapping reasons include 32,164 scores below 0.9/unavailable, 3,722 unresolved status-overlay mappings, 2,078 source closure signals, 170 missing/conflicting municipalities, 117 possible existing-location matches and 14 missing/conflicting countries. These records remain visible as C rather than becoming verified facts. A failed fetch, missing listing or directory closure label never changes an existing studio's status.

The strict retained database has **0 errors / 265 warnings**. The inclusive research schema also has zero errors, with additional nonexclusive warning counts in [coverage.json](coverage.json): all 41,492 new references are unreviewed, all 40,376 new points lack verified facility precision, all 1,116 company references lack coordinates and explicit source redistribution terms. We do not suppress those conditions or add capture claims to meet a target.

The system has acquired tens of thousands of real source references, but **20,000 genuine, current, unique production-facility locations are not yet substantiated**. General POI taxonomy can include unsuitable businesses and duplicates. Game-company references do not identify physical branches. Specialist capture, facial/volumetric capture, retargeting and commercial availability need site-specific evidence. Additional agency/association exports require compatible terms and reliable location fields; broad publisher/broadcasting categories are not automatically eligible studio locations.

## Delivery, validation and performance

The public app loads a hash-bound compressed search index, then country-grouped evidence shards on demand: **238 shards, at most 500 records each**. Original coordinates are preserved; source-only companies get no marker. The coincident-coordinate chooser, viewport grouping, dark styling, responsive layouts, secure links, formula-safe CSV and OpenStreetMap attribution remain. `studios.json` is byte-identical to main (`ae9930e0ec522812c6bc189efc4b5beac48e781e6e60f8164172755e1259b4f4`).

The final local suites pass **167 Python tests, 43 JavaScript tests and 34 HTTP browser checks** (19 compatibility/baseline, six synthetic-sharded, nine actual combined-catalogue checks). Tests cover robots/network failure, immutable snapshots, corruption, repeat import, incomplete history, matching/conflicts, public-data projection, all-class retention, nullable company coordinates, gzip integrity, profiles/history, CSV licences, coincident selection and mobile navigation. `python tools/check_bulk_release.py` restores the committed archive, reclassifies the full source input and reproduces every public JSON file and gzip payload. See [validation.json](validation.json).

Measured local HTTP/headless Chromium results and conditions are in [performance.json](performance.json). The real 41,735-record index is about 3.30 MB gzip / 11.34 MB plain. Initial load was about 1.3 seconds locally and 45 seconds with 96,000 bytes/sec download, 150 ms latency, 4× CPU slowdown and a 390×844 viewport. A 50,000-location synthetic sharded fixture loaded in 1.35 seconds, compared with 11.80 seconds for the full-detail compatibility fixture; these are different delivery representations, not a controlled production speedup claim. Synthetic records exist only in temporary tests.

Operational limits: slow mobile startup remains substantial; a full export loads roughly 105 MB of detail JSON; no physical low-memory handset was tested. These are local HTTP proposal tests, **not a deployed Pages verification**. Full uncached upstream scans cost about 55 minutes; interrupted scans can require restarting, whereas completed snapshots are reusable. The inclusive builder requires a complete snapshot and deterministic rebuild; future releases must explicitly reconcile/preserve prior records absent from a new snapshot. Archives retain all current history, but third-party originals and Actions artifacts are not guaranteed permanent.

## Human review and publication

This release uses the **manually reviewed GitHub PR route**. No human approval is fabricated and no historical approval hash is reused. Discovery and acquisition workflows have read-only repository permissions and never directly publish. An attempted PR-executed archive job with contents-write permission was rejected by automatic approval review and removed; manual reviewable commits provide the archive instead.

The [read-only protection audit](../review-rules-run42287663788.json) returned no effective rules and unavailable classic protection. Required human-review enforcement remains **unconfirmed**; a draft PR or passing test does not enforce it. A maintainer must review the exact code/data/source terms and personally authorise merge. No merge, deployment or Pages-setting change was performed. Public GitHub/Pages access remains public regardless of whether the URL is promoted.
