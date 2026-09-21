# Figures and Tables Inventory (Phase 3R)

All artifacts exist in `reports/generated/` and `reports/figures/`;
status per paper/outline.md conventions.

## Figures

| id | content | source artifact | status |
|----|---------|-----------------|--------|
| F1 | OTI time series, 10 excursions, empty-band (54, 236) annotation | Phase-1 excursion catalog | [READY] |
| F2 | Frozen-threshold replay per-event alert classes (before/at/after crossing; persistence k = 1, 2, 3) | phase_03r_per_event.csv | [READY] |
| F3 | T3 horizon summary: 7 OTI-only features x 1/6/24 h; event windows vs normal windows | phase_03r_t3_horizons.csv | [READY] |
| F4 | Exploratory/oracle sweep ROC by filter type (labeled EXPLORATORY) | filter_roc_by_type.png | [READY] |
| F5 | Threshold sensitivity panels (labeled EXPLORATORY) | filter_threshold_sensitivity.png | [READY] |
| F6 | Lead-time distribution at oracle balanced point (labeled EXPLORATORY) | filter_lead_time_distribution.png | [READY] |
| F7 | Conditional-physics bounding curves (assumption-labeled) | Phase-2 figures | [READY] |

## Tables

| id | content | source artifact | status |
|----|---------|-----------------|--------|
| T1 | Provenance/manifest summary (files, rows, SHA-256) | dataset_manifest.json | [READY] |
| T2 | Repeated-record statistics per file | timestamp_multiplicity.csv | [READY] |
| T3 | Excursion catalog (10 events, spans, steps, rates) | excursion_catalog.csv | [READY] |
| T4 | Calibration rules and frozen thresholds per view (P1–P4) | phase_03r_calibration.json | [READY] |
| T5 | Replay metrics: event recall + exact CI, row precision/recall/F1, FA/day + bootstrap CI, delay, persistence | phase_03r_replay_metrics.csv | [READY] |
| T6 | T3 horizon feature table | phase_03r_t3_horizons.csv | [READY] |
| T7 | Computational cost: exact op counts; compiled sizeof(mif_filter_t) = 72 B; ILLUSTRATIVE cycle estimates | computational_cost_comparison.csv | [READY] |
| T8 | Baselines B1/B2/B3 (exploratory sweep context) | filter_sweep_summary.csv | [READY] |

## Notes

- F4–F6 and T8 derive from the full-data sweep and must carry the
  "exploratory / oracle sensitivity analysis" label wherever shown.
- MLP/GBDT rows in T7 are hypothetical reference models with documented
  assumptions (assumed depth 6, 12 B/node); they are not compiled or
  measured and are kept out of headline results.
- No figure claims measured MCU latency; cycle numbers are illustrative
  estimates from documented instruction-timing tables.
