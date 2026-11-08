# Global research continuation — consolidated delivery

Reviewed company evidence: 7–8 November 2026 UTC. This pass starts from reviewed PR #18 head `db8265e85b259d4b17214244eb0219c869207b1a`. Internal checked checkpoint `64f86921b3e9f088a07676b1b438665c48e9793b` was committed and pushed before continuing through the rest of the saved queue. Parent PR #15 stays draft, unchanged and unmerged at `efd52a86e66417438830aac285e3fffee3aa0fa0`. No merge, deployment, Pages change or fabricated approval.

## Complete saved-key assessment pass

**725 / 725 keys assessed; zero uninvestigated keys.** All 656 keys outstanding at the reviewed head were assessed, without a new company-count stopping point. All 753 original observations and their URLs, hints and outcomes remain bound to the historical source report. A key is a research unit, not necessarily a company. An access-failure assessment is not successful company verification.

| Backlog outcome | Keys |
|---|---:|
| branch or department research | 7 |
| company proposal prepared | 184 |
| existing identity reconciled | 53 |
| geographic facility review | 55 |
| historical operation review | 14 |
| identity review | 263 |
| research out of scope | 44 |
| research unresolved | 104 |
| supported proposal alias | 1 |

The **263 identity holds, 104 unresolved evidence/access/rights cases and 14 historical-operation cases** remain explicit research work. The 55 geography-only keys and seven branch/department cases must not be counted as new companies. Every key, reason, original source observation and evidence-confidence state is in [the checkpoint](reports/research-checkpoint.json) and [the complete audit](reports/report.json). Neither source presence nor automated matching constitutes independent current-operation verification.

## Actual company proposals and identity reconciliation

**184 distinct Class C company-reference payloads across 51 country associations**, including all **30 original proposals**. The original payloads remain in `inputs/reviewed-db8265e.json.gz`; `reports/recommendations.json` provides exact before/after fields, stable IDs and recommended groups. There are no unresolved cross-proposal name/domain conflicts in the admitted proposal set. One Beyond source alias links to one proposal, preserving both source histories; it does not duplicate a company.

The 53 backlog existing-identity reconciliations are company-level matches, not verified new facilities. Additional existing-ID geographic/supplementary reviews are counted separately. Official operating-name/domain evidence resolves Aardman, DNEG Animation, Lil Critter, Cloth Cat, Mukpuddy, Xilam and other straightforward variants. Source-supported homonym distinctions retain the original automatic matches and exact dismissal reasons: Irish Studio 9, Icelandic Sagafilm, Polish Human/PFX, New Zealand Rascal and Beyond, and French Les Films du Nord/MIAM are not forced into unrelated foreign or similarly named records. No canonical identity is merged or overwritten.

Proposed public scope: minimal factual company name/country and source-supported city where available, official website or clearly labelled source-listing URL, company-level service categories, evidence URLs/dates, stable provisional identity and explicit uncertainty. Null original coordinates, empty confirmed capabilities, no inferred ownership, no human approval and no Class A promotion. Rights are minimal factual scope with source-wide reuse unresolved; directory evidence pages are not mislabelled official company websites.

## Commercial correction measured on all 42,296 records

| Role | Reviewed-head policy | Proposed policy |
|---|---:|---:|
| potential client | 36311 | 6950 |
| service provider | 20 | 20 |
| both | 5838 | 19 |
| plausible unconfirmed | 0 | 35295 |
| adjacent uncertain | 123 | 8 |
| out of scope | 4 | 4 |

41114 reversible assessments change; **zero original source categories or records change**. Games/animation/VFX establish sector eligibility as potential clients without mocap or known outsourcing. Visual-production tags alone do not prove an external service offer; both requires separate relevant technical-sector evidence or an individual review. Generic film/video/TV production and game-publishing listings remain plausible, unconfirmed prospects. No budget, purchasing intent or operating-status claim is inferred.

The exact per-record changes are in `reports/classification-changes.json.gz`; its digest is bound by `classification-impact.json`. Public role filters, profiles, counts and CSV use the same six-role assessment; confirmed facility capabilities remain a separate filter.

## Audio scope

The Inside Track, Native Audio, Evoke Audio and The Sound Room remain the only four catalogue exclusions. They remain in explicit audit search, profiles and exports. Normal results are 42,292; audit storage/results remain 42,296. Envy remains eligible on individual visual-service evidence. Audiomotion retains its existing confirmed capture information; no audio-name rule excludes it.

The saved name-signal queue contains **603 records**: three overlap with reviewed audio exclusions and **600 remain name signals, not automatic exclusions**. The fourth exclusion, The Inside Track, has no audio/sound name token. New-intake evidence supports reversible out-of-scope recommendations for 440HZ, BLYND, Emotive Muzik, Studio Le Refuge, Fuse Post and Respeecher; none is silently removed from the catalogue. Multidisciplinary Jinglebell, Audio Projects/Galletly and Blackmeal remain relevant.

## Geography and source coverage

**17 geographic proposals for 16 existing company IDs**, including seven licensed approximate city-reference payloads. Bad Clay (Ho Chi Minh City), Scrawl and Robot Playground (Singapore), ModelFarm (Adelaide plus separately supported Brisbane), Blue Zoo and Lupus Films (London) remain proposals only. Source-backed correction questions include Tumblehead → Viborg, Fantasmagorie → Rome, Gertie → Milan, La Fabrique → Differdange and Tomavision → Santa Cruz de Tenerife; an old association is not automatically declared closed. Unsupported/unlicensed coordinate fields remain absent.

Of all 256 saved city associations, **18 have an individual follow-up and 238 still need one**; every ID and precise reason remains in `reports/geographic-associations.json`. Broader 55 branch/city backlog cases are separately retained. Floating Rock’s original company-only record and Wellington display point, Frame Machine’s Santa Monica point, every original coordinate and shared-coordinate selection remain unchanged. No pin offsets or city references presented as studio entrances.

Research spans **64 supported/historical country associations**. Ten regional source follow-ups document actual access, individually supported identities, matches/proposals, ambiguity, scope and unreviewed pages. SPPA/CEE, official film/trade agencies and company pages provide useful factual evidence. Animation SA returns controls without a roster; Animachi remains inaccessible; Animation UK and PROMPERU have indexed evidence but current direct-fetch failures. CEE’s visible 24-entry page is not a full directory enumeration. Country and source completeness remain false.

EA and PROGISS/3DVF are 12 explicit rights-review keys; restricted collectors remain disabled. No recursive crawling, hidden APIs, screenshots/OCR, alternate-host bypass, bulk reuse grant or copied source prose/media/contacts. Current self-reports and historical profiles are distinguished from independent verification.

## Preservation, review and reproducibility

All **42,296 canonical IDs and complete record hashes** are preserved: 243 retained locations / 119 reviewed organisations, 40,376 source-location references and 1,677 company references. Public evidence classes stay A230/B4,626/C37,440. Reference coverage remains 178 countries/territories, with 38 unknown-country references. These totals do not represent 42,296 independently verified active studios. All 209 protected historical research/source files remain intact. **Zero new canonical records, verified facilities or verified capabilities.**

Start with the [small exception summary](reports/review-exceptions.md), then the searchable [dashboard](reports/dashboard.html) and exact-field [recommendations](reports/recommendations.json). The dashboard contains 737 company/geographic reviews plus seven office/department investigations, not 744 distinct businesses. The 14-item held-out sample still lacks independent human labels; precision/recall remain null.

```sh
python tools/global_continuation.py prepare
python tools/global_continuation.py check
python tools/global_programme.py maintenance-check
python tools/package_global_review.py --output /tmp/motionx-review-fresh
```

Continue unresolved IDs with their existing source history and current evidence; never replace an inaccessible case with a guessed company. All assessed and remaining IDs, input hashes and continuation commands are saved. Human review of exact Class C fields, rights scope, identity/facility exceptions and coordinate corrections is required before a separate authorised database change. Draft status and CI do not enforce a human review; required-review protection remains unconfirmed. Parent PR #15 must first receive its own review; do not merge or retarget either PR automatically.

Executed checks, initial failures, final reruns and measured performance: [validation.md](validation.md).
