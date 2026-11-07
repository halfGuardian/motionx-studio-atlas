# Global programme review checkpoint

[Draft stacked PR #18](https://github.com/halfGuardian/motionx-studio-atlas/pull/18) · branch `codex/global-discovery-visibility` · [umbrella issue #17](https://github.com/halfGuardian/motionx-studio-atlas/issues/17). The parent remains draft PR #15 at exact head `efd52a86e66417438830aac285e3fffee3aa0fa0`; its branch is unchanged. Nothing was merged, deployed or given fabricated human approval. Issue #16 remains open pending reviewed delivery.

## Delivered implementation checkpoints

- Separate approximate company-reference map layer, clear location-status profiles, same-coordinate selection, unlocated-company browsing, original-coordinate CSV preservation and actual Floating Rock / Frame Machine acceptance checks.
- Saved source-discovery receipts for every one of the 178 represented countries/territories, plus fifteen page/access/permission assessments across seven research regions. The 3,562 returned references represent **2,329 distinct URLs**, not companies or complete directories.
- Accountable reconciliation of **44,394** retained/research observations against the full catalogue, including **430** preserved historical checkpoint observations, complete existing factual snapshots and all source provenance. All **209** retained parent research files are hash-checked.
- Independent claim axes for identity, geography, company services and facility capabilities; explicit source age versus observation age, unresolved ownership/geography and no automatic promotion, merge or closure.
- One searchable/filterable [global dashboard](reports/dashboard.html), source ledger, country gaps, full gzip JSON audit, CSV reconciliation and content-bound working-decision exports. These exports cannot approve or publish.
- Durable standard-library CSV/JSON maintenance with scoped source policies, complete/partial/failing snapshot accounting, history integrity, before/after change signals, configurable freshness and read-only manual Actions replay. The actual licensed 424-row snapshot repeated with zero additional signals and no canonical changes.
- Full local regression/browser validation, realistic catalogue and synthetic performance results, and a fourteen-candidate evaluation worksheet frozen before matching. Independent human labels remain pending; precision/recall are null.

## Preserved public catalogue

| Measure | Before | Proposed after |
| --- | ---: | ---: |
| Catalogue references | 42,296 | 42,296 |
| Retained locations / operating organisations | 243 / 119 | 243 / 119 |
| Source-location observations | 40,376 | 40,376 |
| Company-only references | 1,677 | 1,677 |
| Class A / B / C | 230 / 4,626 / 37,440 | 230 / 4,626 / 37,440 |
| Represented countries/territories | 178 | 178 |
| Original coordinate records | 40,619 | 40,619 |
| Separate approximate display references | 0 | 1 |
| New canonical companies / facilities / confirmed capabilities | 0 / 0 / 0 | 0 / 0 / 0 |

Reference totals and provisional source identities are not unique verified operating-company/facility counts. Thirty-eight retained references have no country. Existing IDs, coordinates, evidence and relationships remain unchanged.

Floating Rock's official contact page supports Wellington. A licensed GeoNames city reference is displayed as a separate hollow diamond, explicitly **not its entrance**, while its original lat/lng remain null and its Class C evidence remains unchanged. Frame Machine already has an Animation-tagged Class C source-location point in Santa Monica; filtering by company-only correctly excludes it. Its profile and empty-state text now explain that distinction. Confirmed-capability filters do not invent verified services at either company.

All 1,677 unpinned companies have dispositions: **1,369** source identity/country without verified location; **256** recorded city/region associations awaiting individual geographic review; **1** reviewed display reference; **24** historical/status assertions requiring investigation; **3** identity conflicts; **24** insufficient-evidence cases. Another **1,676** companies still lack a display reference. No parent/foreign-branch location is inherited.

## Research outcomes and unfinished work

Every replayed observation has one accountable outcome: **42,102** represented source-identity observations; **623** existing-company matches; **633** repeated observations; **262** potential-company observations; **7** branch-review leads; **373** research-required observations; **283** out-of-scope/navigation observations; **35** identity conflicts; **24** possible aliases; **52** company/geography review cases. Counts describe observations, not newly verified businesses. Four existing facility dossiers remain pending, with **zero new independent facility reviews**.

[Country-by-country gaps](reports/countries.json), [source-by-source permissions and scopes](reports/source-ledger.json), [complete reconciliation](reports/reconciliation.csv) and [source-assessment explanation](SOURCE-COVERAGE.md) retain the full denominators. No new directory is claimed fully enumerated. Source-wide rights and most local-language/subnational coverage remain unresolved. Korea returned 403, BCTQ 502, Animachi timed out and Dubai returned a loading error. Other pages mix individuals, agencies, distributors, schools and companies. Restricted sources remain disabled; no bypass was used.

The held-out worksheet has **14** purposive candidates across seven regions: **9** model candidate matches and **5** unmatched. It has **0** exact-page overlaps and **2** source-domain overlaps with the replay corpus. None has independently reviewed ground truth. This is an explicit pending evaluation frame, **not** a blind global precision/recall result or proof that the sample businesses currently operate facilities.

## Tests and practical performance

[Machine results and logs](qa/results.json): **283 Python tests, 84 JavaScript tests and 78 HTTP browser checks pass on their latest runs**. Canonical validation has **0 errors / 265 disclosed warnings**. Complete source-layer replay, immutable parent records/history, actual snapshot idempotency, missing/corrupt history, safe exports, filters, profiles, mobile/keyboard use and same-coordinate selection are checked. The first concurrent legacy synthetic run timed out; an isolated rerun passed all 19 checks. Fixture/guard corrections and all raw results are disclosed in the QA report.

Actual 42,296-reference HTTP catalogue: **2.21 s** initial readiness, **12.5 ms** search computation and **33.30 s** readiness at 96,000 bytes/s, 150 ms latency, 4× CPU slowdown and 390 px viewport. The 50,000 synthetic source-location benchmark loaded in **1.55 s**, searched in **7.7 ms**, opened a profile in **42.4 ms** and rendered the measured viewport in **3.5 ms**. These are local headless Chromium measurements on shared cloud hardware, with raw conditions retained. They are not deployed Pages or physical low-memory-phone results, and synthetic locations never enter public data.

The compressed review index is separate from the full research audit and only 25 review cards render at once. It requires browser gzip-stream support. Review notes must be exported to persist; they are not authenticated approval.

## Remaining human and operational gates

Worldwide source enumeration and independent company/facility verification remain **in progress**. Review source-specific rights, ambiguous identities, municipalities, current operation and capability evidence before new collection/publication. Obtain human labels before making quality claims. Work through the saved global queue without new country-by-country prompts; exact commands and next tasks are in [MAINTENANCE.md](MAINTENANCE.md).

Review/authorise PR #15 first, then rebase or retarget PR #18 as appropriate and review its exact changes. The read-only global Actions workflow has not been manually dispatched on the default branch. No schedule or unrestricted crawler is enabled. The API returned no rulesets, while classic branch-protection inspection returned **403: Resource not accessible by integration**; required human-review enforcement therefore **cannot be confirmed**. Draft status and passing CI do not enforce approval by themselves. Do not merge or deploy automatically.
