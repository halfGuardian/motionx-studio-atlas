# v1.5 New Zealand continuation · executed validation

Executed locally on **7 November 2026** against the proposed PR #15 checkout. Machine-readable results and warnings are in [qa/results.json](qa/results.json). These checks validate data/software integrity, not company operation, source-wide reuse rights or human approval.

| Check | Actual result |
| --- | --- |
| Full Python suite (`python -m unittest discover -s tests -p 'test_*.py' -v`) | **254 passed**, zero failures |
| JavaScript (`node --test tests/*.test.js`) | **72 passed**, zero failures |
| HTTP suites | **63 checks passed**, seven suites: browser_smoke 19; bulk_browser 6; public_catalog_smoke 9; unified_ux 9; boutique_browser 10; annecy_browser 5; nz_census_browser 5 |
| `python tools/validate.py studios.json` | **0 errors / 265 warnings**, 243 retained locations / 119 operating organisations |
| `python tools/check_bulk_release.py` | Full original source replay → boutique → Annecy → NZ reproduces exact proposed public JSON; gzip sidecars validated; zero errors |
| `python tools/nz_research.py check` | All 217 observations accounted for; exact proposals/reports/checkpoints; all 42,239 prior IDs and all 240 prior evidence shards preserved |
| Wave 1 / boutique / Annecy reproduction | Frozen historical reports reproduce against their own original cohorts; no rewritten historical approvals or service categories |
| `python tools/launch_readiness.py check --output data/bulk/reports` | Licensing/review queue reproduces; 42,068 non-A records remain pending; no approval granted |
| Repeat application | Refused on an already extended catalogue; clean full replay is deterministic and does not duplicate references |

The 17 new Python tests cover original service labels, source continuity, every retained ID/shard, foreign-country collisions, researched aliases/domain changes, ambiguous brands, programme-year deduplication, historical-only candidates, closure alerts, municipalities, permission restrictions (including forged historical-origin/approval tags), unstable/missing snapshots, malformed duplicate metadata, exact checkpoints, formula-safe/escaped deterministic reports and pending human review. Five new JavaScript tests cover report filters, every real new reference/route, actual lazy-shard loading, scoped licence exports and corrupted/malformed metadata. The new browser suite checks the actual report, evidence links, keyboard/profile routing, A44's retained ID, current counts/OSM attribution, unpinned-company browsing, government-attributed CSV exports and 390px layout.

The existing browser suites retain organisation/history/filter tests, coincident-coordinate selection, source-evidence loading, CSV notices, mixed-class clusters, company-only profiles, network/truncation/library failures and mobile navigation. No original coordinates were offset. No synthetic location enters the public catalogue.

## Measurements and conditions

[Real-catalogue measurements](qa/real-catalogue-performance.json): **42,298 actual proposed references**; compressed lookup index **2,214,097 bytes**, 1.462 seconds to ready locally, measured search compute 11.5 ms, 217.07 ms end to end for the tested search, 50.5 ms map navigation, 81.6 ms uncached tested profile detail. The explicit throttled scenario (96,000 bytes/sec, 150 ms latency, 4× CPU slowdown, 390px viewport) reached ready in **31.261 seconds**. Large initial lookup download remains an operational limitation; progress/failure/retry states do not expose partial data as complete.

The separate [50,000 synthetic location test](qa/synthetic-50000.json) reached ready in 1.247 seconds, tested search at 8 ms, profile at 60.4 ms and the measured viewport render at 2.9 ms. Those compact repeated fixtures are **not acquired companies** and their compression/timings do not predict the real global catalogue's download performance. Existing browser_smoke also exercises selection among 50,000 coincident synthetic locations without coordinate movement.

Tests use local HTTP under a GitHub Pages-style repository subdirectory, installed headless Chromium, desktop and 390px mobile emulation. Runtime versions are recorded in `qa/results.json`. These are **not deployed Pages verification**, a physical low-memory phone or source-independent business verification. CDN/map tests use the existing Leaflet and OpenStreetMap services; attribution remains present.

## Disclosed warnings

The [canonical validation report](qa/canonical-validation.json) retains all **265** existing warnings, including approximate city pins, legacy evidence unknowns and possible legitimate co-located facilities. All **13 legacy unknown-evidence records** remain unchanged; this census does not falsely resolve them.

The [exact source replay report](qa/source-replay.json) includes every combined-catalogue warning category. These overlap and must not be summed as unique failures:

- 42,055 unreviewed source references; 40,376 source points have unverified facility precision.
- 1,679 company references have no coordinates; 1,412 have unspecified company-source reuse terms.
- 170 source-location observations lack a city; 14 lack a country.
- 120 records have possible-duplicate review metadata, including **three** new foreign-name collisions. Records are preserved; no automatic merge/deletion.
- 332 historical boutique, 172 historical Annecy and **59** new NZ references require review.

## Failures found and corrected during development

The browser suite found three new collision references whose duplicate notes lacked the renderer's expected `reasons` array. The schema is now consistent, and Python/JavaScript validation reject malformed duplicate metadata before rendering. The duplicate filter expectation now follows the actual 120 candidates instead of the old 117. The new report's long facility status label caused mobile overflow; readable words and wrapping fix it without hiding content. Two test expectations were corrected to retain both 2Up Games programme-year rows and inspect an evidence link's URL instead of assuming the URL was its visible label. Final suites pass; no failing check is suppressed.

## Review and coverage limitations

**No human approval or precision result is claimed.** The pending NZ worksheet, four facility proposals and historical 37-row Annecy precision review require actual human review. Source self-report/programme participation is not independent operation verification. PR/draft status and passing Actions do not enforce required review; branch-protection enforcement has not been independently confirmed for this update.

The NZ census remains incomplete: Auckland pages 2/4/5 and the full Wellington directory are unavailable; NZGDA's full text roster is not enumerated; VFXG's 45-company list is not obtained; Waikato requires consent and Otago/Southland prohibits commercial roster copying/caching. Regional support pages are not complete vendor rosters. Newly retrieved restricted Otago roster content was redacted after the policy review and was not imported. Full details and 18 source scopes are in [the source report](README.md) and [coverage dashboard](reports/coverage.html).

Maintainer source-rights, identity, current-operation and facility-evidence review is still required before an authorised merge. No merge, deployment, Pages setting change, restricted collector enablement or automatic publication is performed.
