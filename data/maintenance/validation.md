# Maintenance v2 and collapsible map guide — validation

14 November 2026 NZDT / 13 November UTC. Baseline: released main `913dd798bb485a3a60024f7f024cb186c472e574`. This development PR neither merges nor deploys itself. Public company data and Pages settings are unchanged.

## Results

| Check | Actual result |
|---|---|
| Complete Python suite | **364 passed**, 186.227 seconds |
| Current maintenance tests after the final report markup change | **38 passed**, 25.144 seconds |
| Complete JavaScript suite | **95 passed**, 12.572 seconds |
| HTTP browser suites | **109 checks across all 16 suites passed** |
| Canonical `studios.json` | **Zero errors / 265 retained warnings** |
| Source replay, current/historical licensing, research, maintenance and geography CLIs | **All 15 commands passed**, including complete source-to-catalogue reproduction |
| Published-byte preservation | Every `studios.json` / `data/public` file and its Git blob matched released main; no added/missing public files |
| Original discovery artifacts | Both actual ZIPs matched GitHub SHA-256; CRC, paths and all archived JSON bytes verified |
| Workflow syntax | All repository workflow YAML parsed locally; GitHub validates the submitted workflow definitions in PR checks |

The full Python rerun preceded a final report-only addition that exposes existing source/continuity alerts and a link to the original source change digest. All 38 affected maintenance tests and the full HTTP suite passed afterward. Exact-head GitHub Actions results are linked from the PR; local tests are not claimed to be a live monthly workflow run. Machine results, initial failures, final logs, original source coverage and metrics are in [qa](qa/summary.json).

## Map fix

The former floating panel now starts closed as a **115 × 46 px Map guide** in the top-right corner. It is tested at 1440×950, 768×1024, 390×844, 320×568 and 844×390, without horizontal overflow. Native Enter/Space disclosure works; Escape closes the guide and returns focus. The expanded header stays available while its panel scrolls. Click/scroll handling does not pan the underlying map.

A Chromium mobile context with touch enabled verifies actual taps, the unpinned-company directory, focus and profile access. The 390px screenshot is an emulated device, not a physical-phone test. The separate Leaflet-failure case preserves directory and disclosure functionality. Existing shared-coordinate selection, city references, Floating Rock, Frame Machine, profiles/history, AND/OR filters, confirmed-only searches, CSV safety, OpenStreetMap attribution and source-error recovery pass in the complete suite. Original geographic coordinates are unchanged.

[Mobile, closed](qa/map-guide-mobile.png) · [Mobile, expanded](qa/map-guide-mobile-open.png) · [Desktop, closed](qa/map-guide-desktop.png). These are actual local HTTP previews of the proposed UI, not a claim that production was updated.

## Maintenance and approval tests

Tests cover configurable cadence, policy expiry disabling collection, strict source permission/CSV fields, multiple JSON/CSV registrations, exact-source idempotence, conflicting reused snapshot IDs, name/domain/country matching, same-city distinct units, duplicates across permitted sources, foreign branch uncertainty, explicit status assertions, partial/failed/disappearing sources, source-age versus observation-age separation, corruption, missing history and preservation of all current public bytes.

Game development needs no capture evidence for client eligibility; generic film production remains plausible/unconfirmed. Existing individually reviewed audio-only exclusions are retained. New visual/game claims conflicting with an old audio-only review become an explicit review exception, not an automatic public reclassification. Audio names or incomplete service lists alone never exclude a studio. Source technical assertions do not become confirmed facility capabilities.

The GitHub-side tests simulate responses while using real isolated Git repositories and non-force pushes. They cover one open batch, same-period replay, unchanged content across months, merged/closed periods, refused ready-for-review PRs, unexpected public edits, changed heads, previous report revisions, older-state rejection, failed-run artifact recovery, corruption/expiry fallback, network/permission failures, candidate unions and a pushed branch whose PR creation was denied. These are simulation results, not fabricated successful live Actions-bot PR creation. Recognised permission errors retain their exact category without printing credentials.

## Actual schedule and source coverage

The audit enumerated 137 available Actions runs in two pages. It found one successful manual discovery run and one successful scheduled run, and no archive-discovery workflow run. The scheduled run [42666896576](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42666896576) on 9 November used all eight permitted adapters successfully: DNEG, metricminds, Framestore, Larian, RISE, Outpost, Flying Bark and FOLKS. It extracted **58 observations** and retained a **200-candidate queue**. Its recorded creation/start was 17:40:21 UTC, despite the unchanged Monday 07:23 UTC cron; no cause or exact-time guarantee is inferred.

The raw scheduled artifact includes five historical JSON snapshots and a legacy `history_complete: true` flag. All bytes are preserved. V2 treats the flag conservatively because earlier raw completeness is not independently established. The original 6 November 133-candidate artifact is retained too. Source presence, successful extraction and technical integrity are not independent current-operation or capability verification.

The real v2 replay processes the permitted pinned 424-row animation export plus 55 usable observations from the scheduled artifact into **479 source observations / 452 research groups**. It groups 27 duplicate observations, finds existing matches for 419 groups, and leaves 33 with no match. The 180 unresolved groups overlap the matched cohort. This is historical first-ingestion/backfill, not 479 new companies or a completed research batch. It produces **zero reviewed company proposals, approved additions, verified facilities, capability promotions or public updates**. Repeat import adds zero signals and retains identical snapshot history.

Eight official sources are network-scanned automatically. One licensed pinned dataset is processed offline. Seventeen official sources—including EA, Ubisoft and Cinesite—and unregistered/other restricted global sources remain manual. No new source was enabled, no restriction was bypassed, and worldwide research is not declared complete. Per-source status, reuse limits and attribution are retained in the report and [source matrix](README.md#source-coverage).

## Initial failures and final reruns

The first full Python run had two errors in the newly added recovery regressions. A fallback-local `import hashlib` shadowed the module import in the earlier history-copy path. Removing that local import fixed the defect. All nine checkpoint tests, the complete 364-test rerun and the 38-test maintenance rerun then passed. No integrity check was weakened.

The first map-guide browser run inside the command sandbox could not expose the mobile map control. The same test passed outside that sandbox with the configured Leaflet/OSM network access, and the final full suite passed, including a touch-enabled mobile context. The initial failed log is preserved; it is not counted as success. The UI also has an intentional blocked-Leaflet fixture that must preserve directory access. No fake map tiles, relaxed browser assertions or prohibited collection route was substituted.

## Remaining owner actions and limitations

- Review this infrastructure/UI PR and merge only if accepted. The new monthly workflow is not yet on default main and cannot be truthfully claimed as live-tested before that decision. After merge, use its manual `prepare_now` input to inspect a real draft monthly batch. This prepares research, not publication approval.
- Actions-bot draft-PR permissions are unverified until execution. If creation is forbidden, the artifact and any pushed branch remain recoverable. Required-review enforcement is also unverified: a fresh main-protection request returned **403 Resource not accessible by integration**. Drafts and passing tests do not enforce human approval or stale-review dismissal.
- Approving a monthly research archive does not approve company facts. Exact company changes require a separate data PR, source/geography/capability review, rebuilt public assets/checkpoints, full checks and an owner-authorised merge. Existing source-wide rights questions and all historic research queues remain intact.
- Artifacts retain data for 90 days. Rolling weekly history and owner-merged monthly checkpoints provide continuity; deleted or unarchived history cannot be reconstructed. Recovery examines the latest 20 discovery runs and reports gaps. Full archives are bounded at 250 MB and registered source inputs at 100,000 records; larger histories require reviewed partitioning rather than truncation. A long workflow outage or missing checkpoint still requires owner recovery.
- GitHub schedules can be delayed or missed. A missed monthly day can be recovered manually with `prepare_now`. Alerts use Actions failures, annotations and summaries; personal notifications must be enabled. No external uptime monitor or guaranteed email delivery is claimed.
- Current public data quality remains unchanged: all 265 canonical warnings, legacy unknown evidence, unverified source points and historical licensing/research exceptions remain visible. No synthetic benchmark location entered the public database.

The existing 50,000-location and throttled real-catalogue browser scenarios pass. Current measurements are retained in QA, with their actual local HTTP/Chromium conditions; no controlled performance improvement or deployed Pages result is asserted. [Owner operating guide](OPERATIONS.md) gives the weekly/monthly and publication steps.
