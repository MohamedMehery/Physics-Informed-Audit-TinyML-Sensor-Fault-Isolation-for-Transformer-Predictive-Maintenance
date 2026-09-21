# Pre-Publication Documentation Inventory and Source-of-Truth Audit

Inspection-and-organization task. No scientific claims introduced, no
thresholds retuned, no analyses rerun beyond lightweight consistency
verification, no files rewritten other than the four inventory
deliverables. Deliverables: `docs/documentation_map.md`,
`reports/generated/documentation_inventory.csv` (121 rows), this
report, and `reports/prepublication_inventory_handoff.md`.

---

## 1. Repository state

- **Branch:** `main`. **HEAD:** `bd3ff41` ("phase_03r_handoff: record
  Phase-3R commit hash").
- **79e06e6** (Phase 3R content commit) **exists** and is an ancestor
  of HEAD. `bd3ff41` is a later legitimate commit containing only the
  hash-recording edit to `reports/phase_03r_handoff.md` — no scientific
  change. Latest scientifically accepted work = Phase 3R.
- **History:** 15 commits from `6b81c65` (initial) through Phase 1
  (`9d73ab2`), Phase 2 (`2aab096`), the remote README merge
  (`8ec670a`), Phase 3 (`cddb031`), Phase 3R (`79e06e6`), and two
  handoff-hash commits.
- **Working tree:** clean before this task; the only new files are the
  four inventory deliverables (intentionally left uncommitted for owner
  review). No uncommitted scientific changes.
- **Remotes:** `origin` →
  github.com/MohamedMehery/Physics-Informed-Audit-TinyML-Sensor-Fault-Isolation-for-Transformer-Predictive-Maintenance.
  Note: the sandbox environment wiped `.git/config` between sessions
  (a recurring infrastructure issue); the remote was re-added from
  records this session. **Four local commits (`cddb031`…`bd3ff41`) are
  not pushed** — device-flow authorization has been pending since
  Phase 3 (three codes expired unused).
- **Tags:** none. **Stashes:** none.
- **Tracked files:** 117. **Untracked:** `data/raw/` (5 CSVs),
  `data/downloads/` (both gitignored by design — raw Kaggle data are
  NOT tracked and NOT committed, per redistribution caution), and
  `src/transformer_audit.egg-info/` (build artifact).
- **Generated artifacts:** tracked (47 CSV/JSON under
  `reports/generated/`, 6 PNGs under `reports/figures/`) — appropriate,
  since raw data are gitignored and generated files are the citable
  evidence.
- Repository tree (tracked, excluding caches/raw/build): see
  `reports/generated/documentation_inventory.csv`; top-level layout:
  `src/` (12 modules), `scripts/` (7), `tests/` (8 files),
  `docs/` (+`archive/`), `reports/` (+`generated/`, `figures/`),
  `paper/` (5), `provenance/` (2), `firmware_skeleton/` (2),
  `data/README.md`, `pyproject.toml`, `README.md`, `.gitignore`.

## 2. Documentation inventory summary

Full table: `reports/generated/documentation_inventory.csv` — 121 rows
with path, type, purpose, phase, current/superseded, source-of-truth
status, completeness, README reference, update need, notes. Highlights:

- 34 files referenced by README; 8 flagged needs-update (README itself,
  `pyproject.toml`, `paper/figures_tables_inventory.md`,
  `reports/phase_03_report.md`, `reports/phase_03_handoff.md`, and the
  three oracle `filter_*.png` figures).
- Registers: `docs/claim_register.md` (C01–C48, C38/C39 corrected
  in place in 3R) and `docs/assumption_register.md` (A01–A37) —
  current, authoritative.
- Phase reports/handoffs: Phase 1 (report 13 sections, 2,642 words;
  handoff 724), Phase 2 (report 13 sections, 1,333; handoff 1,013),
  Phase 3 (report 10 sections, 2,565 — superseded in part; handoff
  731 — superseded), Phase 3R (report 10 sections, 1,777; handoff
  918; acceptance review 1,089).
- `docs/paper_claim_freeze.md` — **MISSING** (never created; the
  register + `paper/outline.md` §4 "claims NOT made" perform that
  role, but no frozen pre-submission claim list exists).

## 3. Source-of-truth map

See `docs/documentation_map.md` (20 categories, six status classes,
six named conflicts, archival recommendations). Key resolutions:
Phase-3R artifacts are authoritative for filter evaluation;
`phase_03_report.md` body text is superseded where it conflicts;
oracle CSVs remain authoritative *for the exploratory analysis only*;
the registers are authoritative for claim/assumption wording.

## 4. Claim-consistency scan

Scanned: README, all `paper/*.md`, outreach drafts, phase-report
executive summaries, 3R handoff — against the registers, the 3R
handoff, and `phase_03r_replay_metrics.csv`. Most pattern hits were
verified as **correct contexts** (negations, corrections, labels,
their-system attributions). Genuine issues:

| # | File | Line/section | Existing wording | Why inconsistent | Authoritative correction source | Recommended action |
|---|------|--------------|------------------|------------------|--------------------------------|---------------------|
| 1 | `reports/phase_03_report.md` | §1 (L44), §4 (L145) | "upper threshold in (54, 236]"; "jump threshold ≥ 50" | Wrong separation interval and ambiguous strictness — corrected to [54, 236) and \|ΔOTI\| > thr ∈ [42, 182) | `phase_03r_report.md` §2; C38 | Correct body in place or archive file behind 3R report |
| 2 | `reports/phase_03_report.md` | §1, §4, §5, §6 | Oracle "10/10" results without CIs or task definition | 10/10 requires CI [0.69, 1.00] + band-crossing task definition; oracle numbers lack both | `phase_03r_replay_metrics.csv`; C44/C48 | Add CI/task note during documentation repair |
| 3 | `README.md` | Reproducibility § | "69 synthetic-fixture unit tests" | Suite is 137 tests | `tests/`; verification run §8 | Update count and command list |
| 4 | `README.md` | Reproducibility § | command list ends at Phase 3 | Missing `run_leakage_replay.py` (primary 3R analysis) and `check_c_python_parity.py`; no C-compiler requirement stated | `scripts/` | Add commands + `cc/gcc` requirement |
| 5 | `README.md` | Unknowns § | "(assumed °C for rate statements — flagged)" | Stale Phase-1 parenthetical; rates are OTI-units/min; °C assumption applies only to conditional-physics ΔT (A23) | C33, A23, `variable_semantics.csv` | Reword to "OTI units; °C equivalence assumed only in conditional-physics ΔT (A23)" |
| 6 | `pyproject.toml` | `[project]` | description "…(Phase 1)"; deps pandas+numpy only | Project is at 3R; matplotlib used by two scripts but undeclared | `scripts/run_filter_evaluation.py`, `run_phase2_analysis.py` | Update description; declare matplotlib (or make scripts degrade without it) |
| 7 | `paper/figures_tables_inventory.md` | F2/F3 rows | marked [READY] | Those PNGs do not exist (only source CSVs) | `reports/figures/` listing | Mark PENDING or generate figures in a later task |
| 8 | `reports/figures/filter_*.png` (3) | in-image titles | no EXPLORATORY label inside the image | 3R requires the exploratory/oracle label wherever oracle results are shown | `phase_03_filter_summary.json` analysis_type; 3R report §3 | Regenerate with in-image label or replace with replay figures |
| 9 | `reports/phase_03_handoff.md` | item 4 | "F1 > 10/min misses … (11.1, 14.5)" | Factually wrong (both exceed 10) | `phase_03_acceptance_review.md` error 1 | Keep as superseded historical record; ensure no other file repeats it (none does) |

Verified-clean (no instances found): OTI as confirmed Celsius as a
*claim*; proven single-transformer wording; proven sensor-fault
wording; ADC/PT100/open-circuit claims as facts (all mentions are
negations or unknown-lists); TinyML for the filter (all mentions
negated/rejected); oracle results presented as held-out validation
(labels present); false external/prospective-validation statements
(all correctly disclaimed); "prior work is invalid" claims (all
mentions are the required negated form); "no early warning exists"
without tested-rule scope (removed in 3R); unsupported transformer
specifications (1500 kVA always attributed to the Energies authors'
own system). Outreach drafts contain only questions and correct
attributions.

## 5. Paper and technical-report readiness

**A. Technical report: MISSING (consolidated).** Four authoritative
per-phase reports exist (word counts above; sections verified against
each phase's spec; each ~100% complete for its phase scope and
consistent with 3R except issue #1/#2 for the Phase-3 report body). No
single cross-phase technical report exists.

**B. Academic paper draft: NOT a draft.** Exists: `paper/outline.md`
(outline only — story, 14-row section plan with evidence statuses,
figures plan, claims-NOT-made; complete as an outline), abstract
draft (2 lengths, conservative wording, numbers present but not
artifact-linked, no citations — normal for an abstract), title
candidates, limitations (13 items), figures/tables inventory
(aspirational in part). Missing: manuscript sections, methods text,
results text, references list. Completion by declared checklist:
outline 100% (as outline); abstract ~80% (needs artifact links +
final title); no manuscript exists (0%).

**C. README/landing page:** exists, 2,179 words, current through 3R
including all six required standing statements. Checklist
(status/description/dataset/findings/unknowns/structure/history =
present; reproducibility = present but stale; license section =
missing; citation section = missing): ~80%, needs update (issues
3–5).

**D. Release notes: MISSING** (no file, no tag).

**E. Reproducibility guide: PARTIAL** — README section + `data/README.md`
+ `pyproject.toml`; no standalone guide; stale test count; missing 3R
commands and C-compiler requirement; no dependency lock. ~70%.

## 6. Figure and table inventory

Full details in `documentation_inventory.csv`; figure plan vs disk in
`paper/figures_tables_inventory.md`. Existing figures (6):

| ID | Path | Purpose | Data source | Phase | Current? | Publication-ready? | Missing caption? | Obsolete numbers? |
|----|------|---------|-------------|-------|----------|--------------------|------------------|-------------------|
| P1 | `figures/physics_bounds_achievable_dT.png` | Achievable ΔT bounds | `physics_sensitivity.csv` | 2 | yes | near (assumption labels inside) | in report, not in figure file | no |
| P2 | `figures/physics_bounds_critical_mass.png` | Critical-mass bounds | `physics_sensitivity.csv` | 2 | yes | near | same | no |
| P3 | `figures/physics_bounds_power_vs_mass.png` | Power-vs-mass bounds | `physics_sensitivity.csv` | 2 | yes | near | same | no |
| F4 | `figures/filter_roc_by_type.png` | Oracle ROC by type | `filter_sweep_summary.csv` | 3 | exploratory | NO — in-image label missing | captions in reports | oracle-only (labeled in text) |
| F5 | `figures/filter_threshold_sensitivity.png` | Threshold sensitivity | `filter_sweep_summary.csv` | 3 | exploratory | NO — same | same | same |
| F6 | `figures/filter_lead_time_distribution.png` | Oracle lead distribution | `filter_per_event_detail.csv` | 3 | exploratory | NO — same | same | same |

Topic coverage check: dataset/file inventory ✓ (table); repeated-record
analysis ✓ (tables); OTI distribution + observation gap ✓ (tables);
OTI/OTI_T same-sample equivalence ✓ (tables, no figure);
duplicate-policy sensitivity ✓ (table); source-lineage summary ✓
(table/report); conditional-physics bounds ✓ (tables + 3 figures);
apparent time-constant sensitivity ✓ (table, **no figure**);
frozen-threshold replay results ✓ (tables, **no figure**);
confidence intervals ✓ (CSV columns, **no figure**);
oracle-vs-frozen distinction ~ (text tables only, **no figure**);
filter evaluation ✓ (tables + 3 exploratory figures); C/Python parity
~ (script + report text; **no persisted result artifact**);
filter-state diagram **MISSING** (struct documented in code only).
Missing figures are reported, not generated, per task scope.

## 7. Citation, authorship, and release readiness

- **CITATION.cff: MISSING. .zenodo.json: MISSING. references.bib /
  references.md: MISSING.** Best available citation metadata:
  `reports/generated/bibliography_register.csv` (verified entries:
  dataset S1 with license "Data files © Original Authors"; Putchala et
  al. 2022 Springer DOI; Energies 15(21):7981 DOI; manufacturer/utility
  sources) — machine-checkable but not in standard citation formats.
- **LICENSE: MISSING.** No software license, no content/report license.
  Evidence for owner intent: the archived remote README
  (`docs/archive/remote_readme_4ab4b02.md`) displays an MIT badge, but
  no LICENSE file was ever committed. Per standing instruction, no
  license is chosen on the owner's behalf; software and
  document/figure licensing must be decided separately.
- Dataset citation and redistribution notices: **present and correct**
  (`data/README.md`: dataset © Original Authors, owned by
  Sreshta Putchala / not the repository author; raw files gitignored;
  hashes only). The repository does not claim dataset ownership.
- Author name / ORCID / affiliation / DOI / repository-URL metadata:
  not present anywhere (owner identity is operationally the GitHub
  account, but formal authorship metadata is an owner decision — do
  not invent).
- Version: `pyproject.toml` 0.1.0. **Release tag: none. Release date:
  none.**

## 8. Reproducibility status

From a clean clone a researcher gets code, tests, and generated
artifacts, but must download the dataset (official Kaggle route,
scripted + hash-verified). Gaps: dependency list omits matplotlib; no
lock/pin file; README test count stale; two 3R commands missing from
the README; C-compiler requirement undocumented.

Verification run this task (exact commands and results):

```
$ python -c "...verify_raw_files(manifest, data/raw)..."
  all_match: True                       # provenance/hash gate PASS
$ python -m pytest
  137 passed in 6.98s                   # full suite PASS
$ python scripts/check_c_python_parity.py
  official sequence 19,376 samples x 4 filters x 2 gaps, 0 mismatches
  sizeof(mif_filter_t) = 72 bytes; PARITY OK
$ python -m pytest tests/test_phase3r_leakage.py -k "forbidden or required
  or energies or exploratory or honesty"   → 5 passed  # overclaim guards PASS
```

## 9. Outreach readiness — DO NOT SEND

Drafts in `docs/outreach_requests.md`; nothing sent; owner checklist
present.

| Recipient/organization | Draft | Purpose | Contact independently verified? | Claims safe? | DOI/repo placeholder? | Status |
|---|---|---|---|---|---|---|
| Kaggle owner (S. Putchala) | Draft 1 | Origin/scope/units questions | Yes (dataset page/profile, S6) | Yes (questions only) | No — says "hashes published" though nothing is published yet | READY AFTER DOI (add link; minor revision) |
| Putchala et al. authors (CBIT) | Draft 2 | Export vs live stream; semantics | Route verified (Springer corresponding-author route, S11); individual emails not collected | Yes | No | READY AFTER DOI (add link) |
| Ramesh et al. / Energies (AUS Sharjah) | Draft 3 | Kaggle-vs-own-system separation; row counts | Route verified (corresponding authors, CC BY paper S7) | Yes — correctly attributes 1500 kVA to their system | No | READY AFTER DOI (add link) |
| KernelSphere Technologies | Draft 4 | Platform scope, sensor/units questions | Yes (public contact page, phone/CIN verified 2026-09-20) | Yes | No | READY AFTER DOI (add link) |
| Kaggle mirror uploader (pythonafroz) | Draft 5 (optional) | Mirror provenance/rename | No | Yes | No | CONTACT NOT VERIFIED — NOT RECOMMENDED |

All drafts must wait for publication + DOI (priority protection) and
explicit owner authorization.

## 10. Owner decisions required

1. Software license (evidence: archived README's MIT badge).
2. Content license for reports/figures (separate from software).
3. Author list, names, ORCID, affiliation (CITATION.cff/paper).
4. Repository name (current name contains "TinyML-Sensor-Fault-
   Isolation", conflicting with the terminology discipline flagged in
   `paper/title_candidates.md`).
5. Release tag/version scheme and date.
6. Archive target and DOI (e.g., Zenodo) — after push.
7. Authorization to push the four pending commits (device flow
   outstanding since Phase 3).
8. Phase-3 report disposition: correct body in place vs archive.
9. Outreach authorization: which drafts, channel, sender identity,
   timing (after DOI).
10. Optional preprint submission (venue choice, timing).

## 11. Recommended minimum publication sequence

1. **Documentation repair** (issues 1–8 of §4: README repro block and
   °C wording, phase_03_report body correction or archival,
   figures_tables_inventory statuses, pyproject metadata/dependency,
   figure relabeling).
2. **Technical-report completion** (consolidated cross-phase report;
   then paper manuscript if desired).
3. **Owner metadata and license decisions** (§10 items 1–5).
4. **GitHub publication/tag** (push pending commits; tag v0.1.0 or
   owner's scheme; release notes).
5. **Immutable archive/DOI** (deposit; add DOI to CITATION.cff/README).
6. **Outreach** (revise drafts with repository/DOI links; send only
   after 4–5 to protect priority and avoid unstable claims).
7. **Optional preprint submission** (after 1–6).

Journal/conference submission is out of scope for this task. Actions
that must precede outreach: 1 (stable, consistent claims), 4
(priority/public record), and 5 (citable, immutable version) — plus
owner authorization per draft.
