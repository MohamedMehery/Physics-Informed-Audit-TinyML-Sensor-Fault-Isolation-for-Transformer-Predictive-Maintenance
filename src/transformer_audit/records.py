"""Repeated-record and latent-entity analysis.

Terminology (Phase 2 rule): "repeated-timestamp records" — NOT "duplicates",
until their origin is understood.

Record policies (non-destructive interpretations):
  P1 'preserve'  — keep every record as a separate observation;
  P2 'first'     — first raw occurrence per timestamp;
  P3 'last'      — last raw occurrence per timestamp;
  P4 'identical' — collapse only groups whose sensor values are identical;
                   retain EVERY branch of a conflicting group;
  P5             — provisional occurrence-index streams (only if cross-file
                   and temporal evidence supports it; see occurrence_report).

Averaging OTI or binary flags across conflicting records is forbidden here:
it may create a state that never physically existed.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from .io import PARSED_TS_COLUMN, RAW_LINE_COLUMN, canonicalize, read_table, sensor_columns

FLAG_COLUMNS = ["OTI_A", "OTI_T", "MOG_A", "WTI"]


# ----------------------------------------------------------------------------
# Multiplicity
# ----------------------------------------------------------------------------

def multiplicity_table(df: pd.DataFrame) -> pd.DataFrame:
    """Distribution of records-per-timestamp for one file."""
    sizes = df.groupby(PARSED_TS_COLUMN).size()
    vc = sizes.value_counts().sort_index()
    return pd.DataFrame({
        "records_per_timestamp": vc.index.astype(int),
        "n_timestamps": vc.values.astype(int),
        "share_of_timestamps_pct": (vc.values / len(sizes) * 100.0).round(3),
    })


def repeated_timestamps_shared(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Cross-file sharing of repeated-timestamp groups."""
    names = sorted(dfs)
    dup_sets = {}
    for n, df in dfs.items():
        sizes = df.groupby(PARSED_TS_COLUMN).size()
        dup_sets[n] = set(sizes[sizes > 1].index)
    rows = []
    for a in names:
        for b in names:
            if a < b:
                inter = dup_sets[a] & dup_sets[b]
                rows.append({
                    "file_a": a, "file_b": b,
                    "repeated_groups_a": len(dup_sets[a]),
                    "repeated_groups_b": len(dup_sets[b]),
                    "shared_repeated_timestamps": len(inter),
                })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Repeated-group report
# ----------------------------------------------------------------------------

def repeated_group_report(df: pd.DataFrame) -> pd.DataFrame:
    """Per repeated-timestamp group: identical vs conflicting, which columns
    conflict, conflict magnitudes, flag conflicts, raw-line span, monthly tag.
    Nothing is dropped or merged."""
    cols = sensor_columns(df)
    rows = []
    for ts_val, grp in df.groupby(PARSED_TS_COLUMN, sort=True):
        if len(grp) < 2:
            continue
        conflicting = [c for c in cols if grp[c].drop_duplicates().shape[0] > 1]
        magnitudes = {}
        for c in conflicting:
            v = grp[c]
            magnitudes[c] = float(v.max() - v.min())
        flag_cols = [c for c in FLAG_COLUMNS if c in cols]
        flags_conflict = any(grp[c].drop_duplicates().shape[0] > 1 for c in flag_cols)
        lines = sorted(grp[RAW_LINE_COLUMN].tolist())
        rows.append({
            "timestamp": str(ts_val),
            "month": str(ts_val)[:7],
            "n_records": len(grp),
            "raw_line_span": lines[-1] - lines[0],
            "raw_lines_adjacent": lines[-1] - lines[0] == len(lines) - 1,
            "identical_group": len(conflicting) == 0,
            "conflicting_columns": ";".join(conflicting),
            "max_conflict_magnitude": max(magnitudes.values()) if magnitudes else 0.0,
            "conflict_magnitudes": ";".join(f"{k}={v:g}" for k, v in magnitudes.items()),
            "flags_conflict": flags_conflict,
            "conflicting_flags": ";".join(
                c for c in flag_cols if grp[c].drop_duplicates().shape[0] > 1
            ),
        })
    return pd.DataFrame(rows)


def conflict_summary(df: pd.DataFrame) -> Dict:
    rep = repeated_group_report(df)
    if rep.empty:
        return {"repeated_groups": 0}
    return {
        "repeated_groups": int(len(rep)),
        "identical_groups": int(rep["identical_group"].sum()),
        "conflicting_groups": int((~rep["identical_group"]).sum()),
        "groups_with_flag_conflicts": int(rep["flags_conflict"].sum()),
        "median_max_conflict_magnitude": float(rep["max_conflict_magnitude"].median()),
        "max_conflict_magnitude": float(rep["max_conflict_magnitude"].max()),
        "all_groups_raw_line_adjacent": bool(rep["raw_lines_adjacent"].all()),
    }


# ----------------------------------------------------------------------------
# High-OTI / repeated-group intersection
# ----------------------------------------------------------------------------

def high_oti_repeated_intersection(df: pd.DataFrame, threshold: float = 100.0) -> Dict:
    """Do high-OTI records fall inside repeated-timestamp groups?"""
    sizes = df.groupby(PARSED_TS_COLUMN).size()
    high = df[df["OTI"] >= threshold]
    n_high = len(high)
    n_high_in_repeated = int(sum(1 for t in high[PARSED_TS_COLUMN] if sizes[t] > 1))
    return {
        "n_high_oti_records": int(n_high),
        "n_high_oti_records_in_repeated_groups": n_high_in_repeated,
        "threshold": threshold,
    }


def per_record_flag_consistency(df: pd.DataFrame) -> Dict:
    """Per-record check: (OTI >= 236) <=> (OTI_T == 1) across ALL raw records
    (including every branch of repeated groups)."""
    ok = int(((df["OTI"] >= 236) == (df["OTI_T"] == 1)).sum())
    bad = int(((df["OTI"] >= 236) != (df["OTI_T"] == 1)).sum())
    return {"rule_oti_ge_236_iff_oti_t_1_ok": ok, "violations": bad,
            "n_records": int(len(df))}


# ----------------------------------------------------------------------------
# Record policies
# ----------------------------------------------------------------------------

POLICIES = ("P1_preserve", "P2_first", "P3_last", "P4_identical")


def apply_policy(df: pd.DataFrame, policy: str) -> pd.DataFrame:
    """Apply a non-destructive record policy. Never averages values."""
    df = df.sort_values(PARSED_TS_COLUMN, kind="stable").reset_index(drop=True)
    if policy == "P1_preserve":
        return df
    if policy in ("P2_first", "P3_last"):
        keep = "first" if policy == "P2_first" else "last"
        return df.drop_duplicates(subset=[PARSED_TS_COLUMN], keep=keep).reset_index(drop=True)
    if policy == "P4_identical":
        # collapse only identical groups; keep every conflicting branch
        cols = sensor_columns(df)
        first = df.drop_duplicates(subset=[PARSED_TS_COLUMN] + cols, keep="first")
        # a timestamp is "collapsed" if its group is identical; otherwise all its
        # records are retained (they differ in some sensor column, so the
        # drop_duplicates above already retains each distinct branch)
        return first.reset_index(drop=True)
    raise ValueError(f"unknown policy: {policy}")


def policy_metrics(df: pd.DataFrame, policy: str, rate_threshold: float = 5.0,
                   event_gap_minutes: float = 30.0) -> Dict:
    """Recompute excursion-critical metrics under one record policy.

    Rates on P1/P4 (multi-branch series) are computed on the policy series
    ordered by (timestamp, raw line) with guarded division; a rate is only
    computed when the timestamp strictly increases. Branch-to-branch zero
    intervals are excluded by the guard and counted.
    """
    from .events import primitive_events
    from .timestamps import safe_rate

    s = apply_policy(df, policy)
    s = s.sort_values([PARSED_TS_COLUMN, RAW_LINE_COLUMN], kind="stable").reset_index(drop=True)
    dt = s[PARSED_TS_COLUMN].diff().dt.total_seconds() / 60.0
    dv = s["OTI"].diff()
    rates = [safe_rate(dv.iloc[i], dt.iloc[i]) for i in range(len(s))]
    rates = pd.Series(rates)
    valid = rates.dropna()

    # empty OTI intervals: consecutive distinct values with gaps > 5
    u = np.sort(s["OTI"].dropna().unique())
    gaps = [(float(a), float(b)) for a, b in zip(u[:-1], u[1:]) if b - a > 5]

    # OTI_T relationship on all retained records
    rule_ok = int(((s["OTI"] >= 236) == (s["OTI_T"] == 1)).sum())
    rule_acc = rule_ok / len(s)

    # high-OTI transition count (rises from <100 to >=100 on increasing time)
    ishigh = s["OTI"] >= 100
    rises = 0
    for i in range(1, len(s)):
        if dt.iloc[i] > 0 and (not ishigh.iloc[i - 1]) and ishigh.iloc[i]:
            rises += 1

    ev = primitive_events(s, "OTI_T", max_continuity_gap_minutes=event_gap_minutes)
    return {
        "policy": policy,
        "n_records": int(len(s)),
        "n_unique_timestamps": int(s[PARSED_TS_COLUMN].nunique()),
        "high_oti_rising_transitions": int(rises),
        "oti_t_rule_accuracy": float(rule_acc),
        "empty_oti_intervals_gt5": ";".join(f"({a:g},{b:g})" for a, b in gaps) or "none",
        "max_positive_rate_per_min": float(valid.max()) if len(valid) else float("nan"),
        "max_negative_rate_per_min": float(valid.min()) if len(valid) else float("nan"),
        "n_oti_t_primitive_events_gap30": int(len(ev)),
        "n_intervals_excluded_nonpositive": int((dt <= 0).sum()),
    }


def policy_sensitivity(df: pd.DataFrame, policies: Iterable[str] = POLICIES) -> pd.DataFrame:
    return pd.DataFrame([policy_metrics(df, p) for p in policies])


# ----------------------------------------------------------------------------
# Occurrence-index streams (P5 diagnostics)
# ----------------------------------------------------------------------------

def occurrence_report(df: pd.DataFrame) -> Dict:
    """Evidence check for provisional occurrence-index streams (P5).

    If repeated records represented multiple devices, each device would
    appear at (nearly) every timestamp, i.e., multiplicity would be near
    constant at >= 2. We measure how often each occurrence index appears.
    """
    sizes = df.groupby(PARSED_TS_COLUMN).size()
    n_ts = len(sizes)
    share_multi = float((sizes > 1).mean())
    max_mult = int(sizes.max())
    # how often would a 'second device stream' have data?
    return {
        "n_timestamps": int(n_ts),
        "share_of_timestamps_with_repeats": round(share_multi, 4),
        "max_records_per_timestamp": max_mult,
        "verdict_supports_stable_occurrence_streams": bool(share_multi > 0.9),
        "note": (
            "A constant multiplicity >= 2 at ~all timestamps would support "
            "reconstructing per-device occurrence streams. Observed shares are "
            "far below that, so occurrence-index device reconstruction is NOT "
            "supported by multiplicity structure."
        ),
    }


# ----------------------------------------------------------------------------
# Latent-stream diagnostics
# ----------------------------------------------------------------------------

def neighbor_continuity_fit(df: pd.DataFrame) -> Dict:
    """For conflicting repeated groups: does the first or the last branch fit
    neighboring single-record values better? (Neither = ambiguous origin.)"""
    s = df.sort_values(PARSED_TS_COLUMN, kind="stable").reset_index(drop=True)
    groups = {t: g for t, g in s.groupby(PARSED_TS_COLUMN)}
    ts_sorted = sorted(groups)
    first_err, last_err, n = [], [], 0
    for i, t in enumerate(ts_sorted):
        g = groups[t]
        if len(g) < 2 or g["OTI"].nunique() == 1:
            continue
        prev_t = next((ts_sorted[j] for j in range(i - 1, -1, -1) if len(groups[ts_sorted[j]]) == 1), None)
        next_t = next((ts_sorted[j] for j in range(i + 1, len(ts_sorted)) if len(groups[ts_sorted[j]]) == 1), None)
        if prev_t is None or next_t is None:
            continue
        pv = float(groups[prev_t]["OTI"].iloc[0])
        nv = float(groups[next_t]["OTI"].iloc[0])
        vals = g["OTI"].tolist()
        n += 1
        first_err.append(abs(vals[0] - pv) + abs(vals[0] - nv))
        last_err.append(abs(vals[-1] - pv) + abs(vals[-1] - nv))
    if n == 0:
        return {"n_conflicting_groups_with_neighbors": 0}
    return {
        "n_conflicting_groups_with_neighbors": n,
        "mean_fit_error_first_branch": round(float(np.mean(first_err)), 2),
        "mean_fit_error_last_branch": round(float(np.mean(last_err)), 2),
        "first_fits_better": bool(np.mean(first_err) < np.mean(last_err)),
        "note": "Near-equal fit errors mean branch ordering cannot identify a 'true' stream.",
    }


def value_band_unimodality(df: pd.DataFrame, col: str, nonzero: bool = True) -> Dict:
    """Operating-range clustering check: multiple assets with different
    voltage/tap regimes would produce separated value bands."""
    v = df[col]
    if nonzero:
        v = v[v > 50]
    q = v.quantile([0.01, 0.5, 0.99])
    hist = v.round(-1).value_counts().sort_index()
    top = hist.idxmax()
    # contiguous clusters of populated decade bands (>0.5% each): separated
    # regimes (multi-asset signature) show as >1 cluster with an empty gap
    populated = hist[hist / len(v) > 0.005]
    clusters = 0
    prev_band = None
    for band in populated.index:
        if prev_band is None or band - prev_band > 10:
            clusters += 1
        prev_band = band
    return {
        "column": col,
        "n_values": int(len(v)),
        "p01": float(q.loc[0.01]),
        "median": float(q.loc[0.5]),
        "p99": float(q.loc[0.99]),
        "dominant_decade_band": float(top),
        "n_populated_decade_bands": int(len(populated)),
        "n_contiguous_band_clusters": int(clusters),
        "note": "More than one contiguous band cluster (empty gaps between) would hint at multiple voltage regimes (assets). Adjacent populated decades are one regime.",
    }
