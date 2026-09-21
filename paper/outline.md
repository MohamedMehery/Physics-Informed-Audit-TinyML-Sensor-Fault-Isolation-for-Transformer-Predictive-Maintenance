# Paper Outline (Phase 3R revision)

Working title (see `title_candidates.md`):

> **"Auditing a Public Distributed-Transformer-Monitoring Dataset: Record
> Artifacts, Sharp Oil-Temperature-Indicator Excursions, and a
> Deterministic Causal Plausibility Filter"**

Paper character: an AUDIT paper with a leakage-controlled internal
validation of a deterministic filter family. It is NOT a
fault-detection-methods paper and makes no claim of validated physical
fault detection.

## 1. Story in one paragraph

A widely reused public dataset (Kaggle "Distributed Transformer
Monitoring", reused by a peer-reviewed Energies 2022 study) contains
sharp OTI excursions that no published analysis has audited. We show the
archive carries record-level artifacts (repeated timestamps), that the
OTI channel steps from ≤ 54 to ≥ 236 "OTI units" (unit unconfirmed) with
an empty interval between, that the steps are inconsistent with gradual
thermal behavior of the observed load under labeled bounding
assumptions, and that a 1–11-operation-per-sample deterministic causal
plausibility filter — with thresholds frozen from a calibration window
strictly before the first excursion — flags every excursion concurrently
(range/jump rules) at zero to few false alerts per week in a post-hoc
leakage-controlled replay. The tested OTI-only deterministic rules did
not demonstrate robust multi-hour warning. The Energies 24-hour-advance
statement is not reproduced by this project (its features, task, split,
and evaluation were not reproduced either). The value we demonstrate is
concurrent measurement-integrity flagging at negligible compute, not
prediction.

## 2. Section plan with evidence map

Status labels: **[READY]** reproducible artifact exists;
**[PARTIAL]** artifact exists, coverage/verification incomplete;
**[CONDITIONAL]** valid only under labeled assumptions;
**[NEEDS WORK]** required before submission.

| # | Section | Core content | Artifacts | Status |
|---|---------|--------------|-----------|--------|
| 1 | Introduction: dataset reuse without audit | Kaggle export reused by Energies 2022; 30+ notebooks; none audit the OTI excursions | `source_lineage_report.md` | **[READY]** |
| 2 | Dataset and provenance | 19,352 rows; SHA-256 manifest; single version; uploader = first author of Putchala et al. | `dataset_manifest.json` | **[READY]** |
| 3 | Record artifacts | Repeated-timestamp groups; policies P1–P4 | `timestamp_multiplicity.csv` | **[READY]** |
| 4 | Excursion phenomenology | 10 rising band-crossings; 47 high rows; empty interval (54, 236) at sample resolution | `excursion_catalog.csv` | **[READY]** |
| 5 | Entity and scope limits | Entity identity unresolved; adjacency ≠ same physical transformer | `asset_scope_and_entity_analysis.md` | **[READY]** |
| 6 | Conditional physics | Labeled bounding assumptions only; masses 32–426 kg; τ 0.5–26 min | `physics_sensitivity.csv` | **[CONDITIONAL]** |
| 7 | Filter design | F1/F2/F3/F4; strict inequalities; edge-case contract; C skeleton with host parity | `plausibility_filter.py`, `firmware_skeleton/` | **[READY]** |
| 8 | **Leakage-controlled replay (primary quantitative result)** | Calibration strictly before the first crossing; predefined quantile/max rules; frozen thresholds; post-hoc replay on all later records; views P1–P4; persistence 1/2/3; event+row metrics with exact binomial CIs and day-block bootstrap | `phase_03r_*.csv/json` | **[READY]** |
| 9 | Exploratory / oracle sensitivity analysis (clearly separated) | 1,160-config full-data sweep; separation intervals [54, 236) and [42, 182); NOT held-out validation | `filter_sweep_summary.csv` | **[READY]** (labeled exploratory) |
| 10 | T1/T2/T3 task separation | T1 same-sample rule equivalence (OTI ⟺ OTI_T); T2 detector-label concordance with operationally defined band-crossing events (no field-confirmed labels); T3 causal early-warning exploration at 1/6/24 h, OTI-only | `phase_03r_t3_horizons.csv` | **[READY]** |
| 11 | Computational cost | Exact op counts; compiled sizeof(struct) = 72 B (host double reference); cycle counts ILLUSTRATIVE only; MLP/GBDT as documented hypothetical references, not headline | `computational_cost_comparison.csv` | **[READY]** |
| 12 | Related work | Putchala et al. 2022; Energies 2022; notebooks | `bibliography_register.csv` | **[PARTIAL]** — broader sweep **[NEEDS WORK]** |
| 13 | Limitations | See `limitations.md` | — | **[READY]** |
| 14 | Conclusions | Concurrent integrity flagging at negligible cost; no demonstrated robust multi-hour warning from the tested OTI-only rules | — | **[READY]** |

## 3. Figures/tables plan

1. OTI series with 10 excursions + empty-band annotation. **[READY]**
2. Frozen-threshold replay: per-event alert classes (before/at/after
   crossing; persistence k=1,2,3). **[READY]** (from
   `phase_03r_per_event.csv`)
3. T3 horizon summary (1/6/24 h; 7 OTI-only features; event windows vs
   normal windows). **[READY]**
4. Exploratory sweep ROC (clearly labeled exploratory/oracle). **[READY]**
5. Cost table with compiled sizeof. **[READY]**
6. Provenance/manifest table. **[READY]**

## 4. Claims NOT made (paper must state explicitly)

1. No fault detection and no sensor-failure diagnosis; the filter flags
   readings inconsistent with gradual thermal behavior; root cause
   unknown.
2. No validated physical-fault detection: event labels are operationally
   defined from OTI band crossings; no field-confirmed sensor-fault
   labels exist.
3. No claim of robust multi-hour early warning from the tested OTI-only
   rules; horizons, variables, and rules are stated.
4. No multivariate early-warning conclusion (only OTI evaluated in T3).
5. No statement that the Energies 24-hour result is unsupported or
   wrong — only that this project did not reproduce it.
6. No asset identity, nameplate, cooling class, location, manufacturer.
7. No engineering unit for OTI ("OTI units" throughout).
8. No TinyML/AI/intelligence claims; deterministic rules only.
9. No measured MCU latency; cycle counts are illustrative estimates;
   no specific board or vendor claim.
10. No overfitting accusation against third-party notebooks.
11. Entity identity remains unresolved; OTI unit unconfirmed; events
    operationally defined from the export; hardware root cause unknown;
    full-data sweep exploratory; frozen-threshold replay is internal
    validation only.
