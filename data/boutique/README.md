# Boutique discovery — v1.2 review proposal

Reviewed 7 November 2026. This release uses a **draft PR and a human-authorised merge**, not an approval JSON bundle. A score, test, source link, worksheet or generated reviewer name does not approve publication. Existing rule enforcement remains unconfirmed; no repository or Pages setting is changed.

## Actual coverage

All **41,735 previous research records**, all **243 retained location IDs** and every original evidence shard are preserved. `studios.json` remains byte-for-byte identical. The proposed combined atlas has **42,067 records**, not 42,067 verified studios:

| Measure | Result |
| --- | ---: |
| New provisional company references | 332 |
| New confirmed operating locations / verified capture claims | 0 / 0 |
| Retained source-reviewed Class A locations | 230 |
| Existing directory-listed Class B observations | 4,626 |
| Class C research records after extension | 37,211 |
| Geolocated records, original coordinates retained | 40,619 |
| Company-only references, without pins | 1,448 |
| Countries/territories in the full atlas | 178 |
| Retained operating organisations | 119 |
| All identity keys, including provisional source groupings | 41,648 |
| Provisional identity keys, not verified operating companies | 41,529 |

The source audit covers **570 observations**: **332 new reference keys**, **111 observations already represented** (matching **127 existing record IDs**, including multiple branches), **18 repeat observations**, **22 identity-review cases**, and **87 non-studio/insufficient-specialisation cases**. Observation totals and matched location IDs are different units; neither is a count of independently confirmed businesses. All observations, hashes, reasons and dates are retained in [triage.json](reports/triage.json). Duplicate observations are reconciled, not deleted from the audit. The NZFC row labelled Blockhead links to Assembly; that inconsistent name/domain pair is explicitly held for identity review and creates no public company reference.

The Boutique Studios view identifies **5,687 research records / 5,593 identity keys**. Of these, **460 records have additional source/association/company evidence**, while **5,227 are explicitly weak existing-taxonomy leads**. These are not 5,687 verified independent SMEs. The score is service alignment only: eight records score at least 40/100. External support needs, buying intent and independence remain unknown; source size estimates are not current headcounts.

## Source collection and permissions

| Source | Rows examined | New references | Access/reuse scope |
| --- | ---: | ---: | --- |
| European Animation Studios Directory, author-offered GitHub dataset | 424, complete | 235 | **CC BY 4.0** factual projection; pinned commit and licence review |
| Animation Ireland studios | 47, complete reviewed listing | 30 | Minimal factual references; no source-wide reuse grant or automated collector |
| NZ Film Commission facilities | 42, complete reviewed listing | 27 | Minimal factual service/name/domain references; automatic collection disabled |
| NZFC Annecy 2026 delegation | 17, complete reviewed listing | 8 | Event evidence only; not current physical-facility proof |
| Ausfilm member/event pages | 6, partial | 4 | Bounded reviewed factual references; no automated website collector |
| Regional indexed searches and official company pages | 34, partial | 28 | Primary service/geography claims; not a complete global collection |

The 424-row licensed snapshot contains 337 studio, 75 service and 12 support-organisation entries. Every row is processed, including rejection/review decisions. Services are not excluded just because they lack an “animation studio” label. Recognised stop-motion/motion-graphics assertions remain animation leads; generic “Mixed”/blank classifications and non-production organisations require further evidence. Directory statements can be outdated or wrong.

Source commit: `8178b6b5e6db6c5b6f25206359ec44037f6d11b3`. The dataset was generated **12 April 2026**, reviewed **7 November 2026**. [The author's README](https://github.com/tlahitte/animation-studios-directory/blob/8178b6b5e6db6c5b6f25206359ec44037f6d11b3/README.md) offers raw data and [the licence](https://github.com/tlahitte/animation-studios-directory/blob/8178b6b5e6db6c5b6f25206359ec44037f6d11b3/LICENSE) states CC BY 4.0. Credit **Tommy Lahitte and European Animation Studios Directory contributors**. Full [CC BY 4.0 text](../bulk/LICENSES/CC-BY-4.0.txt), per-record attribution and transformation notices accompany the data/export. Emails, authored project descriptions, photographs, TMDB assets and keys are omitted. Bare source domains become HTTPS navigation links without claiming those websites were fetched.

The website `animstudios.org` returned HTTP 530 and remains disabled for scraping. Its author's explicitly offered licensed GitHub dataset is a separately documented download, not a prohibited-page workaround. The pinned Git checkout was retrieved successfully; its 424-row factual projection was exactly reproduced offline. The new robots-aware HTTP downloader was also attempted live, but **failed at public DNS resolution before robots/data retrieval**. [collection-attempt.json](collection-attempt.json) preserves that failure. No end-to-end live downloader success is claimed. The manual read-only Actions workflow is provided for a maintainer to run after merge; it has not been dispatched here.

Screen Wellington and VFX Professionals Guild NZ were inspected. The former corroborates Floating Rock and exposes mixed creative/game-company showcase signals; the guild's personal-member directory is not ingested. Historical visits are not current-operation evidence. Animation UK's directory timed out. An Animetik/data.gouv.fr dataset documents Open Licence 2.0, but its official CSV download could not be retrieved here: **zero records acquired**. EA, Cinesite and other previously restricted sources remain disabled. No screenshots, hidden APIs, alternate-host restriction bypasses or recursive crawl are used.

**235 additions** use the CC BY projection; **97** are minimal factual official-page references with **UNSPECIFIED source-wide terms**. Those 97 do not acquire a reuse licence through publication. The old 1,116 game-company references retain their own unresolved terms and are counted separately in the licensing dashboard. Public accessibility and an intention to use a site internally do not change source permissions. Obtain permission before automated bulk reuse of unresolved sources.

## Golden examples, matching and recall

**Frame Machine already existed** as `overture-39fd34a0-9be1-4ac0-a46e-ebd53a1599ff`, Santa Monica. It is not a new business. Its source-listing URL had been stored where an official business website was unavailable. Matching now distinguishes a listing/evidence URL from a company's domain. [Official services](https://www.framemachine.tv/about-frame_machine/), [studio address](https://www.framemachine.tv/connect/) and [Fortnite real-time work](https://www.framemachine.tv/project/fortnite-live-events-reel/) support separate company-level animation, VFX, Unreal and cinematics research. Its original C record, coordinates and ID remain intact.

**Floating Rock Studio** is discovered from the complete NZFC collections, including the [facilities listing](https://www.nzfilm.co.nz/inbound-productions/filming-in-nz/facilities). [Its official site](https://floating-rock.com/), [Wellington contact page](https://floating-rock.com/contact/) and [Screen Wellington feature](https://www.wellingtonnz.com/screen-wellington/made-in-wellington/game-changer-for-wellington-tech-industry) provide additional evidence. It is a Class C company reference, not an invented geocoded branch. Neither golden example is assumed to own a capture stage.

[Benchmark inputs](benchmarks/) contain 100 service-relevant known examples plus 19 held-out entities, spanning Oceania, North America, Europe and Asia, with source/geography/rationale. Size and independence are not uniformly corroborated; this is not a census of 119 audited independent SMEs. The frozen, entity-disjoint split is **retrospective and shares discovery sources**. It is not blind, source-disjoint or representative of worldwide recall. Acquisition, matching, query planning and public rendering never read benchmark names. Primary seed enrichments can attach only to independently acquired/existing records; they cannot create candidates.

| Evaluation | Correct identity | Alternate identity | Conflicting/misleading match only | Recall |
| --- | ---: | ---: | ---: | ---: |
| Known examples | 92 | 4 | 4 | **96 / 100 = 96%** |
| Held-out entities | 17 | 0 | 2 | **17 / 19 = 89.47%** |

The 100% target is **not met**. Studio 9, Rascal, Studio Eeksaurus and Brilliant Pictures remain conflicted in the development set; Enter Yes and Pictor remain conflicted in held-out evaluation. Exact identities/geography/domains need review. These are coverage/identity gaps, not proof the businesses are irrelevant. See [per-entry reasons](reports/benchmark-results.json). Generic names, shared hosting and conflicting official domains are held for review instead of being forced into an existing identity. Operating brands and distinct facilities are not automatically merged. Country-compatible name matches with an unavailable official domain have medium confidence.

A [25-record precision worksheet](reports/precision-review.json) is generated for a maintainer. **No human-reviewed false-positive rate is available.** Benchmark recall is not precision, an AI/source-assisted review is not human approval, and passing seed tests does not establish current operation. Keep completed human decisions separately with exact record/source hashes; do not edit generated reports and treat a future regeneration as approval.

## Repeatable workflow

Python standard library only; all commands below prepare research, never merge or deploy.

```sh
# Rebuild the exact original atlas from its preserved safe archive, then append
# source-supported boutique references into a FRESH review proposal.
python tools/boutique_release.py --output /tmp/motionx-v12-proposal

# Inspect public/, reports/, and release.json. Review the diff before copying
# any proposal into a development branch. Repeated fresh builds yield the same
# IDs/hashes; existing output folders are rejected rather than overwritten.
python tools/boutique.py preview --output /tmp/motionx-boutique-review
python tools/boutique.py check --output data/boutique/reports
python tools/check_bulk_release.py
python tools/launch_readiness.py check --output data/bulk/reports

# A bounded download of the exact permission-reviewed revision. Failures return
# nonzero and an artifact; there is no fallback host or public-database write.
python tools/boutique_collect.py collect \
  --commit 8178b6b5e6db6c5b6f25206359ec44037f6d11b3 \
  --output /tmp/motionx-boutique-source-snapshot

# Multilingual query plans, not automatically executed searches.
python tools/boutique_collect.py queries --output /tmp/motionx-query-plan.json
```

The registry pins permission-reviewed input versions. A different source revision requires a new access/licence review; it is not silently trusted. Network/robots failures produce no deletion or closure signals. Source snapshots and complete prior discovery queues are preserved. This v1.2 recipe reproduces its fixed 41,735-record baseline; a subsequent release must reconcile against the **then-current complete catalogue**, preserve all existing boutique IDs and audit explicit corrections instead of replacing the atlas with a fresh historical build.

Every observation has its original source ID, hash, URL, date and matching reason/confidence. The release binds inputs, benchmark freeze, region/vocabulary configuration, source policy, original baseline and old shard hashes. Reproduction fails for stale/tampered input or public output. Nothing modifies canonical location evidence or inherits company services into branch capabilities.

The [graph](reports/graph.json) contains bounded company-to-source co-listing/event-participation edges. These are discovery signals, not inferred collaboration, parentage, customers or commercial relationships. No unbounded website traversal follows them. The [query log](query-log.json) distinguishes retained exact queries from earlier exploratory intent summaries. The multilingual [query plan](query-plan.json) is explicitly **not executed**; it does not imply global source coverage.

## Product behaviour and remaining gaps

Choose **Boutique Studios**, then filter by country (Advanced), research region, service specialisation, cinematics, real-time, character/motion-pipeline relevance, source-listed size, A/B/C, advisory score and research status. Controls combine with **AND**. Text search additionally matches the actual recorded company-service terms; a generic rigging signal does not imply facial capture or a capture stage. The existing confirmed-only filter still requires recorded facility evidence. All records remain available through All records; new company references have no pins. Existing profiles, organisation navigation, comparison, back/forward routes, map groups and CSV remain available. Exports keep full source notices and place advisory scores in separate columns.

Service alignment weights: animation 10, CG 10, character/digital-human 20, cinematics 20, real-time 20, rigging/motion pipeline 10, VFX 5, previs/virtual production 5. Scores do not include company budgets, pain points, purchasing intent, support needs or invented employee counts. Company-level evidence remains distinguishable from facility-confirmed capabilities.

Additional source-backed coverage is Europe-heavy: 349 research-visible records in Europe, 45 Oceania, 25 North America, 25 Asia, one Africa and 15 without established country. These count records, not unique independently confirmed facilities. No new comparable primary-source collection covers Latin America or the Middle East. Existing taxonomy-only leads cover those regions, but must not be presented as equivalent evidence. Prioritise permission-reviewed regional associations and film agencies, the blocked French licensed CSV when legitimately accessible, and primary corroboration of current company identity and independent SME status. Do not enable unresolved/restricted websites simply to increase counts.

The old broad strategy prioritised animation/place categories and generic production labels. It missed specialist service descriptions and lacked source-specific company context; some relevant companies were already buried among Class C observations. This release combines official associations, complete licensed company-level collections and primary service research, then reconciles those signals against **all** existing records. It distinguishes newly discovered businesses from better evidence for old references.

[Validation/performance results](reports/validation-results.json) record the executed checks and conditions. Large world-wide CSV exports may still fetch many existing detail shards and consume substantial browser memory; only bounded filtered exports were tested. Boutique metadata is optional/lazy and capped at 10 MB uncompressed; future growth may require its own sharding before that limit. Low-memory physical phones, deployed Pages performance, human precision review and the new manual Actions downloader are not claimed as tested here. The full map/search index and original coordinate selection remain independent of this optional metadata.

## Executed release checks

Local checks passed: **201 Python tests, 59 JavaScript tests and 51 HTTP browser checks** (19 baseline/50,000-location checks, six sharded-50,000 checks, nine actual-catalogue checks, nine research-UX checks and eight boutique checks). Canonical validation: **0 errors / 265 warnings**; full-catalogue and source-provenance reproduction: **0 errors**. All 13 legacy unknown records remain labelled, all 40,376 source points remain unverified facility geocodes, and all 1,448 company-only references remain pin-free. The current hash-bound B/C review queue has 41,837 records; it approves none of them. Identity-review cases, unknown permissions and missing geography remain visible rather than being suppressed.

| Measurement | Actual result / conditions |
| --- | --- |
| Initial full 42,067-record directory | 1.654 s, local HTTP desktop Chromium |
| Full index transport | 5,070,883 bytes plain / 2,200,402 gzip; 20,629 more gzip bytes than v1.1 |
| Throttled initial directory | 31.152 s; 96,000 bytes/s, 150 ms latency, 4× CPU slowdown, 390×844 |
| Warm directory reload | 0.902 s |
| Full-index text search computation | 18.5 ms, one measured query |
| Viewport marker update | 35.6 ms, 140 rendered groups |
| Uncached profile | 84.5 ms |
| Boutique metadata | 4,597,256 bytes plain / 303,821 gzip, fetched lazily |
| First boutique opening | 0.348 s, local unthrottled desktop |
| Boutique combined filters | 15.6 ms, one measured selection |
| Separate 50,000-location synthetic sharded fixture | 1.071 s initial load / 7.1 ms search; zero synthetic public records |

These are individual local runs, not p95 measurements, a controlled cross-release timing comparison, deployed Pages measurements or physical low-memory-device tests. The optional boutique metadata adds no default startup request. Direct location links still open the base/source profile; selecting Boutique Studios makes the additional advisory company-evidence panel available. The 10 MB metadata guard and expensive unbounded CSV export remain operational limits. See [the machine-readable results](reports/validation-results.json) for exact conditions, hashes, warnings and limitations.
