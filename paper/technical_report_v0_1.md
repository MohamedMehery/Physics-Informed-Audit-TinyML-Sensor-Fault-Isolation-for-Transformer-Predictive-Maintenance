# A Data-Centric Audit and Deterministic Plausibility Filter for Transformer Monitoring Telemetry

**Technical Report v0.1.0 — Transformer Telemetry Integrity Audit**

- **Author:** Mohamed Mehery — Independent Researcher
- **Date:** 2026-09-21
- **Status:** technical report / research software artifact. **Not peer
  reviewed.**
- **Code:** https://github.com/MohamedMehery/transformer-telemetry-integrity-audit
  (release v0.1.0)
- **DOI:** 10.5281/zenodo.22904790 (https://doi.org/10.5281/zenodo.22904790 — Zenodo
  archive of release v0.1.0)
- **Licensing:** code Apache-2.0 (`LICENSE`); documentation, reports,
  figures, and this report CC BY 4.0 (`CONTENT_LICENSE.md`)

---

## 1. Abstract

Public datasets that circulate through machine-learning pipelines are
rarely audited at the measurement-channel level. We audit a widely
reused Kaggle export ("Distributed Transformer Monitoring",
`sreshta140/ai-transformer-monitoring`, version 1; CurrentVoltage file
19,352 rows; 2019-06-25 → 2020-04-14; also used by a peer-reviewed 2022
study) and find that its oil-temperature-indicator channel (OTI,
engineering unit unconfirmed; all values are in "OTI units") exhibits
ten sharp excursions: single-step transitions from ≤ 54 to ≥ 236 OTI
units with no observed values in between, at rates up to 91 OTI-units
per minute. Under labeled bounding assumptions these steps are
inconsistent with gradual thermal behavior of the observed electrical
load; there is no field-confirmed hardware root cause, and the dataset
provides no field-confirmed fault labels. We design a family of
deterministic, causal, streaming plausibility filters (rate, range,
combined, jump; 1–11 operations per sample; 72-byte host reference
state; strict inequalities), calibrate thresholds only on records
preceding the first excursion using predefined quantile rules, and
replay them on all later records without retuning — a post-hoc
leakage-controlled replay (internal validation only). Range and jump
rules flag every excursion at or before the crossing sample (10/10;
exact 95% CI [0.6915, 1.0]; n = 10) with zero to 0.26 false-alert
episodes per day; rate rules calibrated to pre-event noise flag 5–9 of
10. The tested OTI-only deterministic rules did not demonstrate robust
multi-hour warning. A 1,160-configuration full-data sweep is reported
separately as exploratory / oracle sensitivity analysis, and a C
reference implementation matches the Python reference on the complete
replay sequence (19,376 samples × 4 filters × 2 gap behaviors, 0
mismatches). This report is not peer reviewed.

## 2. Scope and non-claims

This is a data-centric audit plus a reproducible deterministic
plausibility filter for a single public dataset. Explicit non-claims
(enforced by automated overclaim guards in `tests/test_phase3r_leakage.py`):

- **No field-confirmed hardware root cause.** No mechanism (ADC rail,
  sensor, transmitter, telemetry) is claimed
  (`docs/claim_register.md`, `paper/limitations.md`).
- **Entity identity remains unresolved:** the dataset does not provide
  enough information to establish that adjacent rows belong to the same
  physical transformer (`reports/asset_scope_and_entity_analysis.md`).
- **The OTI engineering unit is unconfirmed.** All values are reported
  in "OTI units"; no °C/% conversion is made anywhere
  (`reports/variable_semantics_report.md`, `docs/assumption_register.md` A23).
- **Events are operationally defined** from the export (rising
  band-crossings of OTI into ≥ 236); they are not field-confirmed
  physical faults, and no validated physical-fault detection is claimed
  (no ground-truth sensor-fault labels exist).
- **Not a "TinyML" or AI solution.** No ML model is trained anywhere in
  this work; the filters are deterministic edge rules at most.
- **Single dataset; no external validity** beyond this export; n = 10
  events bounds all event-level certainty.
- The Energies study's 24-hour-advance statement was **not reproduced
  by this project** (its features, task, split, and evaluation were not
  reproduced either; no judgment on its validity is made).
- **Not peer reviewed.**

## 3. Dataset provenance

| Field | Value (source) |
|---|---|
| Dataset | "Distributed Transformer Monitoring", Kaggle (`data/README.md`) |
| Slug / version | `sreshta140/ai-transformer-monitoring`, version 1 "Initial release", created 2020-05-25T10:08:46.673Z (Kaggle metadata; `provenance/dataset_manifest.json`) |
| Owner / uploader | Sreshta Putchala (`sreshta140`) — first author of Putchala et al. (`reports/source_lineage_report.md`) |
| Access | 2026-09-20 (UTC), official Kaggle API download endpoint, anonymous public access, no mirror (`data/README.md`) |
| Archive | `ai-transformer-monitoring_v1.zip`, 1,481,162 bytes, SHA-256 `b9257e990d480b3486b176bc19304a18b4aa82fd07dc559ec16aaa3ed3fe9c68` (`provenance/dataset_manifest.json`) |
| License displayed | "Data files © Original Authors" — redistribution conditions unverified; raw data NOT redistributed here (gitignored) (`data/README.md`, `CONTENT_LICENSE.md`) |

Extracted files (6,915,767 bytes total; per-file hashes in
`provenance/dataset_manifest.json`) and row counts
(`reports/phase_01_report.md`; `reports/generated/dataset_inventory.csv`):

| file | rows |
|---|---|
| CurrentVoltage.csv | 19,352 |
| Overview.csv | 20,316 |
| Power.csv | 19,309 |
| PowerFactor.csv | 19,308 |
| TotalPower.csv | 19,248 |

Coverage 2019-06-25 → 2020-04-14. The audit pipeline verifies raw-file
SHA-256 hashes against the manifest before and after every run and
aborts on mismatch (`scripts/download_dataset.py`,
`src/transformer_audit/provenance.py`). A third-party mirror was
checked and adds no provenance information (`reports/phase_01_report.md`).

## 4. Source lineage and asset-identity limitations

- The audited archive was uploaded by the first author of Putchala et
  al., "Transformer Data Analysis for Predictive Maintenance"
  (ICCCE/ICACES 2021, Springer; DOI 10.1007/978-981-16-7389-4_21)
  (`reports/source_lineage_report.md`,
  `reports/generated/source_claim_matrix.csv`, `paper/references.bib`).
- The Energies 15(21):7981 (2022) study used this same dataset: its
  Data Availability Statement names `sreshta140/ai-transformer-monitoring`
  (accessed 20 Jun 2022) (`reports/source_lineage_report.md`).
- The dataset authors' paper describes a live KernelSphere IoT platform
  stream (Tripura, 52 locations, from Nov 2020) that covers a *later*
  window than the export (2019-06-25 … 2020-04-14); platform
  attribution of the export remains an inference
  (`reports/source_lineage_report.md`).
- **Required statement — entity identity remains unresolved:** the
  published dataset does not provide enough information to establish
  that adjacent rows belong to the same physical transformer
  (`reports/asset_scope_and_entity_analysis.md`).
- The circulating "1500 kVA, 11/0.4 kV" nameplate figure comes from a
  secondary paper describing its *own* system and is an unverified lead
  for this asset (`reports/asset_identity_evidence.md`,
  `reports/asset_parameter_bounds.md`). Observed apparent power peaks at
  142.9 kVA — an operating load, not a nameplate rating
  (`reports/generated/power_formula_crosscheck.json`).

## 5. Data-quality audit

All numbers below are reproducible from `reports/generated/` (Phase 1;
`reports/phase_01_report.md`):

- **Irregular cadence** despite the "every 15 minutes" description:
  median interval 15 min, but intervals of 1–9 min occur; the largest
  gap is 48,399 min (≈ 33.6 days); 17–19 gaps exceed one day per file
  (`reports/generated/timestamp_interval_summary.csv`).
- **Duplicate timestamps in every file** — see §6.
- **Flag semantics:** `OTI_T = 1` ⟺ OTI ∈ [236, 250] (a ≥ 236 threshold
  reproduces it on every retained record — association, not proven
  causality); `OTI_A = 1` also occurs at OTI 29–30 during 2019-07-03/04,
  which conflicts with a simple OTI-threshold alarm model; `WTI` is
  binary {0, 1} (active only 2020-01→04; 0 during all high-OTI rows);
  `MOG_A = 1` ⇒ OLI ≤ 41 (Jul–Aug 2019 only), not conversely; OLI units
  are unstated (`reports/generated/flag_transition_intervals.csv`,
  `reports/phase_01_report.md`, `reports/generated/variable_semantics.csv`).
- **Electrical context around excursion onsets:** the nearest electrical
  samples (within 1–12 min) show normal band voltages (VL1 219.8–234.2
  V) and observed loads of 33.4–103.0 kW — no coincident disturbance is
  visible in the available channels at the dataset's temporal
  resolution (this does not exclude events beyond that resolution or in
  unobserved variables) (`reports/generated/excursion_electrical_context.csv`).
- Reported KVA cross-checks with Σ(VLx·ILx) to 1.36% median error
  (`reports/generated/power_formula_crosscheck.json`).

## 6. Repeated records and policy sensitivity

- Repeated-timestamp groups per file: 406–931 (2.2–4.8% of timestamps),
  synchronized across files, raw-line adjacent, near-identical in
  value, and never containing the 47 high-OTI records — most
  consistent with ingestion/export re-transmission; no support for
  multi-asset or multi-feeder structure (`reports/phase_02_report.md`,
  `reports/generated/repeated_record_conflict_summary.csv`).
- Overview multiplicity: 18,445 singletons, 923 double, 7 triple, 1
  quadruple (931 duplicate groups; 568 identical, 363 conflicting in
  ATI/OLI/OTI/WTI) — 20,316 rows, 19,376 unique timestamps
  (`reports/generated/timestamp_multiplicity.csv`,
  `reports/generated/duplicate_timestamp_summary.csv`).
- Four record policies were defined — P1 preserve all rows, P2 first
  record per timestamp, P3 last, P4 identical-value duplicates only —
  with record counts 20,316 / 19,376 / 19,376 / 19,742
  (`reports/generated/duplicate_policy_sensitivity.csv`).
- **Policy invariance:** under all four policies the excursion findings
  do not change — 10 rising transitions, OTI_T rule accuracy 1.0, empty
  OTI intervals (0, 9)/(0, 11) and (54, 236), rates +91.0 and −40.8
  OTI-units/min (`reports/generated/duplicate_policy_sensitivity.csv`).
- **OTI_T same-sample rule equivalence (T1):** OTI ≥ 236 ⟺ OTI_T = 1
  holds for every retained record under all views — rule equivalence,
  not prediction (`reports/generated/duplicate_policy_sensitivity.csv`,
  `reports/phase_03r_report.md` §5).

## 7. Operational high-band OTI events

Events are **operationally defined** from the export: rising
band-crossings of OTI into ≥ 236 (the OTI_T rule), with flag +
continuity-gap + merge tolerance always stated. The catalog
(`reports/generated/oti_rate_summary.csv`,
`reports/generated/oti_transitions_phase2.csv`,
`reports/generated/flag_transition_intervals.csv`):

- OTI spans 0–250 with **no observed value between 54 and 236** (the
  empty observed interval (54, 236); 47 rows ≥ 236 in 10 excursion
  windows, 2019-07-16 → 2019-09-03; active spans 10–136 min; 8 windows
  at a 360-min merge tolerance) (`reports/phase_01_report.md`).
- Rising transitions reach +91.0 and falling −40.8 OTI-units/min over
  2–8 min (actual Δt), vs a normal-mode p99 |rate| of 0.33 OTI-units/min
  (max 33 excluding excursion endpoints)
  (`reports/generated/oti_rate_summary.csv`).
- The ten crossing-sample rates are [24.75, 65.33, 22.44, 22.89, 14.5,
  66.67, 25.375, 33.33, 11.111, 91.0] OTI-units/min
  (`reports/phase_03r_report.md` §2).

## 8. Leakage-controlled deterministic plausibility filter

### 8.1 Design

Four **deterministic, causal, streaming plausibility filters** with
strict inequalities: F1 rate (|ΔOTI|/dt > thr), F2 range (OTI > U),
F3 combined (F1 OR F2), F4 jump (|ΔOTI| > thr); 1–11 operations per
sample (F2 1, F4 9, F1 10, F3 11); pure-stdlib Python reference plus a
C99 skeleton (`src/transformer_audit/plausibility_filter.py`,
`reports/generated/computational_cost_comparison.csv`). The filters flag
readings *inconsistent with gradual thermal behavior* at the
measurement-channel level.

### 8.2 Calibration (frozen thresholds)

Thresholds are calibrated **only** on records strictly before the first
operational high-band crossing (cutoff 2019-07-16 13:38) using
predefined rules (F1 = calibration q99.9 of |ΔOTI|/dt over valid pairs
0 < dt ≤ 60 min; F2 upper = calibration max OTI; F4 = calibration q99.9
of |ΔOTI|), then frozen (`reports/generated/phase_03r_calibration.json`,
`reports/phase_03r_report.md` §4):

| view | cal records | F1 rate | F2 upper | F4 jump |
|---|---|---|---|---|
| P1_preserve | 2,167 | 13.4545 | 47.0 | 31.101 |
| P2_first | 1,649 | 24.936 | 47.0 | 33.0 |
| P3_last | 1,649 | 13.4545 | 47.0 | 30.0 |
| P4_identical | 1,703 | 13.4545 | 47.0 | 31.101 |

Calibration normal maximum OTI = 47.0 vs full-data normal maximum 54 —
the oracle separation interval [54, 236) is not reachable from
calibration data alone, which is precisely the leakage the earlier
full-data sweep contained. Alarm-excluded sensitivity (last 60 min of
calibration removed; reported as sensitivity only, never used for the
frozen thresholds): F2 max drops to 45.0; F1 13.5085 (P1/P3/P4) /
24.968 (P2); F4 31.113 (P1/P4) / 30.0 (P3) / 33.0 (P2)
(`reports/generated/phase_03r_calibration.json`).

### 8.3 Replay results (primary result)

All later records replayed with frozen thresholds, no retuning — a
**post-hoc leakage-controlled replay; internal validation only**, not
truly prospective external validation, because the full dataset had
already been inspected. P2_first view shown; F1 shown for all views
because it is view-dependent (`reports/generated/phase_03r_replay_metrics.csv`):

| filter (frozen) | events | event recall, exact 95% CI | row P / R / F1 | FA episodes/day, bootstrap 95% CI | mean delay (min) |
|---|---|---|---|---|---|
| F2 range (U = 47) | 10/10 | 1.00 [0.6915, 1.0] | 0.187 / 1.000 / 0.315 | 0.2598 [0.181, 0.343] | −11.0 |
| F3 combined | 10/10 | 1.00 [0.6915, 1.0] | 0.187 / 1.000 / 0.314 | 0.2598 [0.181, 0.343] | −11.0 |
| F4 jump (33.0) | 10/10 | 1.00 [0.6915, 1.0] | 0.500 / 0.213 / 0.298 | 0.0 [0, 0] | 0.0 |
| F1 rate (P1/P3/P4, 13.4545) | 9/10 | 0.90 [0.555, 0.9975] | 0.692 / 0.192 / 0.300 | 0.0 [0, 0] | 0.0 |
| F1 rate (P2_first, 24.936) | 5/10 | 0.50 [0.1871, 0.8129] | 0.833 / 0.106 / 0.189 | 0.0 [0, 0] | 23.5* |

\* averaged over events with any in-zone flag. Negative delay = first
flag before the crossing sample. F4's low row recall is definitional —
it flags transitions (10 crossing rows), not plateau states
(`reports/phase_03r_report.md` §4). Row-level ground truth: OTI ≥ 100
rows (47). Denominators (P2 view): 17,624 monitored normal-zone rows,
103 excluded event-zone rows, 204 normal day-blocks; flagged samples
per test-day 0.022 (F1) to 0.921 (F2) (`reports/generated/phase_03r_replay_metrics.csv`).
**10/10 recall at n = 10 remains widely uncertain (exact CI
[0.6915, 1.0]).** Persistence requirements (2, 3 valid samples)
eliminate isolated single-sample alerts.

**View sensitivity (P1–P4):** F2/F3/F4 detection is invariant across
views; **F1 is view-dependent** (9/10 under P1/P3/P4 vs 5/10 under
P2_first) because P2_first's calibration rate distribution yields a
higher q99.9 (24.936 vs 13.4545). Reset vs continue gap behavior:
identical results everywhere (`reports/generated/phase_03r_replay_metrics.csv`).

**Sustained alerts before the crossing** (frozen F2, P2 view): 3 of 10
events have sustained (k = 3 valid samples) pre-crossing alerts (leads
−20, −48, −42 min; duty cycles 0.67, 1.00, 0.86); the other 7 are
flagged at the crossing sample. Frozen F4: all 10 at crossing. Frozen
F1 (P2): 5 at crossing; never sustained (k ≥ 2) before crossing
(`reports/phase_03r_report.md` §7,
`reports/generated/phase_03r_per_event.csv`).

### 8.4 Task separation (T1/T2/T3)

- **T1** — OTI ⟺ OTI_T same-sample rule equivalence (§6); not prediction.
- **T2** — concordance with operationally defined band-crossing events;
  no field-confirmed sensor-fault labels exist, so no validated
  physical-fault detection is claimed (`reports/phase_03r_report.md` §5).
- **T3** — causal early-warning exploration, OTI-only, tested rules and
  horizons only: at 1/6/24 h, slope, variability, and sampling-gap
  features flag **0/10** event windows; elevated-max features flag
  5–9/10 but also 3.3–32% of normal windows (calibration q99 ≈ 43–44) —
  low specificity. **The tested OTI-only deterministic rules did not
  demonstrate robust multi-hour warning**; no multivariate
  early-warning conclusion is possible (other channels not evaluated)
  (`reports/generated/phase_03r_t3_horizons.csv`,
  `reports/phase_03r_report.md` §6).

### 8.5 Exploratory / oracle sweep (separate, clearly labeled)

The earlier 1,160-configuration full-data sweep
(`reports/generated/phase_03_filter_summary.json`,
`analysis_type = exploratory_oracle_sensitivity`; figures
`reports/figures/filter_*.png` carry in-image EXPLORATORY / ORACLE SWEEP
labels) selected thresholds with full-dataset knowledge and is **not
held-out validation**. Verified boundary facts within that label
(`reports/phase_03r_report.md` §2): F2 zero-false-alarm separation
holds for U ∈ **[54, 236)** (not (54, 236]; at U = 236 the strict rule
misses the OTI = 236 crossing sample); F4 for thr ∈ **[42, 182)**
(max normal |ΔOTI| = 42; min event rise 182; no step equals 50); rate
thresholds > 14.5 miss the two slowest rises (11.111 and 14.5
OTI-units/min; rate > 10 flags 10/10).

## 9. C implementation and Python/C parity

- `firmware_skeleton/mif_filter.h` / `mif_filter.c`: C99, no dynamic
  allocation, mirrors the Python reference exactly (strict
  inequalities; first-sample/NaN/dt ≤ 0/gap contract; range rule
  active only for F2/F3 — a bug caught by the C self-test and fixed in
  Phase 3R) (`firmware_skeleton/`, `reports/phase_03r_report.md` §8).
- `scripts/check_c_python_parity.py` compiles with
  `cc -std=c99 -Wall -Wextra -Werror -O2` (host gcc 14.2 — **not** a
  Cortex-M0 cross-build), runs hand-computed boundary self-tests, then
  hand-made boundary vectors (7 filter configs × 2 gap behaviors) and
  the **full official replay sequence: 19,376 samples × 4 filters × 2
  gap behaviors — 0 mismatches** (`reports/phase_03r_report.md` §8;
  `tests/test_phase3r_leakage.py`). `--boundary-only` runs without raw
  data.
- Compiled `sizeof(mif_filter_t)` = **72 bytes** (host double-precision
  reference; a fixed-point port would be smaller)
  (`reports/generated/computational_cost_comparison.csv`).
- Operation counts are exact; Cortex-M0 cycle counts are **illustrative
  estimates** from documented instruction-timing tables (deterministic
  filters: 18–291 estimated cycles/sample across fixed-point and
  soft-float variants); no measured MCU latency is reported.
  Hypothetical MLP/GBDT reference models (exact MAC/parameter counts,
  no trained models, no compilation) are kept out of headline results
  (`reports/generated/computational_cost_comparison.csv`).

## 10. Conditional physical plausibility analysis

All physics below is **assumption-labeled (conditional)**; the OTI
engineering unit is unconfirmed (A23: τ is offset-invariant; an unknown
scale factor scales derived masses/powers linearly)
(`docs/assumption_register.md`, `reports/conditional_physics_analysis.md`):

- Under an explicit extreme bound (100% of observed load power into the
  oil), the observed 182–206-OTI-unit rises in 2–18 min imply effective
  thermal masses of ~32–426 kg — far below distribution-class oil
  masses; plausible masses would need sustained 0.1–4.9 MW vs 0.142 MW
  observed (`reports/conditional_physics_analysis.md`,
  `reports/generated/physics_sensitivity.csv`,
  `reports/generated/apparent_tau_per_transition.csv`).
- Apparent channel recovery time constants τ = 0.5–26 min
  (`reports/generated/apparent_tau_per_transition.csv`).
- **Permitted interpretation:** the observations may be inconsistent
  with a normal top-oil thermal transient and may be more consistent
  with a measurement-chain or telemetry anomaly; the exact hardware
  root cause remains unknown (`README.md`, `docs/claim_register.md`).
- Sampled data cannot exclude unobserved sub-interval events.

## 11. Limitations

Full list: `paper/limitations.md` (13 numbered limitations). Key items:
entity identity remains unresolved; OTI engineering unit unconfirmed;
events are operationally defined, not field-confirmed faults; hardware
root cause unknown; the full-data sweep is exploratory; the
frozen-threshold replay is internal validation only; n = 10 events (10/10
recall CI [0.6915, 1.0]); single export with gaps up to 33.6 days;
rate-filter recall is view-dependent (9/10 vs 5/10); T3 is OTI-only
without multiple-comparison correction; cycle counts are illustrative;
MLP/GBDT comparisons are hypothetical; the Energies 24-hour statement
was not reproduced by this project; outreach is stored, not sent.

## 12. Reproducibility checklist

Full quickstart: `docs/reproducibility_quickstart.md`. Summary
(tested environment recorded in `reports/generated/phase_01_summary.json`:
Python 3.13.14, pandas 2.2.3, numpy 2.3.5, matplotlib 3.10.9,
Linux x86_64, gcc 14.2):

```bash
python -m pip install -e ".[test]"        # package + pytest
python scripts/download_dataset.py        # official Kaggle download + hash verify
python scripts/run_data_audit.py          # Phase 1
python scripts/run_phase2_analysis.py     # Phase 2
python scripts/run_filter_evaluation.py   # Phase 3 (exploratory/oracle sweep)
python scripts/run_leakage_replay.py      # Phase 3R (primary replay result)
python scripts/check_c_python_parity.py   # C/Python parity (needs cc/gcc)
python scripts/independent_raw_verification.py  # stdlib-only cross-check (56 checks)
python -m pytest                          # expected: 137 passed
```

Expected key output artifacts: `reports/generated/phase_01_summary.json`,
`phase_02_summary.json`, `phase_03_filter_summary.json`,
`phase_03r_calibration.json`, `phase_03r_replay_metrics.csv`,
`phase_03r_per_event.csv`, `phase_03r_t3_horizons.csv`,
`computational_cost_comparison.csv`, and the labeled figures under
`reports/figures/`. Provenance gates verify raw hashes before and after
every script run and abort on any mismatch.

## 13. Citation and licensing

- **How to cite this repository:** see `CITATION.cff` (GitHub "Cite
  this repository" button) — Mohamed Mehery, Independent Researcher,
  *Transformer Telemetry Integrity Audit*, v0.1.0, 2026-09-21,
  https://github.com/MohamedMehery/transformer-telemetry-integrity-audit.
  DOI: 10.5281/zenodo.22904790 (https://doi.org/10.5281/zenodo.22904790 — Zenodo archive of release v0.1.0).
- **Licensing:** code Apache-2.0 (`LICENSE`); documentation, reports,
  figures, and this report CC BY 4.0 (`CONTENT_LICENSE.md`,
  `NOTICE`).
- **Dataset citation (separate, mandatory):** Sreshta Putchala,
  "Distributed Transformer Monitoring", Kaggle, version 1 (2020),
  https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring
  (accessed Sep. 20, 2026). Data files © Original Authors; the raw
  dataset is not owned by the repository author, is not redistributed
  in this repository, and nothing here endorses or is endorsed by the
  dataset authors or Kaggle.
- **References:** `paper/references.bib` / `paper/references.md`
  (derived from `reports/generated/bibliography_register.csv`; no
  unverified bibliographic fields are asserted).

---

*This technical report is a research artifact accompanying a
reproducible software audit; it is not peer reviewed. Every numerical
statement above cites the repository artifact that supports it.*
