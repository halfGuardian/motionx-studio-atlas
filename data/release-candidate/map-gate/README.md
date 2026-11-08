# Final map and directory acceptance gate

Continues draft PR #19 from `29364389eb69f1da480a15b27b8c28f3bbba7923`. PR #15 (`efd52a86e66417438830aac285e3fffee3aa0fa0`) and #18 (`5c3c838f67eded5988a8f6dd8541582716becb15`) remain unchanged and unmerged.

**All 106 recorded city associations were individually audited. 102 receive separate approximate display references; four remain unpinned with specific reasons.** All 76 companies without a city remain unpinned. Every one of the 182 remains accessible through the same directory and profiles, including the map's direct unpinned-company control. No new company discovery, facility admission, coordinates in canonical records, capability promotion or source-wide permission is introduced.

The gate uses 69 reviewed city/country coordinate references: 68 facts projected unchanged from the hash-pinned GeoNames data distributed in `geonamescache==3.0.2`, plus one directly reviewed GeoNames populated-place entry for Gwacheon. This is permitted open-data redistribution, not an alternate route around source restrictions. The package was downloaded but no package code was installed/executed or added as an application dependency. The complete licensed raw city data stays outside the repository; only the 69 necessary factual projections, source IDs, country/admin context, source-record hashes and receipt are committed. `gazetteer-receipt.json` retains distribution URL/SHA, dataset SHA, actual retrieval date, GeoNames CC BY 4.0 evidence and MIT packaging attribution. The MIT notice and existing complete CC BY notice remain available.

Reviewed homonyms include Long Beach (California, not another US city), Palmas (Tocantins, not Parana), Garachico (Tenerife, not La Palma), Durban (not Durbanville), Shenzhen (Luohu/Guangdong metropolis), Nanning (not Qujing), broad London (not City of London), and Korean municipalities outside Seoul. No largest-city, nearest-city or country-capital rule assigns company points.

The four holds are DeltaRocket (Lyon/Villeurbanne), Ex Nihilo (city not corroborated), Ozone (Corona/state/registry uncertainty) and MenzilMekan (event/weak indexed city evidence). Full reasons and source links are in the machine audit and dashboard. The company data is unchanged even where geographic evidence is weak. The two withheld company proposals remain withheld.

The TAICCA common agency footer is expressly rejected as company evidence. Dottodot has an independently read company-specific Taipei contact; Go Go and Mangowork have explicit company descriptions. Ilya and Zero One use their own dated government-catalogue entries (2021/2022), with age and current-operation uncertainty retained. Adjacent-company addresses are not assigned to them. Image-in uses its company-specific Montreal contact, not Telefilm's footer. Interference Pattern uses Film Edinburgh's company-specific listing; an unexpected homepage redirect is disclosed and never treated as closure proof.

Cape Town/Golden Road and Lome/Mess Pictures are explicitly metropolitan/urban references (`precision: region`). Rascal is a registered-company city association. Historical and indexed evidence is labelled separately from readable current company assertions. These are source associations, never independent current-operation or physical-facility verification. No personal contacts, authored source descriptions or full street addresses are imported.

The original 42,478 full-record hashes, root database, search index, detail shards, gzip/baseline transports and source evidence remain unchanged. Only the display sidecar/manifest, scoped current review reports and interface controls change. `inputs/pr19-2936438` preserves the prior review reports, scope documents, manifest and all eight existing display points; the original parent research checkpoints remain protected. The eight prior points (including Floating Rock and ModelFarm's second city) plus 102 new ones make 110 display points across 109 company IDs. All 17 original geographic decisions, including ten staged cases, remain intact.

```sh
python tools/map_gate.py verify-gazetteer --wheel /path/to/geonamescache-3.0.2-py3-none-any.whl
python tools/map_gate.py check
python tools/release_candidate.py check
python tools/check_bulk_release.py
python tools/launch_readiness.py check --output data/release-candidate/reports/readiness
```

`prepare-draft` is an explicit unapproved display-only preparation command; repeated application is a no-op after integrity checks. It never fetches sources, approves claims, changes source records, merges or deploys. The complete source-to-release reproducer also includes this gate. Historical reports continue to use their frozen original cohorts; current map and release checks validate the full actual catalogue.

Search and filters combine with AND. `Supported company city reference` selects companies with reviewed display references. `Unpinned companies` selects company references with no supported display point. `No original coordinates` retains its broader meaning and includes both groups. Toggling diamond display changes rendering, not the evidence or which records qualify for the unpinned view. CSV keeps original null coordinates and places licensed display references in a separate field.

The complete static bundle now explicitly includes `atlas.css`; the final map browser suite verifies computed dark styling and mobile navigation against the actual packaged files. Both downloadable review/atlas artifacts remain draft review materials, not deployments. See [single owner decision](../OWNER-APPROVAL.md) and [validation](validation.md).
