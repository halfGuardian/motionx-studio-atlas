# MotionX Studio Atlas v0.7 — Global Research Expansion, Batch 1

Public directory of VFX, animation, games, motion capture, performance capture, previs, virtual production, cinematics and related studios. The canonical public database is **`studios.json`**, currently **31 locations across 19 organisations**. v0.7 adds 13 source-reviewed locations across Wētā FX, Industrial Light & Magic and Framestore, preserving all 18 v0.6 records unchanged. Motion capture is an optional searchable capability, not an admission requirement.

The existing dark, responsive Leaflet / OpenStreetMap site remains a static GitHub Pages site. `index.html` loads `data.js` and `app.js`; the app asynchronously requests **`./studios.json`**. There is no embedded database or fallback snapshot. HTTP failures, invalid JSON and invalid records show an explicit error with retry and disable data actions. The map and studio list have separate failure handling.

## v0.7 research batch 1

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
| `legacy_research` | Migration provenance only; original v0.5 claims, dates and replaced pin/address values, not current confidence |

Do not derive company identity from a display name or website: multiple locations may share both. Preserve existing IDs when correcting records. A new location of an existing company gets a new `id` and the same `company_id`. The JSON remains denormalised for a simple static site; a separate company table/backend is not required. `schema.sql` is an older, unused database design sketch, not the v0.6 runtime schema. The archived `MotionX_Studio_Atlas_GitHub_Pages_v0.5/` directory is historical and is not loaded by the root website or tools.

## Research confidence and coordinate policy

Confidence applies to the **specific claim**, not the whole organisation's legal or operating status:

- **confirmed**: a researcher reviewed a dated source directly supporting that claim.
- **likely**: a dated source provides suggestive or indirect support; uncertainty remains.
- **unknown**: not researched, ambiguous, outdated or not yet rechecked. A URL alone is not confirmation.

Both `confirmed` and `likely` require a source URL and review date, at the location level and separately for each capability. Do not copy overall confidence to every capability. Missing/unknown capabilities do not exclude a studio. Keep source URLs and review dates; independently checking a website's presence does not establish current operation, registration, an address or a capability. Validation checks structure, not the truth or availability of external evidence.

The v0.5 seed was explicitly not independently re-verified. v0.6 therefore sets its current confidence and individual capability confidence to `unknown`, retaining legacy dates/source URLs and original labels under `legacy_research`. No new verification is claimed. `verified_on` on these records is a **legacy recorded review date**, labelled accordingly in profiles. These dates are preserved verbatim; the validator may flag them as future dates depending on the runner's date/timezone.

Use city-level approximate coordinates when a street address cannot be verified. The five legacy street-looking pins were replaced by approximate city reference points and the original values retained as provenance. Existing campus/city estimates remain approximate. Records with an unverified city retain their existing regional reference pins explicitly marked `unverified`; their actual city still needs research. Never infer an exact address from a pin. New `exact` records require an address, evidence and a date; a researcher must ensure that evidence actually supports the coordinates. The interface labels every non-exact pin as approximate.

## Research CSV and bulk import

Python **3.9+**, standard library only. Start a batch by copying **`data/research_template.csv`**, which contains headers only so examples cannot accidentally enter the public database. Use a CSV-aware editor or Python's `csv.DictWriter`.

- Retain all required headers. Unknown columns are rejected to help prevent accidental import of private research notes.
- `categories` and `capabilities` use `|` separators (for example, `VFX|Animation`). Empty capabilities are allowed.
- `capability_evidence` is a JSON object inside a CSV cell. For a capability `Animation`, a not-yet-reviewed value is `{"Animation":{"state":"unknown","evidence":"","verified_on":""}}`. Use `{}` when there are no capabilities. A CSV-aware writer handles the embedded quotes.
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

`CHROMIUM=/path/to/chromium` can select a browser. The browser suite uses live unpkg/OSM resources, so network outages can fail its tile check. It checks loading, map attribution/tiles, search, combined filters, profiles, totals, CSV export, mobile navigation, error/retry states, and 5,000 **in-memory synthetic test locations** with pagination. These fixtures never enter `studios.json`. Screenshots go to the system temporary directory. Pull requests run offline validation/tests in GitHub Actions; no deployment workflow is added.

## Limits and public-data safety

The client fetches and validates the whole JSON file; lists are paginated at 50 and markers use Leaflet's canvas renderer. This is a tested foundation for thousands of locations, not an unlimited dataset or a claim of performance on every phone. Server-side search, spatial tiling or clustering may become useful at larger scales. Search includes unknown capabilities; read confidence labels before relying on results. Duplicate detection does not prove identity, and offline validation does not verify sources or geocode addresses.

Only public directory data belongs here. Do **not** commit private CRM data, sales leads, outreach notes, client intelligence, tokens, keys or confidential/personal research. Check directory reuse rights and licences before importing third-party data. Use official public business sources and review contacts before publishing. v0.7 adds no private records or credentials.
