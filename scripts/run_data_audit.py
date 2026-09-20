#!/usr/bin/env python3
"""Run the full Phase-1 data audit.

Pipeline order (evidence rules baked in):
  0. Provenance gate: raw files must match provenance/dataset_manifest.json
     hashes BEFORE and AFTER the audit (raw files are never modified).
  1. Per-file inventory (rows, columns, dtypes, missing, duplicates).
  2. Interval analysis on actual parsed timestamps (never assumed 15 min).
  3. Duplicate-timestamp analysis (identical vs conflicting) BEFORE any
     canonicalization; duplicate-policy sensitivity for onsets.
  4. Value distributions, onsets, value-gap and threshold separability.
  5. OTI rate-of-change using actual delta-t; top transitions with raw
     line numbers.
  6. Event construction + merge-tolerance sensitivity.
  7. Cross-file timestamp alignment (declared tolerance).
  8. Electrical context around OTI excursions + power formula cross-checks.

Outputs machine-readable CSV/JSON under reports/generated/.
"""

from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from transformer_audit import (  # noqa: E402
    PARSED_TS_COLUMN, RAW_LINE_COLUMN, RAW_TS_COLUMN,
    all_files_intersection, autocorrelation_by_lag, canonicalize,
    cross_file_alignment, duplicate_timestamp_report, event_sensitivity,
    excursion_electrical_context, inventory_file, interval_minutes,
    interval_summary, load_manifest, onset_counts_policy_sensitivity,
    power_approximation_errors, primitive_events, rate_summary, read_table,
    sensor_columns, threshold_separability, top_rate_transitions,
    utc_now_iso, value_distribution, value_gap_analysis, verify_raw_files,
)

RAW_DIR = REPO_ROOT / "data" / "raw"
MANIFEST = REPO_ROOT / "provenance" / "dataset_manifest.json"
OUT = REPO_ROOT / "reports" / "generated"
FILES = ["CurrentVoltage.csv", "Overview.csv", "Power.csv", "PowerFactor.csv", "TotalPower.csv"]
FLAGS = ["OTI_A", "OTI_T", "MOG_A", "WTI"]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(MANIFEST)

    # ---- 0. provenance gates -------------------------------------------------
    pre = verify_raw_files(manifest, RAW_DIR)
    if not pre["all_match"]:
        print("PROVENANCE GATE FAILED (pre-run): raw files differ from manifest.", file=sys.stderr)
        return 2
    print(f"[0] Pre-run provenance gate OK ({len(manifest['extracted_files'])} files match manifest hashes)")

    tables = {f: read_table(RAW_DIR / f) for f in FILES}

    # ---- 1. inventory --------------------------------------------------------
    inv_rows = [inventory_file(RAW_DIR / f) for f in FILES]
    inv = pd.DataFrame(inv_rows)
    # dtypes detail
    dtype_rows = []
    for f, df in tables.items():
        for c in sensor_columns(df):
            dtype_rows.append({"filename": f, "column": c, "dtype": str(df[c].dtype),
                               "units_stated_in_dataset": "no"})
    inv.to_csv(OUT / "dataset_inventory.csv", index=False)
    pd.DataFrame(dtype_rows).to_csv(OUT / "dataset_columns_dtypes.csv", index=False)

    # ---- 2. intervals ---------------------------------------------------------
    iv_rows = []
    for f, df in tables.items():
        s = interval_summary(df[PARSED_TS_COLUMN])
        s["filename"] = f
        iv_rows.append(s)
    iv = pd.DataFrame(iv_rows)
    front = ["filename", "n_intervals", "n_nonpositive_intervals", "n_zero_intervals",
             "min_minutes", "median_minutes", "p95_minutes", "p99_minutes", "max_minutes",
             "n_intervals_gt_30min", "n_intervals_gt_60min", "n_intervals_gt_1440min"]
    iv = iv[front + [c for c in iv.columns if c not in front]]
    iv.to_csv(OUT / "timestamp_interval_summary.csv", index=False)

    # intervals around flag transitions (Overview)
    ov = tables["Overview.csv"]
    ovc = canonicalize(ov, policy="first", sort=True).reset_index(drop=True)
    dt_ov = interval_minutes(ovc[PARSED_TS_COLUMN])
    trans_rows = []
    for flag in FLAGS:
        prev = ovc[flag].shift(1)
        for i in ovc.index[(ovc[flag] != prev) & prev.notna()]:
            trans_rows.append({
                "flag": flag,
                "timestamp": str(ovc.loc[i, PARSED_TS_COLUMN]),
                "transition": f"{int(prev.loc[i])}->{int(ovc.loc[i, flag])}",
                "interval_before_minutes": float(dt_ov.loc[i]) if dt_ov.loc[i] == dt_ov.loc[i] else None,
                "interval_after_minutes": (
                    float(dt_ov.loc[i + 1]) if i + 1 in dt_ov.index and dt_ov.loc[i + 1] == dt_ov.loc[i + 1] else None
                ),
            })
    pd.DataFrame(trans_rows).to_csv(OUT / "flag_transition_intervals.csv", index=False)

    # ---- 3. duplicates --------------------------------------------------------
    dup_frames = {}
    dup_summary_rows = []
    for f, df in tables.items():
        rep = duplicate_timestamp_report(df)
        dup_frames[f] = rep
        if len(rep):
            dup_summary_rows.append({
                "filename": f,
                "duplicate_timestamp_groups": int(len(rep)),
                "identical_groups": int(rep["identical_group"].sum()),
                "conflicting_groups": int((~rep["identical_group"]).sum()),
                "max_records_per_timestamp": int(rep["n_records"].max()),
                "conflicting_columns_seen": ";".join(
                    sorted({c for s in rep["conflicting_columns"].dropna() for c in s.split(",") if c})
                ),
            })
    all_rep = pd.concat([dup_frames[f].assign(filename=f) for f in FILES if len(dup_frames[f])],
                        ignore_index=True) if any(len(v) for v in dup_frames.values()) else pd.DataFrame()
    if len(all_rep):
        all_rep = all_rep[["filename"] + [c for c in all_rep.columns if c != "filename"]]
    all_rep.to_csv(OUT / "duplicate_timestamp_report.csv", index=False)
    pd.DataFrame(dup_summary_rows).to_csv(OUT / "duplicate_timestamp_summary.csv", index=False)

    # ---- 4. distributions, onsets, separability --------------------------------
    ov_dist = value_distribution(ov, ["OTI", "WTI", "ATI", "OLI", "OTI_A", "OTI_T", "MOG_A"])
    ov_dist.to_csv(OUT / "overview_value_distributions.csv", index=False)

    onsets = onset_counts_policy_sensitivity(ov, FLAGS, policies=("first", "last", "mean"))
    onsets.to_csv(OUT / "alarm_summary.csv", index=False)

    sep = pd.concat([
        threshold_separability(ov, "OTI", ["OTI_A", "OTI_T"]),
        threshold_separability(ov, "OLI", ["MOG_A"]),
    ], ignore_index=True)
    sep.to_csv(OUT / "oti_threshold_analysis.csv", index=False)

    gaps = value_gap_analysis(ov["OTI"], min_gap=5.0)
    gaps["column"] = "OTI"
    gaps.to_csv(OUT / "oti_value_gaps.csv", index=False)

    ac = autocorrelation_by_lag(ov, "OTI", lags=(1, 2, 4, 8, 96))
    ac.to_csv(OUT / "oti_autocorrelation.csv", index=False)

    # ---- 5. rates ---------------------------------------------------------------
    ovc["ishigh"] = ovc["OTI"] >= 100  # marks excursion-band endpoints
    high_pred = pd.Series((ovc["OTI"] >= 100).to_numpy())
    rs = rate_summary(ov, "OTI", high_predicate=high_pred)
    top = top_rate_transitions(ov, "OTI", n=40, threshold=1.0)
    top.to_csv(OUT / "oti_rate_summary.csv", index=False)
    with open(OUT / "oti_rate_stats.json", "w") as fh:
        json.dump(rs, fh, indent=2)

    # raw lines around high-OTI transitions (raw text, byte-faithful)
    raw_lines = {}
    for f in FILES:
        raw_lines[f] = (RAW_DIR / f).read_text(encoding="utf-8").splitlines()
    ctx_rows = []
    for _, r in top[top["rate_per_min"].abs() > 5].iterrows():
        for k in ("raw_line", "prev_raw_line"):
            ln = int(r[k])
            if 1 <= ln <= len(raw_lines["Overview.csv"]):
                ctx_rows.append({
                    "excursion_transition_timestamp": r["timestamp"],
                    "file": "Overview.csv",
                    "raw_line_number": ln,
                    "raw_line_text": raw_lines["Overview.csv"][ln - 1],
                })
    pd.DataFrame(ctx_rows).to_csv(OUT / "oti_transition_raw_lines.csv", index=False)

    # ---- 6. events ---------------------------------------------------------------
    prim = {}
    for flag in FLAGS:
        p15 = primitive_events(ov, flag, max_continuity_gap_minutes=15.0)
        prim[(flag, 15.0)] = p15
    prim_all = pd.concat([prim[(f, 15.0)].assign(continuity_gap_minutes=15.0) for f in FLAGS],
                         ignore_index=True)
    prim_all.to_csv(OUT / "primitive_events.csv", index=False)
    sens = event_sensitivity(ov, FLAGS, continuity_gaps_minutes=(15.0, 30.0),
                             merge_tolerances_minutes=(0.0, 15.0, 30.0, 60.0, 360.0))
    sens.to_csv(OUT / "event_merge_sensitivity.csv", index=False)

    # ---- 7. cross-file alignment ---------------------------------------------------
    align = cross_file_alignment(tables, tolerance_minutes=15.0)
    align.to_csv(OUT / "cross_file_alignment.csv", index=False)
    n_all = all_files_intersection(tables)

    # ---- 8. electrical context -------------------------------------------------------
    high_prim = prim[("OTI_T", 15.0)]
    onsets_high = list(high_prim["start"])  # OTI_T primitive onsets
    elec = excursion_electrical_context(onsets_high, tables["CurrentVoltage.csv"],
                                        tables["TotalPower.csv"], window_minutes=30)
    elec.to_csv(OUT / "excursion_electrical_context.csv", index=False)
    perr = power_approximation_errors(tables["CurrentVoltage.csv"], tables["TotalPower.csv"])
    with open(OUT / "power_formula_crosscheck.json", "w") as fh:
        json.dump(perr, fh, indent=2)

    # ---- 9. summary json ----------------------------------------------------------
    ov_canon = ovc
    high_rows = ov_canon[ov_canon["OTI"] >= 100]
    summary = {
        "audit_run_utc": utc_now_iso(),
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "provenance_gate": "PASS (pre-run; post-run verified separately)",
        "files": {f: {
            "rows": int(len(tables[f])),
            "unique_timestamps": int(tables[f][PARSED_TS_COLUMN].nunique()),
        } for f in FILES},
        "overview": {
            "oti_max_normal_band": float(ov_canon.loc[ov_canon["OTI"] < 100, "OTI"].max()),
            "oti_min_high_band": float(high_rows["OTI"].min()) if len(high_rows) else None,
            "n_rows_oti_ge_100": int(len(high_rows)),
            "oti_t_active_rows": int((ov_canon["OTI_T"] == 1).sum()),
            "oti_a_active_rows": int((ov_canon["OTI_A"] == 1).sum()),
            "oti_a_active_with_oti_below_100": int(((ov_canon["OTI_A"] == 1) & (ov_canon["OTI"] < 100)).sum()),
            "wti_unique_values": sorted(ov_canon["WTI"].unique().tolist()),
            "all_files_common_timestamps": n_all,
        },
        "oti_rate_stats": rs,
        "power_formula_crosscheck": perr,
    }
    with open(OUT / "phase_01_summary.json", "w") as fh:
        json.dump(summary, fh, indent=2)

    # post-run provenance gate
    post = verify_raw_files(manifest, RAW_DIR)
    if not post["all_match"]:
        print("PROVENANCE GATE FAILED (post-run): raw files modified during audit!", file=sys.stderr)
        return 2
    print("[post] Post-run provenance gate OK (raw files unmodified)")
    print(f"Outputs written to {OUT}")
    for p in sorted(OUT.iterdir()):
        print(f"  - {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
