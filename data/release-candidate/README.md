# Final map gate

**102 / 106 city-associated companies receive separate licensed references; four city holds and 76 without cities remain unpinned in the same searchable directory.** See the [single owner approval summary](OWNER-APPROVAL.md), [complete map audit](map-gate/reports/dashboard.html) and [executed validation](map-gate/validation.md). All 42,478 records remain unchanged. The following sections retain the original admission scope and historical checkpoint.

# Global integrated release candidate

This draft is stacked on PR #18 at `5c3c838f67eded5988a8f6dd8541582716becb15`, which depends on PR #15 at `efd52a86e66417438830aac285e3fffee3aa0fa0`. Both parent branches and all their research/data history remain unchanged.

The actual proposed directory contains **42,478 references**: all 42,296 parent records plus **182 new provisional Class C company references**. Normal results show 42,474 because four individually reviewed audio-only records remain available only in audit scope. There are 1,859 company references and 179 country/territory associations. Turkmenistan is newly represented by source-supported MenzilMekan Animation; this is not independent confirmation of an active physical facility. Retained source-reviewed locations/organisations stay 243/119; the 41,977 source identity keys are provisional/source identities, not verified operating organisations.

[Short maintainer decisions](DECISIONS.md) · [Admission dashboard](reports/dashboard.html) · [Exact fields and complete audit](reports/release-audit.json) · [Current scoped licensing](reports/readiness/licensing.html).

All **184** proposals were audited against the complete parent catalogue, other proposals, saved source evidence, country/city associations and exact limited factual scope. **Siung Film Productions** and **Ventura Interactive** are withheld because broad trade-directory audiovisual/sound/service taxonomy does not establish their specific visual-production relevance. This is neither an audio-only exclusion nor an automatic prohibition based on UNSPECIFIED source-wide rights. Both proposals and the reasons remain in the audit. The other 182 appear in the real search index, lazy detail shard, manifest, compact/gzip transport, filters and exports.

The original proposal set had 117 official-website and 67 source-listing references. The admitted subset has 113 official-website references and 69 source-listing references after correctly labelling three company-maintained LinkedIn profiles and a founder biography as evidence listings. Website ownership/liveness is not independently guaranteed. No company descriptions, images, contacts, proprietary directory payloads, budgets or purchasing intent are imported.

Public fields are limited to name, supported/source-associated country and city where available, official URL or labelled evidence listing, coarse source-supported categories, source URLs/dates, provisional identity and scoped attribution. Every record stays Class C with unknown current operation, null original coordinates, no confirmed capabilities, no inferred physical branch and no invented ownership. `license: UNSPECIFIED` preserves source-wide uncertainty; it neither grants all source rights nor automatically forbids minimal identifiers. The maintainer must judge the exact factual scope of this PR.

Taxonomy maps Animation production/Original animation production → Animation; Game cinematics → Cinematics; Film production → Film / Television Production; Immersive/Digital content production → Digital / Interactive Production. Other supported sectors remain unchanged. Rigging, storyboards, art direction and character design remain original source labels rather than being inferred as confirmed technical services. All original labels are retained in `source_category`, the admission audit and CSV. Games qualify without capture; generic production remains commercially plausible only.

Seven of the 17 geographic payloads prepare separate attributed GeoNames city-reference points, across six existing companies. They cover Bad Clay, Scrawl, Robot Playground, ModelFarm (Adelaide and Brisbane), Blue Zoo and Lupus Films. Ten missing-coordinate/correction/facility questions remain staged. The existing Floating Rock Wellington reference and Frame Machine Santa Monica point remain intact. ModelFarm's two display points retain one company identity and its original null coordinates/Adelaide field; city search, profile and CSV distinguish the additional Brisbane reference. A city centroid is not a studio entrance or proof of a second production facility.

The 381 unresolved research cases, 55 geography/facility keys, seven office/department investigations, 238 unreviewed city associations and partial/restricted source directories remain in their original maintenance queues. They do not block unrelated eligible references. The original 30 proposals, all 725 keys/753 observations and previous source checkpoints remain unchanged.

## Reproducible draft preparation

`python tools/release_candidate.py prepare-draft` only accepts a fresh exact PR #18 parent public dataset and refuses repeated application. The sole mutation path deliberately leaves `human_approved:false` and `publication_approved:false`. It cannot fetch, merge, deploy, grant a licence or promote a facility. Preparing the unmerged draft is authorised by this task; actual publication requires a maintainer's review and authorised merge of the exact candidate.

```sh
python tools/release_candidate.py check
python tools/check_bulk_release.py
python tools/launch_readiness.py check --output data/release-candidate/reports/readiness
python tools/package_release_candidate.py --output /tmp/motionx-release-atlas-fresh
python -m http.server --directory /tmp/motionx-release-atlas-fresh 8000
```

Open `http://localhost:8000/` for the actual integrated atlas. The complete static artifact includes all original data, compressed and fallback transports, licence notices, public app assets and review documents. The smaller decisions artifact is for evidence/field review; its profile links require the complete artifact or matching checkout. Neither is a deployment.

Historical tools explicitly use the hash-bound PR #18 cohort in `catalogue_history.py` to reproduce their original reports. Current release validation and the public application always load all 42,478 records. Original records, shards and research documents are checked byte-for-byte/hash-for-hash; historical index/manifest/sidecar copies preserve parent output. Current index, shard, gzip sidecars, licensing and geographic metadata are independently checked against the actual integrated dataset. This is not an exemption from current-data validation.

Human review is a GitHub review/authorised merge, not a generated reviewer field or an AI-filled approval bundle. Required-review enforcement remains unconfirmed. No source collector is enabled and no Pages setting is changed. Review the [merge prerequisites and operational limits](DECISIONS.md) before any merge.
