# Automated Atlas Maintenance v2

Implements issue [#21](https://github.com/halfGuardian/motionx-studio-atlas/issues/21) from released main `913dd798bb485a3a60024f7f024cb186c472e574`. The public catalogue stays at **42,478 stored / 42,474 normal references**. Every existing identity, coordinate, capability and evidence field is preserved. The separate interface fix makes the map evidence controls a compact, closed-by-default **Map guide** in the top-right corner, including mobile; native keyboard disclosure and Escape retain access to every control.

[Owner operating guide](OPERATIONS.md) · [Execution-history audit](run-history.json) · [Validation and limitations](validation.md).

## Execution evidence, not a schedule assumption

On 14 November 2026 NZDT (13 November UTC), the repository API returned **137 available workflow runs**, enumerated across two pages. Two were main-branch discovery runs:

| Run | Trigger | Actual result |
|---|---|---|
| [42149794259](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42149794259) | Manual, 6 November UTC | Six old configured sources; 92 observations, 133 retained candidates |
| [42666896576](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42666896576) | Schedule, 9 November UTC | All eight currently enabled sources returned `ok`; 58 observations, 200 retained candidates |

The configured cron remains **Monday `23 7 * * 1`**. The scheduled run's recorded creation/start was **17:40:21 UTC**, rather than nominal 07:23; this audit does not establish a cause or guarantee exact execution timing. The UTC schedule corresponds to **20:23 NZDT / 19:23 NZST**. No `archive-discovery.yml` run was present. Deleted runs cannot be reconstructed from this inventory.

Both actual `studio-discovery` ZIPs were downloaded and matched their GitHub SHA-256 digests, then CRC/path/JSON checks. Their queue/report/history bytes and per-file receipts are retained under `inputs/`. The scheduled artifact expires **7 February 2027 UTC** under its 90-day retention. Its legacy recovery file claims complete history; that file is preserved verbatim, but v2 rejects the flag as proof because the earlier raw artifact lacks a completeness chain. The new recovery logic carries partial status forward and suppresses absence inference. The initial 8 November audit is retained separately as `run-history-2026-11-08.json`; it predates the first scheduled run.

## Incremental research path

The system reuses the global standard-library CSV/JSON loader, append-only snapshot state and full-catalogue identity index. Source-specific permission/licence metadata, stable source IDs, country normalization, complete/partial/failed states, input/policy hashes and original dates remain bound to each snapshot. A failed or partial fetch never replaces known facts with an empty roster. An observation date and an underlying source update date remain different fields.

Research groups use exact name/country/city/nonshared-domain and named-unit context. Repeated observations are grouped for review, while distinct brands, foreign identities, cities and separate named facilities remain separate. All original observations stay in the hash chain. Matching reasons and existing record IDs are advisory; common ownership, a domain, a source key or an automated test does not establish an operating identity or facility.

The report includes source changes and before/after facts, duplicate/alias risks, municipality associations, uncertain closure/relocation signals, relationship assertions, technical claims, freshness, licensing and human-review questions. Source disappearance produces only a research signal. No published company is removed or closed. Proposed geographic references retain **null coordinates** pending municipality evidence and a licensed coordinate review. Existing verified capabilities are never overwritten or inferred from parent services.

Commercial relevance uses the established six-role policy: potential client, provider, both, plausible unconfirmed, adjacent uncertain and out of scope. Game development is eligible without capture. Broad film/video listings stay plausible rather than high-confidence clients. Four individually reviewed audio-only exclusions remain intact; audio/sound words or incomplete service lists create review questions, not new exclusions. Multidisciplinary visual studios remain eligible.

## Monthly draft and publication boundary

`monthly-maintenance.yml` checks the configurable UTC cadence daily at 09:23. Defaults are enabled, day 1, interval one month, maximum one open batch. The stable branch is `automation/atlas-maintenance-YYYY-MM`. The writer stages **only `data/maintenance/batches/YYYY-MM/`**, checks all staged paths, refuses unrelated edits, preserves full state and previous report revisions, and uses a normal non-force push. Same-content repeats, already-closed periods and unchanged content from a merged prior batch do not create another PR. Another open batch blocks a new one. Ready-for-review or foreign/retargeted PRs are not edited; head/draft status is checked again before push.

The resulting PR is **research only**. Its proposed minimal company fields and before/after source assertions are review-ready evidence, not an applied public database diff. Merging it makes a durable research checkpoint. Publishing company additions/corrections requires a separate exact-content data PR, appropriate source-rights and capability/geography review, regenerated public assets and an owner-authorised merge. No bot review, automatic merge/deploy, generated human identity, stale approval reuse or approval-file editing is introduced. Existing Pages settings are unchanged.

Weekly permissions remain read-only, so an ordinary scan cannot push any branch or edit live company data. Monthly write permissions are confined by the implementation's research-path checks; repository write access is still a trust boundary. Required human-review protection could not be verified: its API returned **403 Resource not accessible by integration**. Draft PRs and tests do not enforce human approval. GitHub also provides no atomic draft-state/Git-push transaction; owners should enforce stale-review dismissal for data PRs. Actions-bot PR creation permissions remain unverified until the new workflow is run after merge. A recognised permission denial is surfaced without logging secrets, and preserves the artifact/pushed draft branch for manual recovery.

## Retention and failure handling

Weekly artifacts contain the queue, source reports, entire available historical JSON, global snapshot state, review dashboard and byte-bound manifest. Failed runs with valid partial artifacts are recoverable. The recovery order is recent completed main discovery runs (including failed runs), owner-merged monthly checkpoints, then the newest valid committed raw discovery archive. A corrupt/missing archive falls back only with an explicit gap; inability to enumerate runs stops recovery rather than silently resetting. Raw candidate unions preserve both artifact and checkpoint histories after expiration.

Health errors fail the job after available artifacts are uploaded; stale observations, source dates, expiring artifacts and policy holds appear in summaries. Personal GitHub Actions notifications must be enabled by the owner—no external messaging credentials or issue spam is added. Access reviews older than the configured threshold disable collection before requests. Full raw archives must be retained before the 90-day deadline, or merged as an owner-reviewed monthly research PR. No global completeness claim follows from a green job.

## Reproduce without network collection or publication

```sh
python tools/maintenance.py prepare \
  --discovery data/maintenance/inputs/discovery-42666896576 \
  --output /tmp/atlas-maintenance-review
python tools/maintenance.py verify --output /tmp/atlas-maintenance-review
python tools/maintenance.py prepare \
  --discovery data/maintenance/inputs/discovery-42666896576 \
  --state /tmp/atlas-maintenance-review/state.json \
  --output /tmp/atlas-maintenance-repeat
```

The initial v2 replay processes **479 retained source observations into 452 research groups**: 419 groups have existing matches; 33 have no match. The 180 unresolved groups overlap existing matches because they can also have identity, facility or technical questions. Twenty-seven duplicate observations are grouped without deleting evidence. This is a first-ingestion/backfill count, not 479 new companies, independent verification or new collection. **Zero reviewed company proposals, approved additions, verified facilities or capability promotions** result. Repeat replay adds zero signals. The full 200-candidate raw discovery queue remains intact. Current summaries and complete HTML/JSON reports are generated as Actions artifacts.

## Source coverage

Only the eight official rows marked automatic below are network-collected by weekly discovery. Every request remains conditional on current robots/access checks. The separately registered 424-row animation-directory export is processed offline at its reviewed pinned revision under **CC BY 4.0**, attributed to **Tommy Lahitte and European Animation Studios Directory contributors**; replay is not a newly fetched dataset. Additional permitted CSV/JSON sources may be registered through the existing reviewed snapshot registry and global incremental command. Their licence/attribution and original source dates must be supplied; public accessibility alone is not permission.

EA, Ubisoft, Cinesite, ILM, Wētā and the other disabled official sources require manual policy/research review. Overture refreshes, the 1,116-game-company source, regional/native-language directories and unregistered sources retain their separate existing restrictions and manual workflows. No new source is enabled here; no restricted route, screenshot/OCR, hidden API or alternate-host workaround is introduced. No private CRM data, personal contacts or confidential company information belongs in these public research files.

| Official source | Weekly mode | Recorded restriction/scope |
|---|---|---|
| [ubisoft-studios](https://www.ubisoft.com/en-us/company/careers/locations) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [ea-studios](https://www.ea.com/careers/teams/ea-studios) | Manual research only | EA robots.txt reserves rights and explicitly prohibits web scraping/text-data mining without written authorisation. Manual evidence research only; no adapter expansion enabled. |
| [cinesite-group](https://cinesite.com/our-studios/) | Manual research only | Current Terms of Use section 3 expressly prohibits automated scraping/text-data mining. Retain existing observations; no collection or screenshot/OCR workaround without permission. |
| [dneg-studios](https://www.dneg.com/contact) | Automatic bounded metadata | Runtime robots and current bounded-metadata access review required; no source-wide reuse licence. |
| [imaginarium-sites](https://www.imaginariumstudios.co.uk/locations) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [metricminds-services](https://metricminds.com/performance-capture/) | Automatic bounded metadata | Runtime robots and current bounded-metadata access review required; no source-wide reuse licence. |
| [framestore-locations](https://www.framestore.com/contact) | Automatic bounded metadata | Runtime robots and current bounded-metadata access review required; no source-wide reuse licence. |
| [ilm-locations](https://www.ilm.com/locations/) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [weta-locations](https://www.wetafx.co.nz/about) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [imageworks-locations](https://www.imageworks.com/contact-us) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [digital-domain-locations](https://digitaldomain.com/about/contact-us/) | Manual research only | Published policy reserves duplication/redistribution in any form; broader Terms of Use need review. Collection disabled. |
| [eyeline-locations](https://apply.eyelinestudios.com/careers/artist/) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [cdpr-locations](https://www.cdprojektred.com/en/jobs) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [remedy-locations](https://www.remedygames.com/contact) | Manual research only | Terms limit website use/material reuse; explicit permission or clarification is required before extracting facility metadata. Earlier navigation observations retained. |
| [larian-locations](https://larian.com/careers) | Automatic bounded metadata | Runtime robots and current bounded-metadata access review required; no source-wide reuse licence. |
| [rise-locations](https://www.risefx.com/) | Automatic bounded metadata | Runtime robots and current bounded-metadata access review required; no source-wide reuse licence. |
| [outpost-locations](https://www.outpost-vfx.com/en/contact) | Automatic bounded metadata | Runtime robots and current bounded-metadata access review required; no source-wide reuse licence. |
| [flyingbark-locations](https://www.flyingbark.com.au/about) | Automatic bounded metadata | Runtime robots and current bounded-metadata access review required; no source-wide reuse licence. |
| [triggerfish-locations](https://www.triggerfish.com/faq/) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [reelfx-locations](https://www.reelfx.com/contact/) | Manual research only | Terms restrict public/commercial reuse; permission/clarification required. No automated collection. |
| [rodeo-locations](https://www.rodeofx.com/contact) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [chocolate-tribe-locations](https://chocolatetribe.co.za/contact/) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [studiot3d-locations](https://www.studiot3d.com/) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
| [folks-locations](https://folksvfx.com/contact/) | Automatic bounded metadata | Runtime robots and current bounded-metadata access review required; no source-wide reuse licence. |
| [rsp-locations](https://www.rsp.com.au/contact) | Manual research only | Robots/reuse terms unavailable, restrictive or insufficiently reviewed. Manual review or permission required; no automated fallback. |
