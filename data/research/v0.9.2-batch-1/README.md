# v0.9.2 — Verified Discovery Batch 1

Source research reviewed **6 November 2026 (Pacific/Auckland)**. This release proposes **12 new locations / 11 new operating organisations** and **one explicit existing-record correction**. If approved and merged, the directory will contain **141 locations / 77 operating organisations / 30 countries**. The 12 additions span eight countries; Italy and the Philippines are new to the directory.

“Confirmed” means the specific cited claim is directly source-supported, not an independent physical, legal or operational audit. These records have undergone source research by Codex and await maintainer publication review in the release PR. No pending candidate was automatically treated as a trusted record or approved by a fictitious human reviewer.

## Live discovery and continuity

PR #6 (v0.9.1) was reviewed against passing checks and merged, with user authorisation, as `6b98cf7bfe4641d1c20c406a7a2a55139aa0eaaa`. The local GitHub CLI could not dispatch a workflow (API access forbidden), and the connector does not provide workflow dispatch. A read-only PR integration job therefore ran the **merged main collector and registry** inside GitHub.

[Discovery research cycle 42152699759](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42152699759) completed successfully. Download `research-discovery-refresh` for its full queue, source report, archived history and triage output. The five enabled sources succeeded; EA was not fetched. Ubisoft returned 41 links, Cinesite seven operator links, DNEG 19, Imaginarium one index link and metricminds three service links. Cinesite's reduction from 27 to seven confirms the narrower operator filter works on live HTML. All **133 existing candidates** remained and **two prior raw queue/report snapshots** were archived. Historical navigation and disabled-source observations were retained, not erased or mistaken for closures.

[discovery-refresh.json](discovery-refresh.json) records actual run results. [queue.json](queue.json) contains the 17 selected **original candidate objects** copied from the GitHub job log with full-queue digest and provenance; it is explicitly a selection, not a replacement for the full 133-candidate artifact. Existing backlog/candidate confidence remains unknown. The full original history stays in the artifact and older repository files; finite artifact retention still requires deliberate long-term archival.

## All 14 candidate decisions

| Discovery lead | Decision | Proposed operating location / reason |
| --- | --- | --- |
| Atlanta | Add 1 | Blue Mammoth Games, **Alpharetta**. Ubisoft supports Brawlhalla development in the Atlanta market; ESA's current industry map corroborates Alpharetta municipality. No street address invented. |
| Taguig | Add 1 | Ubisoft Philippines; official address and local AAA co-development are explicit. |
| Barcelona | Add 2 | Ubisoft Barcelona and Ubisoft Barcelona Mobile, **both currently in Barcelona**, co-located at Torre Diagonal 00. Separate official branch pages and operating identities; not the historical Sant Cugat office. AAA game production is explicit on the company-authored profile linked back to the official studio page. Mobile production is explicit on its own page. |
| Lyon | Add 1 | Ubisoft Ivory Tower, actual stated municipality **Villeurbanne**; official own-studio page supports The Crew development. |
| Pune | Add 1 | Ubisoft Pune; own address plus official India page explicitly distinguish Pune production from QC/support. |
| Malmö | Add 1 | Massive Entertainment; official local page explicitly supports AAA development. A postal box is not used as a facility geocode. |
| Montpellier | Add 1 | Ubisoft Montpellier, actual municipality **Castelnau-le-Lez**. Own studio page supports development. Pin remains a clearly labelled **Montpellier urban-area reference**, pending a substantiated local/facility geocode. |
| Annecy | Add 1 | Ubisoft Annecy; own production page and matching official street address. |
| Milan | Add 1 | Ubisoft Milan, actual municipality **Assago**, as explicitly given in its official branch address. |
| Cary | Exclude this release | Careers page combines customer support and legacy Red Storm. March 2026 reporting quotes the end of game development; surviving engine/IT support does not establish current production/capture operations. |
| Los Angeles | Exclude this release | Current official page identifies Film & Television teams. IP adaptations do not establish local VFX, game-development, animation or capture facilities. |
| Guildford | Exclude this release | Ubisoft Northern Europe regional office; no local development/capture evidence. Do not imply that a closed development team relocated here. |
| São Paulo | Exclude this release | Ubisoft Brazil office address alone does not establish a restarted development studio. |
| Tokyo | Defer | Address is supported, but production-site type and local capabilities remain unresolved. |

These nine accepted discovery leads produce **10 game-development location records**, because Barcelona identifies two operating studios. Game-development classifications do not imply motion capture, previs, virtual production or animation services. [decisions.json](decisions.json) retains every source, actual review date, rationale and proposed ID; no rejected/deferred item disappears from the queue.

## Three specialist backlog topics

- **Target3D:** separate the equipment supplier/integrator from its operating StudioT3D brand. Official Stage 1 and Stage 2 technical pages and contact page support **two distinct stages at 11C Dock Street, London**. Stage 1 supports motion capture, performance capture and LED virtual production; the official home page explicitly supports face tracking for the London volumes. Stage 2 explicitly supports motion and volumetric capture. Stage 1's LED/full-performance capabilities are **not copied** to Stage 2. The operator's own team page explicitly states Target3D family membership; Stage 2 also explicitly identifies the Guildhall Production Studio partnership. Other Spain/New Zealand office and Gateshead partner/service references remain follow-up research, not new published facilities; [follow-up.json](follow-up.json) preserves those three unverified observations separately from the original 17 research items.
- **Audiomotion:** correct existing `audiomotion` identity rather than add a second Oxford entry. Its current About page explicitly states the capture volume is now at **Rebellion Film Studios, Didcot**, and supports body/performance capture and retargeting. The old record had no verified city and an Oxford regional reference. [updates.json](updates.json) retains the entire before/after record and checked previous-record hash. Migration provenance remains intact. No facial-capture capability is inferred.
- **metricminds additional facilities:** deferred. The current official site identifies Frankfurt, already represented, without substantiating an extra physical branch/stage. Do not convert historical/client/office references into new capture facilities.

[Evidence manifest](evidence.json) links each of the 13 reviewed location records to its sources, exact per-capability evidence, relationship evidence, candidate ID and coordinate reference. Review dates mean source review only. Public email/phone fields are deliberately blank. No private MotionX business intelligence, CRM notes or personal contact information is imported.

## Coordinates, identities and duplicates

All 128 unaffected pre-existing records and coordinates are byte-for-byte equivalent. Only Audiomotion has an intentional sourced location/coordinate correction, with its full former record retained. No coordinates are moved to separate markers.

New references are approximate city/municipality points, except the explicitly regional Montpellier reference for Castelnau-le-Lez. Known street addresses are public source references, not evidence of an exact pin. [city-references.json](city-references.json) records [GeoNames](https://www.geonames.org/) coordinates under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), copied without transformation and without endorsement. Alpharetta uses the municipal reference point; Didcot uses a town reference, not Rebellion's entrance. Existing site GeoNames/OSM attribution remains preserved.

The initial dry run intentionally blocked two matches: the co-located Barcelona operators and StudioT3D Stage 2 against Stage 1. The reviewed dry run explicitly allows the two distinct IDs with source-backed rationales, then the importer adds 12 records. The canonical validator continues to disclose these legitimate duplicate warnings; no heuristic is suppressed and no facilities are merged. Shared city coordinates continue to use the accessible selection popup.

## Import and review audit

- `batch.csv`: 12 additions only; it cannot silently modify an existing ID.
- `batch-validation.json`: required-field/evidence/coordinate validation.
- `import-initial-preview.json`: two unresolved candidate matches, no write.
- `import-preview.json`: 12 proposed additions, both distinct-location matches explicitly reviewed, no write.
- `import-result.json`: 12 appended **on the development branch**.
- `import-repeat.json`: 12 unchanged / zero new / no write after repeat import.
- `updates.json` and `update-result.json`: one explicit hash-checked Audiomotion correction; not a second location or an importer overwrite.
- `records.json`, `queue.json`, `reviews.json`: content-bound review template for the proposed additions/correction. **Every approval decision remains pending, reviewer names blank and human checks false.** Codex source research is not impersonated as named human approval.
- `approval-gate.json`: the real `prepare` invocation against the audited pre-release baseline correctly exits 1, produces no proposal and requires named explicit approval.

This PR presents the actual proposed canonical data diff for maintainer review. The append/import/correction path is tested, and the pending-approval boundary is tested. **A real approved-bundle-to-automated-draft-PR run is not claimed complete:** that requires a maintainer's content-bound approval. Do not fake an approval or weaken the guard merely to make an automated end-to-end demo pass.

For this release, review the evidence/data diff and merge the release PR manually only when satisfied. The review template records the pre-release baseline; after the data PR merges, those hashes are historical, not reusable approvals for another automated publication. Future automation must generate a fresh bundle against current main. The manually dispatched approved-bundle workflow remains available for that process. No v0.9.2 merge or automatic publication is performed by this work.

Re-run append validation/idempotency safely against the already updated development database:

```sh
python tools/validate.py data/research/v0.9.2-batch-1/batch.csv
python tools/import_csv.py data/research/v0.9.2-batch-1/batch.csv --dry-run
python tools/import_csv.py data/research/v0.9.2-batch-1/batch.csv --apply
python tools/validate.py studios.json --report data/validation_report.json
```

To reproduce first import, use a copy of pre-release main and pass both `--allow-distinct-location ubisoft-barcelona-mobile-main` and `--allow-distinct-location studiot3d-london-stage-2` after reviewing their evidence. Apply the separate correction only against its matching previous-record hash. Never use the CSV to overwrite existing records.

## QA and limits

**87 Python tests, 20 JavaScript tests and 16 HTTP browser checks pass.** Coverage includes all 17 research outcomes, original-record preservation, manifest and coordinate consistency, separate stage capabilities, duplicate preview/repeat import, correction identity/provenance, five successful live sources with EA disabled, and pending approvals blocking publication. Historical v0.7/v0.8/v0.9.1 tests reconstruct the audited earlier snapshot rather than falsely require the corrected Audiomotion record to remain unreviewed forever.

Canonical validation: **0 errors / 160 disclosed warnings** = 141 approximate coordinate references + 17 legacy unknown-evidence records + two reviewed co-location duplicate pairs. These are not silently suppressed.

HTTP checks cover the actual 141-location database, source-reviewed legacy date display, Stage 2-only volumetric filtering, profiles, shared-coordinate keyboard navigation, export, OSM tiles/attribution, mobile layout, retry/error states and 10,000-location viewport fixtures. The one UI correction labels a newly reviewed migrated record's date as a current recorded review, while other unknown legacy records retain their legacy date warning. Styling and mapping services remain unchanged.

Remaining limits: Tokyo and additional metricminds facilities still need research; four unsuitable Ubisoft leads are retained with exclusion reasons. Other specialist/Ubisoft/EA gaps are not claimed complete. Exact geocodes, the Castelnau reference and additional StudioT3D partner/overseas references need future work. External website availability and content may change; structural validation and browser tests cannot independently establish business truth. EA automation stays disabled. Full live artifacts retain the existing 90-day expiry.
