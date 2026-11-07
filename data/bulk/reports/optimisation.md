# Unified atlas optimisation & launch readiness — continuation of PR #10

The complete **41,735-record** catalogue is retained in one searchable atlas: **243 established locations + 40,376 Overture observations + all 1,116 game-company references**, across **178 source countries/territories**. No source record, identity, coordinate, website, evidence URL or recorded capability is removed or upgraded by this work.

| Class | Records | Meaning / visual identity |
| --- | ---: | --- |
| A | 230 | Source-reviewed locations; green **#238B67 square / A** |
| B | 4,626 | Directory-listed observations requiring corroboration; blue **#347FBA circle / B** |
| C | 36,879 | Unresolved research references; amber **#B58A2A triangle / C** |

All **13 legacy unknown-evidence locations remain C**. Record totals are not verified unique facility totals. There are **40,619 geolocated records**, **119 retained operating identities**, **41,197 provisional source identities** and **22 locations with source-confirmed Motion/Body/Performance Capture evidence**. Provisional identities are not verified companies; source status labels do not close or relocate an established record. No new confirmed capability claims are added.

## Map, search and research usability

- Every class uses matching colours, symbols and text across markers, cards, profiles, identities, quick controls, legends and evidence breakdowns. Both map and mobile list modes have an available legend. Markers support Enter and Space, with visible keyboard focus and explicit accessible labels.
- Mixed clusters expose A/B/C composition in labelled rings, accessible names and popup totals. Pixel grouping reduces clutter above 120 coordinate groups, using a 96-pixel grid. Cluster anchors are actual member coordinates closest to each grid centre; they are never invented centroids or shifted pins. Shared-coordinate records keep the paginated chooser. Company-only references create no map pins.
- Quick views cover all records, A, B, C, company references and confirmed capture. All records is the default and resets filters. Other quick views combine with advanced controls using AND. The existing capability AND/OR choice and confirmed-only semantics remain. Confirmed capture means a location-specific Motion, Body or Performance Capture claim; it does not establish external commercial availability.
- Advanced controls retain country, city, sector, capability, evidence, record-kind and facility-type filters, with an operating/source identity search. Operating brands, sourced parent/group relationships, physical facilities and company references remain distinct. A source identity matched to an existing operator remains a candidate match, not proof of a branch or ownership.
- Exact/relevant names rank before weaker matches, with reviewed evidence preferred at equal relevance. No B/C class is hidden. Research views surface duplicate risks, permissions, missing geography, missing capability evidence, old/missing dates and countries with fewer than two reviewed atlas records. That geographic heuristic describes atlas coverage, not a country's industry size. Dates are not advanced by caching or report generation.
- Record comparison presents original identity, type, geography, capability evidence, relationship claims, dates, status assertions and source links separately. It does not merge records or approve claims. Profiles retain permanent URLs/back/forward, show source freshness, and offer a copy-link button. The dark MotionX branding, Leaflet, responsive map/list navigation and OpenStreetMap attribution remain.

## Lossless loading strategy

The original 13-column readable search index and all **238 evidence shards remain byte-identical**. A new columnar transport interns repeated metadata and reversibly packs long IDs. Float64 coordinates retain their exact values. Full global search/filter correctness is checked against all original entries; every one of the 1,116 company references remains available.

| Initial data representation | Before | After |
| --- | ---: | ---: |
| Search index, plain | 11,337,757 bytes | 5,027,081 bytes |
| Search index, gzip | 3,296,985 bytes | 2,179,773 bytes |
| Established baseline transfer | 358,282 bytes plain | 25,977 bytes gzip |

The compressed index is **33.9% smaller**. The compressed baseline inflates to the exact original `studios.json` bytes, SHA-256 `ae9930e0ec522812c6bc189efc4b5beac48e781e6e60f8164172755e1259b4f4`. Both compressed and inflated hashes are checked. Versioned, hash-addressed index/baseline URLs support caching without reusing a stale representation after a release. Detail shards remain lazy, bounded and shared during a session. GitHub Pages needs no server/header configuration; browsers without `DecompressionStream` use the hash-checked plain transport.

Download progress is streamed and bounded. Search and export remain disabled until the complete index and baseline pass validation. A truncated, missing or corrupt index fails clearly and permits retry; it never silently displays the old baseline as the full catalogue. Partial search publication was deliberately avoided because it would weaken global completeness/integrity. Background detail loading is retained instead.

Measured results and conditions are in [performance.json](performance.json). The immutable [before snapshot](optimisation-before.json) pins comparison to commit `6314d30da4487b5e23b6656be945a95ca98fe576`. These are individual diagnostic runs, not statistical performance guarantees. Both the real catalogue and the synthetic 50,000-location fixture are tested; repetitive synthetic identities compress much better than real source IDs and cannot stand in for real acquisition or mobile results.

## Licensing, provenance and human research

The [launch-readiness dashboard](licensing.html) and [machine audit](licensing.json) cover **49 scoped datasets / registry-policy entries**, not 49 newly collected independent datasets. Each includes source URL, version, recorded review/retrieval date, licence, attribution, notices, commercial/reuse restrictions, unresolved questions and broader-promotion status. Report generation grants no permission and does not claim to have revisited every source's current terms.

The **1,116 game-company references remain `UNSPECIFIED` / Permission not established**. Their factual names, countries, classifications and websites remain intact; no authored descriptions or photographs are added. Their pinned CSV last changed 14 September 2026, and observation on 6 November is not business verification. Public GitHub/Pages access remains public regardless of internal research intent.

CDLA/Apache permissions apply to the documented projected Overture fields with their required notices. Unresolved operating-status overlay values remain withheld while all affected reference IDs/hashes stay accessible. Access approval for a collector is not a blanket source-wide redistribution grant. EA, Cinesite and other restricted/unresolved sources remain disabled; no workaround is introduced.

The [review queue](review-queue.json) includes all **41,505 B/C records**, binds each exact source-record hash to the current catalogue/baseline, and retains possible matches. `launch_readiness.py template` outputs an **unverified** research template with the original reference, required questions, `canonical_record: null` and `approval_granted: false`. Stale checkpoints, changed source data and fabricated approval flags are rejected. Humans must research current operation, operating identity, physical branches, permissions, each capability and coordinate precision before preparing a reviewed canonical proposal.

This is not a one-click promotion tool. Later canonical changes must regenerate the bound public catalogue, compressed baseline and review checkpoint in the same reviewed PR. Promoting a source reference under its existing ID also requires explicit source/canonical reconciliation; the current builder fails on an identity collision rather than silently overwriting or dropping evidence. All original observations and histories must survive that later review.

## Validation, screenshots and remaining limits

The updated [validation report](validation.json) records the complete Python, JavaScript and four HTTP browser suites, canonical warnings, full source-archive reproduction and readiness-report reproduction. Tests cover colour/symbol semantics, mixed and coincident groups, keyboard selection, null company coordinates, full search coverage, sorting/filtering, progress/error recovery, mixed-class CSV, licensing display, HTML escaping, stale approvals/checkpoints, import idempotency and original-record preservation. Test results never verify a business claim or grant publication approval.

Updated screenshots show the **proposed HTTP-served UI**, not deployed production:

- [Desktop atlas](screenshots/desktop.png)
- [Mobile map](screenshots/mobile-map.png)
- [Mobile list](screenshots/mobile-list.png)
- [Mobile profile](screenshots/mobile-profile.png)

Cold slow-mobile loading is still substantial. The full index is held in browser memory; a full CSV export loads roughly 105 MB of uncompressed detail JSON. No physical low-memory handset or deployed Pages performance was tested. Plain fallback downloads are larger. Older/missing observations and permission/duplicate risks remain research questions, not automatic status changes. Thirteen legacy evidence records remain unresolved. Complete source archives and historical research remain intact; third-party original hosting and Actions artifacts are not guaranteed permanent.

This continues **draft PR #10**, with no new release, automatic merge, deployment or Pages-setting change. Collection/test workflows remain read-only for PR-executed code. Publication uses human PR review and an authorised manual merge, not generated approvals or reused hashes. Required-review rule enforcement remains unconfirmed under the existing read-only API audit. A maintainer must inspect the exact code, evidence and source terms before publication or broader reuse/promotion.

## Final measured results

| Scenario | Before | Final run |
| --- | ---: | ---: |
| Real catalogue, desktop cold load | 1.283 s | 1.682 s |
| Real catalogue, throttled mobile cold load | 45.085 s | 30.945 s |
| 50,000-location synthetic sharded load | 1.353 s | 1.173 s |
| Actual catalogue warm reload | Not measured | 0.924 s |

Mobile cold startup fell **31.36%** in the final run. Desktop startup increased by a fraction of a second with the added ranking/evidence UI; no universal speedup is claimed. Complete-query processing took 17.7 ms; the visible search interaction took 251.33 ms including the 120 ms debounce and browser automation. An uncached source-profile detail opened in 164.6 ms; map navigation took 43.8 ms with 140 markers. These are local diagnostic samples, not percentile guarantees.

**Final local suites: 175 Python + 55 JavaScript + 42 HTTP browser checks passed. Canonical validation: 0 errors / 265 warnings.** Complete archive regeneration matches all public JSON/gzip data; the licensing audit and 41,505-record advisory checkpoint reproduce exactly. See [the byte-preservation audit](optimisation-preservation.json). No synthetic locations are included in the public catalogue.

The blocked-Leaflet HTTP case also passes: the complete directory, advanced/quick filters and profiles remain usable on mobile when the mapping script fails. A truncated compact-index response still fails closed with no partial fallback.
