# Release-candidate validation and publication limits

The executed local checks target the actual integrated catalogue, not just standalone proposals. The two parent PRs remain unchanged. This draft does not merge, deploy or grant human approval.

## Data and research scope

42,478 stored references / 42,474 normal results; 182 new provisional company references across 51 source-associated countries, two withheld. All 42,296 parent full-record hashes, 40,619 original coordinate records, the root database hash and 348 protected history files remain unchanged. Source-reviewed root locations/organisations remain 243/119; A230/B4,626/C37,622. Company references total 1,859. The 41,977 source identity keys and 179 country/territory associations are not independently verified operating-company/facility counts.

All 184 proposals received a minimal-field/identity/sector/source-scope audit using the saved individual research, complete parent catalogue and within-proposal reconciliation. No live-verification pass over all companies is claimed. Three focused official/public exception pages were revisited on 2026-11-08: Moon Face's vendor interview, Ventura's trade listing and Sparkle's national film-institute listing. `inputs/exception-evidence.json` records the limited factual conclusions. A company self-report, programme participation, discovered URL or automated match is not independent confirmation of present operation.

Source-wide rights remain UNSPECIFIED for all 182 admissions. The exact proposal is limited to minimal factual identifiers, country/city associations, source URLs/dates and coarse source-supported sectors; it omits authored descriptions, imagery, contacts, ownership and confirmed technical services. Unknown terms neither grant source-wide rights nor automatically prohibit these identifiers. The maintainer must judge this exact limited scope. Existing restricted collectors and held sources remain disabled. No screenshot/OCR, alternate-host or hidden-API workaround is used.

## Executed checks

- Python: 315 tests passed (140.568 s).
- JavaScript: 92 tests passed (13.813 s).
- Canonical `studios.json`: zero errors / 265 retained warnings.
- Complete source-to-public replay passed: bulk → boutique → Annecy → raw NZ → NZ gate → geography → commercial scope → integrated release candidate. It reproduces the actual complete public file set, gzip transports, exact metadata and original rows.
- Twelve canonical/current-and-historical licensing, report, maintenance and geographic checks passed; the separate current release check validates all 42,478 rows, every original record hash, index entries, shard/gzip hashes and decompressed equality. Historical tools explicitly reproduce their frozen parent cohort; they do not filter the current public loader or exempt new records from validation.
- HTTP/browser final rerun: **96 checks across all 13 suites passed** after the popup correction. The new suite also serves the complete static artifact, rather than only the checkout, and tests the 184-decision dashboard. Checks cover actual intake searches/filters, game-client eligibility without capture, Animation taxonomy/original labels, four audio-only exclusions, source/rights CSV, unpinned profiles, all city-reference display behaviours, shared-coordinate keyboard selection, browser links/history, data/CDN errors and 390px mobile navigation.

## Initial failures and corrections

The first Python run (308 tests before release-specific tests were added) found one historical NZ Wave 1 cohort error after the actual draft additions. The old report reader now explicitly preserves its original cohort; independent current-data checks still verify all additions. The first JavaScript run had three hard-coded historical-count assertions; they now follow actual manifest totals, with release-specific tests asserting exact new totals and preservation. Both complete reruns pass.

The first targeted release check encountered a missing optional legacy coordinate-source field; licensed coordinate matching now reads it safely and still requires a substantiated hash-bound source. An intermediate profile-link string edit failed syntax checking and was corrected before browser runs. An initial new-browser attempt addressed a collapsed advanced control without opening it; the test now opens the existing accessible controls.

An initial non-escalated HTTP smoke could not load the Leaflet CDN; the normal network-enabled rerun used the real CDN/OSM resources successfully. During static-package testing a real bug was found: Leaflet popup auto-pan triggered company-marker reconstruction and removed the shared-coordinate chooser. Viewport refresh now retains an open company popup and refreshes after close. The regression pans the map with the Singapore chooser open, then selects a company using the keyboard. No geographic offsets, coordinates or schema claims were changed. Initial logs and targeted successful reruns are retained in `qa/`.

## Warnings and remaining gates

Warning categories overlap; they must not be summed as distinct companies. The manifest retains 42,235 unreviewed source/company references, 40,376 unverified source-point precision warnings, 1,859 unpinned company references, 1,594 unspecified-term company references, 170 source rows missing cities, 14 source rows missing countries and 120 possible-duplicate-review rows. Historical boutique/Annecy/NZ review warnings remain 332/172/57; three NZ foreign-name collisions, two staged NZ proposals and 27 historical NZ rights-scope questions remain visible. The new cohort adds 182 explicit minimal-fact/rights-scope warnings and two withheld-company warnings. Thirteen legacy unknown-evidence root records remain unresolved; canonical validation still reports all 265 warnings.

PR #15's 57 references are grouped into 30 scoped agency references, 20 limited-facts rights cases, three company-only facility/geography cases and four audio-only audit exclusions. Recommend 53 within those scopes; the 23 UNSPECIFIED cases need one explicit limited-scope cohort decision, while facility/booking/entrance claims stay separate. Melodics and Level stay staged. PR #15 approval is a prerequisite, not an attestation supplied by this report.

GitHub main protection/ruleset read requests returned `Forbidden`, including a network-enabled retry. The current connector has no equivalent protection-read capability. Required human reviews and bypass rights could not be verified; absence of protection is not inferred. Draft PR status and tests do not enforce approval. No settings were changed. The current licensing report also retains the inherited 1,116 game-database reference permission question; approval of this new cohort is not blanket clearance of earlier datasets or expanded reuse.

Recommended authorised order: #15 → #18 → this new draft PR. Review exact heads; manually rebase/retarget and rerun checks if content changes. Do not reuse historical approval hashes. Existing Pages configuration may deploy each authorised main merge; no atomic three-merge release or deployed-site success is claimed. The maintainer must choose the release window and any desired deployment gates.

Retain 381 unresolved research cases, 55 geography/facility keys, seven office/department investigations, 238 city associations, all source restrictions and partial regional directories. No global/source census is declared complete. See `DECISIONS.md` and the complete audit for exact admission/hold fields and geographic exceptions.

## Performance measurements

Single final local runs, installed headless Chromium, actual HTTP subdirectory; not deployed GitHub Pages. The constrained run uses 96,000 bytes/s download, 150 ms latency, 4× CPU emulation and a 390×844 viewport. No physical low-memory-phone test is claimed. Live Leaflet/OSM requests are used, not substituted tiles.

| Measurement | PR #18 recorded run | Integrated draft final run |
|---|---:|---:|
| Real full-catalogue HTTP readiness | 2.166 s | 1.647 s |
| Constrained mobile readiness | 32.666 s | 33.098 s |
| Query all stored records | 26.2 ms / 42,296 | 21 ms / 42,478 |
| Search compute | 11.1 ms | 14.5 ms |
| Uncached detail profile | 122.2 ms | 77.30000000447035 ms |

The compact index is 5,126,978 bytes / 2,224,418 gzip bytes; the compressed root baseline is 358,282 bytes. These compressed fallbacks are explicitly fetched and hash-checked because a static Pages host need not negotiate compression. Detail shards stay lazy. Viewport panning rendered 140 markers in 35.69999999552965 ms in this run. The full download/integrity check remains a roughly half-minute wait in the constrained scenario; sharding/search is not an offline or low-memory guarantee. The same machine was not held at fixed load between historical and final runs, so differences are observations, not a controlled speedup claim.

The separate sharded **50,000 synthetic** fixture became ready in 1.085 s, searched in 14.7 ms and opened a profile in 58.1 ms. The deliberately unsharded 50,000-row compatibility fixture took 11.792 s to load and validate (13.448 s for its scenario). Neither fixture adds real companies, public records, country coverage or verification. Full raw metrics and executed commands/logs are in `qa/`.
