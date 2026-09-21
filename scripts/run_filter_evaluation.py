#!/usr/bin/env python3
"""Phase-3 EXPLORATORY / ORACLE SENSITIVITY ANALYSIS (full-data sweep).

STATUS LABEL (Phase 3R): this 1,160-configuration sweep selects and
evaluates thresholds with knowledge of the FULL dataset (including the
full-data normal maximum 54 and the event minimum 236). It is an
exploratory/oracle sensitivity analysis and must NOT be presented as
held-out detector validation. The leakage-controlled chronological
replay lives in scripts/run_leakage_replay.py.

Original Phase-3 description: deterministic plausibility filters under
P1-P4.

Rules baked in (Phase-3 protocol):
- filters are the deterministic, causal, stdlib-only implementations in
  transformer_audit.plausibility_filter;
- evaluation is EVENT-BASED (10 rising band-crossings), not row-based;
- detection = flag at or before the first OTI >= 236 sample of the event,
  within a bounded 60-min pre-crossing window (documented assumption);
- false alarms are EPISODES during normal operation (not rows), rate per
  day of normal operation;
- lead times use actual timestamps;
- baselines B1 (trivial threshold), B2 (seeded random), B3 (static
  percentile, non-causal, baseline only) use the same metrics;
- raw files provenance-gated before and after the run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import pandas as pd

from transformer_audit import (
    PARSED_TS_COLUMN, RAW_LINE_COLUMN,
    apply_policy, b1_trivial_threshold_flags, b2_random_flags,
    b3_percentile_flags, build_zone_index, est_cycles_m0, evaluate_flags,
    find_rising_crossings, gbdt_100_trees, load_manifest, mlp_28_16_8_1,
    OP_COUNTS, pareto_frontier, read_table, total_ops, utc_now_iso,
    verify_raw_files, PlausibilityFilter,
)

RAW_DIR = REPO_ROOT / "data" / "raw"
MANIFEST = REPO_ROOT / "provenance" / "dataset_manifest.json"
OUT = REPO_ROOT / "reports" / "generated"
FIG = REPO_ROOT / "reports" / "figures"

POLICIES = ("P1_preserve", "P2_first", "P3_last", "P4_identical")
GAP_BEHAVIORS = ("reset", "continue")
RATE_SWEEP = [0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 15.0, 20.0]      # OTI-units/min
# sub-band thresholds 45-54 added after observing pre-crossing values in
# the elevated-normal band (33-54; >=53 is 0.03% of normal samples)
UPPER_SWEEP = [45.0, 48.0, 50.0, 52.0, 54.0,
               60.0, 70.0, 80.0, 90.0, 100.0, 150.0, 200.0, 236.0]  # OTI units
JUMP_SWEEP = [5.0, 10.0, 20.0, 30.0, 50.0, 100.0, 150.0]      # OTI units
B3_PCTS = [95.0, 99.0, 99.5, 99.9]
B2_P_SWEEP = [1e-5, 1e-4, 5e-4, 1e-3, 5e-3, 1e-2, 5e-2]
B2_SEEDS = [42, 43, 44]
PRE_WINDOW_MIN = 60.0
EPOCH = pd.Timestamp("1970-01-01")


def ts_to_min(ts):
    return (ts - EPOCH).total_seconds() / 60.0


def stream(filter_obj, samples):
    flags, anomalies = [], []
    for ts, oti in samples:
        d = filter_obj.process(oti, ts)
        flags.append(d.flagged)
        anomalies.append(d.data_anomaly)
    return flags, anomalies


def _notable(summary):
    sel = summary[(summary["policy"] == "P2_first") &
                  (summary["gap_policy"].isin(["reset", "not_applicable"])) &
                  (summary["threshold"].isin(
                      ["rate>2", "rate>5", "rate>10", "|dOTI|>50",
                       "OTI>50", "OTI>52", "OTI>54", "OTI>236",
                       "rate>2;OTI>50", "rate>5;OTI>50",
                       "OTI>=236", ">p95", ">p99", ">p99.5", ">p99.9"]))]
    out = []
    for _, r in sel.iterrows():
        out.append({"filter_type": r["filter_type"], "threshold": r["threshold"],
                    "detected": r["events_detected_of_10"],
                    "mean_lead_min": r["mean_lead_time_min"],
                    "fa_per_day": r["false_alarm_rate_per_day"]})
    return out


def lead_stats(leads):
    if not leads:
        return "", ""
    s = sorted(leads)
    mean = sum(s) / len(s)
    mid = len(s) // 2
    median = s[mid] if len(s) % 2 else 0.5 * (s[mid - 1] + s[mid])
    return round(mean, 3), round(median, 3)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(MANIFEST)
    if not verify_raw_files(manifest, RAW_DIR)["all_match"]:
        print("PROVENANCE GATE FAILED (pre-run).", file=sys.stderr)
        return 2
    print("[0] Pre-run provenance gate OK")

    ov_raw = read_table(RAW_DIR / "Overview.csv")
    summary_rows = []
    detail_rows = []
    policy_events = {}

    def record(policy, ftype, thr_label, gap_label, flags, anomalies,
               samples, events, zone_idx, ts_iso, seed=None):
        m = evaluate_flags(samples, flags, events,
                           pre_window_minutes=PRE_WINDOW_MIN,
                           data_anomalies=anomalies, zone_idx=zone_idx)
        mean_l, median_l = lead_stats(m["lead_times_min"])
        summary_rows.append({
            "policy": policy, "filter_type": ftype, "threshold": thr_label,
            "gap_policy": gap_label, "seed": seed,
            "events_detected_of_10": m["events_detected"],
            "detection_rate": m["events_detected"] / len(events),
            "events_detected_in_zone_of_10": m["events_detected_in_zone"],
            "mean_lead_time_min": mean_l, "median_lead_time_min": median_l,
            "false_alarm_episodes": m["false_alarm_episodes"],
            "false_alarm_rate_per_day": round(m["false_alarm_rate_per_day"], 6),
            "total_flagged_rows": m["total_flagged_rows"],
            "data_anomaly_rows": m["data_anomaly_rows"],
            "normal_days": round(m["normal_days"], 3),
        })
        for p in m["per_event"]:
            detail_rows.append({
                "policy": policy, "filter_type": ftype,
                "threshold": thr_label, "gap_policy": gap_label,
                "event_id": p["event_id"],
                "event_crossing_time": ts_iso[p["crossing_index"]],
                "detected": p["detected"],
                "detected_in_zone": p["detected_in_zone"],
                "first_flag_time": (ts_iso[min(range(len(samples)),
                                                key=lambda i: abs(samples[i][0] - p["first_flag_ts"]))]
                                    if p["first_flag_ts"] is not None else ""),
                "lead_time_min": (round(p["lead_min"], 3)
                                  if p["lead_min"] is not None else ""),
            })
        return m

    for policy in POLICIES:
        series = apply_policy(ov_raw, policy)
        series = series.sort_values([PARSED_TS_COLUMN, RAW_LINE_COLUMN],
                                    kind="stable").reset_index(drop=True)
        samples = [(ts_to_min(t), float(o))
                   for t, o in zip(series[PARSED_TS_COLUMN], series["OTI"])]
        ts_iso = [str(t) for t in series[PARSED_TS_COLUMN]]
        events = find_rising_crossings(samples)
        policy_events[policy] = len(events)
        print(f"[{policy}] records={len(samples)} events={len(events)}")
        zone_idx = build_zone_index(samples, events, PRE_WINDOW_MIN)

        for gapb in GAP_BEHAVIORS:
            for thr in RATE_SWEEP:  # F1
                f = PlausibilityFilter("rate", rate_threshold=thr, gap_behavior=gapb)
                fl, da = stream(f, samples)
                record(policy, "F1_rate", f"rate>{thr:g}", gapb, fl, da,
                       samples, events, zone_idx, ts_iso)
            for thr in UPPER_SWEEP:  # F2
                f = PlausibilityFilter("range", upper_threshold=thr, gap_behavior=gapb)
                fl, da = stream(f, samples)
                record(policy, "F2_range", f"OTI>{thr:g}", gapb, fl, da,
                       samples, events, zone_idx, ts_iso)
            for thr in JUMP_SWEEP:  # F4
                f = PlausibilityFilter("jump", jump_threshold=thr, gap_behavior=gapb)
                fl, da = stream(f, samples)
                record(policy, "F4_jump", f"|dOTI|>{thr:g}", gapb, fl, da,
                       samples, events, zone_idx, ts_iso)
            for r in RATE_SWEEP:  # F3 grid
                for u in UPPER_SWEEP:
                    f = PlausibilityFilter("combined", rate_threshold=r,
                                           upper_threshold=u, gap_behavior=gapb)
                    fl, da = stream(f, samples)
                    record(policy, "F3_combined", f"rate>{r:g};OTI>{u:g}",
                           gapb, fl, da, samples, events, zone_idx, ts_iso)

        # ---- baselines (stateless; gap policy not applicable) ----------
        fl = b1_trivial_threshold_flags(samples)
        record(policy, "B1_trivial", "OTI>=236", "not_applicable", fl,
               [False] * len(samples), samples, events, zone_idx, ts_iso)
        for x in B3_PCTS:
            fl = b3_percentile_flags(samples, x)
            record(policy, "B3_percentile", f">p{x:g}", "not_applicable", fl,
                   [False] * len(samples), samples, events, zone_idx, ts_iso)
        for p in B2_P_SWEEP:
            for seed in B2_SEEDS:
                fl = b2_random_flags(samples, p, seed)
                record(policy, "B2_random", f"p={p:g}", "not_applicable", fl,
                       [False] * len(samples), samples, events, zone_idx,
                       ts_iso, seed=seed)

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT / "filter_sweep_summary.csv", index=False)
    pd.DataFrame(detail_rows).to_csv(OUT / "filter_per_event_detail.csv", index=False)

    # ---- Pareto frontier over the real filters (F1-F4) ------------------
    real = summary[summary["filter_type"].str.startswith(("F1", "F2", "F3", "F4"))]
    front = pareto_frontier(real.to_dict("records"))
    b1 = summary[summary["filter_type"] == "B1_trivial"].head(1).to_dict("records")
    pareto_rows = []
    for r in front:
        r = dict(r)
        r["is_baseline"] = False
        pareto_rows.append(r)
    for r in b1:
        r = dict(r)
        r["is_baseline"] = True
        pareto_rows.append(r)
    pd.DataFrame(pareto_rows).to_csv(OUT / "pareto_frontier.csv", index=False)

    # ---- computational cost table ---------------------------------------
    mlp = mlp_28_16_8_1()
    gb = gbdt_100_trees()
    state_bytes = {
        "F1_rate": (12, 8), "F2_range": (4, 2), "F3_combined": (16, 10),
        "F4_jump": (12, 8), "B1_threshold": (2, 2),
    }
    cost_rows = []
    for name in ("F1_rate", "F2_range", "F3_combined", "F4_jump", "B1_threshold"):
        c = OP_COUNTS[name]
        cost_rows.append({
            "approach": name, "class": "deterministic filter",
            "ops_per_sample_detail":
                f"sub={c['sub']}, cmp={c['cmp']}, mul={c['mul']}, "
                f"div={c['div']}, str={c['str']}",
            "total_ops_per_sample": total_ops(name),
            "state_variables": "prev_oti, prev_ts, thresholds"
                if name != "B1_threshold" else "none (constant)",
            "state_bytes_float32": state_bytes[name][0],
            "state_bytes_fixedpoint": state_bytes[name][1],
            "model_storage_bytes": state_bytes[name][1],
            "est_cycles_m0_fixedpoint": est_cycles_m0(name, "fixed"),
            "est_cycles_m0_softfloat": est_cycles_m0(name, "float"),
            "evidence_class": "EXACT op counts; cycle counts are ESTIMATES "
                "from documented Cortex-M0 integer timings and typical GCC "
                "libgcc soft-float routine costs",
            "notes": "multiply-form avoids division (|dOTI| > thr*dt); "
                     "state: prev_oti + prev_ts + threshold(s)",
        })
    cost_rows.append({
        "approach": "MLP_28_16_8_1", "class": "MLP reference (28-16-8-1)",
        "ops_per_sample_detail": f"macs={mlp['macs']}, bias-adds={mlp['params']-mlp['macs']}",
        "total_ops_per_sample": mlp["adds"],
        "state_variables": "weights + activations",
        "state_bytes_float32": mlp["activation_bytes_fp32"],
        "state_bytes_fixedpoint": mlp["acts"] * 2,
        "model_storage_bytes": mlp["weights_bytes_fp32"],
        "est_cycles_m0_fixedpoint": mlp["est_cycles_m0_fixed"],
        "est_cycles_m0_softfloat": mlp["est_cycles_m0_float"],
        "evidence_class": "EXACT MAC/parameter counts for the stated "
                          "architecture; cycles ESTIMATED",
        "notes": "584 MACs + 25 bias-adds; 609 params (2436 B fp32); "
                 "activations 53 values",
    })
    cost_rows.append({
        "approach": "GBDT_100_trees", "class": "gradient boosting reference",
        "ops_per_sample_detail": f"compares~={gb['compares_per_sample']} (assumed depth {gb['assumed_depth']})",
        "total_ops_per_sample": gb["compares_per_sample"],
        "state_variables": "tree ensemble",
        "state_bytes_float32": 0,
        "state_bytes_fixedpoint": 0,
        "model_storage_bytes": gb["model_bytes"],
        "est_cycles_m0_fixedpoint": gb["est_cycles_m0_fixed"],
        "est_cycles_m0_softfloat": gb["est_cycles_m0_fixed"],
        "evidence_class": "ESTIMATE parameterized by assumed depth 6 and "
                          "12 B/node (architecture not fixed by any source)",
        "notes": "storage ~100 trees x 127 nodes x 12 B; per-sample cost is "
                 "tree traversal compares + loads",
    })
    pd.DataFrame(cost_rows).to_csv(OUT / "computational_cost_comparison.csv", index=False)

    # ---- figures ----------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    base = summary[(summary["policy"] == "P2_first")
                  & (summary["gap_policy"].isin(["reset", "not_applicable"]))]

    # ROC by type
    fig, ax = plt.subplots(figsize=(7.5, 5))
    for ftype, color in [("F1_rate", "tab:blue"), ("F2_range", "tab:orange"),
                         ("F4_jump", "tab:green"), ("F3_combined", "tab:red")]:
        d = base[base["filter_type"] == ftype].sort_values("false_alarm_rate_per_day")
        ax.plot(d["false_alarm_rate_per_day"], d["detection_rate"], "o-",
                color=color, label=ftype, markersize=4)
    b2 = summary[(summary["policy"] == "P2_first") & (summary["filter_type"] == "B2_random")]
    ax.plot(b2["false_alarm_rate_per_day"], b2["detection_rate"], "x--",
            color="gray", label="B2 random (seeded)", markersize=5)
    b3 = base[base["filter_type"] == "B3_percentile"]
    ax.plot(b3["false_alarm_rate_per_day"], b3["detection_rate"], "s:",
            color="purple", label="B3 percentile (non-causal)", markersize=5)
    b1d = base[base["filter_type"] == "B1_trivial"]
    ax.plot(b1d["false_alarm_rate_per_day"], b1d["detection_rate"], "*",
            color="black", markersize=14, label="B1 trivial threshold (OTI>=236)")
    ax.set_xscale("symlog", linthresh=1e-4)
    ax.set_xlabel("false-alarm episodes per day of normal operation")
    ax.set_ylabel("event detection rate (of 10 rising band-crossings)")
    ax.set_title("Filter ROC by type (P2_first policy, gap=reset)\n"
                 "All detections are CONCURRENT (lead = 0); x-axis log-scale")
    ax.set_ylim(-0.03, 1.05)
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "filter_roc_by_type.png", dpi=140)
    plt.close(fig)

    # threshold sensitivity panels
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    for ax, ftype, xlabel in zip(
            axes, ("F1_rate", "F2_range", "F4_jump"),
            ("rate threshold (OTI-units/min)", "upper threshold (OTI units)",
             "jump threshold (OTI units)")):
        d = base[base["filter_type"] == ftype].copy()
        d["thr"] = d["threshold"].str.extract(r"([0-9.]+)").astype(float)
        d = d.sort_values("thr")
        ax.plot(d["thr"], d["detection_rate"], "o-", label="detection rate")
        ax.set_xlabel(xlabel)
        ax.set_ylabel("event detection rate", color="tab:blue")
        ax2 = ax.twinx()
        ax2.plot(d["thr"], d["false_alarm_rate_per_day"], "s--", color="tab:red",
                 label="false alarms/day")
        ax2.set_ylabel("false-alarm episodes/day", color="tab:red")
        ax.set_title(ftype)
        ax.grid(alpha=0.3)
    fig.suptitle("Threshold sensitivity (P2_first, gap=reset)", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "filter_threshold_sensitivity.png", dpi=140,
                bbox_inches="tight")
    plt.close(fig)

    # lead-time distribution at a balanced operating point
    bal = summary[(summary["policy"] == "P2_first") &
                  (summary["gap_policy"] == "reset") &
                  (summary["filter_type"] == "F3_combined") &
                  (summary["threshold"] == "rate>2;OTI>50")].iloc[0]
    det = detail_rows_df = pd.DataFrame(detail_rows)
    leads = det[(det["policy"] == "P2_first") & (det["gap_policy"] == "reset") &
                (det["filter_type"] == "F3_combined") &
                (det["threshold"] == "rate>2;OTI>50") &
                (det["detected"] == True)]["lead_time_min"]  # noqa: E712
    fig, ax = plt.subplots(figsize=(7, 4.5))
    if len(leads):
        ax.hist(leads.astype(float), bins=20, color="tab:blue", alpha=0.8)
    ax.set_xlabel("lead time (min): crossing_ts - first_flag_ts "
                  "(0 = concurrent detection)")
    ax.set_ylabel("events")
    ax.set_title(f"Lead-time distribution, F3 combined rate>2 & OTI>50 (P2, reset)\n"
                 f"detected {int(bal['events_detected_of_10'])}/10, "
                 f"mean lead {bal['mean_lead_time_min']} min — "
                 "no genuine early warning in this dataset")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG / "filter_lead_time_distribution.png", dpi=140)
    plt.close(fig)

    # ---- summary json ------------------------------------------------------
    headline = {
        "phase3_run_utc": utc_now_iso(),
        "analysis_type": "exploratory_oracle_sensitivity",
        "analysis_status": ("thresholds chosen with full-dataset knowledge; "
                            "NOT held-out validation; see "
                            "phase_03r_* artifacts for the leakage-controlled "
                            "replay"),
        "events_per_policy": policy_events,
        "pre_window_minutes": PRE_WINDOW_MIN,
        "detection_policy_invariant": sorted(
            summary[(summary["filter_type"] == "F3_combined") &
                    (summary["threshold"] == "rate>2;OTI>50") &
                    (summary["gap_policy"] == "reset")]["detection_rate"].unique()),
        "notable_configs_P2_reset": _notable(summary),
        "max_lead_time_min_over_all_filters": float(
            pd.to_numeric(summary["mean_lead_time_min"], errors="coerce").max()),
        "n_configs": len(summary),
        "pareto_points": len(front),
    }
    with open(OUT / "phase_03_filter_summary.json", "w") as fh:
        json.dump(headline, fh, indent=2, default=str)
    print(json.dumps(headline, indent=2, default=str))

    if not verify_raw_files(manifest, RAW_DIR)["all_match"]:
        print("PROVENANCE GATE FAILED (post-run)!", file=sys.stderr)
        return 2
    print("[post] Post-run provenance gate OK (raw files unmodified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
