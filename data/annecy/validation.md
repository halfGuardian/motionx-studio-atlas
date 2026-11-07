# v1.3 executed validation — 7 November 2026

All checks below ran against the proposed checkout from merged v1.2 `cf7a14949ef2ecab1549a39b1c6ef78fa9571b17`. [Machine-readable results](qa/results.json), [canonical warnings](qa/canonical.json), [exact catalogue reproduction](qa/catalogue-reproduction.json) and [GitHub review-enforcement observation](review-enforcement.json) retain the evidence. This is not a deployed-site verification or a completed human research review.

| Check | Result |
| --- | --- |
| Complete Python suite | **227 passed**, 0 failures |
| Complete JavaScript suite | **61 passed**, 0 failures |
| HTTP browser suites | **56 checks passed**: baseline/50k 19, sharded 50k 6, real catalogue 9, unified UX 9, boutique 8, Annecy 5 |
| Canonical validation | **0 errors / 265 warnings**, unchanged 243 locations / 119 operating organisations |
| Full catalogue reproduction | **0 errors**, exact old archive → v1.2 → v1.3 proposal |
| Full historical v1.2 boutique reports | Reproduced without rewriting that release's history |
| Current full-catalogue licensing/review queue | Integrity check passed; 42,009 non-Class-A entries remain pending |
| Annecy checkpoint/report consistency | Complete 1,074-row reconciliation and 566 target research receipts reproduced |
| Existing identities/evidence | All 42,067 prior IDs, 239 detail shards and canonical database hash preserved |

Tests cover attachment recovery, inert formulas/action strings, malicious XML/ZIP inputs, names/domains/aliases/country labels, brand-vs-group risks, repeated exhibitors, failed/empty pages without false closure, historical-only evidence guards, Class C pin/capability limits, source terms, CSV formula safety, HTML escaping, hash-bound pending human review and repeatable append-only preparation. Existing safe importer, deduplication, idempotency, approval, discovery continuity, network/robots restrictions, profile/history, mobile, shared-coordinate chooser and filtering checks remain part of the full suites.

The new HTTP suite opens all 1,074 dashboard rows and both 253/313 groups, follows a keyboard-accessible link into an actual new reference, reloads its shareable profile, searches the actual Boutique catalogue, checks company-service terms and source links, downloads the filtered CSV and tests the 390px review dashboard. No benchmark entity is injected into the public data to make a discovery test pass. No synthetic location enters a committed public shard.

## Actual measured conditions and limitations

Installed headless Chromium, local HTTP under a repository subdirectory, desktop 1440×950/1000 and mobile 390×844. [Real-data measurements](qa/real-catalogue-performance.json): **42,239 records**, 2,209,751-byte compressed columnar index, **1.867s** initial ready, **13.3ms** search computation, **31.2ms** full-result query, **102.7ms** uncached profile detail retrieval. Map navigation took **43.9ms**, including **37.4ms** marker rendering for that viewport. The throttled mobile scenario used **96,000 bytes/s, 150ms latency and 4× CPU slowdown**; initial ready was **31.075s**. Slow first loading remains an operational limitation; progress and failure/retry states do not expose an incomplete catalogue as complete.

The [sharded 50,000-location fixture](qa/synthetic-sharded-performance.json) loaded in **1.560s**, searched in **9.7ms**, opened a profile in **46.5ms** and rendered the measured viewport in **2.8ms**. The [older monolithic 50,000 fixture](qa/synthetic-monolithic-performance.json) loaded in **16.772s** with a 50.5 MB JSON fixture. These are different transport fixtures, not a controlled release-to-release speed comparison, and neither is real acquisition data. [Lazy Boutique metadata](qa/boutique-performance.json) is 314,805 compressed bytes and first opened in **0.407s** in this run. Machine load and network emulation affect timings. No physical low-memory phone or deployed Pages run is claimed.

## Warnings and remaining review

The canonical validator's 265 warnings remain visible, including approximate city pins, legacy unknown evidence and reviewed multi-facility/co-location candidates. The cumulative catalogue manifest separately records **41,996 unreviewed source references**, **40,376 unverified source point precisions**, **1,620 company references without coordinates**, **1,385 unspecified company-source terms** and **117 potential existing duplicate candidates**. These categories overlap and must not be summed as distinct errors. All 172 new references are Class C and independently unverified; no source-wide redistribution clearance is granted.

Annecy outcomes: **161 previously represented, 172 new references, 3 repeated identities, 9 out of scope, 2 reported inactive, 727 unresolved**. All 566 target entries received research attempts; only relevant readable company evidence supports proposed references. Other 508 entries received identity matching, not a complete current-operation investigation. Historical event labels and source self-description cannot establish verified physical facilities or every branch's capabilities.

A maintainer must complete the separate **37-row pending stratified precision worksheet**, check source rights, current operation, identities and service claims, and personally authorise any merge. Human sample size is **0**, precision **null**. The GitHub API reports `main` **unprotected**, required checks **off** and **zero repository rulesets** at the recorded review. Draft PR status and green checks therefore do not enforce approval. No merge, deployment, source enablement or Pages setting change was performed.
