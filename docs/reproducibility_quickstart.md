# Reproducibility Quickstart — Transformer Telemetry Integrity Audit (v0.1.0)

This guide reproduces every number in the repository from the official
Kaggle archive. Tested environment (recorded in
`reports/generated/phase_01_summary.json`): Python 3.13.14,
pandas 2.2.3, numpy 2.3.5, matplotlib 3.10.9, Linux x86_64, gcc 14.2.

## 0. Requirements

- Python ≥ 3.11 (`pyproject.toml`)
- A C compiler (`cc` or `gcc`, C99) for the Python/C parity check
- ~10 MB free space (dataset archive 1.48 MB + extracts + outputs)
- Internet access to kaggle.com for the one-time dataset download

## 1. Create a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Install the package

```bash
python -m pip install -e ".[test]"   # package (transformer-audit) + pytest
```

## 3. Download the Kaggle dataset

```bash
python scripts/download_dataset.py
```

- Downloads the **official** archive from the Kaggle API download
  endpoint (anonymous public access — no Kaggle account or credentials
  were required at access time, 2026-09-20), verifies the archive
  SHA-256 (`b9257e990d480b3486b176bc19304a18b4aa82fd07dc559ec16aaa3ed3fe9c68`),
  extracts to `data/raw/` (gitignored), and writes/verifies
  `provenance/dataset_manifest.json`.
- **Kaggle access requirements / expected failure mode:** if Kaggle
  changes the archive (new version), the script prints a hash-mismatch
  warning and every downstream provenance-gated script **aborts** — all
  numbers must then be re-derived deliberately. If the endpoint becomes
  unavailable or starts requiring credentials, the download fails with
  an HTTP error and no raw data is written; all provenance-gated steps
  (audit, analyses, replay, full parity) then abort by design. The C
  boundary parity check (step 8, `--boundary-only`) and the synthetic
  fixture tests still run without raw data.

## 4. Verify provenance / hashes

Every analysis script re-verifies raw-file SHA-256 hashes against
`provenance/dataset_manifest.json` **before and after** its run and
aborts on any mismatch (raw files are never modified). For a stdlib-only
independent recomputation:

```bash
python scripts/independent_raw_verification.py   # 56 checks; exits non-zero on disagreement
```

## 5. Run the Phase-1 audit

```bash
python scripts/run_data_audit.py    # -> reports/generated/*.csv|json
```

## 6. Run the Phase-2 analysis

```bash
python scripts/run_phase2_analysis.py   # -> generated CSVs + physics figures
```

## 7. Run the Phase-3/3R evaluations

```bash
python scripts/run_filter_evaluation.py   # Phase-3 sweep (1,160 configs) — EXPLORATORY / oracle
python scripts/run_leakage_replay.py     # Phase-3R frozen-threshold replay — PRIMARY result
```

The sweep's `phase_03_filter_summary.json` carries
`analysis_type = exploratory_oracle_sensitivity`; the replay's
`phase_03r_*` artifacts carry the "post-hoc leakage-controlled replay —
internal validation only" label.

## 8. Run the C/Python parity check

```bash
python scripts/check_c_python_parity.py            # full: compiles mif_filter.c and
                                                    # replays the official 19,376-sample
                                                    # sequence x 4 filters x 2 gap behaviors
python scripts/check_c_python_parity.py --boundary-only   # without raw data
```

Expected: compiles with `cc -std=c99 -Wall -Wextra -Werror -O2`,
boundary self-tests pass, **0 mismatches**,
`sizeof(mif_filter_t) = 72` bytes (host double reference).

## 9. Run all tests

```bash
python -m pytest
```

**Expected result: 137 passed** (synthetic-fixture unit tests +
replay/parity/overclaim guards). The suite includes the
forbidden-overclaim scans of the public documentation
(`tests/test_phase3r_leakage.py`).

## 10. Expected key output artifacts

| artifact | content |
|---|---|
| `reports/generated/phase_01_summary.json` | environment + Phase-1 headline numbers |
| `reports/generated/dataset_inventory.csv` | per-file rows/hashes |
| `reports/generated/timestamp_multiplicity.csv` | repeated-timestamp structure |
| `reports/generated/duplicate_policy_sensitivity.csv` | P1–P4 policy invariance |
| `reports/generated/phase_02_summary.json` | Phase-2 headline numbers |
| `reports/generated/phase_03_filter_summary.json` | exploratory/oracle sweep summary |
| `reports/generated/phase_03r_calibration.json` | frozen thresholds per view |
| `reports/generated/phase_03r_replay_metrics.csv` | replay metrics with exact/bootstrap CIs |
| `reports/generated/phase_03r_per_event.csv` | per-event alerts, persistence, lead times |
| `reports/generated/phase_03r_t3_horizons.csv` | T3 horizon features |
| `reports/generated/computational_cost_comparison.csv` | op counts + illustrative cycles |
| `reports/figures/*.png` | 6 figures (filter figures carry in-image EXPLORATORY / ORACLE SWEEP labels) |

All rates use actual timestamp differences, never an assumed 15-minute
cadence. The consolidated narrative with per-number artifact citations
is `paper/technical_report_v0_1.md`.
