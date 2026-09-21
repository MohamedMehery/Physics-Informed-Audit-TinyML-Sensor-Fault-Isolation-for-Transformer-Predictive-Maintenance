# Phase 4B Handoff — Publication Repair, Technical Report, DOI-Ready Package

**1. Status.** COMPLETE. Delivered in commit `019013776f8a27f9e2ff8102d3c41d4266c118d7` plus this
hash-record commit (Phase-3R precedent). No new experiments, no
threshold retuning, no outreach, no tagging (owner action). Duplicated
earlier work was merged, not redone: inventory deliverables already
committed (`411614f`), Apache-2.0 full text (`6310981`), CITATION.cff
(`7c90515`), .zenodo.json (`47c8ccf`), README license section
(`71a63d2`/`228e0f5`). This phase edited/extended those artifacts only
where the Phase-4B prompt required.

**2. Commit hash.** `019013776f8a27f9e2ff8102d3c41d4266c118d7` — "Prepare v0.1.0 release
documentation and citation metadata". Pushed to origin/main (session
device-flow credentials were available). No tag created.

**3. Files created/modified.** Created: `NOTICE`,
`CONTENT_LICENSE.md`, `docs/archive/superseded_phase3/README.md`,
`paper/technical_report_v0_1.md`, `paper/references.bib`,
`paper/references.md`, `docs/release_notes_v0_1.md`,
`docs/reproducibility_quickstart.md`, `docs/release_checklist.md`,
this handoff. Renamed: license.txt → `LICENSE` (git mv, byte-identical
Apache-2.0 text). Moved verbatim (git mv):
`reports/phase_03_report.md`, `reports/phase_03_handoff.md` →
`docs/archive/superseded_phase3/`. Modified: `README.md` (9 repairs),
`data/README.md` (stale "license decision pending" bullet),
`pyproject.toml` (description; +matplotlib), `CITATION.cff` (title),
`.zenodo.json` (title; raw-data-not-included note),
`paper/figures_tables_inventory.md` (statuses),
`docs/claim_register.md` (3 archive paths),
`scripts/run_filter_evaluation.py` (in-image labels) + 3 regenerated
`reports/figures/filter_*.png`, `tests/test_phase3r_leakage.py`
(extended scan list, +13 forbidden phrases, +required-wording checks).

**4. Documentation contradictions repaired.** README: 69→137 tests
(both places); Phase-3R replay + C/Python parity commands, cc/gcc and
`--boundary-only` notes added; stale "(assumed °C for rate
statements)" replaced with C33/A23-aligned unconfirmed-unit wording
(no °C conversion used anywhere); "technical report / research
software artifact — not peer reviewed" statement; pointers updated to
the archived Phase-3 originals; Apache link retargeted to `LICENSE`;
structure block now lists firmware_skeleton/, paper/, license files,
and the 3R scripts. figures inventory: F1–F3 corrected from [READY] to
[NOT GENERATED] with corrected source paths (no excursion_catalog.csv
exists); v0.1.0-safe figures identified (F4–F7). pyproject "(Phase 1)"
removed, matplotlib declared. Superseded Phase-3 report/handoff
removed from the normal reading path, preserved verbatim in the
archive with an explanatory stub.

**5. License/citation metadata.** LICENSE = full official Apache-2.0
(apache.org text, copyright Mohamed Mehery). NOTICE identifies
project, author, dataset source, license split, and no-raw-data
redistribution. CONTENT_LICENSE.md states the Apache-2.0 (code) /
CC BY 4.0 (documentation, reports, figures) split and that dataset
rights remain with the original authors / Kaggle owner. CITATION.cff:
title "Transformer Telemetry Integrity Audit", version 0.1.0, author
Mohamed Mehery (Independent Researcher), real repository URL, ORCID
omitted, DOI omitted — cffconvert-validated (schema 1.2.0).
.zenodo.json: aligned title, v0.1.0, open access, Apache-2.0, keywords,
description now states raw Kaggle data is not included — valid JSON.
references.bib/references.md derived strictly from
`reports/generated/bibliography_register.csv` (8 entries; DOIs only
where verified: 10.1007/978-981-16-7389-4_21 and
10.3390/en15217981; uncertain fields recorded as notes, never
invented).

**6. Technical report.** `paper/technical_report_v0_1.md` — all 13
required sections; required conservative wording present ("OTI
units", "operationally defined high-band OTI events", "post-hoc
leakage-controlled replay", "deterministic plausibility filter", "no
field-confirmed hardware root cause", "entity identity remains
unresolved", "not peer reviewed"); all required metrics included with
per-number artifact citations (slug/version, archive SHA-256, file row
counts, repeated-record summary, OTI_T same-sample rule equivalence,
empty observed interval (54, 236), frozen thresholds per view,
replay metrics F2/F4/F3/F1 with exact binomial CIs, false-alert CIs,
P1–P4 view sensitivity, C/Python parity 19,376 × 4 × 2 with 0
mismatches, sizeof(mif_filter_t) = 72 bytes, 137 tests passed). Note:
event-recall CIs cite `phase_03r_replay_metrics.csv` (F1 9/10 =
[0.555, 0.9975]); the 3R report table rounds this as [0.60, 0.998] —
the CSV is treated as authoritative.

**7. Reproducibility quickstart.**
`docs/reproducibility_quickstart.md` — exact commands for environment
creation, package install, Kaggle download, hash verification,
Phases 1/2/3/3R, C/Python parity (including `--boundary-only` without
raw data), the 56-check independent verification, and the full suite
(expected: 137 passed), plus an expected-artifacts table and Kaggle
access requirements with failure modes (endpoint/credential failure or
archive change → provenance gates abort by design).

**8. Test/provenance/parity results.** Full suite: **137 passed**.
C/Python parity (standalone): **PARITY OK** — official P2_first
sequence 19,376 samples × 4 filters × 2 gap behaviors, 0 mismatches,
sizeof(mif_filter_t) = 72 bytes (host gcc). Provenance/hash gates
passed before and after every run (figure regeneration printed
"Post-run provenance gate OK; raw files unmodified");
`reports/generated/` restored byte-identical afterward — only the 3
labeled PNGs changed. Figure regeneration used the recorded
environment (pandas 2.2.3, numpy 2.3.5, matplotlib 3.10.9).

**9. Forbidden-claim scan.** PASS. Guard extended to scan the
technical report, quickstart, and release notes (plus
release_claims_v0_1.md if ever created); the 13 prompt-specified
phrases added; required-wording checks added for the new documents.
One wording fix applied during validation ("nothing is a measured MCU
latency" → "no measured MCU latency is reported"). No forbidden claim
exists outside explicitly negated contexts.

**10. Raw data.** Absent from git: `git ls-files data/` returns only
`data/README.md`; `.gitignore` protects `data/raw/` and
`data/downloads/`; only hashes/manifests/code/docs are tracked.

**11. Exact remaining manual owner actions.** (a) Review this phase's
diff. (b) Tag and push per `docs/release_checklist.md`:
`git tag -a v0.1.0 -m "v0.1.0 reproducible transformer telemetry
audit"`; `git push origin main`; `git push origin v0.1.0`. (c) Zenodo:
enable the repository, create the GitHub release v0.1.0, let Zenodo
archive it, copy the minted DOI. (d) Update README, CITATION.cff,
.zenodo.json, and the technical report with the DOI; commit as v0.1.1
or a post-release metadata commit. (e) Optional: preprint decision.

**12. Recommended public GitHub release description.** "v0.1.0
reproducible transformer telemetry audit — evidence-first audit of the
Kaggle 'Distributed Transformer Monitoring' dataset (ten operationally
defined high-band OTI excursions; entity identity unresolved; no
field-confirmed root cause) plus a deterministic plausibility filter
with leakage-controlled frozen-threshold replay (10/10 events, exact
95% CI [0.6915, 1.0]; 0–0.26 false-alert episodes/day), a C99
reference implementation with full Python/C parity (0 mismatches, 72 B
state), 137 passing tests, and a consolidated technical report (not
peer reviewed). Raw Kaggle data is not included."

**13. Outreach.** STILL BLOCKED pending publication + DOI and explicit
owner authorization. All drafts remain stored and unsent
(`docs/outreach_requests.md`); the mirror-uploader route remains not
recommended.
