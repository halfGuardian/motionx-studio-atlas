# Global bulk acquisition — v1.1

## Active inclusive research catalogue

The active site combines **243 retained locations + all 40,376 acquired place observations + all 1,116 game-company references = 41,735 records** in one searchable directory. All A/B/C classes are visible together by default. The 13 legacy unknown-evidence identities remain visible. Company-only references are searchable and exportable without invented map coordinates. Record counts are not verified unique facility counts; possible duplicates remain explicit research matches.

The active entry point is `tools/unified_catalog.py`; its research schema permits missing geography only with explicit C/unverified labels. It never changes the strict canonical-location schema or the original `studios.json`. The older `bulk_catalog.py` remains available for a more restrictive B-only proposal, but its A/B-only visibility policy does not govern the active inclusive catalogue.

Game-company references use factual identifiers, source classification/status claims, country and website from the author-provided CSV. All 1,116 identities remain, including 766 Studio, 235 Studio+Publisher and 115 Publisher records; these are 1,001 studio/hybrid and 350 publisher/hybrid entries with overlap. Source statuses are 1,092 Active, four Acquired and 20 Closed, all uncorroborated source labels. No authored descriptions or social/contact profiles are republished. The source README offers download/local use but no explicit dataset redistribution licence: these entries are labelled `UNSPECIFIED` and Class C rather than falsely licensed or verified.

```sh
python tools/unified_catalog.py --snapshots /path/to/verified-redistributable-snapshot --companies data/bulk/unified-input/game-company-references.csv --observed-on 2026-11-06 --output /tmp/motionx-combined
python tools/check_bulk_release.py
```

Dates in source receipts are UTC observation dates from Actions; 2026-11-06 UTC corresponds to 7 November in New Zealand. Public hosting is public access regardless of promotion. The PR presents the exact combined data and code for human review, without merging or deployment.

The acquisition layer processes whole relevant dataset slices, not company-by-company quotas. The reviewed October 2026 Overture Places category inventory scanned **88,418,121 place records / 2,132 categories** and identified **40,376 source listings**: 5,197 animation studios, 18,621 film/television studios and 16,558 film/video-production businesses. These are source taxonomy counts, **not verified MotionX facilities**. Actual retained, deferred and proposed-public counts are recorded in the release reports; synthetic benchmarks are never acquisition counts.

## Evidence and publication boundary

| Class | Meaning | Publication |
| --- | --- | --- |
| A | Current recorded evidence supports a specific studio/facility location; capabilities have their own evidence states | Existing reviewed records / separately reviewed research corrections |
| B | Credible, permitted production-place directory listing; current operation, facility type and services uncorroborated | Proposed on a human-reviewed PR, visibly source-listed |
| C | Evidence, licensing, geography, operation or identity needs research | Visible as research references in the inclusive atlas; never presented as verified facilities |

Source presence, an existence score, a successful test or an automated classifier **never verifies a business claim**. No new A claims or capture services are inferred from this dataset. The three allowed source sectors are kept separate from facility capabilities. The global provider confidence floor is 0.9, a conservative relative-quality filter, **not a calibrated verification probability**. It is not weakened to reach 20,000. Source-listed closures, missing/conflicting municipalities/countries, invalid geometry, unresolved licences and possible duplicates are deferred. A missing listing or failed network request cannot close, move or delete a published studio.

All 243 original records remain unchanged in `studios.json`. Its 230 confirmed-evidence locations form Class A; thirteen legacy unknown-evidence identities remain visible as C. Their IDs, original source evidence and all historical releases remain intact. No confirmed capability is lost. The catalogue audit lists every retained ID.

## Sources and rights reviewed on 6 November 2026

The [source registry](sources.json) records decisions and primary policy URLs. Existing discovery sources and their history are unchanged.

| Source | Decision / permission / scope |
| --- | --- |
| [Overture Places](https://docs.overturemaps.org/guides/places/) | Official documented public S3 GeoParquet dataset. Worldwide complete relevant-category extraction; no website crawl. Places contains no OSM data. [Official attribution](https://docs.overturemaps.org/attribution/) and October 2026 provider/licence table govern redistribution. |
| Meta, Microsoft, BrightQuery, PinMeTo, Krick, RenderSEO, DAC, Birdeye, Uberall, OpenTravel | Overture original providers under CDLA-Permissive-2.0. Preserve per-record provider IDs, timestamps, licence and transformation notices. Only providers actually present are counted as used. |
| Foursquare through Overture | Apache-2.0; full licence, Foursquare NOTICE and transformation notice included. No direct Foursquare scraping/API collection. |
| AllThePlaces through Overture | CC0-1.0; only if present. Not counted as an acquired provider when absent. |
| Overture confidence-only metadata | Official guide pairs original providers **and Overture** under each provider's licence. This derived confidence field does not create independent verification. |
| Overture-signals operating-status overlays | Per-field redistribution mapping not established in reviewed primary documentation. Affected candidates remain C. Redistributable snapshots withhold overlay payloads, preserve every source ID and original observation/page hashes, and retain a link to the complete original Actions artifact. No overlay licence is invented. |
| Wikidata SPARQL | Structured data CC0, but the canonical endpoint's runtime robots check **denied** the collector in run 42282499526. Zero records collected. Disabled; no alternate host/user-agent/dump workaround. |
| OSM / Overpass | ODbL obligations evaluated, but runtime robots denied the configured API in the same run. Zero records collected. Disabled. No bulk Nominatim geocoding or API-host workaround. OSM **map tile attribution remains**. |
| gamedev-studios-db | Automated feed disabled: no explicit dataset redistribution licence established. The inclusive catalogue contains all 1,116 factual company references from the author-provided CSV, pinned to its source commit, with `UNSPECIFIED` terms and Class C. Authored descriptions and social/contact profiles are omitted; no compatible licence is invented. |
| gamedevmap | No explicit compatible bulk redistribution grant established. Disabled; no directory scrape. Public access alone is insufficient permission. |
| Scottish Games Industry | CC BY-NC-SA; compatibility with a general public/commercially useful directory unresolved. Disabled. |
| Texas / Michigan production directories | No bulk redistribution grant established; mixed personal crew data unsuitable. Disabled pending a licensed company/facility export. |
| Singapore cultural statistics | Open licence, but aggregate counts rather than individual studio locations; excluded. |
| EA | Previously restricted automation remains disabled. No screenshots, OCR, alternate hosts or hidden APIs. |

The documented S3 object dataset download is distinct from website scraping: its official bulk-access documentation is the access grant. Website robots denials from other sources are not bypassed. Acquisition selects public business/place metadata only, stripping phones, emails, people/contact fields, social profiles and street addresses. Parent/ownership relationships are not inferred from directory categories or corporate domains.

Licence copies are in [LICENSES](LICENSES/). They accompany redistributable archives and exports. CSV exports place full applicable licence texts and Foursquare NOTICE once in `export_licences` / `export_notices`, with SPDX licences and attribution on every source-listed row. Keep the entire CSV, including those columns, when redistributing. Source data objects are large GeoParquet files: the GERS/source ID identifies the relevant row.

## Repeatable workflow

Run from the repository root (Python standard library except the optional GeoParquet acquisition adapter):

```sh
python -m pip install duckdb==1.4.3
python tools/bulk_collect.py --output /tmp/motionx-raw
python tools/bulk_overture.py --output /tmp/motionx-raw
python tools/bulk_snapshot.py /tmp/motionx-raw --output /tmp/motionx-redistributable
python tools/bulk_ingest.py --input /tmp/motionx-redistributable --output /tmp/motionx-preview --ledger /tmp/motionx-ledger.sqlite
python tools/unified_catalog.py --snapshots /tmp/motionx-redistributable --companies data/bulk/unified-input/game-company-references.csv --observed-on 2026-11-06 --company-source https://github.com/EddieWing/gamedev-studios-db/blob/2ed3b6c1dbf38085ecc7053bb1ef00c27bb9183d/data/companies.csv --output /tmp/motionx-proposed-catalog
```

`bulk_collect.py` honours runtime robots and stops on denied/failed canonical API endpoints. `bulk_overture.py` inventories the entire documented Places release and extracts all matching rows, without a record LIMIT. It preserves the **actual WKB Point**, never rounded bbox minima or guessed city coordinates. Source points are still labelled approximate/unverified facility geocodes. Full cached immutable snapshots are hash-checked and reused without advancing observation dates. Acquisition has bounded response sizes, memory, request timeouts and retries. A workflow success means reports were produced; inspect each source's `complete` / error fields before claiming collection success.

The SQLite ledger keeps immutable observation versions, first/last observation dates, policy/baseline/processor-bound research runs and candidate decisions. The CSV/JSONL/HTML reports include every accepted, rejected/deferred and duplicate-review identity. Repeated source rows coalesce by stable source ID; possible physical duplicates are **held for review**, not automatically deleted or merged. Same-owner, same-city facilities are not assumed to be duplicates. Nearby same-organisation matches across metropolitan/municipality labels are deferred rather than creating an unreviewed second facility. Duplicate pair detail is bounded with explicit additional-group counts, avoiding quadratic report expansion; all input identities remain in the audit.

The inclusive builder writes a **fresh proposal directory**, never `studios.json`, never approval. It preserves every baseline ID and includes every observation from this complete snapshot plus the company references. Rebuilding the same inputs is deterministic. For future releases, compare and preserve prior research records explicitly: the inclusive builder does not yet reconcile records absent from a newer complete source release. A missing observation is never a deletion instruction. The immutable ledger and committed archives preserve historical inputs. Review the exact generated diff and audit before copying proposed files onto a development branch. Only an authorised merge changes the public site. The original A-record research/import/approval-bundle tools remain separate and unchanged.

The optional older `bulk_catalog.py` implements a restrictive B-only view with previous-catalogue retention (`--previous path`) and deferred before/proposed hashes for changes. It is tested as an alternative policy, but is not the active site's visibility policy. In the active atlas, C means research is unresolved, not that the record is hidden.

### Licensed CSV / JSON datasets

Enable a source only after recording an explicit licence, attribution, access-policy review and appropriate `licensed_batch` field mapping in the registry. `physical_place_directory` must be supported; a company register alone cannot establish production premises. The accepted public projection fields are:

`source_record_id, name, city, country, lat, lng, website, sectors, source_url, source_updated_on, parent_claims`

CSV sectors use `|`; JSON/JSONL use arrays. Parent claims contain public `name` / `source_url` only and stay research claims. Unsupported columns, personal contacts and supplied verification/approval flags are rejected and counted.

```sh
python tools/bulk_batch.py permitted-export.csv --source reviewed-source-id --observed-on YYYY-MM-DD --output /tmp/motionx-batch
python tools/bulk_ingest.py --input /tmp/motionx-batch --output /tmp/motionx-batch-review --ledger /tmp/motionx-ledger.sqlite
```

There is no automatic Class A promotion. Country names use a reviewed ISO-3166 / Unicode CLDR lookup; municipalities are copied from supplied locality evidence, not invented. Source-listed organisation identities are provisional unless matched to a retained operating identity. Shared web platforms do not establish ownership. Existing operating brands, IDs and sourced group relationships are preserved.

## Durable research and review

The read-only `Licensed global bulk acquisition` Actions workflow uploads source snapshots, a SQLite ledger, machine-readable reports, an offline searchable/paginated HTML dashboard and integrity archives. Artifacts have **90-day retention**, not permanent storage. Check complete-source flags and hashes. Download originals before expiry if retaining withheld overlay payloads is necessary. Redistributable projections and audit receipts can be committed manually on the draft PR; that preserves source identities/history without redistributing unresolved overlay content.

```sh
python tools/bulk_archive.py archive --snapshots /tmp/motionx-redistributable --review /tmp/motionx-preview --output /tmp/motionx-archive --run-id ACTIONS_RUN_ID
python tools/bulk_archive.py restore /tmp/motionx-archive --output /tmp/motionx-restored
```

Restore verifies manifest, compressed and uncompressed hashes before exposing any state. Missing/corrupt objects fail closed; partial history cannot create closure signals. An expired original artifact is recoverable from a complete committed projection for conservative triage; withheld raw overlay details require the original artifact/offline archive or a hash-checked re-extraction of the dated upstream release. We do not claim permanent availability of third-party hosting.

An automated branch-write archive job was rejected by automatic approval review for granting contents-write access to PR-executed code. It was removed. Workflows retain **read-only repository permissions**, never commit published data or grant automatic publication rights. Manual commits to the draft development PR carry reviewable research archives. Draft PRs and tests do not enforce human approval; the [current Actions rule audit](review-rules-run42287663788.json) returned an empty effective-rules list and unavailable classic protection. Required-review enforcement remains unconfirmed.

## Static delivery and scale

`studios.json` remains the unchanged reviewed baseline. `data/public/manifest.json` binds its exact bytes and all 243 active IDs to a compact search index and 238 country-grouped detail shards of at most **500 records**. Initial search/counts, organisation identities and spatial-map access use summaries; profiles lazily fetch and validate full evidence. Shard/index identity mismatches, missing data and licence-copy errors fail clearly. CSV loads all matching full records before downloading, including companies without coordinates. Requests are bounded and shared per shard. A full export loads about 105 MB of uncompressed detail JSON; it is substantially heavier than searching or opening a single profile.

The active transport is `index.compact.json.gz`: dictionary-encoded columns, reversibly packed IDs and unchanged Float64 coordinate values. It is 2,179,773 bytes gzip / 5,027,081 bytes plain. The original 13-column `index.json` remains byte-identical for audit and compatibility. `baseline.json.gz` is a 25,977-byte compressed copy of the exact original 358,282-byte `studios.json`, not a replacement database. Both compressed and inflated bytes are SHA-256 checked. Hash-addressed transport URLs permit safe browser caching across visits; a new hash requests a new representation. Browsers without `DecompressionStream` use the hash-checked plain transport. Corrupt or incomplete compact data never silently falls back to older records. Download progress does not present partial results as complete.

The existing spatial buckets, viewport rendering, keyboard-accessible coincident-coordinate chooser and original coordinates remain. Above 120 coordinate groups, a 96-pixel grid reduces marker clutter. Each cluster anchors to an actual member closest to its grid centre, never to a fabricated or offset coordinate. Green square A, blue circle B and amber triangle C markers and labelled mixed-class rings expose evidence composition. No new framework, paid map API or backend is introduced. Explicit gzip decoding does not depend on GitHub Pages Content-Encoding negotiation. Detail sharding is by supplied country, not a claim of independently geocoded boundaries. Country totals include ISO territories and should not be interpreted as sovereign-state counts.

## Research review and future launch

All records still share one atlas. Quick views and advanced filters expose evidence class, record kind, stable organisation/name, country/city, sector, confirmed capabilities and facility type. A source category never becomes a verified facility capability. Research focus can surface 117 possible existing-location matches, unresolved permissions, missing geography, old/missing dates, status assertions and countries with fewer than two reviewed atlas records. Geographic priority describes this atlas's evidence coverage, not the actual size of a country's industry. Ranking is advisory and never grants verification. Record comparison keeps original IDs, evidence, capability states, relationship claims and coordinates separate.

The [launch dashboard](reports/licensing.html) and [machine audit](reports/licensing.json) cover all acquired datasets and registered source policies, with version/date, licence, notices, commercial/reuse restrictions and unresolved questions. A documented field-level licence is not source-wide permission. The 1,116 factual game-company references retain `UNSPECIFIED` terms. All websites, countries and source classifications remain intact. The repository is still public; internal research intent grants no access restriction or new permission.

```sh
python tools/launch_readiness.py generate --output /tmp/motionx-launch-review
python tools/launch_readiness.py check --output data/bulk/reports
python tools/launch_readiness.py template --record-id EXISTING_RECORD_ID --output /tmp/pending-research.json
```

The queue includes all 41,505 B/C records and binds each to its exact source-record hash, current catalogue and baseline. A stale/corrupted checkpoint blocks template preparation. Templates retain the original reference and set `canonical_record: null` and `approval_granted: false`. Humans must corroborate operating identity, physical branches, each capability, permissions, duplicates and coordinate accuracy before preparing an exact-content `research.py stage-pr` bundle. Future promotion also needs explicit reconciliation of the source reference and canonical record; this release does not implement automatic promotion or silently resolve the identity collision. Established IDs and all source provenance must survive any later correction.

See [the release report](reports/summary.md), [coverage dashboard](reports/coverage.html), [coverage metrics](reports/coverage.json), [performance measurements](reports/performance.json) and the [complete source research dashboard](runs/42300014355/review/coverage.html.gz). The full source dashboard is a compressed, self-contained review artifact: download and decompress it before opening. The source decisions in that original dashboard precede the inclusive visibility policy; Class C remains unverified but is now visible in the atlas.

Tests include real-source schema adaptation where acquisition succeeds, network/robots errors, malformed fields, hash corruption, duplicate conflicts, repeat import, state continuity, withheld-overlay safety, catalogue preservation, HTML/CSV safety, lazy profile links, licence-aware CSV and **50,000 synthetic locations**. Synthetic data lives only in temporary test directories. See the release performance report for actual conditions and limitations; browser timings are not business verification.

## Gaps toward 20,000

The source taxonomy also includes 7,039 `game_publisher`, 51,258 `broadcasting_media_production`, 2,732 `b2b_audio_visual_production` and 109 `studio_taping` listings. These broad categories do not prove game development, a physical production studio or capture-stage services. They are coverage leads, not published facility counts; targeted, permission-reviewed additional source adapters and corroboration are still needed. Music studios, dance/fitness studios, cinemas, retailers, film-festival venues and personal videographer listings are not treated as production facilities merely because their names contain “studio” or “video”.

General POI data has junk, duplicate and property-completeness limits documented by Overture. Lower-scoring business-register-style listings, unknown/closed operation signals, missing municipalities, overlay-licence questions and identity conflicts account for much of the gap. Capture, facial/volumetric capture, motion editing, retargeting, virtual production and game development require better **site-specific** evidence; this release does not manufacture those claims. Regional film/game agencies and associations need compatible bulk redistribution licences and usable physical-location exports before ingestion. Preserve deferred candidates for further research rather than weakening the threshold.
