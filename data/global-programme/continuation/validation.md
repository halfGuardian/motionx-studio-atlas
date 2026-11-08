# Executed continuation checks

This is a draft research/code checkpoint, not publication approval. See
[the company/branch dashboard](reports/dashboard.html),
[delivery and exact resumption commands](DELIVERY.md) and
[machine results](qa/results.json). The parent PR #15 remains unchanged at
`efd52a86e66417438830aac285e3fffee3aa0fa0`.

## Results

| Check | Actual local result |
|---|---|
| Complete Python suite | 303 passed, 0 failed; 81.941 seconds |
| JavaScript suite | 88 passed, 0 failed |
| Public atlas / dashboard HTTP suites | 86 checks passed across 11 suites, including corrected reruns |
| Actual standalone continuation bundle | 3 additional HTTP checks passed; total 89 |
| Canonical validation | 0 errors, all 265 retained warnings disclosed |
| Licensed-source catalogue reproduction | Passed; all 42,296 original full records preserved |
| Geographic/visibility audit | Passed; all 1,677 original company references retained |
| Permitted maintenance snapshot | 424 existing rows, 1 historical event, repeat import 0 new signals, 0 canonical changes |
| Current licensing/readiness reproduction | Passed: 59 source/policy entries and 42,066 advisory queue entries; no approval granted |
| Readiness tests after return-link correction | 8 passed |

The continuation check replays all 753 pending observations / 725 queue keys,
binds complete original record hashes, checks new proposals against the entire
catalogue and one another, and reproduces every generated continuation report.
The 70 company reviews and seven branch/department investigations account for
69 queue keys; 656 remain explicitly uninvestigated. Eight company/geography
reviews address separately identified existing records. Thirty new Class C
company payloads are prepared, with no cross-proposal identity conflicts,
capability verification, published additions or canonical coordinate changes.

The 265 canonical warnings are retained in [the complete JSON](qa/canonical-validation.json),
not suppressed. The unchanged public-manifest warnings additionally distinguish
unreviewed source references, unspecified reuse terms, duplicate-review records,
unpinned companies, legacy unknowns and staged proposals. Source-sector audience
classification does not resolve those warnings. All 14 independent evaluation
labels remain absent; precision/recall are null.

## Performance conditions and limits

Local Python 3.12.14, Node 24.22.1 and installed Chromium 155.0.8059.79 were used.
CI uses its documented Python 3.12 / Node 22 / runner Chrome environment. HTTP
tests serve the actual repository under a GitHub Pages style subdirectory.
The standalone test serves a freshly packaged directory outside the checkout.

| Workload | Current observed result |
|---|---:|
| Actual 42,296 retained references / 42,292 normal results, cold HTTP readiness | 2.027 s |
| Same real data, 96,000 bytes/s + 150 ms latency + 4× CPU + 390px | 33.165 s |
| Real-data complete audit query | 23.1 ms |
| Real-data searched filter computation | 12.3 ms |
| Temporary 50,000 synthetic locations, sharded transport readiness | 1.701 s |
| Sharded synthetic search | 7.7 ms |
| Temporary 50,000-row legacy raw JSON fixture, readiness | 17.449 s |

The original checkpoint observed 2.21 s / 33.30 s for real-data readiness and
1.55 s / 7.7 ms for its sharded synthetic fixture. These are separate single
samples, not evidence of a statistically established speed change. The actual
compressed index is 2,213,984 bytes. Synthetic repetition compresses unusually
well and does not establish acquisition of 50,000 genuine locations. The legacy
raw fixture is about 50.5 MB; the sharded synthetic details remain lazy-loaded.
No synthetic row enters the public dataset.

These are local HTTP and emulated-mobile measurements. Deployed Pages performance,
physical low-memory devices, business current-operation claims and independent
facility verification are not established by these checks.

## Failures, corrections and archive evidence

Initial attempts are recorded in `qa/results.json` and retained logs where
available. A filter test asserted before its scheduled render; a report JSON
summary overflowed at 390px; one smoke assertion compared retained storage totals
with intentionally filtered visible totals; newly added branch cards initially
escaped company filters; and the nested licensing return link resolved to
`data/index.html`. The corrected suites pass, including all-record audit queries,
77-card company/branch filters, unresolved country, mobile containment and the
actual standalone licensing-to-landing-page round trip. An initial validator
command also omitted its required input; `validate.py studios.json` passed.

The first pushed code/research checkpoint `b35f39cf5581126708215523064f387a5dc7f81e`
passed [Actions run 42425951452](https://github.com/halfGuardian/motionx-studio-atlas/actions/runs/42425951452).
Its actual downloaded artifact 13595732112 was 16,305,974 bytes, with SHA-256
`88d1b1964fafb655a0740e661ac4383367bd25bc914322689e25014828c46b5a`, matching
GitHub's digest. Its archive preserves that earlier 68-company / 30-proposal
checkpoint; it is not mislabeled as the subsequent branch-review checkpoint.
The latest PR-head Actions run provides the current artifact and repeats the
complete checks. A successful workflow, downloaded file or draft PR is not human
review or permission to publish. Required-review enforcement remains unconfirmed.

No merge, deployment, Pages setting change, restricted-source enablement or
fabricated approval is performed. The programme remains in progress.
