#!/usr/bin/env python3
"""Phase 3R: leakage-controlled chronological replay (frozen thresholds).

CALIBRATION  - records strictly before the first operational high-band
               crossing (2019-07-16 13:38) only; PREDEFINED quantile/max
               rules; guard enforces temporal separation; no test data,
               later maxima, or test metrics are consulted.
EVALUATION   - frozen thresholds replayed on all later records, no
               retuning, all four record-policy views (P1-P4) and both
               gap behaviors.

HONESTY LABEL: this is a POST-HOC LEAKAGE-CONTROLLED REPLAY — an
internal validation only — not a truly prospective external validation,
because the researchers have already inspected the full dataset. The
companion full-data sweep (run_filter_evaluation.py) is an
EXPLORATORY / ORACLE sensitivity analysis and must not be presented as
held-out detector validation.

Raw files provenance-gated before and after the run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import pandas as pd

from transformer_audit import (
    PARSED_TS_COLUMN, RAW_LINE_COLUMN, PlausibilityFilter,
    apply_policy, build_zone_index, find_rising_crossings,
    load_manifest, read_table, verify_raw_files,
)
from transformer_audit.replay import (
    CAL_RULES, FIRST_CROSSING_ISO, calibrate, clopper_pearson,
    day_block_bootstrap, horizon_features, quantile, sliding_windows,
    split_chronological, sustained_alert_times,
)

RAW_DIR = REPO_ROOT / "data" / "raw"
MANIFEST = REPO_ROOT / "provenance" / "dataset_manifest.json"
OUT = REPO_ROOT / "reports" / "generated"
POLICIES = ("P1_preserve", "P2_first", "P3_last", "P4_identical")
GAPS = ("reset", "continue")
PRE_WINDOW = 60.0
EPOCH = pd.Timestamp("1970-01-01")
HONESTY = ("post-hoc leakage-controlled replay (internal validation only; "
           "researchers had prior full-dataset access)")


def ts_to_min(ts):
    return (ts - EPOCH).total_seconds() / 60.0


def stream(filter_obj, samples):
    flags, valid = [], []
    for ts, oti in samples:
        d = filter_obj.process(oti, ts)
        flags.append(d.flagged)
        valid.append((not d.data_anomaly) and (oti == oti))
    return flags, valid


def persistence_in_zone(samples, flags, valid, start, end, ks=(1, 2, 3)):
    """First ts in (start, end] where >= k consecutive valid flagged."""
    out = {}
    for k in ks:
        run = 0
        first = None
        for i, (ts, _v) in enumerate(samples):
            if start < ts <= end:
                if flags[i] and valid[i]:
                    run += 1
                    if run >= k and first is None:
                        first = ts
                else:
                    run = 0
            elif ts > end:
                break
        out[k] = first
    return out


def classify(alert_ts, crossing_ts):
    if alert_ts is None:
        return "none"
    if alert_ts < crossing_ts:
        return "before_crossing"
    if alert_ts == crossing_ts:
        return "at_crossing"
    return "after_crossing"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(MANIFEST)
    if not verify_raw_files(manifest, RAW_DIR)["all_match"]:
        print("PROVENANCE GATE FAILED (pre-run).", file=sys.stderr)
        return 2
    print("[0] Pre-run provenance gate OK")

    cutoff = ts_to_min(pd.Timestamp(FIRST_CROSSING_ISO))
    ov = read_table(RAW_DIR / "Overview.csv")

    cal_records = {}
    replay_rows = []
    per_event_rows = []

    for policy in POLICIES:
        series = apply_policy(ov, policy)
        series = series.sort_values([PARSED_TS_COLUMN, RAW_LINE_COLUMN],
                                    kind="stable").reset_index(drop=True)
        samples = [(ts_to_min(t), float(o))
                   for t, o in zip(series[PARSED_TS_COLUMN], series["OTI"])]
        cal, test = split_chronological(samples, cutoff)
        calib = calibrate(cal, cutoff)          # guard + predefined rules
        # SENSITIVITY ONLY: alarm-excluded calibration (drops the 60-min
        # stretch immediately before the cutoff). Primary calibration
        # above includes ALL valid pre-event records, as predefined.
        cal_excl = [(ts, v) for ts, v in cal if ts < cutoff - 60.0]
        calib_excl = calibrate(cal_excl, cutoff)
        cal_records[policy] = {
            "cutoff_iso": FIRST_CROSSING_ISO,
            "calibration_records": calib["n_records"],
            "calibration_valid_pairs": calib["n_valid_pairs"],
            "calibration_oti_max": calib["oti_max"],
            "sensitivity_alarm_excluded": {
                "note": "SENSITIVITY ONLY - not used for frozen thresholds",
                "calibration_records": calib_excl["n_records"],
                "thresholds": calib_excl["thresholds"]},
            "rules": {k: {"primary": CAL_RULES[k]["primary"],
                          "sensitivity": CAL_RULES[k]["sensitivity"]}
                      for k in CAL_RULES},
            "thresholds": calib["thresholds"],
        }
        print(f"[{policy}] cal={calib['n_records']} rec, "
              f"thr={ {k: v['primary'] for k, v in calib['thresholds'].items()} }")

        events = find_rising_crossings(samples)   # full-series crossings
        events = [e for e in events if e["crossing_ts"] >= cutoff]
        zone_idx = build_zone_index(test, events, PRE_WINDOW)

        # ground truth rows: OTI >= 100 (high band) in the TEST segment
        high = [v >= 100.0 for _t, v in test]

        frozen = {
            "F1_rate": ("rate", {"rate_threshold":
                                 calib["thresholds"]["F1_rate"]["primary"]}),
            "F2_range": ("range", {"upper_threshold":
                                   calib["thresholds"]["F2_upper"]["primary"]}),
            "F3_combined": ("combined", {
                "rate_threshold": calib["thresholds"]["F1_rate"]["primary"],
                "upper_threshold": calib["thresholds"]["F2_upper"]["primary"]}),
            "F4_jump": ("jump", {"jump_threshold":
                                 calib["thresholds"]["F4_jump"]["primary"]}),
        }
        gap_opts = {"F1_rate": GAPS, "F2_range": (None,),
                    "F3_combined": GAPS, "F4_jump": GAPS}

        def thr_summary_for(ftype):
            out = {}
            if ftype in ("rate", "combined"):
                out["F1_rate_q999"] = calib["thresholds"]["F1_rate"]["primary"]
            if ftype in ("range", "combined"):
                out["F2_cal_max"] = calib["thresholds"]["F2_upper"]["primary"]
            if ftype == "jump":
                out["F4_q999"] = calib["thresholds"]["F4_jump"]["primary"]
            return out

        for fname, (ftype, kwargs) in frozen.items():
            thr_summary = thr_summary_for(ftype)
            for gap in gap_opts[fname]:
                kw = dict(kwargs)
                if gap is not None:
                    kw["gap_behavior"] = gap
                f = PlausibilityFilter(ftype, **kw)
                flags_full, _valid_full = stream(f, samples)  # continuous run
                flags = flags_full[len(samples) - len(test):]
                valid = _valid_full[len(samples) - len(test):]

                tp = sum(1 for fl, h in zip(flags, high) if fl and h)
                fp = sum(1 for fl, h in zip(flags, high) if fl and not h)
                fn = sum(1 for fl, h in zip(flags, high) if (not fl) and h)
                prec = tp / (tp + fp) if (tp + fp) else float("nan")
                rec = tp / (tp + fn) if (tp + fn) else float("nan")
                f1s = (2 * prec * rec / (prec + rec)
                       if (prec + rec) and prec == prec and rec == rec
                       else float("nan"))

                # event-level via evaluate machinery on TEST segment
                ev_det = 0
                delays = []
                for k, ev in enumerate(events):
                    start = ev["crossing_ts"] - PRE_WINDOW
                    if k > 0 and events[k - 1]["recovery_ts"] is not None:
                        start = max(start, events[k - 1]["recovery_ts"])
                    end = ev["recovery_ts"] if ev["recovery_ts"] is not None \
                        else test[-1][0]
                    first_flag = next((ts for i, (ts, _v) in enumerate(test)
                                       if start < ts <= end and flags[i]), None)
                    strict = (first_flag is not None
                              and first_flag <= ev["crossing_ts"])
                    if strict:
                        ev_det += 1
                    if first_flag is not None:
                        delays.append(round(first_flag - ev["crossing_ts"], 3))
                    if policy == "P2_first" and gap in (None, "reset"):
                        pers = persistence_in_zone(test, flags, valid,
                                                   start, end)
                        pw_start = start
                        row = {
                            "policy": policy, "filter": fname,
                            "gap_policy": gap or "stateless",
                            "event_id": k + 1,
                            "crossing_ts_min": round(ev["crossing_ts"], 2),
                            "window_hit": first_flag is not None
                            and first_flag <= ev["crossing_ts"],
                            "first_alert_ts_min":
                                round(first_flag, 2) if first_flag else None,
                            "first_alert_class": classify(first_flag,
                                                          ev["crossing_ts"]),
                            "detection_delay_min":
                                round(first_flag - ev["crossing_ts"], 3)
                                if first_flag else None,
                        }
                        nval = nflag = 0
                        for i, (ts, _v) in enumerate(test):
                            if pw_start < ts <= ev["crossing_ts"] and valid[i]:
                                nval += 1
                                if flags[i]:
                                    nflag += 1
                        row["prewindow_duty_cycle"] = (round(nflag / nval, 4)
                                                       if nval else None)
                        for kk in (1, 2, 3):
                            row[f"sustained_k{kk}_ts_min"] = (
                                round(pers[kk], 2) if pers[kk] else None)
                            row[f"sustained_k{kk}_class"] = classify(
                                pers[kk], ev["crossing_ts"])
                        per_event_rows.append(row)

                # FA episodes per calendar day of normal test operation
                ep_per_day = {}
                day_has_normal = set()
                for i, (ts, _v) in enumerate(test):
                    if zone_idx[i] == -1:
                        day_has_normal.add(int(ts // 1440))
                in_ep = False
                ep_start = None
                for i, (ts, _v) in enumerate(test):
                    if zone_idx[i] == -1 and flags[i]:
                        if not in_ep:
                            in_ep = True
                            ep_start = ts
                    else:
                        if in_ep:
                            d = int(ep_start // 1440)
                            ep_per_day[d] = ep_per_day.get(d, 0) + 1
                            in_ep = False
                if in_ep:
                    d = int(ep_start // 1440)
                    ep_per_day[d] = ep_per_day.get(d, 0) + 1
                for d in day_has_normal:
                    ep_per_day.setdefault(d, 0)
                fa_point, fa_lo, fa_hi = day_block_bootstrap(ep_per_day)

                test_days = (test[-1][0] - test[0][0]) / 1440.0
                n_normal_rows = sum(1 for z in zone_idx if z == -1)
                n_excluded_rows = sum(1 for z in zone_idx if z >= 0)

                lo_ci, hi_ci = clopper_pearson(ev_det, len(events))
                replay_rows.append({
                    "policy": policy, "filter": fname,
                    "gap_policy": gap or "stateless",
                    "frozen_thresholds": json.dumps(thr_summary),
                    "events_detected": ev_det, "events_total": len(events),
                    "event_recall": round(ev_det / len(events), 3),
                    "event_recall_ci95": f"[{lo_ci}, {hi_ci}]",
                    "row_tp": tp, "row_fp": fp, "row_fn": fn,
                    "row_precision": round(prec, 4),
                    "row_recall": round(rec, 4), "row_f1": round(f1s, 4),
                    "mean_detection_delay_min": (round(sum(delays) / len(delays), 3)
                                                 if delays else None),
                    "fa_episodes_total": sum(ep_per_day.values()),
                    "fa_rate_per_day": fa_point,
                    "fa_rate_ci95_bootstrap": f"[{fa_lo}, {fa_hi}]",
                    "flagged_samples_per_test_day": round(sum(flags) / test_days, 4),
                    "monitored_rows_normal_zones": n_normal_rows,
                    "excluded_rows_event_zones": n_excluded_rows,
                    "normal_day_blocks": len(day_has_normal),
                })

    pd.DataFrame(replay_rows).to_csv(OUT / "phase_03r_replay_metrics.csv",
                                     index=False)
    pd.DataFrame(per_event_rows).to_csv(OUT / "phase_03r_per_event.csv",
                                        index=False)

    # ---------------- T3: OTI-only horizon exploration (P2_first) --------
    series = apply_policy(ov, "P2_first")
    series = series.sort_values([PARSED_TS_COLUMN, RAW_LINE_COLUMN],
                                kind="stable").reset_index(drop=True)
    samples = [(ts_to_min(t), float(o))
               for t, o in zip(series[PARSED_TS_COLUMN], series["OTI"])]
    cal, test = split_chronological(samples, cutoff)
    events = [e for e in find_rising_crossings(samples)
              if e["crossing_ts"] >= cutoff]

    t3_rows = []
    feats = ("last", "maximum", "mean", "slope_per_min", "variability",
             "max_gap_min", "missing_frac")
    for H in (60.0, 360.0, 1440.0):
        ref_windows = [horizon_features(w) for _s, w in
                       sliding_windows(cal, H)]
        ref = {f: sorted(r[f] for r in ref_windows) for f in feats}
        thr = {f: quantile(ref[f], 0.99) for f in feats}
        # event windows: strictly before each onset
        hits = {f: 0 for f in feats}
        for ev in events:
            w = [(t, v) for t, v in samples
                 if ev["crossing_ts"] - H <= t < ev["crossing_ts"]]
            fw = horizon_features(w)
            for f in feats:
                if fw[f] > thr[f]:
                    hits[f] += 1
        # normal-window context: test-period normal zones
        zone_idx = build_zone_index(test, events, PRE_WINDOW)
        normal_test = [s for i, s in enumerate(test) if zone_idx[i] == -1]
        nw = list(sliding_windows(normal_test, H))
        nflag = {f: 0 for f in feats}
        for _s, w in nw:
            fw = horizon_features(w)
            for f in feats:
                if fw[f] > thr[f]:
                    nflag[f] += 1
        for f in feats:
            t3_rows.append({
                "horizon_min": H, "feature": f,
                "calibration_q99_threshold": round(thr[f], 4),
                "event_windows_flagged_of_10": hits[f],
                "normal_windows_flagged_frac": round(nflag[f] / len(nw), 4)
                if nw else None,
                "n_normal_windows": len(nw),
            })
    pd.DataFrame(t3_rows).to_csv(OUT / "phase_03r_t3_horizons.csv", index=False)

    summary = {
        "honesty_label": HONESTY,
        "cutoff": FIRST_CROSSING_ISO,
        "calibration": cal_records,
        "note_multichannel": ("OTI-only summaries evaluated; NO multivariate "
                              "early-warning conclusion is possible (other "
                              "channels not evaluated in T3)."),
    }
    with open(OUT / "phase_03r_summary.json", "w") as fh:
        json.dump(summary, fh, indent=2, default=str)
    with open(OUT / "phase_03r_calibration.json", "w") as fh:
        json.dump(cal_records, fh, indent=2, default=str)

    if not verify_raw_files(manifest, RAW_DIR)["all_match"]:
        print("PROVENANCE GATE FAILED (post-run)!", file=sys.stderr)
        return 2
    print("[post] Post-run provenance gate OK (raw files unmodified)")
    print(f"replay rows: {len(replay_rows)}, per-event rows: "
          f"{len(per_event_rows)}, t3 rows: {len(t3_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
