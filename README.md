# MotionX Studio Atlas v1.1 — Global Bulk Data Acquisition

**One unified research atlas: 41,735 records.** Browse the existing **243 locations**, all **40,376 Overture source observations**, and all **1,116 game-company references** together. Nothing is excluded from the directory merely because it requires research. The full dataset, map, search, filters, profiles and CSV export use one catalogue. Record totals include overlapping references and company-only entries; they are not counts of independently verified physical studios.

All 243 original IDs, coordinates, evidence and company relationships remain byte-for-byte in `studios.json`. The [combined catalogue](data/public/manifest.json) adds hash-bound, country-grouped research shards and a compressed search index. All 13 legacy unknown-evidence records remain visible with research labels. Company references have no invented cities, branches, facilities or map pins.

- **A — Source-reviewed location:** 230 retained records. Capability evidence stays specific to each claim; source review is not an independent business audit.
- **B — Source-listed location observation:** 4,626 records. The permitted directory supports the listing; current operation, physical facility type and services remain uncorroborated.
- **C — Research required:** 36,879 records, including company references, uncertain observations and legacy unknowns. They remain searchable alongside A/B with explicit warnings. Inclusion does not approve their claims.

No new confirmed capture or other facility-capability claims are created. Source closure/status labels are displayed as assertions and never silently overwrite reviewed records. Possible duplicates are linked for research rather than automatically merged or deleted. All original geographical points and the shared-coordinate selection popup remain intact.

The [bulk report and workflow](data/bulk/README.md), [combined audit](data/public/audit.json) and [source receipts](data/bulk/unified-input/source-receipt.json) retain provenance and limitations. Overture records carry their provider licences and notices. Game-company entries are factual references: the source README offers download/local use but does not state an explicit dataset redistribution licence; that limitation is labelled and authored descriptions are omitted. No source is described as permissively licensed without evidence.

This remains a **public GitHub Pages site**, even if its URL is not promoted. No private CRM data, personal contacts, credentials or confidential business intelligence are added. Loading/error states, secure links, CSV formula protection, Leaflet and OpenStreetMap attribution are preserved. Gzip assets are explicitly fetched and decompressed where supported, with uncompressed equivalents for other browsers; all representations are hash-checked.

The release is a **draft PR requiring human review and an authorised merge**. Nothing automatically merges, deploys or changes Pages settings. Source collection produces research artifacts only. The existing content-bound approval-bundle workflow remains separate; no historical approval is invented or reused. The [read-only GitHub rule audit](data/bulk/review-rules-run42287663788.json) returned no effective rules and could not expose classic protection, so required-review enforcement remains unconfirmed.

The unified atlas now uses **green squares (A), blue circles (B) and amber triangles (C)**, with text labels and permanent map/list legends. Mixed clusters show evidence composition and open a keyboard-accessible record chooser. Quick views cover all records, each class, company-only references and facilities with confirmed Motion/Body/Performance Capture evidence. Advanced filters include organisation identity and advisory research signals. Results prefer relevant names and reviewed evidence; B/C references remain accessible. Record comparisons preserve each source's evidence and never merge identities.

The lossless columnar search transport is **2.18 MB gzip**, compared with the original 3.30 MB. IDs and original coordinates reconstruct exactly; the original readable index and every evidence shard remain unchanged. A compressed, hash-bound copy of the unchanged baseline and versioned index cache reduce repeat downloads. Progress is explicit, and complete global results are exposed only after all data and integrity checks finish. Profiles still load full evidence on demand. See the [optimisation report](data/bulk/reports/optimisation.md) for measured desktop/mobile results and limitations.

The [licensing and launch-readiness dashboard](data/bulk/reports/licensing.html) covers datasets, coordinate references and every registered source policy. **The 1,116 company references remain permission-unresolved**, not licence-cleared. The [advisory review queue](data/bulk/reports/review-queue.json) binds all 41,505 B/C records to their exact content and baseline. `tools/launch_readiness.py` generates pending research templates; no score, report or template grants publication approval. Source review, canonical reconciliation and a human-authorised PR remain required.

## Public atlas

- Browse locations or operating organisations, then open a location, all branches under its stable operating ID, or sourced parent/group and related-brand views. Distinct subsidiaries remain separate operating identities. Partnerships are not ownership.
- Share `#/location/dneg-london` or `#/organisation/dneg` URLs. Hash routes work under GitHub Pages subdirectories, reloads and browser back/forward. Profiles show evidence/date, confirmed/likely/unknown claims, location type, coordinate precision, official links and other branches.
- Search words combine with **AND**, ignoring accents/case. Search covers studio, operating ID/name, city, country, sectors, capabilities and sourced relationship names. City matches text; country/type are exact. Different controls combine with **AND**.
- Select multiple facility capabilities with **all (AND)**, or explicitly choose **any (OR)**. Confirmed-only checks the selected capabilities, selected sector when no capability is selected, or at least one confirmed capability when neither is selected. Parent services never become branch capabilities.
- Reset filters, inspect visible result totals and export **all filtered locations across pages**. CSV preserves IDs, relationships and evidence, omits contact fields and neutralises spreadsheet-formula prefixes. Capability evidence states are retained; “confirmed” describes a reviewed source claim, not an independent audit of business operation.
- Individual access to coincident coordinates is preserved through paginated selection. Above 2,000 coordinate groups, spatial buckets select the viewport and pixel-grid map groups reduce marker overhead. A group uses one actual member coordinate; original coordinates are never offset. The full directory and CSV remain available outside the viewport.

## Historical v1.0 research, safety and review

The [release audit](data/research/v1.0-launch/README.md), [readable review dashboard](data/research/v1.0-launch/review.html), [evidence manifest](data/research/v1.0-launch/evidence.json), [CSV](data/research/v1.0-launch/batch.csv), [import audit](data/research/v1.0-launch/import-audit.json) and [deferred queue](data/research/v1.0-launch/review-queue.json) present exact additions and before/after corrections. The dashboard is a research file/downloadable Actions artifact; the public app never loads it or the discovery queue. Seven new capture locations have individual site evidence. Thirteen legacy unknown-evidence records remain. Canonical validation: **0 errors / 265 warnings**, all listed in the release bundle.

The registry remains **25 entries / eight enabled collectors**. No new source permission is inferred from research access. EA, Cinesite and other prohibited/unresolved sources remain disabled. Collection does not use screenshots, OCR, hidden APIs, alternate hosts, recursive crawling or paywall workarounds. Failed fetches or changed/disappearing pages never remove a published studio.

Discovery now scopes shared contact-page matches by company and place, flags ambiguous same-city facilities, highlights fresh genuinely new candidates, and labels stale observations for revisit. `restore_discovery.py` tries recent successful main-branch artifacts, then a SHA-256-bound committed checkpoint. Partial recovery is explicit and suppresses disappearance signals; missing history cannot be reconstructed. Invalid checkpoint identity conflicts fail closed. Both the original 172-candidate checkpoint and 28 new deferred review topics are preserved. `archive-discovery.yml` can archive a complete main discovery run into a **state-only draft PR** before artifacts expire; it grants no business approval.

This release uses **the manually reviewed GitHub PR route**, not a fabricated approval JSON bundle. `research.py stage-pr` binds the current baseline, every exact proposed record, previous update contents, per-capability evidence and review dates. Actions regenerate the readable review and reject an unexpected canonical diff. Only an authorised human merge publishes. `review_rules.py` inventories main's effective/classic protection read-only; unavailable API results mean enforcement is unconfirmed. Maintainers must inspect required reviewers and bypass rights; a passing test, clicked link or generated report never grants approval. The separate historical content-bound approval-bundle workflow remains available and is not retroactively approved by this release.

See the release audit for full tests, identical-fixture v0.9.3/1.0 performance measurements, source results and operational limits. Synthetic 50,000-location fixtures exist only in test memory or temporary files and never enter the public database.

## Historical v0.9.3 research and automation

The [release report](data/research/v0.9.3-global/README.md), [exact-record evidence manifest](data/research/v0.9.3-global/evidence.json), [CSV batch](data/research/v0.9.3-global/batch.csv), import reports, before/after correction and deferred queue document this proposal. All 141 previous IDs remain; Centroid Riverside alone receives an explicit evidence update. All original coordinates remain unchanged. New locations use attributed approximate city references, including Burbank for facilities marketed as Los Angeles. No organisation-wide capture claims are copied to branches.

The registry contains **25 official source entries; eight are enabled for bounded factual metadata collection** after recorded policy review. Seventeen remain disabled pending access/reuse clarification or permission. This deliberately falls short of 15–25 enabled collectors. EA remains disabled; newly reviewed Cinesite terms explicitly prohibit scraping, so its collection is disabled too. Unavailable or restrictive policies, JS-only pages and access failures are reported, never bypassed with browser screenshots/OCR or hidden APIs. A robots allowance or absence of policy keywords is not a reuse licence. Initial/second/final policy audits preserve the rejected URL guesses and corrected source decisions.

Source adapters identify branch links or explicit location cards, retain separate facility keys and ignore navigation/scripts. Evidence-byte changes, openings, acquisition/rebrand, relocation and missing-link signals require investigation; none changes business status. A redesigned/failed/empty page cannot withdraw records. Label-card adapters cover reviewed labels; unknown new labels require reviewing the page-change alert and updating the mapping. Collection is bounded to configured pages, not recursive crawling.

### Downloadable review report

Weekly/manual **Discover studio candidates** runs generate `studio-research-review` (`review.html`, `proposals.json`, `summary.md`). PR source checks also upload `global-research-review`, including original discovery state/history, source-policy results, staged data and a company/country-grouped dashboard with before/after comparisons. Download and open `review.html` locally: it is self-contained, keyboard accessible and makes no script/network requests. This report is separate from the public directory. All discovered claims remain unverified; source-researched proposals are separately labelled **pending human PR review**.

```sh
python tools/research.py report --queue path/to/queue.json --report path/to/report.json \
  --config data/discovery/sources.json --output /tmp/motionx-review
# Add --records data/research/<batch>/records.json to display authored before/after proposals.
```

Dossiers include operating-identity hints, supported place references, potential sector/parent relationships, local capability terms, observation dates/freshness, existing matches and reasons, identity risks, change alerts and unresolved questions. Confidence is routing/evidence context, not human approval or independent confirmation of current operation.

### Publication: two distinct routes

**This v0.9.3 release uses GitHub-native human PR review and manual merge.** No human approval is claimed and no historical approval hashes are generated or reused. A maintainer must inspect the exact canonical diff and evidence, run the checks and personally authorise merge. New commits require renewed review. Configure required reviews and dismissal of stale approvals in repository rules for enforced review; this change does not alter repository/Pages settings. The informational review workflow reports exact-head account metadata, explicitly without claiming it proves human intent or authorises publication.

For subsequent source-researched bundles committed to `main`, manually dispatch **Draft a source-researched data PR** with `data/research/<batch>`. It validates `records.json`/`evidence.json`, exact baseline/record/previous-record hashes, review dates, capability evidence and explicit distinct-facility rationales. It stages a draft branch/PR only; it cannot approve or merge. A stale baseline blocks preparation. GITHUB_TOKEN-created PRs may need maintainer-triggered required checks. Historical release bundles are audit records and cannot be re-used against a changed database.

```sh
python tools/research.py stage-pr --database path/to/current-baseline.json \
  --records data/research/<batch>/records.json --manifest data/research/<batch>/evidence.json \
  --output /tmp/motionx-staged-proposal
```

The **older content-bound approval-bundle route** (`prepare-studio-proposal.yml`, `discovery.py prepare`) remains separate and unchanged. It requires committed, named, exact-content approvals before preparing a proposal. Its historical pending approvals remain pending. Neither passing tests, clicking an evidence link, a reviewer-name string nor an AI-generated review is human approval.

The public UI adds an optional **Confirmed capability evidence only** filter. With a specialisation selected, that specific capability must be confirmed; otherwise at least one capability must be confirmed. Confirmed means a cited claim was reviewed, not independently verified current business operation. Search, counts, profiles, co-located selection and CSV export use the same filtered records. The 20,000-location HTTP performance test retains original coordinates and viewport rendering without a paid API or backend.

## Historical v0.9.2 researched data release

The [release research log](data/research/v0.9.2-batch-1/README.md), [evidence manifest](data/research/v0.9.2-batch-1/evidence.json), [candidate decisions](data/research/v0.9.2-batch-1/decisions.json) and import/repeat reports retain the complete audit. All 14 discovery leads plus three specialist topics were researched: ten game-development locations and two distinct StudioT3D London capture stages are proposed, while Audiomotion's existing record is corrected to its officially stated Didcot facility. Four leads are excluded and two research topics remain deferred. No capture capabilities are inferred from game development.

PR #7 merged this data into main. The five-source collector refresh at that release retained all 133 candidates plus history. Historical JSON approval bundles remain pending and are not retroactively approved by that merge; v0.9.3 uses a separately documented human PR-review route. Cinesite automation is now disabled under its newly reviewed terms. Validation reports **0 errors / 160 warnings** covering approximate pins, remaining legacy unknown evidence and two reviewed co-location pairs. The public website continues to load only canonical data, never the unverified discovery queue.

## Historical v0.9.1 discovery triage

The [triage release report](data/discovery/triage-v0.9.1/README.md) documents the actual first successful Actions artifact: **133 candidates → 46 represented, 14 potentially new, 24 irrelevant, 49 requiring research**. Eight represented matches are organisation-only; no new studio or capability is approved. All 41 backlog entries remain intact.

Read-only Actions jobs produce `triage.json`, `summary.md` and preserved original inputs. Discovery now carries raw report/queue history forward and handles filter changes without false disappearance signals. Cinesite collection targets operator links. EA automation is disabled because its current access policy prohibits scraping/text-data mining without written authorisation; screenshots/OCR are not an access-rule workaround. The public database remains unchanged.

## Historical v0.9 discovery infrastructure

[Discovery documentation](data/discovery/README.md) explains the source registry, bounded robots-aware collection, unverified queue, change signals and content-bound evidence reviews. Weekly discovery produces an artifact only. A separate manually dispatched workflow prepares a validated **draft PR** from an approved review bundle; humans review and merge before publication. No newly discovered studio is automatically trusted or added. The public database remains the v0.8 dataset; 41 deferred candidates are preserved separately for follow-up.

```sh
python tools/discovery.py scan --output /tmp/motionx-discovery-run
```

The local live-source attempt was blocked by this environment's domain/DNS access; the [run report](data/discovery/initial-run-report.json) records all six failures without claiming discoveries. Offline fixtures exercise the full pipeline. New industry directory sources require explicit terms/robots/adapter review before enabling. The original live-run source review is recorded in v0.9.1; current global collection results are linked in the v0.9.3 report above.

## Historical v0.8 research release

The [research report](data/research/v0.8-global-expansion/README.md) documents imported organisations, six source-supported capture facilities, branch-coverage limits, coordinate licensing, tests and performance. The [evidence manifest](data/research/v0.8-global-expansion/evidence.json), [CSV batch](data/research/v0.8-global-expansion/batch.csv), dry-run/apply/repeat reports and [review queue](data/research/v0.8-global-expansion/review-queue.json) are retained. Review date: **6 November 2026**. Validation at v0.8: **0 errors / 147 warnings**, covering 129 approximate coordinates and 18 legacy unknown-evidence records. Ubisoft and EA coverage remains partial; unresolved candidates are queued rather than published.

## Historical v0.7 research batch 1

The [batch research log](data/research/v0.7-batch-1/README.md) documents every imported location, primary source, coordinate reference and unresolved claim. The [CSV](data/research/v0.7-batch-1/batch.csv), [per-location evidence manifest](data/research/v0.7-batch-1/evidence.json), dry-run/import/repeat reports and batch validation are retained together. Verification dates use **6 November 2026, Pacific/Auckland**; these indicate review of the cited claims, not independent verification of registration or current operation.

Imported: Wētā FX Wellington (1), ILM San Francisco/Vancouver/London/Sydney/Mumbai (5), and Framestore London/Montréal/Chicago/Los Angeles/New York/Mumbai/Melbourne (7). No duplicates or rejected candidates were found. New pins are explicitly approximate city references; facility geocodes and capture capabilities are not asserted. Coordinates are from [GeoNames](https://www.geonames.org/), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), copied without transformation and used as city reference points. This is attribution, not a claim of GeoNames endorsement.

## Run locally

From the repository root:

```sh
python -m http.server 8000
```

Open `http://localhost:8000/` in a browser. Use HTTP rather than opening `index.html` through `file://`, which browsers restrict. Relative asset/data paths also work below `/motionx-studio-atlas/` on GitHub Pages. The existing GitHub Pages configuration can continue to serve `main` at the repository root after a reviewed merge. This change does not deploy or change hosting settings.

Leaflet 1.9.4 is loaded from unpkg; public OpenStreetMap tiles and attribution are preserved. Internet access is required for those resources. No API key, paid API, build process or mandatory backend is needed. Follow the [OpenStreetMap tile usage policy](https://operations.osmfoundation.org/policies/tiles/); do not bulk-download or prefetch tiles.

## Database model

The JSON root is an array of **location** objects, preserving the v0.5 layout:

| Field | Meaning |
| --- | --- |
| `id` | Unique, stable location ID, lowercase letters/digits separated by hyphens |
| `company_id` | Stable organisation identity, distinct from location identity; reuse for every location of that organisation |
| `name`, `city`, `country` | Public display labels; `name` may describe a particular facility |
| `lat`, `lng` | Finite numeric latitude / longitude within ±90 / ±180 |
| `categories` | Nonempty array of sector labels; not restricted to mocap |
| `capabilities` | Array of capability labels; may be empty when unknown |
| `capability_evidence` | Object keyed by every capability, with `state`, `evidence` (HTTPS URL or empty string), and `verified_on` (`YYYY-MM-DD` or empty string) |
| `evidence_state` | Overall location claim confidence: `confirmed`, `likely` or `unknown` |
| `evidence`, `verified_on` | Location research source and recorded review date; not proof of independent verification |
| `coordinate_precision` | `exact`, `city`, `approximate`, `region` or `unverified` |
| `website` | Required public HTTPS website |
| `address`, `email`, `phone`, `status` | Optional public location reference, business contacts and research caveat |
| `location_type` | Optional: `production_studio`, `capture_facility`, `creative_hub`, `mixed_campus`, `production_office` or `uncertain` |
| `coordinate_source` | Optional HTTPS provenance for the coordinate reference, distinct from location evidence |
| `relationships` | Optional array of `{id, name, type, evidence, verified_on}` for sourced `subsidiary_of`, `group_member` or `partner_of` relationships; does not merge operating identities |
| `legacy_research` | Migration provenance only; original v0.5 claims, dates and replaced pin/address values, not current confidence |

Do not derive company identity from a display name or website: multiple locations may share both. Preserve existing IDs when correcting records. A new location of an existing company gets a new `id` and the same `company_id`. The JSON remains denormalised for a simple static site; a separate company table/backend is not required. `schema.sql` is an older, unused database design sketch, not the v0.6 runtime schema. The archived `MotionX_Studio_Atlas_GitHub_Pages_v0.5/` directory is historical and is not loaded by the root website or tools.

## Research confidence and coordinate policy

Confidence applies to the **specific claim**, not the whole organisation's legal or operating status:

- **confirmed**: a researcher reviewed a dated source directly supporting that claim.
- **likely**: a dated source provides suggestive or indirect support; uncertainty remains.
- **unknown**: not researched, ambiguous, outdated or not yet rechecked. A URL alone is not confirmation.

Both `confirmed` and `likely` require a source URL and review date, at the location level and separately for each capability. Do not copy overall confidence to every capability. Missing/unknown capabilities do not exclude a studio. Keep source URLs and review dates; independently checking a website's presence does not establish current operation, registration, an address or a capability. Validation checks structure, not the truth or availability of external evidence.

The v0.5 seed was explicitly not independently re-verified. v0.6 therefore set its current confidence and individual capability confidence to `unknown`, retaining legacy dates/source URLs and original labels under `legacy_research`. v0.9.2 explicitly re-researches Audiomotion and v0.9.3 reviews Centroid Riverside, preserving their complete former records in release audits; 16 other unreviewed seeds remain unknown. `verified_on` on these records is a **legacy recorded review date**, labelled accordingly in profiles. These dates are preserved verbatim; the validator may flag them as future dates depending on the runner's date/timezone.

Use city-level approximate coordinates when a street address cannot be verified. The five legacy street-looking pins were replaced by approximate city reference points and the original values retained as provenance. Existing campus/city estimates remain approximate. Records with an unverified city retain their existing regional reference pins explicitly marked `unverified`; their actual city still needs research. Never infer an exact address from a pin. New `exact` records require an address, evidence and a date; a researcher must ensure that evidence actually supports the coordinates. The interface labels every non-exact pin as approximate.

## Research CSV and bulk import

Python **3.9+**, standard library only. Start a batch by copying **`data/research_template.csv`**, which contains headers only so examples cannot accidentally enter the public database. Use a CSV-aware editor or Python's `csv.DictWriter`.

- Retain all required headers. Unknown columns are rejected to help prevent accidental import of private research notes.
- `categories` and `capabilities` use `|` separators (for example, `VFX|Animation`). Empty capabilities are allowed.
- `capability_evidence` is a JSON object inside a CSV cell. For a capability `Animation`, a not-yet-reviewed value is `{"Animation":{"state":"unknown","evidence":"","verified_on":""}}`. Use `{}` when there are no capabilities. A CSV-aware writer handles the embedded quotes.
- Optional `company_name` supplies a consistent operating-organisation display name for a stable `company_id`; it never replaces subsidiary or parent identities.
- Optional `relationships` uses a JSON array inside a CSV cell; each entry requires a stable parent/group ID, name, type, evidence URL and review date. Blank optional metadata stays absent for legacy compatibility. `coordinate_source` documents geocoding provenance; `location_type` distinguishes studios, capture stages, creative hubs, campuses and production offices. Do not infer a relationship or site type from a shared address.
- Use HTTPS URLs, numeric coordinates and calendar dates in `YYYY-MM-DD`. Unknown evidence can have a blank URL/date. Future dates produce warnings; malformed dates are errors.
- Do not change existing records through a batch. Make corrections explicitly in `studios.json` in a separate reviewed change.

Validate and preview first:

```sh
python tools/validate.py studios.json --report data/validation_report.json
python tools/validate.py path/to/batch.csv --report /tmp/batch-validation.json
python tools/import_csv.py path/to/batch.csv --dry-run --report /tmp/import-preview.json
```

The importer defaults to dry-run even without `--dry-run`. Reports list proposed new IDs, unchanged IDs, potential duplicates and their matching reasons, rejected rows, validation warnings and whether anything was written. Review both evidence and warnings before applying:

```sh
python tools/import_csv.py path/to/batch.csv --apply --report /tmp/import-result.json
python tools/validate.py studios.json --report data/validation_report.json
```

Imports are append-only and all-or-nothing: any invalid record, ID conflict, invalid existing database or unresolved duplicate candidate prevents the entire batch from being written. Identical repeated IDs are skipped, including within a batch; an ID with different content is rejected. Repeating a successful import does not add records or rewrite the database. Writes use a temporary file and atomic replacement, with a check for a changed database. Run one importer at a time; this is not a multi-writer database lock.

Duplicate detection uses normalised name, company ID or website hostname **within the same city/country**. It includes earlier rows in the same batch. Matches are candidates, not proof: multiple legitimate facilities can exist in one city. To approve a researched, distinct facility, give it a stable new location ID and explicitly allow that ID in both preview and apply:

```sh
python tools/import_csv.py path/to/batch.csv --dry-run --allow-distinct-location researched-location-id
python tools/import_csv.py path/to/batch.csv --apply --allow-distinct-location researched-location-id
```

This approval is recorded in the report and never bypasses ID conflicts or validation. No record is automatically merged or deleted. Spelling changes, different domains or nearby cities may evade the heuristic, so manually review the preview. Keep approved batch/report artifacts with your research process. `--database path/to/copy.json` supports experiments without changing the canonical file. CSV exports in the UI describe the filtered results and protect spreadsheet formulas; they are **not** lossless research-import batches (use the research template).

## Tests and QA

Required offline checks (Python standard library and Node 18+; no npm install):

```sh
python -m unittest discover -s tests -p 'test_*.py' -v
node tests/data.test.js
python tools/validate.py studios.json --report data/validation_report.json
```

Optional real-browser integration checks, including HTTP hosting below a repository subpath:

```sh
python -m pip install playwright
python -m playwright install chromium  # or use an existing Chromium
python tests/browser_smoke.py
```

`CHROMIUM=/path/to/chromium` can select a browser. The browser suite uses live unpkg/OSM resources, so network outages can fail its tile check. It checks loading, map attribution/tiles, search, combined filters, profiles, totals, CSV export, mobile navigation, error/retry states, and 50,000 **in-memory synthetic test locations**, including shared coordinates with pagination. These fixtures never enter `studios.json`. Screenshots go to the system temporary directory. Pull requests run Python, JavaScript and HTTP browser checks in GitHub Actions; no deployment workflow is added. `tests/performance_compare.py --baseline /tmp/v093-checkout --output /tmp/comparison.json` compares an archived baseline against the same 50,000-record HTTP fixture. Baseline files must be the original `index.html`, `data.js` and `app.js`.

## Limits and public-data safety

The client fetches and validates the whole JSON file; lists are paginated at 50 and markers use Leaflet's canvas renderer. Above 2,000 filtered coordinate groups, marker rendering follows the padded viewport while counts, search, CSV export and fit-results retain the complete filtered results. This is a tested foundation for thousands of locations, not an unlimited dataset or a claim of performance on every phone. Spatial buckets and pixel-grid marker groups are implemented; larger future datasets may need partitioned data or tiling after measurement. Discovery remains separate from the public database and cannot prove business facts. Search includes unknown capabilities by default; use the confirmed-only filter and read confidence labels before relying on results. Duplicate detection does not prove identity, and offline validation does not verify sources or geocode addresses.

Only public directory data belongs here. Do **not** commit private CRM data, sales leads, outreach notes, client intelligence, tokens, keys or confidential/personal research. Check directory reuse rights and licences before importing third-party data. Use official public business sources and review contacts before publishing. v1.0 adds no private records or credentials.

Committed PR discovery checkpoints are merged additively into later scans: missing candidates and earliest observation dates are retained without replacing newer run evidence or reviews. The checkpoint itself is archived and grants no approval.
