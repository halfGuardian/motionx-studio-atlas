# v0.7 — Global Research Expansion, Batch 1

Reviewed **6 November 2026 (Pacific/Auckland)** against the v0.6 database merged at `4d29470`. Each requested city was checked separately on official company pages. This is a review of specific published claims, not a site visit, registration check or independent audit of current operation. Descriptions below are short factual research notes; no source page content or images are republished.

## Outcome and identities

**13 locations imported, 3 new organisations; canonical total: 31 locations / 19 organisations.** All original 18 records remain unchanged. None of the candidates matched an existing location ID, organisation ID, normalised company/name+city pair, or website+city pair. The importer also checked within the batch. No duplicate overrides were needed, no records were rejected and no requested location was deferred. Specialist claims and facility-level coordinates were deferred where evidence was insufficient.

| Organisation ID | New location IDs | Count |
| --- | --- | ---: |
| `weta-fx` | `weta-fx-wellington` | 1 |
| `ilm` | `ilm-san-francisco`, `ilm-vancouver`, `ilm-london`, `ilm-sydney`, `ilm-mumbai` | 5 |
| `framestore` | `framestore-london`, `framestore-montreal`, `framestore-chicago`, `framestore-los-angeles`, `framestore-new-york`, `framestore-mumbai`, `framestore-melbourne` | 7 |

Location and company IDs stay distinct. New locations share their organisation's stable ID; names, co-located city pins and shared domains do not collapse them into a single location. Existing companies in the same cities remain separate.

## Per-location primary-source decisions

Every imported row is `confirmed` for the **official city listing**, with a dated source for each asserted capability. Sector labels below are deliberately narrower than each company's worldwide offering. Capability lists repeat these supported labels so each classification has an explicit evidence record.

| Location | Imported classifications | Official evidence reviewed |
| --- | --- | --- |
| Wētā FX — Wellington, New Zealand | VFX, Animation | [About](https://www.wetafx.co.nz/about) identifies Wellington headquarters and VFX/animation activity; [home page](https://www.wetafx.co.nz/) also supplies the New Zealand physical contact. |
| ILM — San Francisco, United States | VFX | [Locations, San Francisco entry](https://www.ilm.com/locations/) describes the effects facility; [city archive](https://www.ilm.com/locations/san-francisco/) was also reviewed. |
| ILM — Vancouver, Canada | VFX | [Locations, Vancouver entry](https://www.ilm.com/locations/) identifies local VFX work and the 2025 move to The Stack; [city archive](https://www.ilm.com/locations/vancouver/) corroborates the listing. |
| ILM — London, United Kingdom | VFX | [Locations, London entry](https://www.ilm.com/locations/) identifies the studio and local projects; [city archive](https://www.ilm.com/locations/london/) was also reviewed. |
| ILM — Sydney, Australia | VFX | [Locations, Sydney entry](https://www.ilm.com/locations/) explicitly describes local VFX services; [city archive](https://www.ilm.com/locations/sydney/) was also reviewed. |
| ILM — Mumbai, India | VFX, Animation | [Locations, Mumbai entry](https://www.ilm.com/locations/) explicitly identifies both disciplines; [city archive](https://www.ilm.com/locations/mumbai/) was also reviewed. |
| Framestore — London, United Kingdom | VFX, Previsualization | [Contact, London entry](https://www.framestore.com/contact) and [studio description](https://www.framestore.com/our-studios) establish the location. [Loki Season 2](https://www.framestore.com/work/loki-season-2) identifies London VFX teams; [Foundation Season 2](https://www.framestore.com/work/foundation-season-2) specifically locates the pre-production team in London. |
| Framestore — Montréal, Canada | VFX | [Contact, Montréal entry](https://www.framestore.com/contact) and [studio description](https://www.framestore.com/our-studios) establish the location; [Foundation Season 2](https://www.framestore.com/work/foundation-season-2) specifically identifies Montréal VFX work. |
| Framestore — Chicago, United States | VFX | [Contact, Chicago entry](https://www.framestore.com/contact) and [studio description](https://www.framestore.com/our-studios) establish the location; [Advertising Services](https://www.framestore.com/advertising/services) names Chicago among its team bases and describes the VFX pipeline. |
| Framestore — Los Angeles, United States | VFX | [Contact, Los Angeles entry](https://www.framestore.com/contact), [studio description](https://www.framestore.com/our-studios) and [Advertising Services](https://www.framestore.com/advertising/services) establish the published studio label and VFX team. See the Santa Monica uncertainty below. |
| Framestore — New York, United States | VFX | [Contact, New York entry](https://www.framestore.com/contact), [studio description](https://www.framestore.com/our-studios) and [Advertising Services](https://www.framestore.com/advertising/services) identify this location and its VFX team. |
| Framestore — Mumbai, India | VFX, Animation | [Contact, Mumbai entry](https://www.framestore.com/contact) establishes the location. [Foundation Season 2](https://www.framestore.com/work/foundation-season-2) identifies VFX work; [Our Studios, Mumbai section](https://www.framestore.com/our-studios) explicitly includes animation. |
| Framestore — Melbourne, Australia | VFX | [Contact, Melbourne entry](https://www.framestore.com/contact) and [studio description](https://www.framestore.com/our-studios) establish the location; [Furiosa](https://www.framestore.com/work/furiosa) identifies the local VFX pipeline. |

## Coordinate evidence and attribution

All new records use `coordinate_precision: city`. No exact studio geocode was independently substantiated. An official postal/contact address does not establish a latitude/longitude. The `address` field therefore explicitly says that the pin is an approximate city reference, not a studio street address. Official company sources establish the studio's city; the following gazetteer records supply **WGS84 city reference coordinates** only. References were read on the same review date, copied without rounding/transformation, and individually mapped to location IDs in `evidence.json`.

City reference data © [GeoNames](https://www.geonames.org/), used under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); [source/licensing and datum information](https://www.geonames.org/about.html). Attribution is also displayed in the directory. GeoNames does not verify the studio locations or endorse this directory.

| City reference | Latitude | Longitude | GeoNames evidence |
| --- | ---: | ---: | --- |
| Wellington | -41.28664 | 174.77557 | [2179537](https://www.geonames.org/2179537/wellington.html) |
| San Francisco | 37.77493 | -122.41942 | [5391959](https://www.geonames.org/5391959/san-francisco.html) |
| Vancouver | 49.24966 | -123.11934 | [6173331](https://www.geonames.org/6173331/vancouver.html) |
| London | 51.50853 | -0.12574 | [2643743](https://www.geonames.org/2643743/london.html) |
| Sydney | -33.86785 | 151.20732 | [2147714](https://www.geonames.org/2147714/sydney.html) |
| Mumbai | 19.07283 | 72.88261 | [1275339](https://www.geonames.org/1275339/mumbai.html) |
| Montréal | 45.50884 | -73.58781 | [6077243](https://www.geonames.org/6077243/montreal.html) |
| Chicago | 41.85003 | -87.65005 | [4887398](https://www.geonames.org/4887398/chicago.html) |
| Los Angeles | 34.05223 | -118.24368 | [5368361](https://www.geonames.org/5368361/los-angeles.html) |
| New York | 40.71427 | -74.00597 | [5128581](https://www.geonames.org/5128581/new-york-city.html) |
| Melbourne | -37.81400 | 144.96332 | [2158177](https://www.geonames.org/2158177/melbourne.html) |

## Unresolved and intentionally omitted claims

- **Capture services:** no motion-capture or performance-capture claims are added. General service menus and staff titles are insufficient to locate an on-site capture facility. Omission means not established in this batch, not that a company lacks the capability.
- **Virtual production and games:** no location-specific assertions are made here. Network services or a game engine do not establish a local game-development studio, LED volume or virtual-production stage.
- **Animation outside the explicitly listed locations:** not propagated from group-level credits to every office. Previs is attributed only to Framestore London, where the source identifies the local team.
- **Framestore Los Angeles:** the contact page labels the office Los Angeles, while the studio narrative describes a Santa Monica team. The record retains the requested official Los Angeles label, flags the discrepancy in its visible status, and uses only a Los Angeles city/market reference. Municipality, postal details and the exact office position remain unresolved; the pin is not placed at a guessed Santa Monica address.
- **Changing addresses:** ILM Vancouver's move is noted without reusing an older street address. Existing listed addresses for other offices were not converted to invented exact geocodes. New email and phone fields are blank: no unnecessary contacts collected.
- **Scope:** Wētā FX's other hubs and specialist facilities associated with these organisations were not added. This batch covers only the 13 requested city candidates.
- **Source limits:** official published claims can become stale. Old project pages corroborate capabilities, not current capacity or availability. Legal registration, current trading status and facility capacity require separate research.

## Import audit and validation

The importer was used unchanged from v0.6. Artifacts:

- `batch.csv`: 13 researched rows, written with the standard-library CSV writer.
- `evidence.json`: per-location duplicate checks, primary sources, capability sources, dates, city-coordinate sources and uncertainties.
- `batch-validation.json`: 13 rows / 3 organisations, zero errors, 43 warnings at run time.
- `import-preview.json`: dry-run against the original 18-record database; 13 proposed records, no duplicates/rejections, `written: false`.
- `import-result.json`: successful apply; 13 new IDs, no duplicates/rejections, `written: true`.
- `import-repeat.json`: second apply; 13 unchanged IDs, no new records, `written: false`. The database was not rewritten.
- `../../validation_report.json`: canonical 31 locations / 19 organisations, zero errors, **97 warnings** at run time.

Warning breakdown: **31 approximate-coordinate warnings**, **18 legacy/unreviewed-evidence warnings**, and **48 future-date warnings**. Of the 97, 54 already applied to the v0.6 seed and 43 accompany the new batch. The runner's UTC calendar was still 5 November while the actual review date in Pacific/Auckland was 6 November: 31 record-level dates and 17 new capability dates are consequently flagged by the unchanged date validator. These are intentional timezone warnings, not backdated or invented reviews; keep the actual review dates. On later days the future-date warnings disappear. The approximate-coordinate and legacy-evidence warnings remain actionable limitations.

Reproduce the preview against the pre-import database:

```sh
git show 4d29470:studios.json > /tmp/motionx-v06.json
python tools/import_csv.py data/research/v0.7-batch-1/batch.csv --database /tmp/motionx-v06.json --dry-run
```

Recheck the current database and repeat-import safety:

```sh
python tools/validate.py studios.json
python tools/import_csv.py data/research/v0.7-batch-1/batch.csv --dry-run
python -m unittest discover -s tests -p 'test_*.py' -v
node tests/data.test.js
python tests/browser_smoke.py
```

## QA results

- **28 Python tests passed**: validation, importer conflicts/deduplication, schema failures, exact batch-to-database equality, replay from the preserved seed and repeat-import idempotency.
- **13 JavaScript tests passed**: HTTP loading/failure paths, schema validation, VFX-only inclusion, new organisation grouping and combined filters.
- **12 Chromium browser checks passed** over HTTP below the repository subpath: live Leaflet/OpenStreetMap tiles and attribution, search, filters, counts, legacy/new profiles, CSV download, mobile navigation, error/retry paths and 5,000 in-memory synthetic records. No synthetic fixtures were imported.
- Canonical validation: **31 locations / 19 organisations, zero errors, 97 warnings** at run time (breakdown above).
- `git diff --check` passed.

Only public directory facts and source links are included; no private MotionX CRM, sales or outreach data is collected. No merge, deployment or production hosting change is part of this batch.
