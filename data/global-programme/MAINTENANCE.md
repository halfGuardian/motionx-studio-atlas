# Reproducible global maintenance and continuation

The new global workflow is **offline replay**, with no new crawler, active cron schedule or direct publishing. Existing discovery collectors remain governed by their own unchanged policy registry. A failed/missing source must not remove an Atlas record. EA and other restricted/unresolved sources remain disabled. Future network adapters or schedules need a reviewed source-access decision; robots availability alone is not a redistribution licence.

## Actual source replay

`maintenance/snapshot.json` is a public-facts projection of all **424** rows in the existing, explicitly downloadable CC BY 4.0 animation-directory snapshot. The policy cites its fixed source commit, licence and attribution. It contains no emails, street addresses, prose, photographs or synthetic studios. The source's April 2026 update and November observation dates remain distinct. Its completeness covers that offered snapshot, not European industry completeness or current operation.

The first actual replay produced 424 newly observed research signals, one embedded historical snapshot and **zero canonical updates**. The repeat produced **zero signals** and the same history. Both reports, the original projection and hash-bound state are retained under `maintenance/`. This is a local execution result, not a claim that a new Actions workflow has already run.

```sh
python tools/global_programme.py maintenance-check
python tools/global_programme.py incremental \
  --snapshot data/global-programme/maintenance/snapshot.json \
  --policy data/global-programme/maintenance/policy.json \
  --freshness data/global-programme/maintenance/freshness-policy.json \
  --state /tmp/motionx-global-state.json --output /tmp/motionx-global-first
# Repeat the same command with the same state and another --output directory.
```

Each source has its own policy and stable snapshot/source-record IDs. New offline JSON/CSV inputs require an explicit scoped dataset-reuse decision, source URL, licence, attribution, actual review date, access status and enumeration scope. CSV requires a separate metadata JSON (`--metadata`) and JSON-encoded claim/alias arrays. Unsupported/private columns, unsafe URLs, ID conflicts, future dates, oversized inputs, inconsistent completeness and expired permission decisions fail closed. No URL download option exists in this tool. The importer never consumes dashboard approval notes.

## Connect permitted snapshots to the global dashboard

After `incremental` validates a permitted snapshot and updates its durable research state, register the source's **policy, snapshot and state** repository paths in `inputs/snapshot-registry.json`. CSV entries also specify the separate `metadata` JSON path. The included entry uses the real 424-row licensed snapshot and its existing hashed state; it exercises the same configurable bridge future sources use. No source-specific Python adapter edit is needed for a compatible factual CSV/JSON export.

The registry admits only paths under repository `data/`, validates licence/access/schema again and requires the state head to match the supplied snapshot. It replays **all retained historical versions**, so a failed or partial latest snapshot cannot remove prior candidates from the dashboard. Recovered name/geography/service changes compare with the last known facts across failed fetches; before/after assertions are visible as investigation signals. Changed source-policy hashes require explicit review; they cannot silently rewrite historical permissions. Original records and the canonical database are never updated by this bridge.

The 424 configured snapshot rows duplicate source keys already in the historical replay. They therefore add **424 audit observations**, not companies, source coverage or published locations: the combined audit is 44,818 observations / 43,761 distinct source identity keys, including 1,057 repeated observations. Registered snapshot completeness covers only the named offered dataset.

Resource bounds are explicit: up to 100,000 records / 50 MB per source snapshot and 500 MB per embedded maintenance-state file, with at most 1,000 explicitly registered sources. The current dashboard index supports 250,000 observations. Larger or long-running histories need reviewed archive/partition work; nothing is silently truncated. Actual demonstrations use 424 licensed rows and the complete current global catalogue; larger synthetic website benchmarks do not establish real business coverage.

The runtime state-file cap is not a GitHub file-size allowance. GitHub's 100 MB per-file limit requires compressed/partitioned history before any oversized state is committed. The included `maintenance/` demo and checkpoint remain frozen; use a separate source directory for subsequent operational snapshots. Policy revisions need an explicit reviewed history migration rather than reusing a changed policy hash as if it covered earlier observations.

Snapshots retain all records and review signals in a hash-linked history. Reused snapshot IDs with changed content are rejected. Before/after values remain in change signals. Only comparable complete successful snapshots can produce **source-absence investigation** signals, which explicitly do not establish closure. Partial/failing sources and missing/corrupt history suppress absence inference. A policy/validation failure writes a failure report and leaves prior state untouched. Hashes detect accidental/stale changes; they are not authenticated approvals or proof of business facts.

`maintenance/freshness-policy.json` configures separate identity, geography, service, facility-capability and source-policy windows. The current offline replay emits stale company-assertion signals. Other axes remain explicit review queues; no evidence class is promoted. Source observation date is not necessarily the age of the underlying assertion. Missing source assertion dates stay unknown.

## Global reports and history

```sh
python tools/global_visibility.py check
python tools/global_programme.py prepare
python tools/global_programme.py check
python -m http.server 8000
# Open http://localhost:8000/data/global-programme/reports/dashboard.html
```

The dashboard filters every replayed observation by country, research region, source, rights, outcome and text. It includes per-source enumeration limits, all represented-country gaps, unpinned-company dispositions and human-review gates. Large machine reports and the review index are deterministic gzip files. Download/decompress `global-report.json.gz` for the complete audit; the browser needs gzip stream support and renders only 25 review cards at a time. Working decisions are not persisted until explicitly exported. Profile/source links and CSV remain safely escaped/protected.

`inputs/history-checkpoint.json` binds all 209 retained parent research files. Historical discovery/backlog queues, including the original 41 entries and later 200-candidate checkpoint, are replayed additively with their original hashes/dates/review states. The committed discovery archive explicitly lacks complete raw history; this programme does not invent expired artifacts or closure signals. Existing `restore_discovery.py`, `checkpoints.py` and archive workflows stay unchanged. The global workflow can replay committed state even when an Actions artifact expires. Recovery tests cover partial/failing/corrupt states locally; no new claim of a live archive round trip is made.

`.github/workflows/global-programme.yml` is a read-only manually dispatched replay with downloadable artifacts. It grants no write/PR/merge permissions. Its PR counterpart runs in `test.yml` against main or the protected parent branch and uploads the same self-contained review bundle now. `package_global_review.py` preserves `data/global-programme/reports/` and the relative root scripts; serving the downloaded bundle opens a working review dashboard. Its landing page explains that public Atlas profiles require the matching checkout. New manual workflow dispatch is unavailable until GitHub recognises that workflow on the default branch; maintainer dispatch after authorised merge is a remaining manual step, not a test result. No schedule has been enabled.

```sh
python tools/package_global_review.py --output /tmp/motionx-global-review-bundle
MOTIONX_REVIEW_ROOT=/tmp/motionx-global-review-bundle python tests/global_review_browser.py
python -m http.server 8000 --directory /tmp/motionx-global-review-bundle
```

## Exact unfinished work

1. Inspect `reports/countries.json` for country/region gaps and all saved query URLs. Perform native-language and subnational source review; query receipts alone are not industry discovery completion.
2. Resolve access/rights for each entry in `inputs/source-assessments.json`, then review additional appropriate source leads. Do not fetch prohibited sources or bypass a disallowed resource route. Retain partial-page and failure denominators.
3. Enumerate each permitted source's full eligible scope using the bounded JSON/CSV snapshot schema, retain all rejected/unresolved rows and replay incrementally. Review candidates against all 42,296 retained records before proposing identities.
4. Filter `reports/reconciliation.csv` for potential new companies, generic-production qualification, aliases, geographic conflicts and historical operations. Prepare source-backed company/facility proposals separately; do not infer addresses, municipalities, ownership or capabilities.
5. Obtain independent human labels on the frozen fourteen-candidate worksheet. It is purposive, not representative; two source domains overlap retained data. No independent precision/recall exists yet. Expand an independently labelled sampling frame before reporting global quality.
6. Review the 256 unpinned city associations individually before any additional display coordinates. Maintain original IDs/coordinates, separate city-reference provenance and facility evidence.
7. Review PR #15 first. After its authorised merge, rebase/retarget draft PR #18, review the exact global changes and run the offline workflow on GitHub. Do not merge/deploy automatically or close issue #16 before reviewed delivery.

This checkpoint delivers reusable infrastructure and an accountable global work queue. Worldwide enumeration, source rights and independent business/facility review remain unfinished. No country-by-country prompt is required to continue the queued research.
