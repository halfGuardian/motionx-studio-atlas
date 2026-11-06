# v0.9.1 — Discovery Triage and Source Coverage

Research/triage reviewed **6 November 2026 (Pacific/Auckland)**. Public database unchanged: **129 locations / 66 organisations**. No studio records or research claims are published or approved.

## Actual artifact inspection

Input: [successful discovery run 42149794259](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42149794259), `studio-discovery` artifact `13472231299`, ZIP digest `c3f498744edc26da7d0e627e2b1da1e87ac41b28c8b304e49d0c2ace2b66ecc3`. It contains **92 extracted observations** and **41 older backlog entries**, totalling **133 candidates**.

Codex could inspect artifact metadata, but could not download ZIP bytes into its workspace: both the GitHub CLI artifact endpoint and the connector-provided temporary file URL were inaccessible. The requested fallback runs **inside GitHub Actions** with read-only repository/actions permissions. It downloaded the original artifact successfully, verified its digest, read `queue.json` and `report.json`, cross-referenced the canonical database and generated the reports. Codex inspected the real per-candidate decisions, counts and coverage through decoded GitHub job logs. No local re-creation is presented as the original artifact.

[Completed triage run 42151392352](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42151392352) provides the [machine/human reports and preserved original inputs](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42151392352/artifacts/13471249912). Later PR runs repeat the process with the final code. Download `studio-discovery-triage` to inspect `triage.json`, `summary.md`, byte-preserved `queue.json` and `report.json`, and any carried `history/` snapshots. Artifacts have 90-day retention; this committed summary and the labelled observed-link projection preserve the release findings beyond that retention window.

| Classification | Candidates |
| --- | ---: |
| Already represented | **46** |
| Potentially new | **14** |
| Irrelevant / non-studio observation | **24** |
| Requiring research / unresolved | **49** |
| Total | **133** |

These are **observation counts, not additional studios**. The 46 represented observations include **38 location matches and eight organisation-only matches**. The latter seven Cinesite operator homepages and legacy Ubisoft Toronto identity do not prove facility identity or complete branch coverage. All discovery evidence confidence remains `unknown`; triage confidence describes matching/routing only. The 49 unresolved entries include all **41 preserved v0.8 backlog candidates**.

## What each source actually returned

| Source | Original observations | Triage result | Interpretation / change |
| --- | ---: | --- | --- |
| Ubisoft | 41 | 20 represented, 14 potentially new, 7 research | 19 scoped location matches plus legacy Toronto organisation identity; 14 unmatched branch links remain candidates. Stockholm, Sydney and San Francisco conflict with historical closure/ramp-down research. Paris area, Taiwan and two HQ links do not establish individual production facilities. |
| Cinesite group | 27 | 7 represented organisations, 20 irrelevant | Seven “Find out more” operator homepages are meaningful organisation pointers. The rest are navigation, services, policy, contact or article links, not 20 studios. Narrow future collection to operator CTA labels and root URLs, allowing future operator domains without fetching them. |
| DNEG | 19 | 19 represented locations | Every branch URL matches an existing location-specific published source. Meaningful branch links, zero new facilities from this run. |
| Electronic Arts | 1 | 1 irrelevant | The single URL is `https://www.ea.com/careers/locations`, labelled “Locations”: general navigation, not an identified studio. Automation disabled pending written permission. |
| Imaginarium | 1 | 1 research | A “Skip to Content” link normalised to the locations index. The index is a useful research page but the observation identifies neither of its two stages individually. |
| metricminds | 3 | 3 irrelevant | Performance capture, animation and cinematics service/self-navigation links, not three separate facilities. Existing Frankfurt facility remains unchanged. |

The 14 unmatched Ubisoft links concern Cary, Los Angeles, Atlanta, Tokyo, Taguig, Guildford, Barcelona, São Paulo, Lyon, Pune, Malmö, Montpellier, Annecy and Milan. **No current operation, exact municipality, physical production-site type or capability is newly asserted.** Several may overlap older unresolved research or encompass support/corporate functions. They require primary-source review and safe duplicate checks before any import.

### EA coverage and access decision

The original link adapter accepts only ordinary `<a>` links matching `www.ea.com/(ea-studios/|careers/locations)`. The [current studio roster](https://www.ea.com/careers/teams/ea-studios) exposes many studio/job links outside those accepted URL shapes/domains. The artifact proves the one retained observation was only the generic Locations link; this is **not** evidence that EA has one studio. Parser/URL selection limits explain the coverage gap; no JavaScript execution or access-block bypass is introduced.

EA's [current robots file](https://www.ea.com/robots.txt), reviewed on 6 November, explicitly prohibits web scraping and text/data mining unless authorised in writing. The registry now records `enabled: false`, the review date/source and the reason. The historical observation, sources and dates are preserved. No expanded EA adapter is enabled. A researcher can seek permission or a permitted official feed/export. Screenshots can support human review where terms permit, but automated screenshots/OCR are not used to work around an automated-collection restriction. Public source review is not independent physical verification.

## Repeatable triage

```sh
python tools/triage.py \
  --queue /path/to/studio-discovery/queue.json \
  --report /path/to/studio-discovery/report.json \
  --discovery-run 42149794259 \
  --output /tmp/motionx-triage-run-1
```

Use a fresh output directory. The command validates inputs and does **no network requests**. It preserves the original candidate objects, URLs, confidence, observation dates and content hashes, then records separate classification, match scope, location/organisation IDs, matching reasons and triage confidence. Input file checksums and canonical/config hashes identify the exact inputs. A matching source is not a new capability verification.

Matching uses source organisation/group scope, exact location URLs, scoped stable location IDs and city slugs, or structured city/country evidence. It does not match different operators solely because they share a city. Generic contact/service/navigation links do not become physical facilities. Parent rosters match operating identities without collapsing subsidiaries or all their branches. Known historical conflicts, HQs, market indexes, missing links and change signals go to research.

Exact repeated observations across sources are linked for review by URL + label + city/country; nothing is deleted or merged. Different backlog candidates sharing one roster URL are not duplicates merely because they cite the same source. Classification remains advisory and is recomputed against the supplied database. It does not edit `review_status`, `confidence`, canonical data or approval files, and cannot satisfy the existing content-bound publication approval checks.

## GitHub Actions reports and continuity

- The ordinary weekly/manual **Discover studio candidates** workflow now triages its queue and uploads **both** `studio-discovery` and `studio-discovery-triage`, with a Markdown Actions summary.
- **Triage discovery observations** can process an existing run via manual `discovery_run` input (defaulting to the user-specified initial run). Its PR integration check uses the latest successful main-branch discovery run, avoiding a permanent dependency on one expiring historical artifact. Missing/expired artifacts fail visibly rather than fabricating counts. These workflows have only `contents: read` and `actions: read`.
- The original queue and source report are copied byte-for-byte into the triage output. Existing `history/` is carried into the fallback artifact too.
- Discovery uses `--previous-run` to archive prior raw queue/report files and carry earlier archives forward by SHA-256 filename. Identical snapshots are stored once; distinct historical content is not truncated. This preserves previous observed labels, evidence hashes and event reports rather than only the latest state. Artifacts still need intentional long-term archival because GitHub retention is finite.
- Extraction fingerprints record URL/adapter/filter changes. A changed filter does not create disappearance events on upgrade. Historical candidates excluded by a new filter stay in the queue and are not marked missing in later runs. Network errors, empty extraction and disabled EA collection do not delete observations or imply closures.
- The observed-link fixture is explicitly a **projection from GitHub job logs**, not the original queue or a new evidence review. It tests routing of the real 92 link labels/URLs plus the existing backlog. Full original metadata remains in the Actions artifacts.

Cinesite filtering improves signal without claiming complete facility coverage. DNEG/Ubisoft branch links remain navigation pointers requiring current site evidence. Service/facility indexes need future source-specific extraction or manual review; no address/capability is invented to fill those gaps. Acquisition/closure news requires separately approved sources and human research, not conclusions from omitted roster links.

## Tests

**78 Python tests, 20 JavaScript tests and 15 HTTP browser checks passed.** GitHub Actions triage and public-atlas validation succeeded against the actual artifact. New coverage exercises source/label filtering, source-scoped matching, organisation-versus-location scope, historical conflicts, repeat observation deduplication, network failures, disabled source retention, unchanged candidate confidence, raw snapshot history and continuity across filter changes.

Canonical validation remains **0 errors / 147 documented warnings**. The public `studios.json` is byte-for-byte unchanged from the v0.9 baseline. HTTP checks preserve map/search/filter/profile/CSV/mobile behaviour and pass the 10,000-location viewport/selection fixtures. No automatic approval, import, merge, deploy or Pages-setting change is included.
