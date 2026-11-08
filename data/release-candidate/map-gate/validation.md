# Final map acceptance — checks and publication limits

This gate continues PR #19 from `29364389eb69f1da480a15b27b8c28f3bbba7923`. Source review dates are actual UTC dates (8 November 2026); the owner decision uses 9 November in Pacific/Auckland. No merge, deployment, Pages change or human approval is asserted.

## Geographic outcome and preservation

All **106 recorded city associations** among the 182 admitted companies received an individual evidence assessment: **102 separate approximate city/urban references**, **four city holds**, and **76 companies without a city**. All **80 unpinned companies** remain searchable in the same directory, with a map-to-directory control that preserves search, country and sector filters. The dashboard and CSV explain every outcome.

The four holds are DeltaRocket (Lyon versus Villeurbanne), Ex Nihilo (company city not corroborated), Ozone Story Tech (Corona/state and registry uncertainty), and MenzilMekan (event/weak indexed evidence does not establish its base). No capital, nearest-city or largest-city default fills these gaps. The 102 points use 69 distinct city/country references: 68 byte-verified projections from the hash-pinned GeoNames distribution and one directly reviewed Gwacheon entry. All carry CC BY 4.0 attribution; the packaging MIT notice is retained. Coordinates grant no rights to company-source content.

Every one of the **42,478 complete record hashes** remains unchanged, including all 182 admitted companies' null original coordinates and empty capability evidence. The root database, search index, detail shards, baseline/gzip transports and original source evidence are unchanged. The 348 protected parent history files and the additional frozen `2936438` review/visibility checkpoint are checked. Floating Rock's separate Wellington point, Frame Machine's original Santa Monica coordinates, and the seven prior city-reference proposals remain intact: **110 total display points across 109 company IDs**, including the previous eight points. The 17 original geographic decisions, including ten staged cases, are preserved.

Two points are explicitly metropolitan/urban references. Historical, indexed and registered-company evidence is distinguished from readable company assertions. TAICCA/Telefilm agency footers and adjacent-company addresses are not company-location evidence. The Ilya/Zero One entries retain their 2021/2022 source age. Interference Pattern's unexpected homepage redirect is disclosed without inferring closure. Class C, unknown current operation and UNSPECIFIED source-wide rights remain unchanged. Siung Film Productions and Ventura Interactive remain withheld. No new companies, verified facilities, foreign branches or confirmed capture capabilities are added by this gate.

## Executed checks

| Check | Result |
|---|---|
| Complete Python suite | 324 passed, 173.959 seconds |
| Complete JavaScript suite | 95 passed, 18.143 seconds |
| Existing HTTP browser suites | 96 checks across all 13 suites passed |
| New map acceptance suite, complete static package | Six checks passed (also passed against the checkout): **102 final HTTP checks across 14 suites** |
| Canonical database | Zero errors, 265 retained warnings |
| Complete source-to-public replay | Passed, including exact manifest/JSON/gzip reproduction |
| Canonical, historical/current licensing, maintenance, research and geography CLIs | All 14 checks passed; current map/release/readiness checks also rerun after serialization correction |
| Coordinate distribution verification | All 68 copied projections match the pinned wheel/data/source hashes; one direct GeoNames entry reviewed separately |

The Python regressions bind all 182 outcomes and all original records, reject agency-footers/future dates/fabricated approvals/private fields, verify municipality homonyms and historical Taiwan evidence, preserve old points, enforce repeat preparation as a no-op, and reproduce identical bytes despite reversed input/shard arrival order. JavaScript tests use the actual catalogue for the 102/80 partition, category/country/confirmed-only filters, original-null CSV fields, coincident clustering and invalid sidecar handling.

The six new HTTP checks exercise styled loading, animation/game/VFX/mocap company searches with country and category filters, confirmed-only exclusion of unsupported capabilities, keyboard marker-to-profile selection, all four geographic holds, the no-city directory path, London coincident selection, cluster membership, separate CSV coordinate attribution, Floating Rock/Frame Machine, 390px map/list navigation and all 182 dashboard decisions. Existing suites also cover deep links/history, source errors/recovery, blocked Leaflet, safe URLs/HTML/CSV, subsidiaries, mobile profiles, and 50,000-location fixtures. Live Leaflet/OSM requests are used; no substitute tile success is claimed.

## Initial failures and corrections

The initial new browser run timed out waiting for a chooser. A diagnostic rerun passed that stage; the exact initial cause was not conclusively isolated. The fixture now waits for the named debounced result rather than accepting a stale one-record count. Subsequent runs exposed two test-harness mistakes: a positional Playwright argument that must be keyword-only, then an attempt to click a directory control while the mobile map tab was active. Both were corrected; no product timeout was relaxed. The six-check rerun passed. Original logs remain in `qa/`.

The first complete replay found a genuine reproducibility defect: equivalent visibility dictionaries arrived in different object-key orders from loaded shards versus the source replay, producing different JSON/gzip hashes and manifest metadata. The projection now canonicalises object keys before serialization. A regression reverses both row and object arrival order and compares exact JSON/gzip bytes. The complete replay then passed; hash verification was not weakened.

Packaging inspection found the previous complete-static whitelist omitted `atlas.css`. The bundle now explicitly includes it, and the new browser suite asserts both HTTP 200 and the computed dark background before exercising mobile navigation. An initial Python invalid-escape warning in the HTML template was corrected with a raw string. These corrections change neither source records nor evidence claims.

## Performance conditions and observations

Single local HTTP runs in installed headless Chromium, desktop 1440px and mobile 390×844. The constrained run uses 96,000 bytes/second, 150 ms latency and 4× CPU emulation. These are neither deployed Pages measurements nor physical low-memory-device tests. Historical and final runs did not hold machine load constant; differences do not establish a controlled speedup/regression.

| Measurement | Reviewed `2936438` run | Final map-gate run |
|---|---:|---:|
| Real catalogue readiness | 1.647 s | 1.765 s |
| Throttled mobile readiness | 33.098 s | 33.923 s |
| Query all 42,478 stored records | 21 ms | 22.5 ms |
| Search compute | 14.5 ms | 16 ms |
| Uncached profile detail | 77.3 ms | 144.5 ms |
| Viewport update | 140 markers / 35.7 ms | 140 markers / 34.2 ms |

The unchanged compact index is 5,126,978 bytes / 2,224,418 gzip bytes; the compressed baseline is 358,282 bytes. The expanded display sidecar is 59,719 gzip bytes. The half-minute constrained first load remains a limitation; details stay lazy and explicitly fetched compression works without Pages compression negotiation.

The sharded **50,000 synthetic** fixture plus the 243 retained locations became ready in **1.150 s**, searched in **7.4 ms**, opened a profile in **40.9 ms**, and rendered a viewport in **8 ms**. The separate deliberately unsharded 50,000-row compatibility fixture became ready in **12.464 s** (14.202 s scenario), searched in 8.9 ms and combined filters in 8.6 ms. These fixtures are temporary and add no real companies, evidence or geographic coverage. All actual metrics and conditions remain in `qa/`.

## Warnings and owner decision

Warning categories overlap. The full replay retains 42,235 unreviewed references, 40,376 source-point precision warnings, 1,859 company references without **original** coordinates, 1,594 unspecified-term company references, 170 missing cities, 14 missing countries, 120 potential duplicates, and historical boutique/Annecy/NZ warnings (332/172/57). Three NZ foreign-name collisions, two staged NZ proposals, 27 historical NZ rights-scope cases, 182 minimal-factual/source-wide-rights warnings and two withheld-company warnings remain visible. The 13 legacy unknown-evidence root records and all 265 canonical warnings remain unresolved. A separate display reference does not resolve these warnings.

Totals remain 42,478 stored / 42,474 normal results, 1,859 company references, 179 country/territory associations, 243 retained locations / 119 reviewed organisations, and A230/B4,626/C37,622. These counts are not independently verified active-facility totals. The preserved ongoing workload includes 381 unresolved cases, 55 geography/facility keys, seven office cases, 238 city associations and partial/restricted sources; this gate does not conduct another discovery batch or declare worldwide completion.

Use the [single owner decision](../OWNER-APPROVAL.md) for the exact PR #15 → #18 → #19 scopes. All remain drafts. The recorded protection/ruleset requests returned `Forbidden`; required human-review enforcement and bypass rights remain unverified. Draft status and passing tests are not approval. Existing Pages settings may deploy an authorised main merge; the maintainer must choose the release window, review the exact heads, retarget/rebase as needed and rerun checks after changes. This gate changes no settings and grants no blanket rights to the 1,116-game-company cohort or any other source.

The replay commands are in [README](README.md). Logs include initial failures and final reruns; machine results are in [qa/summary.json](qa/summary.json). The unchanged earlier release report is archived under `inputs/pr19-2936438/`; the complete current company and geographic audit is linked from the release dashboard.
