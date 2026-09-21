# Pre-Publication Inventory Handoff

## 1. Status

**NEEDS_REPAIR** — scientifically sound and fully verified, but
documentation inconsistencies (8), missing publication infrastructure
(license, citation metadata, release assets, consolidated report), and
an unpushed history block publication. No scientific blockers.

## 2. Current branch and HEAD commit

Branch `main`; HEAD `bd3ff41` (hash-record edit only). Phase-3R commit
`79e06e6` exists as its parent — latest scientifically accepted work =
Phase 3R. History: 15 commits, Phase 1→3R lineage intact, no tags.

## 3. Working-tree status

Clean before this task; the only new/modified files are the four
inventory deliverables (left uncommitted for owner review). Untracked:
gitignored `data/raw/` + `data/downloads/` (raw Kaggle data correctly
NOT tracked) and `egg-info` build artifact. Note: the sandbox
environment wiped `.git/config` between sessions; `origin` was
re-added from records — **4 commits (cddb031…bd3ff41) remain unpushed**
(device-flow authorization pending since Phase 3).

## 4. Authoritative source-of-truth files

- Dataset provenance/hashes: `data/README.md`,
  `provenance/dataset_manifest.json`, `provenance/source_register.csv`.
- Lineage: `reports/source_lineage_report.md` (+`source_claim_matrix.csv`).
- Entity/units/policies/physics/events:
  `asset_scope_and_entity_analysis.md` (C32 statement),
  `variable_semantics_report.md`, `records.py` (P1–P4) +
  `phase_02_report.md`, `conditional_physics_analysis.md`,
  `events.py`/`filter_metrics.py`.
- Calibration/replay/CIs: `phase_03r_calibration.json`,
  `phase_03r_replay_metrics.csv`, `phase_03r_per_event.csv`,
  `phase_03r_t3_horizons.csv`, `replay.py`.
- Parity: `check_c_python_parity.py` + `firmware_skeleton/mif_filter.{h,c}`.
- Claims/assumptions/limitations: `docs/claim_register.md` (C01–C48),
  `docs/assumption_register.md` (A01–A37), `paper/limitations.md`.
- Outreach: `docs/outreach_requests.md` (NOT SENT).
- Public claims: `README.md` jointly with the claim register.
- Citations: `reports/generated/bibliography_register.csv` (only
  machine-checkable citation source).
Full map: `docs/documentation_map.md`.

## 5. Superseded or conflicting files

- `reports/phase_03_report.md` — superseded in part by 3R; body still
  contains "(54, 236]", "jump ≥ 50", and oracle 10/10 without CIs
  (banner corrects; body contradicts C38).
- `reports/phase_03_handoff.md` — superseded; item 4 contains the
  documented F1>10 factual error.
- `docs/paper_outline.md` — superseded by `paper/outline.md` (banner
  present).
- `docs/archive/*` — archival (owner's old README with MIT badge;
  unverified AI draft slot).
- Oracle CSVs/PNGs — authoritative for the exploratory analysis only;
  the three `filter_*.png` lack in-image EXPLORATORY labels.
- `paper/figures_tables_inventory.md` — lists replay figures as
  [READY] that do not exist on disk.

## 6. Existing writing assets

- **README:** 2,179 words; current through 3R with all six required
  standing statements; stale reproducibility block.
- **Technical report:** MISSING as a consolidated document; four
  per-phase reports exist and are authoritative for their phases.
- **Paper draft:** no manuscript; outline (complete as outline),
  conservative abstract (2 lengths), title candidates, limitations
  (13 items), figures/tables inventory.
- **References:** no references.bib; verified citation data only in
  `bibliography_register.csv`.
- **Figures/tables:** 6 figures (3 physics current; 3 filter oracle,
  label gap), 47 generated tables/CSVs current.
- **Outreach drafts:** 4 + 1 optional, all unsent, owner checklist
  present.

## 7. Top documentation gaps (max 10)

1. Consolidated technical report — MISSING.
2. Paper manuscript — MISSING (outline/abstract only).
3. README reproducibility block stale (69 vs 137 tests; two 3R
   commands and C-compiler requirement missing).
4. `phase_03_report.md` body retains corrected-away boundary wording.
5. No LICENSE (software or content) — owner decision.
6. No CITATION.cff / .zenodo.json / references.bib.
7. No release notes, tag, or version decision.
8. Replay/T3/CI figures and filter-state diagram not generated.
9. `pyproject.toml` stale (Phase-1 description; matplotlib undeclared).
10. No dependency lock/pin file.

## 8. Claim-consistency issues (max 10)

1. `phase_03_report.md` §1/§4: "(54, 236]" and "jump ≥ 50" (correct:
   [54, 236); |ΔOTI| > thr ∈ [42, 182)) — correct via 3R report/C38.
2. Same file: oracle 10/10 results without CI/task definition (correct
   via `phase_03r_replay_metrics.csv`; C44/C48).
3. README: "69 tests" (actual 137).
4. README: missing `run_leakage_replay.py` / `check_c_python_parity.py`
   commands.
5. README Unknowns: stale "(assumed °C for rate statements)"
   parenthetical (correct: C33/A23).
6. `pyproject.toml`: "(Phase 1)" description; matplotlib undeclared.
7. `paper/figures_tables_inventory.md`: [READY] statuses for
   non-existent figures.
8. Oracle PNGs: no in-image EXPLORATORY label.
9. `phase_03_handoff.md` item 4 F1>10 error (superseded; no other file
   repeats it).
10. No `docs/paper_claim_freeze.md` (referenced by convention; register
    + outline §4 serve the role).

Verified clean: no proven-fault/sensor/Celsius/ADC/PT100 claims, no
TinyML-for-filter, no oracle-as-validation, no prior-work-invalid
statements, no unscoped no-early-warning wording.

## 9. Test/provenance/parity results

- Hash gate: PASS (all raw SHA-256 match manifest).
- Suite: 137 passed, 0 failed.
- C/Python parity: PASS — 19,376-sample official sequence × 4 filters
  × 2 gap behaviors, 0 mismatches; sizeof(mif_filter_t) = 72 bytes.
- Forbidden-claim tests: PASS (5/5 targeted).

## 10. Citation/license/release readiness

CITATION.cff, .zenodo.json, references.bib, LICENSE, content-license
notice, DOI, release tag/date: all MISSING. Dataset citation and
redistribution notices present and correct (dataset © Original
Authors; not owned by the repository author). Version 0.1.0 in
pyproject only. Archived remote README shows an MIT badge (owner-intent
evidence, not a license). Author/ORCID/affiliation metadata absent —
owner decisions, not to be invented.

## 11. Outreach readiness

All drafts unsent and question-only (claims safe). Kaggle owner,
Putchala authors, Energies authors, KernelSphere: contact routes
verified → READY AFTER DOI (add repository/DOI links; minor revision).
Mirror-uploader draft: CONTACT NOT VERIFIED — NOT RECOMMENDED. Sending
requires publication + DOI first (priority protection) and explicit
owner authorization (checklist in the drafts file).

## 12. Decisions required from the owner

Software license; content license; author names/ORCID/affiliation;
repository name (current name conflicts with terminology discipline);
release tag/version/date; archive/DOI target; push authorization for
the 4 pending commits; phase_03_report correct-vs-archive; outreach
authorization (drafts, channel, sender, timing); optional preprint.

## 13. Exact recommended next action

**Documentation repair first:** commit these four inventory
deliverables; fix README reproducibility block and °C parenthetical;
correct or archive the `phase_03_report.md` body; fix
`pyproject.toml`; mark `figures_tables_inventory.md` statuses
accurately. Then: owner license/metadata decisions → push + tag →
DOI/archive → outreach. Do not send any outreach before the push and
DOI exist.
