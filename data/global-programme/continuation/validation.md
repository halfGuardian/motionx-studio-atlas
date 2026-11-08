# Validation of the completed backlog assessment pass

These checks concern the proposed PR checkout and downloaded/local review bundle. They are not production deployment, independent business verification or human publication approval.

## Executed suites

- Full Python: **308 passed** (final run 99.264 s; earlier full run also 308 passed).
- JavaScript: **90 passed**, zero failed.
- Canonical `python tools/validate.py studios.json`: **zero errors / 265 retained warnings**.
- Eleven complete reproduction/preservation commands: all passed; exact commands and return codes in `qa/completion-reproduction.json`.
- **89 HTTP/browser checks passed across all 12 suites**, including final reruns of the two initially failing suites. Results and performance are recorded in `qa/completion-results.json`; the isolated large-fixture result is recorded separately from the initial timeout.
- Exact report reproduction also passed with `PYTHONHASHSEED=42`, guarding against order-dependent generated files.

The reproduction commands cover the full bulk catalogue, lossless compressed data, boutique and Annecy history, frozen Wave 1, NZ continuation/final gate, current licensing/readiness reports, commercial sidecar, every company-only geography, global source checkpoints and actual permitted snapshot replay. Repeat snapshot ingestion produces no new signals; discovery cannot write the canonical database. Stable IDs, all full-record/evidence hashes, original coordinates and the 209 protected historical files remain unchanged. No synthetic row is admitted.

Regressions cover game-developer eligibility without capture; generic production/publishing as plausible only; visual tags without an invented service offer; formula-safe CSV; matching search/map/filter/export scope; individual reversible audio-only exclusions and multidisciplinary retention; country evidence and homonym dismissal requirements; duplicate proposal prevention and explicit alias targets; all original 30 payloads; Floating Rock, Frame Machine, shared-coordinate selection, mobile keyboard access and error recovery; additional city references versus correction proposals; complete saved-key and city-queue continuity.

## Initial failures and corrections

An earlier targeted continuation run encountered the stale-generated-report guard during ongoing input expansion; regeneration and reruns passed. The first checked checkpoint `64f8692` passed its local 303 Python / 89 JavaScript tests, but [Actions run 42453732576](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42453732576) subsequently failed: its generated dashboard was stale, and a browser test still assumed exactly one unknown-country card when 46 were present. The current reports are regenerated/reproducible; selectors now account for all country matches and distinguish branch cards.

In the final local browser pass, the legacy 50,000-row raw-JSON fixture hit the existing request timeout while complete source reproduction was running. No database/schema failure was reported; the app displayed its explicit timeout state. That attempt and its traceback are retained, followed by an isolated rerun. The first standalone artifact attempt also found two cards containing “Ubisoft Japan”, rather than the expected one; the assertion now specifically checks the branch card and separately verifies the full country count. The corrected standalone suite passes all three checks.

The initial attempts are evidence, not suppressed by later success. No timeout was increased and no production fetch/schema guard was weakened. Large unsharded raw fixtures remain a resource-sensitive path; the real compressed catalogue and separate sharded synthetic fixture are measured separately.

## Measured performance and conditions

Local Python 3.12, Node 24 and installed Chromium 155; HTTP served under a GitHub Pages style subdirectory. Real-data and sharded-fixture measurements came from the complete browser pass, with source-reproduction work also running in the same workspace. They are single samples, not a statistically established speed comparison or physical low-memory-device test.

| Workload | Reviewed db8265e sample | Current sample |
|---|---:|---:|
| Real 42,296 stored / 42,292 normal records, cold readiness | 2.027 s | 2.166 s |
| Real data, 96,000 bytes/s + 150 ms + 4× CPU + 390px | 33.165 s | 32.666 s |
| Complete audit query | 23.1 ms | 26.2 ms |
| Search computation | 12.3 ms | 11.1 ms |
| 50,000 synthetic locations, sharded readiness | 1.701 s | 1.545 s |
| Sharded synthetic search | 7.7 ms | 7.1 ms |

Current real-data profile detail: 122.2 ms uncached; map navigation: 38.3 ms. Sharded synthetic profile: 57.5 ms; viewport update: 10.6 ms. The real compressed index remains 2,213,984 bytes and uncompressed compact index 5,100,321 bytes. Synthetic repeated fields compress unusually well and do not establish acquisition of 50,000 actual studios. The isolated raw-JSON 50,000-row fixture passed in 13.4 s; exact timing is in `qa/completion-raw-performance.json`.

## Warnings, evidence and approval limits

The 265 canonical warnings remain visible: approximate coordinates, legacy unknown evidence and possible legitimate co-located facilities are not silently removed. The catalogue still contains 13 legacy unknowns, 42,053 source references without independent current-operation verification and 1,677 unpinned company references. Existing source-specific/UNSPECIFIED rights and duplicate-review warnings remain in the reproduced licensing/readiness reports. Proposed Class C references are not included in these published counts.

All 725 keys have an assessment, while 263 identity, 104 unresolved evidence/access/rights, 14 historical-operation and 55 geography-only outcomes remain explicit follow-up work. The separate geographic queue still needs 238 individual reviews. Twelve keys are explicit EA/PROGISS rights holds; ten new regional follow-ups are partial or inaccessible, never declared complete. The 14 independent evaluation labels remain absent; precision/recall stay null.

Draft PR #18 remains stacked on unchanged PR #15. Passing tests or downloading the review artifact does not approve company claims, source reuse or canonical publication. Required-review enforcement remains unconfirmed. No merge, deployment, Pages settings change, restricted collector enablement or fabricated reviewer is performed.
