# Atlas maintenance v2 — owner operating guide

**Weekly discovery gathers evidence. Monthly drafts stage research. Neither changes published company data.** This is a bounded research system, not a worldwide census or a verified active-studio count.

## What runs

- **Weekly:** the existing `23 7 * * 1` schedule stays Monday **07:23 UTC**: **20:23 NZDT / 19:23 NZST**. GitHub may start late. The job restores raw candidate/history unions, applies access-review expiry, scans only eight approved bounded official sources, matches against the complete catalogue and uploads discovery, triage and maintenance artifacts. Permissions remain `contents: read` / `actions: read`.
- **Monthly:** a lightweight daily **09:23 UTC** gate prepares a batch on the configured day, default **first day of each month** (22:23 NZDT / 21:23 NZST). `config.json` controls enable/disable, UTC day 1–28 and month interval. Manual **Consolidate monthly Atlas research → prepare_now** permits catch-up. This input prepares research; it grants no approval. The workflow becomes runnable only after this infrastructure PR is reviewed and merged.
- **One open batch:** `automation/atlas-maintenance-YYYY-MM` is stable and deduplicated. An earlier open batch blocks another. Ready-for-review, foreign or retargeted PRs are not edited. Previous reports/history remain; pushes are never forced.

## Review and approve a monthly batch

1. Download **monthly-atlas-owner-review** from its Actions run, or browse `data/maintenance/batches/YYYY-MM` in the draft PR. Serve the downloaded folder with `python -m http.server 8000` and open `http://localhost:8000/review.html`. It groups company/country evidence, existing matches, duplicates, changes, technical claims, source permissions and unresolved questions. `report.json`, `state.json` and `integrity.json` retain the complete audit and exact hashes.
2. Check original source and observation dates separately. A refreshed download does not make an old source current. Names/domains are matching signals, not independent company verification. Absence, an empty extraction, a failed fetch or a changed website never proves closure. Game developers need no capture evidence to be eligible clients. Audio-only exclusions need individual service evidence; an audio-sounding name or a directory category is insufficient. The four existing reviewed exclusions remain unchanged.
3. **Merging the monthly PR archives research only.** It cannot change `studios.json`, `data/public`, capabilities or coordinates. Accepted company changes need a **separate exact-content data PR**: identity/rights review, before/after values, actual dates, licensed geography, regenerated public assets/checkpoints and full validation. Approve those exact fields and manually authorise merge; never reuse old approval hashes or bypass history checks.
4. Actions-bot PRs may not trigger CI. In **Actions → Validate public atlas → Run workflow**, select the batch branch `automation/atlas-maintenance-YYYY-MM` and enter its current full 40-character head commit as `expected_sha`. Both validation and browser jobs reject a different commit. Require both jobs to pass on that exact SHA before approval; repeat after any new commit. The manual option becomes available after this infrastructure PR reaches main. Do not substitute a successful main-branch run. Required-review enforcement is **unverified**: the protection API returned **403 Resource not accessible by integration**. Configure required reviews/stale-review dismissal if needed. Drafts/tests are not approval. GitHub write access remains a trust boundary.

## Finish this release

After the final PR checks pass, the owner approves the exact PR #22 head and authorises merge/deployment. Confirm main's review rules and Actions permission to create PRs in repository settings. Existing Pages settings may publish automatically when main changes, so treat merge as a deployment decision. After the authorised merge, verify the live Map guide, company search/profiles and mobile layout; then run the monthly workflow with `prepare_now`, inspect its research-only draft, and validate that batch using step 4. A repeated preparation must create no duplicate PR. If bot PR creation is denied, use the retained branch/artifact for manual recovery. Close issue #21 after recording those activation results. Remaining manual-source research is ongoing operation, not unfinished release work.

## Coverage and exceptions

Automatic bounded source scans: **DNEG, metricminds, Framestore, Larian, RISE, Outpost, Flying Bark and FOLKS**. Every fetch still obeys robots, same-origin redirects, public DNS, limits and its recorded policy. Expired access reviews disable collection until renewed through a reviewed PR.

The **424-row animation-directory export** is **processed offline at its reviewed pinned revision**, with CC BY 4.0 attribution. Additional CSV/JSON sources require a reviewed permission/licence policy, stable IDs, metadata and append-only state registration. New versions need their own access/reuse review; no new crawler is introduced.

**17 official sources remain manual**, including EA, Ubisoft, Cinesite, ILM and Wētā. All other source restrictions remain. No screenshots/OCR, hidden APIs, alternate-host bypasses or private/contact/CRM data. The [source matrix and execution audit](README.md) distinguish automatic coverage from manual gaps.

## When something fails

Source failures fail the weekly job **after available artifacts are saved**. Stale observations, old source assertions, expiring artifacts and policy holds appear in the summary/dashboard. Enable personal GitHub Actions failure notifications or watch the workflow; no email/Slack service or automatic issue spam is configured. A green scan does not verify studios or worldwide coverage.

Artifacts expire after **90 days**. Merge an owner-reviewed monthly research checkpoint or retain a full offline copy before expiry. Recovery tries valid artifacts from completed main discovery runs, including failed runs with useful partial evidence; then merged monthly checkpoints; then the newest hash-bound raw discovery archive. Gaps stay explicitly partial and suppress absence inference. Corruption never silently creates a fresh empty queue. If PR creation is forbidden, the pushed branch and downloadable artifact remain available for manual recovery; the exact recognised permission restriction is reported. No settings, studios or historical evidence are deleted to make a run pass.
