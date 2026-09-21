# Transformer Monitoring Dataset — Evidence-First Audit

**Status: Phase 3R — leakage-controlled evaluation and claim
correction** (complete; see `reports/phase_03r_report.md` and
`reports/phase_03r_handoff.md`; Phases 1–3 also complete:
`reports/phase_01_report.md`, `reports/phase_02_report.md`,
`reports/phase_03_report.md`)

An evidence-first investigation of the public Kaggle dataset
**"Distributed Transformer Monitoring"**, focused on data quality,
provenance, asset identity, and reproducible characterization of the
recorded alarm/excursion behavior. **Phase 2 investigates whether the
published rows form a valid time series for one physical transformer** —
examining the dataset authors' paper and downstream users in full text,
analyzing repeated-timestamp records without averaging or discarding them,
and bounding the abrupt OTI transitions with assumption-labeled (conditional)
physics. This repository deliberately separates what is *known* from what is
*unknown*, and does not claim any hardware root cause.

**Phase-2 headline results:**

- **Lineage closed:** the audited archive was uploaded by the first author of
  Putchala et al. 2022 (Springer, ICCCE/ICACES), and the Energies 15(21):7981
  study used this same dataset (its Data Availability Statement names it).
  The paper's live-stream description (KernelSphere, Tripura, 52 locations,
  from Nov 2020) covers a *later* window than the export (2019-06-25 …
  2020-04-14); platform attribution of the export remains an inference.
- **Entity unresolved (required statement):** *The published dataset does not
  provide enough information to establish that adjacent rows belong to the
  same physical transformer.*
- **Repeats:** 406–931 repeated-timestamp groups per file (2.2–4.8 % of
  timestamps), synchronized across files, raw-line adjacent, near-identical
  in value, never containing the 47 high-OTI records — most consistent with
  ingestion/export re-transmission for the repeats; no support for
  multi-asset or multi-feeder structure.
- **Policy invariance:** under P1/P2/P3/P4 record policies the excursion
  findings do not change (10 rising transitions, OTI_T rule 100 %, empty
  interval (54, 236), rates +91.0/−40.8 OTI-units/min).
- **Conditional physics:** under an explicit extreme bound (100 % of
  observed load power into the oil), the observed 182–206-unit rises in
  2–18 min imply effective thermal masses of ~32–426 kg — far below
  distribution-class oil masses; plausible masses need sustained 0.1–4.9 MW
  vs 0.142 MW observed. Apparent channel recovery τ = 0.5–26 min. No root
  cause claimed; sampled data cannot exclude unobserved sub-interval events.

## Phase 3 / 3R — deterministic plausibility filter: design, evaluation, claim correction

A family of **deterministic, causal, streaming plausibility filters**
(F1 rate, F2 range, F3 combined, F4 jump; 1–11 operations/sample,
pure-stdlib reference implementation + C skeleton with host parity) was
designed, evaluated, and then **repaired in Phase 3R** after an
acceptance review found that the original threshold selection used the
full dataset. Full details: `reports/phase_03_report.md`,
`reports/phase_03r_report.md`, `reports/phase_03_acceptance_review.md`;
paper plan: `paper/outline.md`.

**Phase-3R headline results (frozen-threshold chronological replay;
`reports/generated/phase_03r_*.csv/json`):**

- **Leakage control:** thresholds are frozen from a calibration window
  strictly before the first excursion (2019-07-16 13:38) using
  predefined quantile/max rules, then replayed unchanged on all later
  records. This is a post-hoc leakage-controlled replay — internal
  validation only, not truly prospective external validation.
- **Replay results (all four views P1–P4, both gap behaviors):**
  range (upper = calibration max 47) and jump (calibration q99.9) rules
  flag 10/10 events at or before the crossing sample (exact 95% CI
  [0.69, 1.00]; n = 10), range at 0.26 false-alert episodes/day
  (day-block bootstrap CI [0.18, 0.34]), jump at 0.0; rate rules
  calibrated to pre-event noise flag 9/10 under P1/P3/P4 and 5/10 under
  P2_first (view-dependent). Persistence requirements (2, 3 valid
  samples) eliminate isolated single-sample alerts.
- **Exploratory / oracle sensitivity analysis (clearly separated):** the
  earlier 1,160-configuration full-data sweep remains available but is
  labeled exploratory — thresholds there were chosen with full-dataset
  knowledge (normal max 54, event min 236) and it is not held-out
  validation. Verified boundary facts: F2 zero-false-alarm separation
  holds for upper thresholds in [54, 236) (not (54, 236]); F4 for
  [42, 182); rate thresholds > 14.5 (not > 10) miss the two slowest
  rises (11.1 and 14.5 OTI-units/min both exceed 10).
- **T1/T2/T3 task separation:** T1 — OTI ⟺ OTI_T same-sample rule
  equivalence (not prediction). T2 — concordance with operationally
  defined band-crossing events; **no field-confirmed sensor-fault labels
  exist**, so no validated physical-fault detection is claimed. T3 —
  causal early-warning exploration restricted to tested variables, rules,
  and horizons: the tested OTI-only deterministic rules did not
  demonstrate robust multi-hour warning (1/6/24 h horizons; slope,
  variability, and sampling-gap features flagged 0/10 event windows).
  No multivariate early-warning conclusion is possible (other channels
  not evaluated in T3). The Energies 24-hour statement was **not
  reproduced by this project** (its features, task, split, and
  evaluation were not reproduced either; no judgment on its validity).
- **Firmware:** `firmware_skeleton/mif_filter.{h,c}` compiles at
  -Wall -Wextra -Werror -O2; the C reference matches the Python
  reference on boundary vectors and the full official replay sequence
  (19,376 samples × 4 filters × 2 gap behaviors, 0 mismatches);
  compiled `sizeof(mif_filter_t)` = 72 bytes (host double reference).
  Cycle counts remain illustrative estimates from documented
  instruction-timing tables — no Cortex-M0 cross-compiler or board was
  used, so nothing is a measured MCU latency. Hypothetical MLP/GBDT
  comparisons are kept out of headline results.

**Standing Phase-3R wording (tested):** entity identity remains
unresolved; the OTI engineering unit is unconfirmed; events are
operationally defined from the export; the hardware root cause is
unknown; the full-data sweep is exploratory; the frozen-threshold
replay is internal validation only. The filters flag readings
*inconsistent with gradual thermal behavior* at the measurement-channel
level — they are not "TinyML"/AI/intelligent, and all values are in
"OTI units". All Phase-2 caveats remain in force.

## Dataset (primary source)

| Field | Value |
|---|---|
| Title | Distributed Transformer Monitoring |
| URL | https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring |
| Slug | `sreshta140/ai-transformer-monitoring` |
| Owner | Sreshta Putchala (`sreshta140`) |
| Version | 1 — "Initial release" (created 2020-05-25T10:08:46.673Z, per Kaggle metadata) |
| Accessed | 2026-09-20 (UTC), official Kaggle API download endpoint (anonymous public access; no mirror) |
| License displayed | "Data files © Original Authors" — **redistribution conditions unverified** |
| Archive | 1,481,162 bytes, SHA-256 `b9257e990d480b3486b176bc19304a18b4aa82fd07dc559ec16aaa3ed3fe9c68` |
| Files | `CurrentVoltage.csv`, `Overview.csv`, `Power.csv`, `PowerFactor.csv`, `TotalPower.csv` (per-file hashes: `provenance/dataset_manifest.json`) |

Citation (dataset): Sreshta Putchala, "Distributed Transformer Monitoring",
Kaggle, version 1 (2020), https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring
(accessed Sep. 20, 2026).

> **License caution:** the raw dataset files are **not** redistributed in
> this repository (gitignored). The repository code license is a separate
> decision that the repository owner has not yet made; no license file is
> created on the owner's behalf, and no code license would permit
> redistribution of the Kaggle dataset.

## Research questions

1. **Provenance:** What exactly was downloaded, from where, and can it be
   verified byte-for-byte? (Done — manifest + provenance gates.)
2. **Asset identity:** Can the monitored transformer be identified beyond
   "an oil-immersed three-phase distribution transformer monitored on its
   LV side in a 50 Hz system"? (Phase 1 result: no — see
   `reports/asset_identity_evidence.md`.)
3. **Data quality:** How irregular is the timestamp cadence, how many
   duplicate/conflicting records exist, and how much do duplicate-handling
   policies and event definitions change the reported counts?
4. **Excursion behavior:** What exactly do the OTI alarm/trip channels and
   the OTI value discontinuity look like, at what rates (using *actual*
   Δt), and is anything visible in the electrical channels around them?
5. **Interpretation discipline:** Which conclusions are permitted by the
   evidence, and which popular claims (specific nameplates, cooling
   classes, sensor-failure stories, trendy ML labels) go beyond it?

## Evidence classification

Every claim is labeled (see `docs/research_protocol.md`):

- `[CONFIRMED-DATA]` — directly reproducible from the official raw dataset
  (artifacts under `reports/generated/`)
- `[CONFIRMED-SOURCE]` — explicitly stated by an identifiable primary source
- `[DERIVED]` — mathematically derived from confirmed measurements, with
  equations, units, assumptions, uncertainty documented
- `[INFERENCE]` — plausible but not uniquely established
- `[UNKNOWN]` — not available from current evidence (never guessed)

Registers: `docs/claim_register.md` (claims), `docs/assumption_register.md`
(assumptions; required-UNKNOWN parameters listed there).

## Reproducibility

Tested environment (recorded in `reports/generated/phase_01_summary.json`):
Python 3.13.14, pandas 2.2.3, numpy 2.3.5, Linux x86_64.

```bash
python -m pip install -e ".[test]"       # install package + pytest
python scripts/download_dataset.py       # official Kaggle download; verifies hash;
                                         # extracts raw/ (gitignored); writes manifest
python scripts/run_data_audit.py         # Phase-1 audit -> reports/generated/*.csv|json
python scripts/run_phase2_analysis.py    # Phase-2 analysis -> generated CSVs + figures
python scripts/run_filter_evaluation.py  # Phase-3 filter sweep (1,160 configs, provenance-gated)
python scripts/independent_raw_verification.py  # stdlib-only recomputation; 56 checks;
                                                 # exits non-zero on any disagreement
python -m pytest                         # 69 synthetic-fixture unit tests
```

`run_data_audit.py` and `run_phase2_analysis.py` verify raw-file SHA-256
hashes against the manifest **before and after** the run and abort on any
mismatch (raw files are never modified). All rates use actual timestamp
differences, never an assumed 15-minute cadence. Tested environment:
Python 3.13.14, pandas 2.2.3, numpy 2.3.5, matplotlib 3.10.9, Linux x86_64
(also recorded in `reports/generated/phase_0{1,2}_summary.json`).

## Repository structure

```
README.md                     this file
pyproject.toml                package config (transformer-audit)
data/                         gitignored raw+download data; policy in data/README.md
docs/
  research_protocol.md        evidence rules, prohibitions, event definitions
  claim_register.md           every claim + evidence class
  assumption_register.md      every assumption + required-UNKNOWN parameters
  archive/                    archive slot for the prior README (none existed; see file)
provenance/
  dataset_manifest.json       dataset metadata, archive+file hashes
  source_register.csv         all sources (S1–S16), primary/secondary
src/transformer_audit/        io, timestamps, provenance, audit, events,
                              electrical, records (Phase 2), physics (Phase 2)
scripts/
  download_dataset.py         official download + hash verify + manifest
  run_data_audit.py           Phase-1 audit
  run_phase2_analysis.py      Phase-2 analysis (artifacts + figures)
  run_filter_evaluation.py    Phase-3 filter sweep + baselines + cost table
  independent_raw_verification.py  stdlib-only cross-check (56 checks)
tests/                        69 unit tests (synthetic fixtures only)
docs/outreach_requests.md     provider/uploader question drafts — NOT SENT
reports/
  asset_identity_evidence.md  asset-identity investigation (Phase 1)
  phase_01_report.md          detailed Phase-1 report
  phase_01_handoff.md         compact Phase-1 handoff
  phase_01_code_review.md     Phase-1 code review (mean-policy fix)
  source_lineage_report.md    Phase-2 full-text lineage triangle
  asset_scope_and_entity_analysis.md  H1–H5 assessment; required statement
  variable_semantics_report.md        per-channel semantics; unit discipline
  asset_parameter_bounds.md           parameters + official manufacturer envelope
  conditional_physics_analysis.md     assumption-labeled energy/tau bounds
  phase_02_report.md         detailed Phase-2 report (13 sections)
  phase_03_report.md         Phase-3 filter report (10 sections)
  phase_03_handoff.md        compact Phase-3 handoff
  phase_02_handoff.md        compact Phase-2 handoff
  figures/                   physics bounds figures (PNG)
  generated/                 machine-readable audit outputs (CSV/JSON)
```

## Confirmed findings (Phase 1) — all reproducible

Full lists with artifacts: `docs/claim_register.md`, `reports/phase_01_report.md`.
Highlights (numbers: `reports/generated/`):

- **Provenance:** official archive obtained from Kaggle and hash-verified;
  a third-party mirror was checked and its shared files are byte-identical
  (it adds no provenance information).
- **Files:** 19,352 / 20,316 / 19,309 / 19,308 / 19,248 rows
  (CurrentVoltage / Overview / Power / PowerFactor / TotalPower);
  coverage 2019-06-25 → 2020-04-14.
- **Cadence is irregular** despite the "every 15 minutes" description:
  median interval 15 min, but intervals of 1–9 min occur, and the largest
  gap is 48,399 min (≈33.6 days); 17–19 gaps exceed 1 day per file.
- **Duplicate timestamps in every file** (e.g., Overview: 931 duplicate
  groups — 568 identical, 363 conflicting in ATI/OLI/OTI/WTI). Analyzed
  before canonicalization; onset counts for OTI_A/OTI_T/MOG_A are stable
  across duplicate policies, WTI varies (277–288 onsets).
- **OTI discontinuity:** OTI spans 0–250 with *no observed value between
  54 and 236*; 47 rows ≥ 236 (10 excursion windows, 2019-07-16 → 2019-09-03,
  active spans 10–136 min; 8 windows at a 360-min merge tolerance).
  Rising transitions reach +91 and falling −40.8 units/min over 2–8 min
  (actual Δt), vs a normal-mode p99 |rate| of 0.33 units/min.
- **Flags:** `OTI_T=1` ⟺ OTI ∈ [236, 250] in this dataset (a ≥236 threshold
  reproduces it 100% — association, not proven causality); `OTI_A=1` also
  occurs at OTI 29–30 during 2019-07-03/04, contradicting a simple
  OTI-threshold alarm model; `WTI` is binary {0,1} (not a temperature
  series; active only in 2020-01→04; 0 during all high-OTI rows);
  `MOG_A=1` ⇒ OLI ≤ 41 but not conversely (Jul–Aug 2019 only); OLI units
  are unstated.
- **Electrical context:** around every excursion onset the nearest
  electrical samples (within 1–12 min) show normal band voltages
  (VL1 219.8–234.2 V) and observed loads of 33.4–103.0 kW — *no coincident
  disturbance is visible in the available electrical channels at the
  dataset's temporal resolution* (this does not exclude events beyond that
  resolution/those variables). Observed apparent power over the whole
  record peaks at 142.9 kVA (operating load, not a nameplate rating);
  reported KVA cross-checks with Σ(VLx·ILx) to 1.36% median error.

### Permitted interpretation (current strength)

> The observations may be inconsistent with a normal top-oil thermal
> transient and may be more consistent with a measurement-chain or
> telemetry anomaly. The exact hardware root cause remains unknown.

## Unknowns and limitations (explicit)

**Unknown:** nameplate rating (the circulating "1500 kVA, 11/0.4 kV" figure
comes from a secondary paper describing *its own* system and is an
unverified lead for this asset), oil mass/volume, cooling class, oil type,
thermal time constant, sensor types, transmitter range, protection logic,
manufacturer/model, site/country (50 Hz system only), time zone, OTI units
(assumed °C for rate statements — flagged), OLI units, WTI's physical
semantics.

**Limitations:** sampling irregular and gappy; duplicate/conflicting
records present (quantified, with policy sensitivity); event counts are
definition-dependent (flag + continuity gap + merge tolerance always
stated); cross-file joins rely on timestamp equality (median nearest-delta
0 min, per-event deltas always reported); no thermal model was fitted in
Phase 1 by design.

**Not claimed anywhere in this repository:** any specific hardware root
cause (ADC railing, sensor open-circuit, etc.), any transformer
specification beyond the confirmed data structure, any "TinyML" solution
(no ML model is trained here — deterministic checks would be
physics-informed edge rules at most), and any rebuttal of third-party
published ML results (none was independently reproduced here).

## History note

This repository's working tree arrived **empty** (no README, no Git
history) on 2026-09-20; the "unverified AI-generated README" that Phase 1
was asked to archive did not exist, so nothing was inherited and nothing is
fabricated. See `docs/archive/README_initial_unverified.md` and
`reports/phase_01_report.md` §1.
