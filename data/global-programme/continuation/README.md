# Global company research and commercial-scope review

Continue draft PR #18 on `codex/global-discovery-visibility`, stacked on unchanged PR #15 (`efd52a86e66417438830aac285e3fffee3aa0fa0`). This pass resumes reviewed head `db8265e85b259d4b17214244eb0219c869207b1a`; the original programme checkpoint remains bound to its historical inputs.

[Delivery and exact outcomes](DELIVERY.md) · [Evidence dashboard](reports/dashboard.html) · [Concise exceptions](reports/review-exceptions.md) · [Validation](validation.md).

All **725 saved research keys / 753 observations** now have an individual assessment, including the **656 outstanding keys** at the reviewed head. This is an assessment pass, not completed verification: identity, access, rights, historical-operation and geography questions remain explicit. The complete machine-readable checkpoint retains every key and precise unresolved reason. Historical exhibitor participation, a matching algorithm and a working website do not independently verify an operating studio.

**184 provisional Class C company-reference proposals** are consolidated with the original 30 exact payloads and their before/after audit. Proposals have stable research/company IDs, source URLs and actual review dates, null coordinates, no confirmed facility capabilities and no invented ownership or approval. They are outside the canonical public database. Company-level service claims are distinct from verified site capabilities.

Commercial scope uses six roles: explicit sector eligibility as potential client, service provider, both, plausible unconfirmed prospect, adjacent/insufficient evidence, or individually reviewed out of scope. Games, animation and VFX are eligible client sectors without capture evidence. Generic production/agency or publishing categories do not establish a high-confidence client; visual-production tags alone do not establish an external service offer. Original source categories remain unchanged. Purchasing intent, budgets and current operation remain unknown.

All **42,296 original records**, full evidence/coordinates and historical source checkpoints remain frozen. Four reviewed audio-only references remain reversibly excluded from normal search/map/CSV and accessible in audit mode; sound-name signals are never automatic exclusions. Floating Rock's separate Wellington display reference and Frame Machine's Santa Monica point remain unchanged.

Reproduce without network, publication or human approval:

```sh
python tools/global_continuation.py prepare
python tools/global_continuation.py check
python tools/global_programme.py maintenance-check
python tools/package_global_review.py --output /tmp/motionx-review-new
python -m http.server --directory /tmp/motionx-review-new 8000
```

Use a fresh output directory. Open `http://localhost:8000/` to review the standalone bundle. `prepare` only reproduces research reports and the reversible commercial sidecar; it cannot import company proposals, move coordinates or authorise publication. Main database/shards and historic source records are not changed.

`reports/recommendations.json` groups the exact proposed fields and original-30 audit. `reports/research-checkpoint.json` records every completed, uninvestigated and evidence-unresolved key, input hashes and continuation commands. `reports/geographic-associations.json` preserves all 256 saved city associations, including 238 requiring individual geographic research. `reports/source-followup.json` documents ten regional source follow-ups with actual access results, enumeration limits and reuse uncertainty. No source or country census is declared complete.

Continue unresolved cases using their existing candidate IDs and append evidence-backed decisions; do not replace historical values or treat a failed fetch as closure. Source-wide collection permissions, independent human precision labels and publication approval remain separate gates. No confidential information, personal contacts, CRM notes, copied source prose or media are included.
