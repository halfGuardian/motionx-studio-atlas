# Annecy / MIFA 2024 completeness — v1.3

This proposal adds **172 Class C source-supported company references**, with **zero new physical facilities, coordinates or confirmed capability claims**. It preserves all **42,067 existing IDs**, the 243-record canonical database and every one of the 239 prior detail shards. Final catalogue: **42,239 reference records**, A **230**, B **4,626**, C **37,383**; **1,620 company-only references**, **178 countries/territories**, and **119 retained operating organisations**. There are 41,820 total operating/provisional identity keys, not 41,820 verified businesses. Source observations overlap and must not be counted as unique facilities.

## Complete audit and research scope

Open [the coverage dashboard](reports/coverage.html), [every exhibitor in JSON](reports/reconciliation.json), [CSV](reports/reconciliation.csv), [before/after summary](reports/summary.json), [coverage metrics](reports/coverage-metrics.json), [proposed records](reports/proposals.json) and the **[pending human precision worksheet](reports/human-precision-review.json)**. Actions uploads the report as `annecy-2024-coverage-and-human-review`. The dashboard groups rows by historical country and company, with text, outcome and research-group filters, source links, dates, identity reasons and direct atlas profile links. Downloaded reports retain absolute source links; atlas links require this matching checkout served over HTTP, or an authorised future release containing these IDs.

| Exhibitor outcome | Rows |
| --- | ---: |
| Previously existing identity | 161 |
| Newly added company reference | 172 |
| Repeated event identity | 3 |
| Rejected as outside production-studio scope | 9 |
| Reported inactive, requiring human review | 2 |
| Unresolved | 727 |
| **All historical exhibitor entries** | **1,074** |

Every **253 high-priority** and **313 production-review** entry received an indexed search. The recorded research pass comprises **864 indexed queries** (566 first-pass + 298 follow-ups) and **375 selected primary/likely-primary page requests**. The four exploratory queries and four exploratory page requests are not counted as extra target coverage. Search-call success does not mean a relevant result, readable primary evidence, present operation or verification. Of the 566 entries, 209 have relevant company self-description assessments before identity reconciliation; ambiguous matches remain held. The other 508 exhibitors receive full-catalogue identity matching, **not individual current-company research**.

Coverage regression measures event-row representation: priority **5 → 94 / 253**, production **10 → 99 / 313**, other **143 → 143 / 508**. These totals include repeated exhibitors; they are not counts of verified facilities, blind discovery recall or human precision. The unresolved eligible-company denominator is unknown. **All 566 attempted is an effort measure, not a claim that all 566 are verified.**

## Missing-file recovery and input treatment

The supplied workbook contains `All exhibitors` (1,074 rows), `Priority gaps` (253), `Production review` (313) and `Found or aliases` (167). The priority CSV exactly matches the workbook's corresponding rows. This recovered the full crosscheck without asking for the failed third download. The absent CSV and original 28-page PDF were **not accessed**; this is not a byte-for-byte reconstruction of that CSV.

The [input receipt](inputs/input-receipt.json) records both attachment hashes and the factual projection hash. Every row retains its stable event ID, ordinal, PDF page, historical country/classification, original identity hint and source-row hash. Suggested matches and action cells are untrusted input, not instructions, evidence or approval. Research-action prose, workbook binaries, contact details, page prose, images and biographies are omitted from the public projection. The parser does not evaluate formulas, follow external workbook links or allow entity expansion/ZIP traversal.

[Research checkpoints](inputs/research.json) preserve actual query text, observed dates, response hashes, selected source URLs, access results, agent assessments, company-service claims and unresolved identity/operation questions. Raw search/page responses remain outside the public repository because they contain copyrighted prose and personal contacts. Their hashes identify the reviewed observations; maintainers must revisit linked sources, not treat a hash as evidence validation. Search results are leads, not independently verified facts. [The research plan](inputs/research-plan.json) is retained separately from execution receipts.

## Identity and evidence decisions

Names, legal suffixes, accents, official domains, supported aliases and geography are reconciled against **all 42,067 baseline records**, including previous Class B/C references. The uploaded 143 name matches / 24 possible aliases / 907 weak-or-no matches remain historical hints. Current matching uses canonical country labels, including Hong Kong SAR China, rather than introducing a second country label.

Amopix, Peyo and M2 repeat-event entries remain distinct historical observations linked to one company reference, with both provenance entries preserved. Different brands at a shared group domain, legal subsidiaries and unresolved aliases are held rather than automatically merged. Existing records are not rewritten or silently promoted. A company reference is not evidence of every branch or production stage.

Examples of new source-supported companies include [Marmota](https://www.marmotastudio.com/services) (animation/rigging), [Studio Unagi](https://studio-unagi.com/) (2D animation and game cinematics), [Three Bohemians](https://threebohemians.studio/studio/) (animation, Unreal workflows, mocap cleanup and character work), [Folktail](https://www.folktailstudios.com/) (2D animation in Nigeria) and [Minimo VFX](https://minimovfx.com/about-us/) (CG/VFX, virtual-production content and pipeline services). These are **company claims**, not independently verified technical services at a geocoded facility. Mocap cleanup is not an assertion that a company operates a capture stage. No retargeting, facial capture or external support need is invented.

Pudoctopus's official page describes Toronto and Chilean representation; the historical Chile listing does not create a Chilean branch. Anima Kitchent Canarias remains held because the global brand page does not substantiate the separately listed legal identity or another facility. Schools, an audiobook producer, a distributor and industry-support organisations are excluded where assessed evidence supports that decision. Wrong namesakes, stale projects, empty pages and expired domains stay unresolved; fetch failure is never a closure signal.

Cyber Group's [reported liquidation](https://www.awn.com/news/cyber-group-studios-ordered-liquidate) and the [reported Technicolor India shutdown](https://economictimes.indiatimes.com/tech/technology/technicolor-india-shuts-down-operations-impacting-over-3370-employees/articleshow/118628051.cms?from=mdr) are review alerts. They do not delete existing records or establish successor-brand status. Animaskin bankruptcy and Wild Child administration leads remain unresolved rather than being converted into confirmed closures.

## Rights and publication review

[Source policy](source-policy.json) records attribution and **UNSPECIFIED** reuse terms. The official 2024 exhibitor page was readable. The legal notice was indexed but direct review returned 502; robots.txt was inaccessible through the page tool. No permissive robots decision, blanket PDF/database redistribution licence or source-wide clearance is asserted. There is **no new automated collector**. Each company keeps its own evidence URL as its unresolved licence pointer. EA, Cinesite and other restricted sources stay disabled. No screenshots, OCR, hidden API or alternate host was used to bypass restrictions.

This release uses a **manually reviewed draft PR**, not a historical approval bundle. Before merging, a maintainer must review the actual proposed records, current operating identities, facility-vs-company distinctions, service claims, source rights and the hash-bound stratified precision worksheet. **Human-reviewed sample size is zero; precision is null.** Agent decisions, test success, clicked links, reports and a draft flag do not grant approval. The [read-only GitHub API audit](review-enforcement.json) on 7 November 2026 reports `main` unprotected, required checks off and no repository rulesets. Human approval is procedural, not enforced by the observed configuration. This change does not configure protection. New commits require renewed review.

Existing research queues, discovery snapshots, approval safeguards and v1.2 reports remain intact. The current full-catalogue licensing/review queue is refreshed separately; historical boutique counts are deliberately frozen at their own release. No merge, deployment or Pages setting change is performed.

## Reproduction and validation

```sh
python tools/annecy.py check
python tools/check_bulk_release.py
python tools/boutique.py check --output data/boutique/reports
python tools/launch_readiness.py check --output data/bulk/reports
python tools/validate.py studios.json
python -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.js
python tests/browser_smoke.py
python tests/bulk_browser.py
python tests/public_catalog_smoke.py
python tests/unified_ux.py
python tests/boutique_browser.py
python tests/annecy_browser.py
```

`annecy.py prepare` is an explicit append-only preparation step on a **reproduced v1.2 baseline**, not a crawler or publication command. Reapplying an existing extension is refused; the release reproducer always restores the exact baseline before extending. Checkpoints bind all inputs and policies, original ID-set digest, every retained shard hash and canonical database hash. The safe CSV importer and its existing idempotency tests remain unchanged. To ingest different research, create a new reviewed checkpoint and draft diff; never reuse an old approval hash.

Final executed results and browser/performance conditions are recorded in [validation.md](validation.md). Sources with uncertain freshness, identity, production relevance or terms remain in the full row-level queue. Geographic and technical claims require further review before upgrading to a physical studio or a higher evidence class.
