# Global discovery, identity and geographic visibility programme

This is one worldwide programme, tracked in [issue #17](https://github.com/halfGuardian/motionx-studio-atlas/issues/17). It is **not globally complete**. Source observations, company identities and physical facilities are separate denominators. Software checks do not independently establish current business operation.

## Protected parent and delivery

The development branch is `codex/global-discovery-visibility`, based on exactly `efd52a86e66417438830aac285e3fffee3aa0fa0`. Its draft PR must target `codex/v1.5-nz-census-wave1` and depend on draft PR #15. Do not update that parent branch, merge, deploy or change Pages settings. A maintainer may rebase/retarget this work after the parent's authorised merge. Issue #16 remains open pending reviewed delivery.

The parent contains 42,296 references: 243 retained locations, 40,376 source-location observations and 1,677 company references. These are not 42,296 independently verified facilities. `inputs/baseline.json` binds all original record identities and values, public files, counts and the root database. The display sidecar does not change them.

## Internal checkpoints

1. **Visibility implemented; review pending.** All 1,677 company references have a reproducible geographic disposition. Floating Rock has one separate, licensed Wellington city reference, supported by its official contact page and GeoNames. It retains null original coordinates, Class C and no verified facility capability. Frame Machine retains its existing Class C source-location point. Five actual-catalogue HTTP browser checks passed, including filters, keyboard, mobile, CSV and coincident-coordinate selection.
2. **Worldwide source assessment in progress.** Track every existing catalogue country/territory. Search results identify source leads only; page access, reuse policy and demonstrable enumeration are separate assessments. Reuse complete permissible snapshots and retain partial/blocked source scopes.
3. **Global identity reconciliation pending.** Compare every admitted source observation with the complete catalogue. Name/domain matches never independently establish a branch, parent relationship or current operation.
4. **Evidence rules and proposals in progress.** Identity, geography, company service assertions and independently reviewed facility capabilities remain distinct. No automatic evidence promotion or inherited foreign geography.
5. **Consolidated dashboard pending.** Country, region, source scope, dispositions, rights, geography and review decisions must have explicit denominators.
6. **Incremental maintenance pending.** Durable snapshots, integrity checks, freshness and investigation signals; no automatic closures or canonical publishing. Future scheduling requires a reviewed policy decision.
7. **Global QA pending.** Full existing suites, actual-data browser/performance checks, deterministic replay and a source-separated held-out worksheet. Human precision/recall remain null until independent labels exist.

## Resume and validate

Run from the repository root:

```sh
git status --short
git branch --show-current
python tools/global_visibility.py check
python -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.js
python tests/global_visibility_browser.py
python tools/check_bulk_release.py
python tools/launch_readiness.py check --output data/global-programme/reports/readiness
```

To regenerate the separate display projection after an explicitly reviewed input change, run `python tools/global_visibility.py prepare`, then regenerate the new readiness reports with `python tools/launch_readiness.py generate --output data/global-programme/reports/readiness`. Historical parent readiness reports stay unchanged.

Continue source assessment, then reconciliation, dashboard, incremental maintenance and full QA without new country-by-country prompts. Never mark an inaccessible or unenumerated directory complete. Keep unsupported company/facility claims in research proposals. Source review dates describe actual review, not blanket independent verification. No personal contacts, private business data, authored directory prose or media belong in these reports.

## Human gates

All new display references and research assessments are agent-prepared proposals in this stacked draft PR. They are not fabricated human approvals. Canonical additions/corrections require evidence review and an authorised PR merge. Source-wide collection/reuse permissions, ambiguous operating identities, physical facility capabilities and closure/relocation claims require separate review where unresolved. A draft PR or passing test does not itself enforce required human review.
