# Final v1.5 validation · READY FOR HUMAN REVIEW

Executed **7 November 2026** against the proposed PR #15 checkout. [Machine-readable results](qa/results.json) include runtime versions, all warning categories, initial attempts and conditions. Passing tests do not verify business claims or authorise publication.

| Check | Final result |
| --- | --- |
| Full Python suite | **269 passed**, zero failures |
| All JavaScript tests | **78 passed**, zero failures |
| Full HTTP/browser suites | **69 checks passed**, eight suites: canonical smoke 19; 50k sharded catalogue 6; real catalogue 9; unified UX 9; boutique 10; Annecy 5; original NZ 5; final quality review 6 |
| Canonical `studios.json` validation | **0 errors / 265 retained warnings**, 243 locations / 119 operating organisations |
| Full source reproduction | **Passed**: licensed bulk archive → boutique → Annecy → frozen raw-59 NZ → final gate |
| NZ parent/final checks | Exact original source reports and new input/report checkpoints reproduce; no source/approval history rewritten |
| Original-data integrity | **42,239 previous IDs, 240 prior detail shards, root database, original coordinates/evidence/relationships unchanged** |
| Human review continuity | Original 29-entry NZ and 37-row Annecy worksheets unchanged; new 91-item sheet has zero completed decisions/approvals |
| Current licensing/research queue | Reproduces 42,066 non-A review entries; no approval granted |
| Repeat application | Refused on the already gated tree; clean source replay is deterministic |

New regressions cover every one of the 59 audits, source-only programme classifications, the playtesting correction, rights-scope distinctions, all 27 identity keys and the separate office-closure alert, four dossiers, staged-record exclusion, source/ID/hash preservation, unsupported approval/facility metadata, malformed review inputs and private-field rejection, formula-safe/escaped reports and deterministic outputs. The JavaScript checks exercise actual lazy records and ensure staged identities cannot be loaded or exported through the directory. Selecting “accept” in the working sheet never becomes an approval or a reviewer identity.

The new browser suite opens the actual 91-item dashboard, AND-filters companies by relevance/readiness, downloads a local working draft without POSTs or publication, reads municipality/current-operation conflicts and the dated closure alert, visits a staged deep link, checks source-association and no-pin profile labels, exports the corrected playtesting reference with scoped attribution and review metadata, and checks 390px keyboard layout. Existing suites continue to exercise organisation/history navigation, filters, map/shared coordinates, hostile text/links, CSV formulas, network/library/truncated-data failures, partial-result protection, profiles and synthetic scale.

## Actual measurements and limits

[Real proposed catalogue](qa/real-catalogue-performance.json): **42,296 actual references**, compressed lookup index **2,213,984 bytes**, local initial-ready **1.881 seconds**, tested search compute **13.2 ms**, tested uncached profile detail **147.7 ms**. The explicit 390px / 96,000 bytes/sec / 150ms / 4× CPU scenario reached ready in **31.808 seconds**. The initial lookup download remains substantial. No sharding/backend migration or performance improvement is claimed from these noisy single-run comparisons.

The [separate 50,000 synthetic-record test](qa/synthetic-50000-performance.json) reached ready in **1.599 seconds**, search **14.8 ms**, profile **41 ms**, measured viewport render **4 ms**. Repeated synthetic data compresses very differently from the real catalogue; it is not acquired company coverage and does not enter public files. The canonical compatibility suite also passes selection/navigation among 50,000 coincident synthetic locations without moving coordinates.

Conditions: local HTTP in a repository subdirectory, installed headless Chromium, desktop and 390px mobile emulation. Network/CPU throttling is explicit only where recorded. These checks are **not deployed GitHub Pages verification**, physical low-memory-device testing or independent company/facility verification.

## Failures observed and addressed

- A pending search debounce could close a newly opened hash profile. Route handling now cancels that pending timer; the final browser check waits beyond the debounce and verifies the profile stays visible.
- The mobile worksheet test initially targeted an ambiguous profile selector after comparison links were added. It now explicitly targets the intended provisional-company link; actual comparison links remain available.
- An initial browser-smoke run, concurrent with full Python/source replay, failed to load the 50,000 canonical compatibility fixture and displayed “Studio data unavailable”. The original cause was not conclusively established. A complete isolated rerun passed all 19 checks, and the independent 50,000 sharded test passed. The test now records the actual data-error text if this recurs. Initial attempt exit codes are retained in `qa/initial-browser-attempts.json`; no failure is hidden as a successful initial attempt.

Final local suites pass. CI is run again on the pushed commit; its actual status and artifact links are reported in the PR instead of being predeclared here.

## Warnings and remaining review

All **265 canonical warnings** remain disclosed in [the canonical report](qa/canonical-validation.json), including city references, 13 unknown-evidence legacy records and legitimate possible co-located facilities. No record is deleted or auto-corrected to silence them.

The [source-reproduction report](qa/source-reproduction.json) records overlapping combined-catalogue warnings: **42,053** unreviewed source references; **40,376** source points with unverified facility precision; **1,677** company references without coordinates; **1,412** unspecified-term company references; **170** source locations missing a city and **14** missing a country; **120** possible-duplicate review records, including three NZ foreign-name collisions. The 332 historical boutique, 172 Annecy and 57 current NZ leads remain review material. Two proposals are staged, and 27 new minimal-reference scopes require maintainer rights review. These categories overlap and must not be summed as unique failures.

Human decisions, independent facility reviews, current-operation research and the 27 exact minimal-rights-scope decisions remain pending. Source-authorised agency fields do not clear company material. Staging in a public repository is not private storage. Required-review/branch-protection enforcement has not been independently confirmed; draft status, working-sheet selections and tests alone do not enforce human approval.

The census remains incomplete because partial/unavailable and restricted regional sources have not been fully accounted for. VFXG's 45-business list remains unobtained. No restricted source is enabled or accessed through a workaround, and no merge, deployment or Pages settings change is performed.
