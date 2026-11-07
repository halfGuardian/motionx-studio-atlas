# MotionX Studio Atlas · New Zealand Census Wave 1

**Observed 7 November 2026.** This is a bounded source-led matching pass, not a completed census of every operating NZ facility. Existing catalogue references, evidence classes, coordinates, historic audits and individual service claims are unchanged. The same source list can be rerun against the full index.

## Why this release exists

The NZFC vendor list is included in the existing research, but company visibility, complete source categories and location-specific claims were confused. Counting 42,239 reference records is not counting 42,239 distinct active studios. This stage examines named NZ sources, preserves their original labels, reconciles names against **every 42,239-index record**, and exposes what requires human investigation.

## Enumerated observations

| Source | Rows examined | Enumeration status |
| --- | ---: | --- |
| [NZFC facilities](https://www.nzfilm.co.nz/inbound-productions/filming-in-nz/facilities) | 42 | Complete historical published list, imported from v1.4 source-code snapshot |
| [Screen Auckland digital & post-production](https://www.screenauckland.com/choose-auckland/digital-post-production) | 24 | **Partial**: pages 0, 1, 3 and 6 examined. Pages 2, 4, 5 were inaccessible and have not been counted as reviewed |
| [Screen Wellington directory showcase](https://www.wellingtonnz.com/screen-wellington/screen-industry-directory) | 9 | **Showcase only**, not the dynamic full directory; the rendered results interface returned 0/0 |
| [Screen Wellington “Why Wellington” creative showreel list](https://www.wellingtonnz.com/screen-wellington/why-wellington) | 21 | Complete set of *named showreel participants*, not a verified studio/service directory |
| [Film Otago Southland industry directory](https://www.filmotagosouthland.com/production-support/industry-directory) | 2 | **Selected, not exhaustive**: Graphic Monk Ltd and Shotover Media Ltd individual published listing pages |
| **Total source observations** | **98** | Source rows overlap; the denominator of eligible operating NZ studios is still unknown |

The input is [wave1.json](inputs/wave1.json), with source URLs, listing labels, regional context and completeness limitations. It contains no biography, private email, phone, authored webpage paragraphs, copyrighted assets, bulk copies, postal address lists or generated coordinates. Historical NZFC source categories are preserved at [nzfc-2026-11-07.json](../coverage/nzfc-2026-11-07.json).

### Reconciliation

`python tools/nz_census.py check` reads the actual 42,239-record public index and original 243 retained records, matches exact normalized identities plus bounded recorded name variants, then produces a per-source matching outcome. For a saved HTML, JSON and CSV report, use:

```sh
python tools/nz_census.py prepare --output data/nz-census/reports
```

This runs in the PR's **Validate public atlas** GitHub Actions workflow and uploads the `nz-source-census-wave1-full-catalogue` artifact (including a searchable HTML report and all 98 source rows). The browser-accessible report must be served under the same repository checkout as the Atlas for profile links to resolve.

Results explicitly distinguish: NZ identity name matched; multiple NZ identities; no-country candidate; foreign-only name collision; no exact/recorded alias match; and human identity hold. **A successful name match is not independent verification of a company being active or the recorded service being present at a physical facility.** Source-specific NZ regional listings do not imply every company has an exact geocoded branch. Map pins and facility services remain unchanged.

### Research leads requiring attention

- **Blockhead vs Assembly.** NZFC’s Blockhead entry links to the Assembly website. The separately published Screen Auckland listing and [Blockhead’s official website](https://www.blockheadvfx.com/about/) support distinct brands; Blockhead's current site documents its Sydney studio. Maintain the NZ operating branch as **pending human operation/location review**. Never assign Assembly’s domain or a fictitious Auckland capture stage to Blockhead.
- **Screen Auckland entries** include additional VFX/animation candidates such as Assembly, Creature Post, Eleven FX, Mandy VFX, The Machine Room and The Rig. The CI report determines whether each already has a catalogue name/alias match; an indexed website hit alone is not validation.
- **Screen Wellington** names include boutique studios and game/creative-tech companies (e.g., A44, PikPok, Rascal Kids, Storybox, RiffRaff Games). Participation in a showreel does not establish their service offering, studio address or demand for MotionX work.
- **Otago and Southland** need a distinct regional source sweep. Graphic Monk Ltd’s listing mentions motion capture; this is a **source claim**, not proof of a permanent commercial capture stage. Shotover Media Ltd’s listing includes animation and post-production.
- **Regional film-office coverage:** [Regional Film Offices NZ](https://www.filmoffices.nz/) identifies the wider NZ regional network. Screen Canterbury, Film Dunedin, Film Queenstown Lakes, Northland, Bay of Plenty and others remain queued for enumeration, not falsely marked complete.
- **VFXG NZ:** the guild publicly offers its separate list of **45 businesses by email**. That list has **not** been obtained or silently reconstructed; permission/actual data are needed to crosscheck it.

## Release guarantees

- All **42,239** pre-existing Atlas records remain unchanged; **0 new geocodes**, **0 new verified capture claims** and **0 automatic identity publications**.
- New source inputs are minimal factual references; source-wide reuse rights remain **UNSPECIFIED**.
- Geographies are used to reject unsafe foreign-branch matches, not assign source country to unsourced records. An unspecified country cannot become a verified NZ location.
- Source-specific categories are retained as listing labels, not converted into Class A or confirmed capabilities.
- **Partial inputs stay partial** and unresolved names remain visible; no false global 100% coverage metric.
- Human identity/active-operation/permission checks and the outstanding 37-row Annecy human precision review remain separate publication tasks.

## Next release gate

Complete missing Screen Auckland pages through normal authorised source access or obtain a permitted official export; obtain the Wellington directory's full roster; review alias/country collisions and all not-name-matched rows; validate credible facility addresses/capabilities independently; then propose **Class C candidate references only where the evidence and rights allow**, without inventing coordinates. Run an entity-disjoint human sample before promoting higher evidence classes.

