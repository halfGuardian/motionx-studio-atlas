# MotionX Studio Atlas v1.0 — Public Launch & Global Scale

Draft PR #9: https://github.com/halfGuardian/motionx-studio-atlas/pull/9

Research reviewed **6 November 2026 (UTC)**. This branch proposes source-researched changes; it grants no human approval, independent business verification or production deployment.

## Proposed release

| Measure | v0.9.3 main | v1.0 proposal |
| --- | ---: | ---: |
| Locations | 182 | 243 |
| Operating organisations | 88 | 119 |
| Countries | 32 | 38 |
| Unknown-evidence locations | 16 | 13 |
| Validation errors | 0 | 0 |
| Validation warnings | 201 | 265 |

**61 additions, 31 new operating identities and three explicit evidence updates.** The new locations span 24 countries. All 182 prior IDs and coordinates remain intact. No studio is deleted or automatically marked closed. New pins are labelled approximate city references, including Cergy rather than marketed Paris, Shah Alam rather than Kuala Lumpur, Gateshead rather than Newcastle, and Rhodes in the Sydney metropolitan area. GeoNames sources are attributed in [city-references.json](city-references.json); Rhodes uses a factual Geodatos locality reference. No street address is presented as an exact geocode.

[records.json](records.json) and [evidence.json](evidence.json) bind each location/capability claim to its official source and actual review date. The [before/after audit](import-audit.json) and [updates.json](updates.json) preserve previous contents. The proposed updates revisit Beyond Vancouver, Beyond Montréal and Animatrik Burnaby individually. Body/performance capture is supported by current facility pages. Previously unknown facial/finger/virtual-camera labels are omitted from these three proposed rows where the reviewed facility evidence was insufficient; their previous claims remain in the audit. This is not a claim those services are unavailable. Beyond's named volumes remain documented within its existing campuses, without counting campus plus rooms as extra locations.

## Newly researched operating studios

Each link opens the location's official evidence/website. Names remain separate from parent/group identities; a sourced group link is not permission to copy capabilities between brands.

| Operating identity | Proposed branches / official sources |
| --- | --- |
| Abstraction | [Valkenswaard](https://abstraction.games/contact) |
| Atomhawk | [Gateshead](https://atomhawk.com/contact/); [Leamington Spa](https://www.sumo-digital.com/our-studios/) |
| Barajoun Studios | [Dubai](https://www.barajoun.com/contact.html) |
| Beyond-FX | [Los Angeles](https://www.virtuosgames.com/studio/beyond-fx/) |
| Black Shamrock | [Dublin](https://www.virtuosgames.com/studio/black-shamrock/) |
| CounterPunch | [Los Angeles](https://www.virtuosgames.com/studio/counterpunch/) |
| Demente Animation Studio | [Guadalajara](https://demente.studio/) |
| Gameloft | [Barcelona](https://www.gameloft.com/gameloft-studios/barcelona); [Brisbane](https://www.gameloft.com/gameloft-studios/brisbane); [Bucharest](https://www.gameloft.com/gameloft-studios/bucharest); [Hanoi](https://www.gameloft.com/gameloft-studios/hanoi); [Montréal](https://www.gameloft.com/gameloft-studios/montreal); [Paris](https://www.gameloft.com/gameloft-studios/paris); [Ho Chi Minh City](https://www.gameloft.com/gameloft-studios/saigon); [Sofia](https://www.gameloft.com/gameloft-studios/sofia); [Yogyakarta](https://www.gameloft.com/gameloft-studios/yogyakarta) |
| Glass Egg | [Da Lat](https://www.virtuosgames.com/studio/glass-egg/dalat/); [Ho Chi Minh City](https://www.virtuosgames.com/studio/glass-egg/) |
| Hype Entertainment | [Porto Alegre](https://www.hype.cg/) |
| Lab42 Games | [Leamington Spa](https://www.sumo-digital.com/our-studios/) |
| Lemon Sky Studios | [Shah Alam](https://www.lemonskystudios.com/) |
| Lightfarm Studios | [Rio de Janeiro](https://lightfarm.com.br/about) |
| Luma Pictures | [Melbourne](https://www.lumapictures.com/about); [Vancouver](https://www.lumapictures.com/about) |
| Passion Republic | [Petaling Jaya](https://www.passionrepublic.com/contact/) |
| Pipeworks Studios | [Eugene](https://www.pipeworks.com/new-careers/) |
| Plastic Wax | [Rhodes](https://www.plasticwax.com/enquiries) |
| Platige Image | [Warsaw](https://platige.com/studio/); [Warsaw](https://platige.com/pl/mocap/) |
| Red Kite Games | [Leeds](https://www.sumo-digital.com/our-studios/) |
| Resin | [Adelaide](https://www.resin.com.au/contact) |
| Sea Monster | [Cape Town](https://www.seamonster.digital/contact) |
| Sparx* | [Ho Chi Minh City](https://www.virtuosgames.com/studio/sparx/) |
| Sperasoft | [Kraków](https://sperasoft.com/about/); [Warsaw](https://sperasoft.com/about/); [Abu Dhabi](https://sperasoft.com/about/); [Belgrade](https://sperasoft.com/about/); [Yerevan](https://sperasoft.com/about/) |
| Studio du Château | [Montréal](https://studioduchateau.com/video-mocap-studio-location-montreal.html) |
| Sumo Digital | [Sheffield](https://www.sumo-digital.com/our-studios/); [Nottingham](https://www.sumo-digital.com/our-studios/); [Leamington Spa](https://www.sumo-digital.com/our-studios/); [Prague](https://www.sumo-digital.com/our-studios/); [Pune](https://www.sumo-digital.com/our-studios/); [Bengaluru](https://www.sumo-digital.com/our-studios/) |
| The Monk Studios | [Bangkok](https://themonkstudios.com/about-us/) |
| Third Kind Games | [Leamington Spa](https://thirdkindgames.com/) |
| Trident Motion Capture Lab | [Los Angeles](https://mocapschool.com/) |
| University for the Creative Arts | [Farnham](https://www.theagency.uca.ac.uk/hire/facility-hire/motion-capture/) |
| University of Portsmouth | [Portsmouth](https://www.port.ac.uk/about-us/our-facilities/teaching-and-learning-spaces/motion-capture-studio) |
| Virtuos | [Kuala Lumpur](https://www.virtuosgames.com/studio/kuala-lumpur/); [Xi’an](https://www.virtuosgames.com/studio/xian/); [Chengdu](https://www.virtuosgames.com/studio/chengdu/); [Shanghai](https://www.virtuosgames.com/studio/shanghai/); [Cergy](https://www.virtuosgames.com/studio/paris/); [Lyon](https://www.virtuosgames.com/studio/lyon/); [Montpellier](https://www.virtuosgames.com/studio/montpellier/); [Prague](https://www.virtuosgames.com/studio/prague/); [Warsaw](https://www.virtuosgames.com/studio/warsaw/); [Montréal](https://www.virtuosgames.com/studio/montreal/) |

## Capture evidence and deferred scope

Seven new locations have specific capture evidence:

| Location | Supported capture / specialist claims |
| --- | --- |
| [Platige, Warsaw Jutrzenki](https://platige.com/pl/mocap/) | Motion/performance capture, retargeting and on-session previs; distinct from W. Szpilmana production HQ |
| [Plastic Wax, Rhodes](https://www.plasticwax.com/motion-capture) | Owned body/facial capture stage, retargeting and previs; animation/VFX supported separately |
| [Passion Republic, Petaling Jaya](https://www.passionrepublic.com/studio/) | On-site motion capture studio; game-art production supported separately |
| [Trident, Hollywood district of Los Angeles](https://mocapschool.com/) | Physical body motion capture production/training stage; partner services not inherited |
| [Studio du Château, Montréal](https://studioduchateau.com/motion-capture-mocap-studio-montreal.html) | Body, facial and performance capture at the St-Ferdinand studio |
| [Portsmouth, Eldon Building](https://www.port.ac.uk/about-us/our-facilities/teaching-and-learning-spaces/motion-capture-studio) | Body/facial/performance equipment; explicitly offered to external commercial productions |
| [UCA, Farnham](https://www.theagency.uca.ac.uk/hire/facility-hire/motion-capture/) | Body/facial capture; explicit commercial facility hire |

No new volumetric or LED virtual-production stage claim was added without sufficiently specific evidence. Supplying game art, cinematics, animation or VFX is not used to infer on-site capture or full game development. Virtuos Montréal remains concept art; Glass Egg/Atomhawk remain game art. University facilities are included because their official pages explicitly offer external production services, not merely student teaching.

[28 deferred review topics](review-queue.json) include multiple unresolved facilities, not 28 verified studios. Examples: Virtuos sales/offices and co-located Umanaia; Third Kind's Poland/Spain municipalities; Sperasoft's Valletta versus Saint Julian's evidence; Gameloft Ukraine's wartime physical footprint; Midoki versus the Sumo Leamington team; Motus's move from Dallas to an unspecified Colorado base; Luma's Santa Monica correspondence/production distinction; Resin's secondary studio spaces; Platige overseas representation; and inaccessible/insufficiently located independent studios. No current-operation conclusions were invented from historical listings or failed requests. The remaining 13 legacy unknown-evidence records need individual research.

Latin America gains Hype, Lightfarm and Demente, Africa gains Sea Monster, Southeast Asia gains several art/game/capture facilities, and the Middle East gains Barajoun and Sperasoft Abu Dhabi. Oceania gains Plastic Wax, Gameloft Brisbane, Luma Melbourne and Resin Adelaide. These are researched gaps, not comprehensive national coverage. Ubisoft and EA branch completeness, African independent facilities, additional Latin American studios, facial/volumetric providers and specialist motion-editing operations remain priorities. EA's access restrictions remain in force.

## Import replay and validation

- [batch.csv](batch.csv) contains all 64 exact proposed rows; [additions.csv](additions.csv) isolates the 61 additions for the append-only importer. Updates use the explicit previous-record hashes in `stage-pr`, never silent CSV overwrites.
- [Dry run](dry-run-report.json): 61 accepted additions; five incoming IDs require explicit distinct-location review, representing six new warning pairs. No rejected rows. The shared Virtuos/Sumo websites do not establish one studio, and Platige's source names two street locations. Existing three warning pairs remain documented.
- [Apply](apply-report.json) was run against a disposable database with the three separately staged updates. It exactly reproduces this branch's canonical JSON. [Repeat apply](repeat-report.json): 61 unchanged additions, zero new records and no write. Re-staging all 64 proposed rows similarly leaves 64 unchanged.
- [validation.json](validation.json): **zero errors / 265 unsuppressed warnings** — 243 imprecise pins, 13 legacy evidence warnings and nine possible-duplicate pairs. Distinct facilities/brands are retained with explicit evidence rationale; warnings are not deleted to make the report appear clean.

Reproduce the exact staged proposal against the v0.9.3 baseline (a fresh output directory is required):

```sh
git show 2e814f063c7faacab8d44b1b61336bc631544d94:studios.json > /tmp/motionx-v093.json
python - <<'PYCODE'
import json, subprocess
from pathlib import Path
p=Path('data/research/v1.0-launch')
a=['python','tools/research.py','stage-pr','--database','/tmp/motionx-v093.json','--records',str(p/'records.json'),'--manifest',str(p/'evidence.json'),'--output','/tmp/motionx-v10-staged']
for entry in json.loads((p/'evidence.json').read_text())['records']:
    if entry.get('distinct_reason'):a+=['--allow-distinct-location',entry['id']]
subprocess.run(a,check=True)
PYCODE
```

The stage checks freshness against the date it runs; after 30 days evidence must be revisited. Historical regression tests fix the original research date to test the original exact bundle, not to make a stale future proposal publishable.

## Discovery continuity and source collection

The source registry remains **25 sources, eight enabled and 17 disabled**. No new collector was enabled as a side effect of manual research. [source-results.json](source-results.json) records the successful Actions run's actual statuses and evidence-byte hashes: DNEG 19 observations, metricminds 3, Framestore 7, Larian 6, RISE 5, Outpost 5, Flying Bark 3, FOLKS 10 (**58 total**). Access-policy checks are advisory, never automatic permission grants. Runtime robots checks, redirect/DNS restrictions and parser limits remain mandatory. EA, Cinesite and other prohibited/unresolved sources remain disabled; no screenshots/OCR, hidden APIs or alternate hosts are used as workarounds.

The successful run restored the original main discovery artifact, retained its 133 candidates, merged the unchanged reviewed 172-observation checkpoint plus the new 28-topic review queue, and preserved five history snapshots. Its 200 observations triaged against the published baseline as **91 represented, seven potentially new, 25 irrelevant and 77 requiring research**. These are observation counts, not unique unlisted facilities. The source results file is explicitly a job-log audit projection; the Actions artifact contains raw queue/report/history. Old committed histories and approval bundles are unchanged.

The new restore path tries up to 20 successful main discovery runs. Missing/expired artifacts fall back to the last hash-bound committed checkpoint with an explicit partial-history warning and suppression of disappearance signals. Network/auth/list failures fail closed instead of resetting the queue. A committed checkpoint cannot reconstruct missing observations that were never archived. The manual archive workflow can preserve a full successful main run in a new state-only draft PR, with no automatic merge or business approval. Its checkpoint/restore helpers are tested; the main-only archival workflow has not been dispatched end to end from this unmerged branch. Repository permission for Actions to open that future draft PR must be checked by a maintainer.

## Review workflow and security

`research.py report` generates an unverified dossier dashboard with company/country groups, priorities, source links, freshness/identity risks, facility claims, change alerts and before/after comparisons. [review.html](review.html) is the committed source-research dashboard; download `global-research-review` from Actions, open `research-review/review.html` and the exact `staged-proposal/review.html` locally. The public atlas never loads these files or the discovery queue.

This release uses **human review of this exact GitHub PR and manual merge**. It does not fabricate or consume historical JSON approvals. Baseline/record/update hashes, evidence dates and duplicate rationales bind the proposal; Actions reject an unrelated canonical diff. Passing checks, clicking links, a generated reviewer name or an HTML report does not approve a claim.

[Read-only rules audit](review-rules-audit.json): GitHub returned an empty effective-rules list and did not expose classic branch protection. Required-human-review enforcement is **unconfirmed**. A maintainer must inspect the repository's required reviewers and bypass rights before authorising publication. No repository rules, Pages settings or merge settings were changed.

Security review covers escaped text in cards/profiles/popups/reports; strict profile ID/hash parsing; safe HTTPS external links with `noopener noreferrer`; exclusion of credentials, local/IP-literal links, control characters and token query fields; CSV formula neutralisation; public source-only metadata; bounded source parsing; origin-restricted redirects and public DNS checks; bounded regular-file checkpoint recovery and immutable observation identities. The standard-library collector still relies on runtime TLS/proxy/network policy for connection safety: preflight DNS validation is not DNS pinning and is not claimed to defeat every rebinding attack. No credentials, personal contacts or private MotionX intelligence were added.

## Performance and tests

[performance-comparison.json](performance-comparison.json) compares the exact v0.9.3 main commit with v1.0 using the same **50,000-record, 50.5 MB synthetic JSON served over local HTTP**. Synthetic records never enter `studios.json`. The only intercepted script change adds loader/validation timers. Measurements are one local headless Chromium run, not statistical benchmarks or a real mobile-device/network lab.

| Same fixture | v0.9.3 | v1.0 |
| --- | ---: | ---: |
| Initial HTTP readiness | 1.666 s | 1.779 s |
| Load, parse and validate | 981 ms | 1,029 ms |
| Validation alone | 546 ms | 567 ms |
| Initial rendered markers | 50,000 | 168 |
| Measured pan | 257 ms | 80 ms |
| Search UI, including debounce/render | 407 ms | 231 ms |
| Profile UI | 108 ms | 99 ms |
| Mobile horizontal overflow | none | none |

Both versions already page lists at 50. Initial loading is similar and slightly slower here after the added indexes/checks. The improvement is marker/pan overhead and indexed filtering; no claim of faster networking is made. The separate [browser metrics](performance-browser-local.json) include Playwright's large-JSON interception overhead, so their ~11-second readiness is not a network benchmark. Multi-filter computation takes milliseconds locally. The browser suite also verifies all viewport member IDs, antimeridian handling, profile access, 65 coincident studios through 30-item chooser pages, and coincident identities inside the 50,000-record fixture.

Final test totals and workflow links are recorded in `test-results.json`. Full Python, JavaScript and HTTP suites pass, including preservation/import idempotency, source network/robots failures, disappearance/change handling, checkpoint recovery/identity conflicts, evidence freshness, approval enforcement, escaping/CSV safety, operating/parent identities, direct links/back/forward, combined confirmed-only filters, real Leaflet/OSM attribution, mobile layout, and 50,000-location behavior. No merge or production deployment was performed.

Remaining limits: the client still downloads/parses the whole JSON and maintains indexes in memory; a 50 MB directory can be expensive on slow networks or low-memory phones. Panning is improved but not a promised 60 fps. Synthetic/mobile emulation does not establish performance on every device. Grid grouping uses an original member coordinate rather than moving records. Labels in bounded adapters need maintenance when sites redesign; a changed page is an investigation signal, never automatic closure/capability evidence. Current source claims can become stale and exact street coordinates remain largely unverified.
