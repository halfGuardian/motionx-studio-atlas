# New Zealand census · v1.5 continuation

Reviewed **7 November 2026**. Continues the original Wave 1 in draft PR #15, tracking issue #14. **The census remains incomplete.** The target is traceable coverage of relevant operating businesses, not an inflated count of verified facilities.

## Results and definitions

- **217 source observations / 132 normalized source-name keys**: 98 preserved Wave 1 rows, 116 permitted programme-year rows and three selected regional leads. Rows overlap across sources and years.
- **41 existing company identities reconciled**, across 73 represented observations. This is company representation, not independent current-operation/facility verification. Domain-conflict rows for some represented names remain held.
- **59 new provisional Class C company references**; 46 further observations resolve to those proposals. Countries express source association; city is empty and coordinates are null. No fabricated addresses, relationships, confirmed technical capabilities or capture stages.
- **27 unresolved source-name keys** across 34 observations (12 identity holds, 22 unresolved). These are not 27 proven distinct missing companies. Historical-year aliases may still refer to existing proposals; they are not silently merged.
- One **reported NZ office closure identity**, appearing under three name variants/four observations, remains a review alert. No global-company closure or automatic removal is inferred.
- One equipment-rental observation is out of target scope, with its existing record retained.
- **Four separate source-supported facility proposals**, zero independent human facility reviews, zero approvals. Avalon is in **Lower Hutt**, Lane Street in **Upper Hutt**, Stone Street in Wellington and Te Whare Piringa in Rotorua. Marketing-region names do not replace municipalities. There are no new pins or Class A promotions.

The proposed combined catalogue has **42,298 references**, **A 230 / B 4,626 / C 37,442**, 178 countries/territories, 1,679 company-only references, and 40,619 records with original coordinates. The root database remains **243 retained locations / 119 operating organisations**. The 59 new provisional company identities are not added to the independently reviewed organisation total. All 42,239 prior IDs, all 240 prior detail shards and the entire root database are unchanged.

## Source coverage

All sources below were assessed on 7 November 2026; observations are the actual retained factual rows, not estimated directory sizes. Zero means a page/access/policy assessment with no roster projection, not an empty regional industry.

| Source | Retained observations | Enumeration scope | Rights checkpoint |
| --- | ---: | --- | --- |
| [NZ Film Commission facilities](https://www.nzfilm.co.nz/inbound-productions/filming-in-nz/facilities) | 42 | complete historical 42 row snapshot | not established |
| [Screen Auckland digital/post-production](https://www.screenauckland.com/choose-auckland/digital-post-production) | 24 | partial four of seven pages | not established |
| [Screen Wellington showcase](https://www.wellingtonnz.com/screen-wellington/screen-industry-directory) | 9 | nine showcase cards only | not established |
| [Wellington creative showreel](https://www.wellingtonnz.com/screen-wellington/why-wellington) | 21 | complete 21 named participants not directory | not established |
| [Film Otago Southland historical selections](https://www.filmotagosouthland.com/production-support/industry-directory) | 2 | two legacy selections only | commercial reuse restricted |
| [NZ On Air GDSR published recipients](https://www.nzonair.govt.nz/funding/game-development-sector-rebate-scheme-gdsr/gdsr-recipients/) | 116 | complete published 2024 2026 sections | accurate attributed reproduction permitted |
| [Screen CanterburyNZ](https://www.christchurchnz.com/business/screen-canterburynz) | 2 | landing page and selected public announcements | not established |
| [Film Bay of Plenty studio feature](https://filmbayofplenty.com/why-film-in-the-bay-of-plenty/film-studios-production-hubs/) | 1 | one featured facility not full directory | not established |
| [Waikato Screen directory](https://www.waikatoscreen.nz/waikato-film-directory/) | 0 | permission pending no roster projection | written consent required |
| [Film Queenstown Lakes](https://www.qldc.govt.nz/community/economic-development/film) | 0 | regional referral not separate roster | not established |
| [Film Dunedin](https://www.dunedinnz.com/screen) | 0 | regional landing page not enumerated roster | not established |
| [Screen Hawke’s Bay](https://screenhawkesbay.co.nz/) | 0 | inaccessible no enumeration | not established |
| [Screen Northland](https://www.filmoffices.nz/) | 0 | social contact referral no roster | not established |
| [Venture Taranaki film office](https://www.venture.org.nz/sector-development/film-and-screen) | 0 | regional support page no roster | not established |
| [Film Whanganui](https://www.filmwhanganui.nz/) | 0 | filming guidelines no roster | not established |
| [Screen Marlborough](https://marlboroughnz.com/screen-marlborough/) | 0 | regional landing page no roster | not established |
| [NZ Game Developers Association](https://www.nzgda.com/studio-partner) | 0 | no text roster enumerated | not established |
| [VFX Professionals Guild NZ 45-business list](https://www.vfxg.nz/) | 0 | not obtained permission pending | permission pending |

Only the **declared NZ On Air 2024–2026 sections** have coherent complete permitted enumeration: 2026 **43**, 2025 **40**, 2024 **33**. This is not complete NZ game-studio coverage, NZGDA membership coverage or current-operation verification. The agency's [terms](https://www.nzonair.govt.nz/copyright-and-terms-use/) permit accurate, non-misleading reproduction with source and copyright acknowledgement. The scoped `NZ-On-Air-Permission` notice accompanies exports. It is **not CC BY**, and does not clear company pages or third-party photos/videos. No financial amounts/bands, personal contacts, media or authored prose are projected.

Screen Auckland's normal pages 0/1/3/6 were readable; 2/4/5 remain inaccessible. No `origin` host workaround was used. Wellington's nine showcase cards are readable; the full dynamic results render **0 of 0**, which does not establish an empty directory. NZGDA's Studios & Partners view returned a heading without an enumerable text roster; no screenshot/OCR, login or embedded alternate-host workaround was used.

**Film Otago Southland:** after early page review, [terms](https://www.filmotagosouthland.com/terms-of-use) were found to prohibit commercial copying/caching. New roster projection stopped. Newly retrieved restricted roster text and derived line-merge data were redacted from scratch caches; receipt hashes were retained. Prior two Wave 1 selections remain historical, not retroactively licensed. Their company research uses their own websites and the names explicitly prioritised by the user. Changing listing order across normal views also invalidated attempted line-offset aggregation: complete enumeration cannot be inferred from mixed fragments. No newly retrieved roster company list is published.

**Waikato:** [terms](https://www.waikatoscreen.nz/terms-and-conditions/) require written consent; no new roster names are projected. Queenstown's referral does not separately clear the linked Otago source. **VFXG's actual 45-company list remains unobtained and permission pending**; no email was sent and no substitute roster reconstructed. Other regional landing pages are not labelled full studio directories. No source-wide reuse rights are inferred from public visibility.

## Identity and evidence decisions

All 42 distinct outstanding Wave 1 source-name keys received recorded indexed research; receipts are in [research-receipts.json](inputs/research-receipts.json). A query receipt is not company verification. Each of all 217 observations has an outcome, matching reason/confidence, original service labels, URL, date and links to applicable Atlas identities. The complete [reconciliation](reports/reconciliation.json) keeps before/after matching and company assessments; historical input snapshots remain unchanged.

- **A44 → A44 Games** and **Fox & Co → Fox & Co Animation** reconcile supported aliases to existing IDs, including Fox's documented official-domain change. No duplicate reference is created.
- **Assembly NZ** is distinct from the US Assembly record. **Stone Street NZ** is distinct from the overseas name match. Foreign IDs/coordinates remain unchanged and collision warnings stay visible. Big Picture / Creative Technology NZ is a provisional NZ operating reference with documented brand context, not an invented parent relationship or VP stage.
- **Blockhead** remains distinct from Assembly: the NZFC domain conflict and a current Sydney company page do not establish a current NZ branch. A failed or changed page is never proof of closure.
- Creature Post, Eleven FX, Mandy VFX, The Rig, The Machine Room, Metia Interactive and the named regional businesses gain references only at the supported company level. Sparse Resn/Storybox pages are not used to invent detailed animation, gaming or capture services. RiffRaff's publisher evidence is labelled evidence, not its own official website.
- **Graphic Monk Ltd** uses company-site post-production/editing evidence. Its prior regional capture label remains a historical assertion in the audit, not a confirmed stage/service or a newly imported brand. **Shotover Creative / Shotover Media** is linked by company-source name history, not confused with SHOTOVER camera equipment or another founder's later company.
- Cause and FX/Cirkus already have company references; conflicting source-domain rows remain visible for investigation. Wrong-country homonyms (e.g. Beyond Fun, Rascal Kids) are not silently accepted.
- The recent Niantic NZ office closure report is retained as a **human investigation alert**, not automatic truth or a global Niantic deletion. Historical GDSR/showreel evidence does not override it.

Original NZFC **PP/A/VFX/S/DIT** and regional service labels are preserved for every source observation. MotionX sectors and company-service assertions are separate from confirmed facility capability arrays, which are empty for all additions. Unverified claims remain unverified even after tests pass.

### Outstanding names

The following source identities still have an unresolved/held observation (some also have a represented variant elsewhere):

2Up Games, Bespoke Post, Beyond Fun, Beyond Studio, Blind Squirrel Entertainment, Blockhead, Cause and FX, Cirkus, Conical, Franklin Rd Music & Sound, Futureverse, Geo AR, Hashbane Interactive, Jon Online, Lets Play.Live, Lost Cosmonauts, Mighty Eyes, Mohawk Media, PlaySide Studios, Rascal Kids, Runaway Play, Staples Productions, Te Whare Piringa Film Studio, Usual Suspects Studios, WhitebaitMedia, Wrestler, ZeroKing.

The dashboard exposes the specific conflict, historical period, evidence and next review step for each. WhitebaitMedia requires production-service qualification; Te Whare Piringa's operator/facility evidence remains separate. Programme-name variants such as Runaway/Runaway Play, Geo AR/Geo AR Games and Blind Squirrel variants require evidence-backed alias review, not name-only consolidation. Neither historic-only absence nor a failed fetch is a closure signal.

## Reproduction, review and historical continuity

```sh
python tools/nz_research.py check
python tools/check_bulk_release.py
python tools/nz_census.py prepare --output /tmp/nz-wave1-reports
python tools/boutique.py check --output data/boutique/reports
python tools/annecy.py check
python tools/launch_readiness.py check --output data/bulk/reports
```

`nz_research.py` indexes names, legal suffixes, supported aliases, non-shared domains, geography and source provenance across the full original catalogue. Provenance-only and fuzzy/domain-only matches are review leads, not merges. Country guards prevent overseas pins becoming NZ facilities. Programme-year observations deduplicate to proposed identities while keeping every original row, source period, label and provenance entry. Conflicting identities remain held. Existing records are never overwritten. Reapplication to an already extended catalogue is refused; full source replay reproduces the exact release instead.

The current HTML/CSV/JSON dashboard supports query, source and outcome filters, existing/new profile links, source scope, permissions and facility proposals. It is served in this checkout so profile links resolve, or downloaded with the **`nz-census-reconciliation-and-pending-human-review` Actions artifact**. No runtime collector or backend is added.

`release.json` binds all inputs and source policy hashes, the 42,239-ID baseline digest, 240 immutable shard hashes and root SHA. The full catalogue reproducer replays bulk → boutique → Annecy → NZ. Historical boutique/Annecy/Wave 1 reports reproduce against their original cohorts and are not rewritten to pretend new approvals or historical coverage. New report generation fails on input/checkpoint drift. The source-access audit refuses complete/reusable claims for missing pages, empty widgets, unstable snapshots, overlapping-fragment conflicts and restricted terms.

`prepare` is a developer-only proposal operation on a freshly reproduced baseline. It does not contact sources or grant approval. It appends only a deterministic proposal shard and index metadata. The public site changes only after an authorised merge; no merge, deployment or Pages settings change is performed by this PR.

The [pending human worksheet](reports/human-review.json) is bound to exact reconciliation content. Its decisions/reviewers/precision are empty. Agent assessments, clicking links, draft status and passing tests are **not human approval**. Historical Annecy's 37-row human precision review remains pending. Source-rights review, current-operation/facility corroboration and maintainer review are required; required-review enforcement has not been independently confirmed for this PR. No approval hashes are fabricated or reused.

See [actual test results and limitations](validation.md). No complete-NZ or worldwide recall/precision percentage is claimed.
