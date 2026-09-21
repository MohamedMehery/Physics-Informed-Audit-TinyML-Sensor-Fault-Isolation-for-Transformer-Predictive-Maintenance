# Figures and Tables Inventory (Phase 3R) — v0.1.0 status

Tables derive from `reports/generated/` (all present). Figures marked
[READY] exist in `reports/figures/`. **F1–F3 are NOT GENERATED** —
their data sources exist, but no PNG has been rendered. (Status
corrected 2026-09-21; earlier versions of this file wrongly marked
F1–F3 as [READY] although no figure files existed.)

## Figures

| id | content | source artifact | status |
|----|---------|-----------------|--------|
| F1 | OTI time series, 10 excursions, empty-band (54, 236) annotation | oti_rate_summary.csv, oti_transitions_phase2.csv | [NOT GENERATED — TODO; deferred past v0.1.0] |
| F2 | Frozen-threshold replay per-event alert classes (before/at/after crossing; persistence k = 1, 2, 3) | phase_03r_per_event.csv | [NOT GENERATED — TODO; data ready] |
| F3 | T3 horizon summary: 7 OTI-only features x 1/6/24 h; event windows vs normal windows | phase_03r_t3_horizons.csv | [NOT GENERATED — TODO; data ready] |
| F4 | Exploratory/oracle sweep ROC by filter type | filter_roc_by_type.png | [READY — carries in-image EXPLORATORY / ORACLE SWEEP label] |
| F5 | Threshold sensitivity panels | filter_threshold_sensitivity.png | [READY — carries in-image EXPLORATORY / ORACLE SWEEP label] |
| F6 | Lead-time distribution at oracle balanced point | filter_lead_time_distribution.png | [READY — carries in-image EXPLORATORY / ORACLE SWEEP label] |
| F7 | Conditional-physics bounding curves (assumption-labeled) | physics_bounds_achievable_dT.png, physics_bounds_critical_mass.png, physics_bounds_power_vs_mass.png | [READY — assumption-labeled conditional analysis] |

## Tables

| id | content | source artifact | status |
|----|---------|-----------------|--------|
| T1 | Provenance/manifest summary (files, rows, SHA-256) | dataset_manifest.json | [READY] |
| T2 | Repeated-record statistics per file | timestamp_multiplicity.csv | [READY] |
| T3 | Excursion catalog (10 events, spans, steps, rates) | oti_transitions_phase2.csv + oti_rate_summary.csv + flag_transition_intervals.csv (source path corrected — no excursion_catalog.csv exists) | [READY] |
| T4 | Calibration rules and frozen thresholds per view (P1–P4) | phase_03r_calibration.json | [READY] |
| T5 | Replay metrics: event recall + exact CI, row precision/recall/F1, FA/day + bootstrap CI, delay, persistence | phase_03r_replay_metrics.csv | [READY] |
| T6 | T3 horizon feature table | phase_03r_t3_horizons.csv | [READY] |
| T7 | Computational cost: exact op counts; compiled sizeof(mif_filter_t) = 72 B; ILLUSTRATIVE cycle estimates | computational_cost_comparison.csv | [READY] |
| T8 | Baselines B1/B2/B3 (exploratory sweep context) | filter_sweep_summary.csv | [READY] |

## v0.1.0 figure status

Safe for v0.1.0: **F4–F7** (existing PNGs; F4–F6 carry in-image
"EXPLORATORY / ORACLE SWEEP" titles and must keep such labels wherever
shown; F7 is assumption-labeled conditional physics). **F1–F3 are not
included in v0.1.0** — the technical report
(`paper/technical_report_v0_1.md`) presents their content as tables
(§7 events, §8 replay/T3) instead, so no figure is missing from the
release.

## Notes

- F4–F6 and T8 derive from the full-data sweep and must carry the
  "exploratory / oracle sensitivity analysis" label wherever shown.
- MLP/GBDT rows in T7 are hypothetical reference models with documented
  assumptions (assumed GBDT depth 6, 12 B/node); they are not compiled
  or measured and are kept out of headline results.
- No figure claims measured MCU latency; cycle numbers are illustrative
  estimates from documented instruction-timing tables.
