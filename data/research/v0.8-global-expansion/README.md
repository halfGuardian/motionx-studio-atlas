# v0.8 — Global Studio Expansion: research and release report

Reviewed **6 November 2026 (Pacific/Auckland)** against official location pages, current careers pages, group rosters and dated primary announcements. The baseline is main commit `5b5d94cb3153ab19564855d810ba93eda647d4d7`. This is public directory research, not an independent physical-site inspection or legal/operational audit. “Confirmed” means the cited source directly supports the specific claim at that location. A source's existence alone is insufficient.

## Results

- **98 imported locations**, **47 new operating organisations**, **26 countries** in this batch.
- Directory after import: **129 locations / 66 operating organisations / 28 countries**. Parent groups are relationships, not extra operating-organisation totals.
- **6 individually source-supported capture facilities**; no claim of independent site inspection. All specialist claims have separate dated evidence.
- All original 31 records, identities and coordinates are unchanged, checked against the baseline digest in `evidence.json`.
- **41 deferred candidates**, **14 rejected candidates**, **14 already-present checks** are retained with individual sources/reasons in [review-queue.json](review-queue.json). These are research decisions, not 69 additional studios.
- Canonical validation: **0 errors / 147 warnings** (129 approximate coordinate references and 18 legacy unknown-evidence records). The new batch has 98 approximate-coordinate warnings and no errors. Warnings are disclosed, not suppressed.

The imported operating identities and cities are listed below. Marketed “Los Angeles”/“Vancouver” labels are retained in names or caveats where the supported municipality is Culver City, West Hollywood or Burnaby. Imaginarium's Pinewood stage and SIDE stage remain distinct physical facilities; a registered office is not a capture stage.

| Operating organisation ID | New locations | Municipalities |
| --- | ---: | --- |
| `dneg` | 19 | London, Vancouver, Mumbai, West Hollywood, Chennai, Montréal, Mohali, Bengaluru, Toronto, Sydney, Barcelona, Budapest, Sofia, Pune, Kolkata, Thiruvananthapuram, Hyderabad, Patna, Benaulim |
| `cinesite` | 3 | London, Montréal, Vancouver |
| `latelier-animation` | 1 | Montréal |
| `assemblage` | 2 | Mumbai, Bengaluru |
| `fx3x` | 2 | Skopje, Belgrade |
| `image-engine` | 1 | Vancouver |
| `squeeze` | 2 | Montréal, Québec |
| `trixter` | 2 | Munich, Berlin |
| `imaginarium` | 2 | Iver Heath, London |
| `the-mill` | 4 | Paris, London, Liège, Bengaluru |
| `sony-imageworks` | 3 | Vancouver, Montréal, Los Angeles |
| `digital-domain` | 5 | Culver City, Vancouver, Montréal, Hyderabad, Shanghai |
| `eyeline` | 5 | Los Angeles, Vancouver, Seoul, London, Hyderabad |
| `weta-fx` | 2 | Vancouver, Melbourne |
| `criterion-games` | 1 | Guildford |
| `dice` | 1 | Stockholm |
| `motive` | 1 | Montréal |
| `respawn` | 2 | Los Angeles, Madison |
| `ripple-effect` | 1 | Marina del Rey |
| `ea-sports` | 4 | Orlando, Bucharest, Madrid, Burnaby |
| `metalhead` | 1 | Victoria |
| `codemasters` | 3 | Southam, Birmingham, Kuala Lumpur |
| `ea-korea` | 1 | Seoul |
| `ea-sports-fc-mobile` | 1 | Shanghai |
| `blackhouse` | 1 | São Paulo |
| `xr-africa` | 1 | Cape Town |
| `ubisoft-montreal` | 1 | Montréal |
| `ubisoft-quebec-city` | 1 | Québec |
| `ubisoft-saguenay` | 1 | Saguenay |
| `ubisoft-sherbrooke` | 1 | Sherbrooke |
| `ubisoft-sofia` | 1 | Sofia |
| `ubisoft-singapore` | 1 | Singapore |
| `ubisoft-redlynx` | 1 | Helsinki |
| `ubisoft-abu-dhabi` | 1 | Abu Dhabi |
| `ubisoft-da-nang` | 1 | Da Nang |
| `ubisoft-chengdu` | 1 | Chengdu |
| `ubisoft-shanghai` | 1 | Shanghai |
| `ubisoft-berlin` | 1 | Berlin |
| `ubisoft-dusseldorf` | 1 | Düsseldorf |
| `ubisoft-mainz` | 1 | Mainz |
| `ubisoft-bucharest` | 1 | Bucharest |
| `ubisoft-craiova` | 1 | Craiova |
| `ubisoft-kyiv` | 1 | Kyiv |
| `ubisoft-odesa` | 1 | Odesa |
| `ubisoft-bordeaux` | 1 | Bordeaux |
| `cd-projekt-red` | 5 | Warsaw, Kraków, Wrocław, Burnaby, Boston |
| `remedy` | 2 | Espoo, Stockholm |
| `metricminds` | 1 | Frankfurt am Main |

## Evidence and capability decisions

The [per-location manifest](evidence.json) links every imported ID to location sources, reviewed claims, per-capability evidence, coordinate provenance, relationship evidence and duplicate review. The CSV is the actual importer input, not an illustrative list. New public contact fields are blank. No personal contacts or private commercial intelligence are included.

| Facility | Source-supported capabilities | Location evidence |
| --- | --- | --- |
| Imaginarium Studios — Pinewood N Stage — Iver Heath | Motion Capture, Performance Capture, Facial Capture, Virtual Production | [Official evidence](https://www.imaginariumstudios.co.uk/locations) |
| Imaginarium Studios — SIDE Studio 1 — London | Motion Capture, Performance Capture, Facial Capture | [Official evidence](https://www.imaginariumstudios.co.uk/locations) |
| EA SPORTS — EA Vancouver campus — Burnaby | Game Development, Motion Capture | [Official evidence](https://careers.ea.com/ea-studios/ea-sports/job-opportunities) |
| BlackHouse — São Paulo | Motion Capture, Facial Capture, Retargeting, Motion Editing | [Official evidence](https://www.blackhouse.com.br/work-1) |
| XR Africa — Cape Town | Virtual Production, Motion Capture, Previsualization, VFX | [Official evidence](https://hapogroup.co.za/companies/xr-africa) |
| metricminds — Frankfurt am Main | Motion Capture, Performance Capture, Facial Capture, Animation, Cinematics | [Official evidence](https://metricminds.com/performance-capture/) |

Capture details are deliberately narrow. EA's Burnaby campus explicitly has a motion-capture lab; this does not establish capture at other EA studios. Imaginarium's Pinewood LED volume is available on request, not asserted as a permanent installation. SIDE Studio 1 has its own capture evidence. BlackHouse explicitly offers capture plus motion editing/retargeting. XR Africa's Cape Town facility supports virtual production, capture and previs. metricminds documents its Frankfurt capture volume and facial/body/voice service. VFX, animation or game development elsewhere does not imply any capture, previs or virtual-production capability.

### Coverage and identity changes

- **DNEG:** all 19 branches in the current official roster are represented; local pages support VFX, with animation added only where locally explicit. Los Angeles is labelled a production office; Toronto has no invented street address.
- **Cinesite group:** current group roster covered with Cinesite, L’Atelier Animation, Assemblage, FX3X, Image Engine, Squeeze, TRIXTER and Imaginarium. Each keeps its operating identity. `group_member` expresses sourced affiliation without inventing legal ownership percentages. Assemblage Bengaluru is supported by the current parent roster despite incomplete own-contact coverage.
- **MPC / The Mill:** the official 2026 unified-brand announcement and current four-location Mill contact roster govern imports. Historical MPC addresses are not republished as separately active facilities.
- **Sony Pictures Imageworks:** current Vancouver, Montréal and Los Angeles branches represented; Los Angeles is a production office. **Digital Domain:** five production sites imported; London “Coming Soon” excluded and Hong Kong's corporate/R&D/site ambiguity deferred.
- **Scanline / Eyeline:** current Netflix announcement identifies five global Eyeline sites and the India move to Hyderabad. Use present operating identity with the former name searchable. Historical Munich, Stuttgart and Montréal claims conflict with that newer roster and remain deferred; Mumbai is not duplicated as a current site. Corporate VP language does not prove VP at every branch.
- **Wētā FX / ILM / Framestore:** added Wētā Vancouver and Melbourne creative hubs; existing Wellington, five ILM and seven Framestore records checked and retained rather than duplicated.
- **Ubisoft:** 19 new individually supported studio identities plus the existing Toronto record. Current rosters contain stale or ambiguous entries. Known closure/ramp-down announcements override historical location pages. Remaining branches, including uncertain physical-site versus corporate/support/mobile-team distinctions, are explicitly queued. **This is partial Ubisoft coverage, not a complete worldwide roster.**
- **EA:** current named studio/campus evidence supports the imported branches. Generic older location lists conflict with more recent studio-specific pages and closure announcements, including BioWare Edmonton and Codemasters Runcorn. Unresolved subsidiaries, internal teams and physical-site scopes are queued. **EA coverage is partial.** A shared campus is not split into invented facilities for each internal team.
- **Other developers:** current CD PROJEKT RED jobs give five actual cities/addresses; Remedy supports Espoo and Stockholm. Larian's inaccessible/insufficient source coverage remains deferred.

Potential duplicate candidates were reviewed against the original database and within the batch. Squeeze's initial same-city/parent-domain match against Cinesite was resolved by using its actual operating website and distinct supported identity. No blanket duplicate override, silent update, merge or deletion was used. Distinct facilities retain their IDs even when city coordinates coincide.

### Geography and remaining research

New locations span Australia, Belgium, Brazil, Bulgaria, Canada, China, Finland, France, Germany, Hungary, India, Malaysia, North Macedonia, Poland, Romania, Serbia, Singapore, South Africa, South Korea, Spain, Sweden, Ukraine, United Arab Emirates, United Kingdom, United States, Vietnam. Existing New Zealand and other baseline countries are retained. North America, South America, Europe/UK, Asia/India, Australia, Africa and the Middle East have sourced additions; distribution was not used as an acceptance criterion.

Further work is needed especially outside São Paulo in South America, outside Cape Town in Africa, and outside Abu Dhabi in the Middle East; New Zealand specialist branches and additional small independent facilities also need deeper research. Complete the queued Ubisoft/EA branch work before claiming comprehensive group coverage. The queue preserves uncertainties and sources; rejection here means unsuitable evidence for this release, not a universal claim that an organisation cannot operate elsewhere.

## Coordinates and attribution

All new coordinates are explicitly **approximate city/settlement references**, not facility entrances or verified street-level geocodes. `coordinate_source` and [city-references.json](city-references.json) preserve provenance. No original coordinates are moved and no pin jitter is used. Shared-coordinate popups list every filtered matching studio with native keyboard-selectable buttons that open existing profiles.

City references use [GeoNames](https://www.geonames.org/) under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), copied as reference points without transformation; this implies no endorsement. Iver Heath uses the [ONS settlement reference via Planning Data](https://www.planning.data.gov.uk/entity/2504906), under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). These attributions also appear on the website. Leaflet and OpenStreetMap attribution remain intact.

## Reproducible pipeline and reports

- [batch.csv](batch.csv): 98 public source-reviewed records, with stable location and organisation IDs.
- [batch-validation.json](batch-validation.json): schema validation before import.
- [import-preview.json](import-preview.json): 98 new, 0 unresolved potential duplicates, 0 rejected rows, no write.
- [import-result.json](import-result.json): 98 appended; existing records unchanged.
- [import-repeat.json](import-repeat.json): 98 unchanged, 0 new, no write. Repeated imports are idempotent.
- [summary.json](summary.json): machine-readable release counts and test results.

From the repository root, validate and replay safely against a copy (the committed canonical database already includes the batch):

```sh
python tools/validate.py data/research/v0.8-global-expansion/batch.csv
python tools/import_csv.py data/research/v0.8-global-expansion/batch.csv --dry-run --report /tmp/v08-preview.json
python tools/import_csv.py data/research/v0.8-global-expansion/batch.csv --apply --report /tmp/v08-repeat.json
python tools/validate.py studios.json --report data/validation_report.json
```

Optional backwards-compatible fields are `location_type`, `coordinate_source`, and `relationships` (a JSON array in CSV). Relationships have stable ID, public name, kind, source URL and review date; allowed kinds distinguish subsidiary ownership, group membership and partnerships. Legacy rows without these fields remain valid. Search includes relationship names, profiles show provenance and site type, and CSV export retains the optional metadata. These changes do not reclassify old records.

## QA and operational limits

**38 Python tests, 18 JavaScript tests and 14 HTTP browser checks passed.** Tests cover optional metadata, original-record preservation, manifest consistency, CSV round-trip, batch preview/apply/repeat, duplicate rejection, shared-coordinate selection and keyboard profile navigation. HTTP checks use a repository subpath and live Leaflet/OSM tiles; search, country/capability filters, counts, profiles, export, retry/error states and 390px mobile navigation pass.

The Chromium smoke test loads **10,000 in-memory synthetic locations with 10,000 distinct coordinate markers**; load/paginate/filter completed in **1.942 seconds on this runner**. Only 50 list rows render per page and markers use Leaflet canvas. A separate JavaScript grouping fixture includes coincident coordinates without changing source geometry. Synthetic records never enter the public database. Existing shared-coordinate selection is preserved. No clustering or extra mapping service was required for this test.

This timing is a reproducible smoke-test observation, not a guarantee for every phone or network. The client still fetches/validates the complete JSON and builds all markers. Larger datasets, slow devices or denser real-world distributions may justify viewport rendering or clustering later. Browser checks require live external resources; offline tests do not validate remote source truth or availability. No paid mapping API, backend, token, deployment or Pages-setting change is introduced. Historical v0.7 reports are preserved as audit snapshots rather than rewritten to today's validation date.
