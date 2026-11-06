# v0.9.3 — Global Discovery & Research Automation

This is a **proposed GitHub-native human-review release**, not an approved discovery bundle. Review date: **2026-11-06**. Codex assembled the research; no historical approvals, human reviewer names or approval hashes have been manufactured. The maintainer must review the exact PR and manually authorise merge. No merge, deployment or Pages-setting changes are performed.

## Proposed data

**41 new locations / 11 new operating organisations**, spanning **14 countries** in this batch. Proposed canonical totals: **182 locations / 88 operating organisations / 32 countries**, up from 141 / 77 / 30. Colombia and Ireland are new countries. Counts use operating organisation IDs; parent/group metadata does not add phantom operators.

| Operating organisation | New locations | Scope and evidence |
| --- | ---: | --- |
| Larian Studios | 7 | Ghent, Barcelona, Dublin, Guildford, Kuala Lumpur, Québec City, Warsaw; individual official branch pages plus current careers roster |
| RISE Visual Effects Studios | 5 | Berlin, Cologne, London, Munich, Stuttgart; five individual current contact pages |
| Outpost VFX | 5 | Bournemouth, London, Montréal, Mumbai, Stuttgart; current official contacts and production context; October 2026 German opening announcement corroborates Stuttgart |
| Flying Bark Productions | 3 | Sydney, Burbank (marketed Los Angeles), Madrid; official three-studio production page and sourced Studio 100 ownership |
| Triggerfish Animation | 2 | Cape Town and Galway physical bases, explicitly distinguished from worldwide remote staff |
| FOLKS | 9 | Montréal, Toronto, Bogotá, Saguenay, Mumbai, Burbank (marketed Los Angeles), New York, Atlanta, Vancouver; London remains Upcoming and is deferred |
| Chocolate Tribe | 2 | Johannesburg and Cape Town; current contact roster plus production/relocation announcement |
| Rising Sun Pictures | 2 | Adelaide and Brisbane; current parent roster and Ausfilm production evidence for both sites |
| El Ranchito | 2 | Madrid and Barcelona; current operator studio statement/contact pages and Pitch Black relationship |
| Annapurna Studios | 2 | Distinct A&M MoCap Lab and ANR virtual-production stage at Hyderabad campus; separate official facility pages and Qube corroboration |
| Ubisoft Reflections | 1 | Newcastle upon Tyne; current official branch and UK studio pages |
| Massive Entertainment | 1 | Stockholm; official current studio/contact pages; retains existing Massive organisation identity alongside Malmö |

There are 12 operating organisations in the batch; Massive already exists, so 11 are new. [records.json](records.json) includes these 41 additions and the explicitly updated existing Centroid Riverside record. [evidence.json](evidence.json) binds every exact record hash to its location/capability sources, review date, parent relationships and coordinate reference. Production sectors are supported independently from specialised capture claims. Source support is not independent confirmation of current registration or business operation.

**Two newly added locations have individual motion-capture evidence**: Larian Kuala Lumpur (on-site mocap studio on its branch page) and A&M MoCap Lab (body, facial, performance capture and retargeting on its facility page). **One additional new facility has virtual-production evidence**, the separate ANR LED stage. No facial/performance/volumetric/retargeting services are copied to other game/VFX branches. Larian Dublin and Guildford have explicitly described cinematics teams.

## Existing data, municipalities and coordinates

All **141 original IDs** remain. Only `centroid-uxbridge` changes: official Riverside facilities/contact evidence supports body, face and full-performance capture. Unsupported generic retargeting, motion-editing, animation and previs claims are removed pending research; the complete old row is retained in [updates.json](updates.json), the manifest and proposal audit. Its coordinates and original legacy provenance are preserved. Molinare and Serbia do not inherit this evidence. Sixteen legacy locations still have unknown evidence and remain visibly labelled.

All 41 new pins are **approximate city references**, never asserted facility geocodes. [city-references.json](city-references.json) retains attributed GeoNames points (CC BY 4.0). New points were inspected on GeoNames; previously researched city references are reused with their evidence. Marketed Los Angeles sites are recorded in **Burbank**; Chicoutimi remains a Saguenay district, not a duplicate city branch. No pins are offset to avoid overlap.

## Imports and publication boundaries

[batch.csv](batch.csv) contains additions only. [dry-run-initial.json](dry-run-initial.json) correctly blocks the ANR stage as a potential duplicate of A&M in the same city/website. [dry-run-reviewed.json](dry-run-reviewed.json) records the explicit distinct-facility rationale; [apply.json](apply.json) records 41 additions on an **isolated baseline copy**, and [repeat-import.json](repeat-import.json) records **zero additions / 41 unchanged**. No existing row is silently overwritten by the CSV importer. The separate exact-hash correction is staged through `research.py stage-pr`; [proposal-audit.json](proposal-audit.json) retains all before/after records and pending human-review state. The canonical change exists only on the unmerged PR branch.

Reproduce using a copy of the exact v0.9.2 database, not the already-expanded current JSON:

```sh
python tools/import_csv.py data/research/v0.9.3-global/batch.csv --database /tmp/baseline.json --dry-run --allow-distinct-location annapurna-anr-vp-hyderabad
python tools/import_csv.py data/research/v0.9.3-global/batch.csv --database /tmp/baseline.json --apply --allow-distinct-location annapurna-anr-vp-hyderabad
python tools/research.py stage-pr --database /tmp/original-v092.json --records data/research/v0.9.3-global/records.json --manifest data/research/v0.9.3-global/evidence.json --allow-distinct-location annapurna-anr-vp-hyderabad --output /tmp/staged-proposal
```

Freshness checks intentionally block old/future research or a changed baseline. For a later release, re-research and create a new manifest rather than reusing historical hashes. The old approval-bundle workflow remains unchanged and separate; its pending approvals stay pending. This release uses human PR review/manual merge instead of requiring manual JSON approval edits.

## Discovery, source access and research dashboard

The registry grows from six to **25 official entries**. **Nine** are enabled for scoped metadata after review; **16** remain disabled. This release does **not** claim 15–25 active collectors: inaccessible/restrictive policies take precedence over the target. [source-policy-initial.json](source-policy-initial.json) and [source-policy-second.json](source-policy-second.json) retain real Actions policy checks, hashes and failed initial URL guesses. Later checks/results are retained alongside these, not substituted for failed runs.

EA remains prohibited. Cinesite's current Terms of Use explicitly prohibit automated collection and text/data mining, so its former collector is disabled too. Its old observations are retained. Reel FX and Digital Domain have reuse restrictions; Eyeline/access failures, JS-only Rodeo pages, unavailable terms and other uncertain policies remain disabled. No screenshot/OCR, recursive crawl, login, hidden API or paywall workaround is used. Privacy-page keywords describe review leads only; neither robots permission nor lack of a keyword grants a licence. Source re-enablement requires a documented review and runtime robots checks still apply.

The initial successful PR refresh (run **42158704983**) retained **all 133 prior candidates** and produced **154 unverified candidates**. Seven of eight then-enabled sources yielded 43 observations: DNEG 19, metricminds 3, Remedy 2, Larian 6, RISE 5, Outpost 5, Flying Bark 3. Framestore was safely blocked on its noncanonical host. The source URL was corrected to its explicit www origin and Larian's separate Québec branch link was added. FOLKS was enabled after robots/policy review. The later run **42159808255** completed its policy audit but failed at baseline checkout before collection/report generation; checkout history was fixed rather than claiming a successful run.

[observations-42158704983.json](observations-42158704983.json) preserves exact job-log candidate objects; [queue.json](queue.json) is a documented projection combined with the unchanged 41-entry committed backlog. Full raw queues, reports and hash-addressed historical snapshots remain in the downloadable Actions artifacts. No discovered claim is approved or published. Historical artifacts expire after 90 days: archive them before expiry. The weekly workflow now stops on failed restoration instead of silently losing history. A maintainer must restore a reviewed archive/checkpoint if this happens.

Weekly/manual discovery now generates a self-contained **research-review dashboard** (`studio-research-review`). The PR job generates `global-research-review`, with company/country grouping, existing matches/reasons/confidence, evidence links, potential sectors/parents/capability claims, freshness and identity risks, unresolved questions, change alerts and authored before/after proposals. Download and open `review.html` locally. It is separate from the public directory and contains no active scripts or external assets. Individual source failures and changing/missing evidence cannot establish closure, relocation or changed capability.

## Deferred research and gaps

[review-queue.json](review-queue.json) adds **21 unresolved research topics** with URLs/reasons: FOLKS London, historical Outpost Los Angeles, six Rodeo branches, three Reel FX sites, three Zombie office/studio claims, three historical Glassworks sites with conflicting closure reporting, Centroid Molinare/Serbia, the mixed Ubisoft Paris-area roster and Barajoun Dubai. These are excluded from the publication batch without erasing history. The original **41 deferred backlog entries** remain unchanged, including topics now partly represented by this proposal; no automated approval/deletion is inferred.

Coverage improves in Latin America (Bogotá), Africa (three additional locations), Southeast Asia (Kuala Lumpur) and Oceania (three additional locations). Middle East coverage, remaining Ubisoft/EA facilities, independent capture providers, source access permissions and exact geocoding still need research. No geographic quota is used. Parent rosters are not independent corroboration, and historical announcements alone do not establish current operation.

## Validation and operational limits

Canonical validation: **0 errors / 201 warnings** — 182 approximate pins, 16 remaining unknown-evidence legacy records and three reviewed duplicate pairs. [validation.json](validation.json) retains every warning. No warning is hidden or suppressed.

Full local Python suite: **106 passed**; JavaScript suite: **22 passed**; HTTP Chromium suite: **17 checks passed**, including live Leaflet/OSM, attribution, mobile layout, profiles, filters, CSV, failure/retry states, real co-located facilities and keyboard selection. **20,000 synthetic locations** remain outside canonical data; the local load/pan/paginate/filter path took **3.405 seconds**, with 3,201 viewport markers at zoom 4 and a 50-record list page. The original shared-coordinate chooser is preserved. Timing is environment-specific, not a guarantee for every device.

The entire database is still fetched/validated client-side; markers scan coordinate groups on viewport changes. At much larger scales a spatial index, clustering or tiled data may be useful. Fixed-label adapters require maintenance for new city labels; page-change alerts expose redesigns/new content. Source terms may change and must be reviewed. Automated tests validate infrastructure and claim structure, not whether every company's claims remain current. GitHub-native review metadata cannot prove human intent; require repository review protections and a maintainer's personal approval/manual merge. No settings are changed here.
