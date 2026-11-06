# v0.9 — Automated Studio Discovery

Discovery gathers **unverified research candidates**, not trusted public studio records. No new studio is published by this release: the canonical database remains **129 locations / 66 operating organisations / 28 countries**, with all v0.8 records and coordinates unchanged.

## v0.9.1 follow-up

The [v0.9.1 triage report](triage-v0.9.1/README.md) records the successful live Actions run and its actual classifications, replacing the earlier local-only coverage uncertainty. It documents read-only triage artifacts, preserved queue/report history and EA's automation restriction. The original v0.9 QA results below remain historical release snapshots.

## Pipeline and approval boundary

```text
Maintainer-approved source registry
    ↓ bounded collection (robots, rate limits, no recursive crawl)
Link / JSON-LD / RSS-Atom observations
    ↓ stable candidate IDs, hashes, change signals, source failures
Unverified queue + run report (GitHub artifact)
    ↓ researcher revisits primary evidence and authors full location records
Pending review bundle → explicit claim-by-claim approval
    ↓ candidate + record + database hashes must match
Safe importer preview + duplicate review + repeat-import check
    ↓ separate proposed database / CSV / audit report
Manually dispatched draft pull request → human review and manual merge
```

The weekly discovery workflow has **read-only** repository permissions and cannot change `studios.json` or open/merge a publication PR. Preparing a PR is a separate **manual** workflow, using a review bundle already committed under `data/research/` on `main`. It creates a draft branch/PR and has no merge, approval, deployment or Pages-setting step. Do not configure auto-merge for these proposals. Repository maintainers must require human review in their branch protection/rulesets if they want that policy enforced outside this tool; this release does not change repository settings.

Recorded approval is a maintainer trust boundary, not cryptographic proof of a person's identity or business truth. The tool rejects pending reviews, missing checks, changed input hashes, stale/future observations/reviews, invalid records, unresolved duplicates and ID conflicts. A changed candidate/record/database needs a fresh review bundle. Hashes bind the **submitted snapshot**, not unseen later website changes; `prepare` does not refetch the web. Review observations must be at most 30 days old and reviews must follow the observation date.

## Source registry and collection

[`sources.json`](sources.json) contains 25 official source entries. Eight are enabled after policy review: DNEG, metricminds, Framestore, Larian, RISE, Outpost, Flying Bark and FOLKS. Seventeen remain disabled, including EA, Cinesite and Remedy. The original six-source registry is retained in the historical source-policy audit; see the v0.9.3 section below for current access decisions. `company_id` here is a **hint** for duplicate review, never a new public identity or an inherited capability.

No third-party industry directory has been approved for automated collection yet. Before enabling one, review its terms/reuse rights, confirm public directory content, choose narrow link rules and document that decision in `reuse_note` in a reviewed registry PR. [`sources.example.json`](sources.example.json) contains **disabled fictitious-host examples**, not working sources or evidence. The `directory` kind is supported but always yields unknown-confidence candidates.

Supported adapters:

- `links`: extract anchor text and HTTPS URLs matching a source-specific pattern; ignore scripts/styles and strip query tracking/fragments. Labels are capped and email/phone-like text removed. A directory listing or company link alone never proves a physical studio.
- `jsonld`: extract public organisation/business names plus city/country from structured addresses. Ignore Person objects, street addresses, telephone and email. No capabilities or geocodes are inferred.
- `feed`: parse RSS/Atom item titles and URLs. Closure/acquisition/relocation phrases create **possible** change signals, not verified events. DTD/entity feeds are rejected.

Only explicitly configured source pages and their `robots.txt` are fetched. Extracted links are **not followed**; JavaScript is not executed and PDFs are not parsed. New evidence URLs require source-registry review before collection. HTTPS only, no credentials/query secrets, public DNS/IPs, same-origin redirects, 15-second request timeout, 2 MB/page limit, 2,000 extracted items/source and 50 sources/run. Requests use `MotionXDiscovery/0.9`, at least one second apart per host, honour `Crawl-delay`/`Request-rate`, and refuse delays over 60 seconds for a separate slower/manual run. Robots disallow/unavailability fails closed; a missing robots file (HTTP 404) permits collection. Content-type mismatches and access failures are reported, never bypassed. No auth cookies or paid search/mapping API are needed.

The per-page digest is an audit/change hint, not a publicly redistributed page snapshot. Navigation links can produce noisy candidates. Broad text notices, images, dynamic rosters and site redesigns need human research or a future source-specific adapter. No generic extractor promises comprehensive branch coverage or site-specific capabilities.

## Queue, change detection and continuity

[`backlog.json`](backlog.json) carries all **41 deferred v0.8 candidates**, retaining their original public rationale, sources and review date. All remain pending with `confidence: unknown`; a previous decision to defer is not evidence of current operation. Rejected/already-present v0.8 decisions remain in their historical research manifest.

Candidate IDs are stable per source + normalised URL + structured city/country, separate from public organisation/location IDs. Repeated identical observations do not create new candidates or events. Records retain first/last seen dates, source kind, observation hash, advisory existing-record matches and missing-since dates. Different sources may point to the same business: this intentionally remains a research duplicate to resolve, not an automatic merge.

Events include new candidate, changed extracted evidence, changed page bytes, disappearance from a **successfully nonempty** source, and reappearance. Missing links can mean a redesign, not closure. Empty extraction or failed fetch never withdraws candidates. Acquisition/closure/relocation keywords only flag titles/labels where present; business facts must be researched. Raw HTML, headers, secrets and arbitrary response errors are not retained in public reports.

The weekly `Discover studio candidates` workflow runs on `main` and restores the last successful run's `studio-discovery` artifact before scanning. Artifacts retain queue + report for 90 days. If none is available, it explicitly warns and starts from the committed backlog; disappearance detection then has no prior live history. Download evidence you need and commit dated research bundles rather than relying on artifact retention forever. Avoid concurrent manual scans writing shared state; outputs must be fresh directories.

A successful workflow means the collection job ran, **not that every source succeeded**. Per-source statuses and warnings appear in its report and Actions summary. Review those before using candidates. Disabled sources retain history but are not fetched.

```sh
python tools/discovery.py scan --output /tmp/motionx-discovery-run-1
python tools/discovery.py scan --state /tmp/motionx-discovery-run-1/queue.json --previous-run /tmp/motionx-discovery-run-1 --output /tmp/motionx-discovery-run-2
```

[`initial-run-report.json`](initial-run-report.json) is the actual local attempt on 6 November 2026: **six DNS/access failures, 41 retained pending candidates, zero published records**. This managed environment does not provide access to these company domains. No successful live-source extraction is claimed for that initial local attempt; current successful Actions results are linked below. Deterministic fixtures test all adapters and approval paths; the first live Actions source/adapter review is now recorded in the v0.9.1 report linked above. There is no synthetic studio disguised as a real discovery result.

## Research, review and preparation

1. Download the discovery artifact. Revisit each promising candidate against primary current location/careers/announcement evidence. Independently cross-check uncertainty. Reject/defer historical offices, corporate addresses, remote teams or ambiguous operators. A source changing does not justify rewriting the public database.
2. Author `records.json` as an array of fully researched canonical-schema rows. Use existing stable organisation IDs; use a separate stable location ID per physical site. Record location type, ownership/group evidence and site-specific capabilities separately. Use approximate city references with provenance unless exact facility coordinates are supported. Do not populate private CRM, personal contacts or confidential notes. The automated preparation path excludes phone/email values and unknown record fields.
3. Generate a **pending** snapshot bundle. Supply one candidate ID per record, in the same order:

   ```sh
   python tools/discovery.py review-template \
     --queue /tmp/motionx-discovery-run-1/queue.json \
     --records /tmp/researched-records.json \
     --candidate discovery-CANDIDATE-ID \
     --output data/research/my-reviewed-batch
   ```

   This writes `queue.json`, `records.json`, `reviews.json`. It grants no approval. Replace the example ID with a real queue ID. For multiple rows repeat `--candidate`. Several distinct facilities can reference one discovered page, but each needs a separate reviewed record and approval.
4. A reviewer checks **location, city/country, sectors, capabilities, coordinates and identity**, setting each `checks` field to `true` only after researching that claim. Set `decision: approved`, a public `reviewed_by` alias, actual `reviewed_on` date and public `reason`. Set the record's location `verified_on` to that review date. Never claim an independent site inspection from a source link. Empty/missing capabilities are acceptable; VFX/animation does not establish capture.
5. Generated hashes bind candidate, record and current database. Do not edit the record after approval; regenerate the pending template and re-review. `action: add` never overwrites; `action: update` requires the previous record hash, and an organisation identity change requires `identity_change_reason`. Potential duplicate facilities require `allow_distinct_location: true` and a sourced `distinct_reason`. No delete action exists. Closure or relocation proposals must be explicit reviewed record updates, not inferred removals.
6. Prepare locally against a fresh output directory:

   ```sh
   python tools/discovery.py prepare \
     --queue data/research/my-reviewed-batch/queue.json \
     --records data/research/my-reviewed-batch/records.json \
     --reviews data/research/my-reviewed-batch/reviews.json \
     --output /tmp/motionx-proposal
   python tools/validate.py /tmp/motionx-proposal/studios.json
   ```

   The command **never edits canonical `studios.json`**. It writes a proposed copy, an additions-only CSV and a report with explicit updates, bound approvals, baseline/proposed hashes, importer preview, repeat check and warnings. Update-only batches produce a header-only CSV; updates are represented in the proposed JSON/report, not applied by the append-only CSV importer. Unaffected records remain unchanged. A second import of additions creates nothing. A proposal against a changed canonical database is blocked and needs re-review.
7. Commit the review bundle in a reviewed infrastructure/research PR. Once on `main`, manually run `Prepare approved studio proposal` with its repository directory as the `bundle` input. It validates Python and browser schemas against the proposed data, runs regression tests, uploads the proposal, and opens a **draft PR against main**. A maintainer reviews the data diff/report and merges manually. The workflow cannot silently overwrite main or merge.

GitHub must permit Actions to create pull requests for the manual PR step; no setting is changed automatically. If disabled, download the proposal artifact and create the reviewed PR manually. `GITHUB_TOKEN`-created PRs may not trigger other Actions workflows; preparation validation runs before opening the draft, and a maintainer must rerun required PR checks before merging. No deploy workflow is introduced. A later ordinary merge may trigger the repository's existing Pages deployment.

Approvals are declarations, not a replacement for public evidence. Repository write access remains a trust boundary. The tool does not independently prove a reviewer inspected a website, verify business operation, infer capability truth or enforce GitHub branch protections.

## Map scalability

The public website loads only `studios.json`; it never loads discovery candidates or review artifacts. Lists remain paginated at 50. Above 2,000 filtered coordinate groups, only the padded viewport's groups have Leaflet canvas markers; panning refreshes them. Filtering/counts/search/CSV export and fit-results use the **whole filtered dataset**. All matching studios at a shared original coordinate stay in a single accessible chooser. A chooser retains keyboard focus when Leaflet auto-pans it; markers refresh after it closes. Longitude wrapping includes antimeridian and repeated-world views. No coordinate is moved and no paid map service is added.

The current browser suite exercises 20,000 distinct groups, panning, filtering and pagination, then a second 20,000-location fixture with coincident studios and keyboard selection. The older v0.9 measurements below used 10,000 records. This limits rendering work at local zooms, but the browser still fetches, validates and indexes the entire file. Viewport filtering is linear in coordinate groups; further indexing/worker/tiling work may be warranted at much larger scales. See `qa-report.json` for actual runner observations, not a promise for every device.

## Release QA

**63 Python tests, 20 JavaScript tests and 15 HTTP browser checks passed.** Canonical validation remains **0 errors / 147 disclosed warnings** (129 approximate coordinates, 18 legacy unknown-evidence records); no original record or coordinate changed.

The 10,000-distinct-coordinate browser fixture completed load/pan/paginate/filter in **1.693 seconds** on this runner. At the tested local zoom, **1,617 markers** were rendered instead of 10,000; list pagination remained 50. A second fixture proved keyboard selection of overlapping studios in viewport mode. Live Leaflet/OSM tiles, attribution, mobile layout and error/retry paths also passed. These observations are saved in [qa-report.json](qa-report.json). Full live collection is still blocked locally as disclosed above; fixture success is not a live research result.


## v0.9.3 review reports and source coverage

The current registry has 25 official source entries, with eight enabled for bounded factual metadata and 17 disabled pending policy/access review or permission. EA and Cinesite are expressly disabled; the latter's current Terms of Use prohibit automated scraping/text-data mining. Existing observations from disabled sources remain in the queue. Robots are checked at collection time; policy-review notes are not a licence or independent business verification. Refer to the [v0.9.3 release audit](../research/v0.9.3-global/README.md) for all attempts and limitations.

`location_labels` adapters extract only reviewed visible location cards, carry a separate facility key, ignore navigation/scripts and never copy capability terms to the next card. Link adapters are narrowed to actual branch pages (RISE and Larian included). Unrecognised new labels cause source page-change alerts rather than invented geographic classifications. Opening/rebrand/acquisition/relocation/missing-link signals need investigation; failures/empty extraction never invalidate a studio.

`tools/research.py report` creates offline `review.html`, `proposals.json` and `summary.md`. Weekly discovery uploads `studio-research-review`; PR checks upload `global-research-review`. Dossiers and authored proposals have separate unverified/pending-review states. Authored comparisons group by company and country and include direct evidence links. Reports have no approve button or active scripts and never edit public data.

For GitHub-native review, the manual `prepare-research-pr.yml` workflow validates an exact source-researched bundle and opens a draft data PR, with a downloadable staged HTML review. It grants no approval and cannot merge. Configure required reviews/stale-review dismissal and personally review the exact head before manual merge. The informational review-state workflow does not turn account metadata into proof of human intent. The older hash-bound approval-bundle workflow remains available separately and is unchanged; historical pending reviews are not fabricated or reused.

History is carried forward from the latest successful discovery artifact. If that artifact cannot be restored, or lacks its queue, the workflow now stops instead of resetting to the 41-entry seed. Download/archive artifacts before their 90-day expiry; a maintainer must restore a reviewed archive/checkpoint if needed. All older research/backlog files remain unchanged.

Committed PR discovery checkpoints are merged additively into later scans: missing candidates and earliest observation dates are retained without replacing newer run evidence or reviews. The checkpoint itself is archived and grants no approval.
