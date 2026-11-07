# Global discovery, identity and geographic visibility programme

This is one worldwide programme, tracked in [issue #17](https://github.com/halfGuardian/motionx-studio-atlas/issues/17). It is **not globally complete**. Source observations, company identities and physical facilities are separate denominators. Software checks do not independently establish current business operation.

## Protected parent and delivery

The development branch is `codex/global-discovery-visibility`, based on exactly `efd52a86e66417438830aac285e3fffee3aa0fa0`. Its draft PR must target `codex/v1.5-nz-census-wave1` and depend on draft PR #15. Do not update that parent branch, merge, deploy or change Pages settings. A maintainer may rebase/retarget this work after the parent's authorised merge. Issue #16 remains open pending reviewed delivery.

The parent contains 42,296 references: 243 retained locations, 40,376 source-location observations and 1,677 company references. These are not 42,296 independently verified facilities. `inputs/baseline.json` binds all original record identities and values, public files, counts and the root database. The display sidecar does not change them.

## Internal checkpoints

1. **Visibility implemented; review pending.** All 1,677 company references have a reproducible geographic disposition. Floating Rock has one separate, licensed Wellington city reference, supported by its official contact page and GeoNames. It retains null original coordinates, Class C and no verified facility capability. Frame Machine retains its existing Class C source-location point. Five actual-catalogue HTTP browser checks passed, including filters, keyboard, mobile, CSV and coincident-coordinate selection.
2. **Worldwide assessment checkpoint implemented; enumeration incomplete.** All 178 represented countries/territories have saved English source-search receipts (3,562 references / 2,329 distinct result URLs). Fifteen sources have additional page/access assessments across seven regions. Search leads are not directory enumeration or reuse permission. Native-language/subnational research and most source rights remain pending.
3. **Global reconciliation checkpoint implemented; identities pending review.** Every 44,394 replayed observation is compared with the complete catalogue, including whole retained datasets and historical discovery queues. Stable IDs, duplicate observations, aliases, operating-name conflicts, branch-shaped links and foreign-geography cases remain separate. Navigation links and generic production entries are not new companies by default. No automatic merges or company additions.
4. **Evidence rules and geographic audit implemented; facility review pending.** Identity, geography, company service assertions and facility capabilities have independent claim states. Every unpinned company is accounted for. The four retained facility dossiers still need independent review; no new confirmed capability or facility is created.
5. **Consolidated dashboard implemented.** All country gaps, source scopes, outcomes, rights, company geography and human gates are readable in one dashboard. Region/country/source/rights/outcome/text filters and content-bound working-decision exports are tested. Downloads are not authenticated approval.
6. **Offline maintenance implemented and actually replayed.** Full 424-row licensed snapshot, durable embedded history, integrity checks and repeat replay with zero new signals. Failure/partial-history tests suppress closure inference. Manual Actions replay is defined with read-only permissions; no new continuous monitor or schedule is enabled.
7. **QA checkpoint in progress.** Full suites, real 42,296-reference and 50,000 synthetic-location browser benchmarks are run locally. Fourteen purposive evaluation candidates were frozen before matching, across seven regions; 0 exact-source overlaps / 2 source-domain overlaps with replay are disclosed. Nine have candidate matches, five are unmatched. All lack independent human labels; precision/recall remain null. This is not a blind global business-verification benchmark.

## Resume and validate

Run from the repository root:

```sh
git status --short
git branch --show-current
python tools/global_visibility.py check
python tools/global_programme.py check
python tools/global_programme.py maintenance-check
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.js
python tests/global_visibility_browser.py
python tests/global_review_browser.py
python tools/check_bulk_release.py
python tools/launch_readiness.py check --output data/global-programme/reports/readiness
```

To regenerate the separate display projection after an explicitly reviewed input change, run `python tools/global_visibility.py prepare`, then regenerate the new readiness reports with `python tools/launch_readiness.py generate --output data/global-programme/reports/readiness`. Historical parent readiness reports stay unchanged.

Continue source assessment, then reconciliation, dashboard, incremental maintenance and full QA without new country-by-country prompts. Never mark an inaccessible or unenumerated directory complete. Keep unsupported company/facility claims in research proposals. Source review dates describe actual review, not blanket independent verification. No personal contacts, private business data, authored directory prose or media belong in these reports.

## Human gates

All new display references and research assessments are agent-prepared proposals in this stacked draft PR. They are not fabricated human approvals. Canonical additions/corrections require evidence review and an authorised PR merge. Source-wide collection/reuse permissions, ambiguous operating identities, physical facility capabilities and closure/relocation claims require separate review where unresolved. A draft PR or passing test does not itself enforce required human review.
