"""Core audit computations: inventory, intervals, duplicates, distributions,
onsets, threshold separability, autocorrelation, rates, cross-file alignment.

All rate computations use actual per-row delta-t (never an assumed 15-minute
cadence). Duplicate timestamps are always analysed, never silently dropped.
"""

from __future__ import annotations

from itertools import combinations
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd

from .io import PARSED_TS_COLUMN, RAW_LINE_COLUMN, RAW_TS_COLUMN, read_table, sensor_columns
from .timestamps import interval_minutes, safe_rate

# "Large gap" thresholds (minutes) reported in interval summaries.
GAP_THRESHOLDS_MIN = [30.0, 60.0, 1440.0]


# ----------------------------------------------------------------------------
# Inventory
# ----------------------------------------------------------------------------

def inventory_file(path: str | Path) -> Dict:
    """Full inventory of one dataset file."""
    df = read_table(path)
    ts = df[PARSED_TS_COLUMN]
    sensor_cols = sensor_columns(df)
    dup_ts_mask = ts.duplicated(keep=False)
    n_dup_rows = int(ts.duplicated().sum())  # rows beyond the first per timestamp
    exact_dup_rows = int(df.duplicated(subset=[RAW_TS_COLUMN] + sensor_cols).sum())
    inv = {
        "filename": Path(path).name,
        "columns": ",".join([RAW_TS_COLUMN] + sensor_cols),
        "n_columns": 1 + len(sensor_cols),
        "n_rows": int(len(df)),
        "n_unique_timestamps": int(ts.nunique()),
        "n_duplicate_timestamp_rows": n_dup_rows,
        "n_exact_duplicate_rows": exact_dup_rows,
        "timestamp_min": str(ts.min()),
        "timestamp_max": str(ts.max()),
        "missing_values_total": int(sum(df[c].isna().sum() for c in sensor_cols)),
        "nonpositive_intervals": 0,  # filled by interval summary on canonical order
    }
    return inv


# ----------------------------------------------------------------------------
# Intervals
# ----------------------------------------------------------------------------

def interval_summary(ts: pd.Series) -> Dict:
    """Interval (delta-t) distribution in minutes for a parsed, sorted
    timestamp series. Nonpositive intervals are counted, never hidden."""
    ts = pd.Series(pd.to_datetime(ts.values)).sort_values().reset_index(drop=True)
    dt = interval_minutes(ts)
    pos = dt[dt > 0]
    out = {
        "n_intervals": int(dt.notna().sum()),
        "n_nonpositive_intervals": int((dt <= 0).sum()),
        "n_zero_intervals": int((dt == 0).sum()),
        "min_minutes": float(pos.min()) if len(pos) else float("nan"),
        "median_minutes": float(pos.median()) if len(pos) else float("nan"),
        "p95_minutes": float(pos.quantile(0.95)) if len(pos) else float("nan"),
        "p99_minutes": float(pos.quantile(0.99)) if len(pos) else float("nan"),
        "max_minutes": float(pos.max()) if len(pos) else float("nan"),
        "mean_minutes": float(pos.mean()) if len(pos) else float("nan"),
    }
    for thr in GAP_THRESHOLDS_MIN:
        out[f"n_intervals_gt_{int(thr)}min"] = int((pos > thr).sum())
    return out


# ----------------------------------------------------------------------------
# Duplicates
# ----------------------------------------------------------------------------

def duplicate_timestamp_report(df: pd.DataFrame) -> pd.DataFrame:
    """Per-duplicate-timestamp-group report.

    For every timestamp with more than one raw record: number of records,
    whether all sensor values are identical across the group, how many
    sensor columns conflict, and the distinct-value spread of conflicting
    columns. Never drops or merges anything.
    """
    cols = sensor_columns(df)
    rows = []
    for ts_val, grp in df.groupby(PARSED_TS_COLUMN, sort=True):
        if len(grp) < 2:
            continue
        n_records = len(grp)
        identical = all(grp[c].drop_duplicates().shape[0] == 1 for c in cols)
        conflicting_cols = [c for c in cols if grp[c].drop_duplicates().shape[0] > 1]
        spreads = {
            c: f"{grp[c].min()}..{grp[c].max()}" for c in conflicting_cols
        }
        rows.append({
            "timestamp": str(ts_val),
            "n_records": n_records,
            "raw_lines": ",".join(str(x) for x in sorted(grp[RAW_LINE_COLUMN].tolist())),
            "identical_group": identical,
            "n_conflicting_columns": len(conflicting_cols),
            "conflicting_columns": ",".join(conflicting_cols),
            "conflicting_value_spreads": ";".join(f"{k}={v}" for k, v in spreads.items()),
        })
    return pd.DataFrame(rows, columns=[
        "timestamp", "n_records", "raw_lines", "identical_group",
        "n_conflicting_columns", "conflicting_columns", "conflicting_value_spreads",
    ])


# ----------------------------------------------------------------------------
# Distributions / onsets
# ----------------------------------------------------------------------------

def value_distribution(df: pd.DataFrame, cols: Optional[Iterable[str]] = None) -> pd.DataFrame:
    cols = list(cols) if cols is not None else sensor_columns(df)
    rows = []
    for c in cols:
        v = df[c]
        nrows = {
            "column": c,
            "n_unique": int(v.nunique()),
            "min": float(v.min()) if len(v) else float("nan"),
            "p25": float(v.quantile(0.25)) if len(v) else float("nan"),
            "median": float(v.median()) if len(v) else float("nan"),
            "mean": float(v.mean()) if len(v) else float("nan"),
            "p75": float(v.quantile(0.75)) if len(v) else float("nan"),
            "max": float(v.max()) if len(v) else float("nan"),
            "behaviour": (
                "binary" if v.nunique() == 2 and set(v.dropna().unique()) <= {0.0, 1.0}
                else ("categorical/discrete" if v.nunique() <= 30 else "continuous-ish")
            ),
        }
        top = v.value_counts().head(5)
        nrows["top_values"] = "; ".join(f"{k}: {int(x)}" for k, x in top.items())
        rows.append(nrows)
    return pd.DataFrame(rows)


def onset_counts(df: pd.DataFrame, flags: Iterable[str], policy: str = "first") -> pd.DataFrame:
    """0->1 onsets and 1->0 offsets of binary flags on the canonical series."""
    from .io import canonicalize
    canon = canonicalize(df, policy=policy, sort=True)
    rows = []
    for f in flags:
        s = canon[f]
        prev = s.shift(1)
        rows.append({
            "flag": f,
            "duplicate_policy": policy,
            "n_active_rows": int((s == 1).sum()),
            "onsets_0_to_1": int(((s == 1) & (prev == 0)).sum()),
            "offsets_1_to_0": int(((s == 0) & (prev == 1)).sum()),
        })
    return pd.DataFrame(rows)


def onset_counts_policy_sensitivity(df: pd.DataFrame, flags: Iterable[str],
                                    policies: Iterable[str] = ("first", "last", "identical")) -> pd.DataFrame:
    """Onset counts under non-destructive record policies.

    Phase-2 rule: 'mean' is NOT used — averaging binary flags across
    conflicting records can create states that never physically existed.
    """
    frames = [onset_counts(df, flags, policy=p) for p in policies]
    return pd.concat(frames, ignore_index=True)


# ----------------------------------------------------------------------------
# Value gaps & threshold separability
# ----------------------------------------------------------------------------

def value_gap_analysis(values: pd.Series, min_gap: float = 5.0) -> pd.DataFrame:
    """Maximal empty intervals in the observed value range.

    Reports every pair of consecutive distinct observed values whose
    difference exceeds ``min_gap``. This is data evidence about a
    discontinuous / two-state value distribution; it is NOT proof of any
    hardware behaviour.
    """
    u = np.sort(pd.Series(values).dropna().unique())
    rows = []
    for a, b in zip(u[:-1], u[1:]):
        gap = float(b - a)
        if gap > min_gap:
            rows.append({
                "lower_observed_value": float(a),
                "upper_observed_value": float(b),
                "gap_size": gap,
                "n_values_in_between_observed": 0,
            })
    return pd.DataFrame(rows, columns=[
        "lower_observed_value", "upper_observed_value", "gap_size",
        "n_values_in_between_observed",
    ]).sort_values("gap_size", ascending=False)


def threshold_separability(df: pd.DataFrame, value_col: str, flag_cols: Iterable[str]) -> pd.DataFrame:
    """Relationship between a continuous channel and binary flags.

    Reports the value range observed at flag=0 and flag=1, the best simple
    separating threshold, whether the classes overlap, and the accuracy of
    that threshold rule. A high threshold-rule accuracy means only that the
    flag is separable by a threshold on this channel in this dataset; it
    does NOT identify the flag's causal logic.
    """
    rows = []
    for f in flag_cols:
        v1 = df.loc[df[f] == 1, value_col]
        v0 = df.loc[df[f] == 0, value_col]
        if len(v1) == 0 or len(v0) == 0:
            continue
        lo1, hi1 = float(v1.min()), float(v1.max())
        lo0, hi0 = float(v0.min()), float(v0.max())
        overlap = lo1 <= hi0 and lo0 <= hi1
        # best threshold: sweep midpoints of sorted distinct values in BOTH
        # directions (flag == value >= thr  and  flag == value <= thr)
        candidates = np.sort(df[value_col].dropna().unique())
        best_thr, best_dir, best_acc = float("nan"), "", -1.0
        for thr in candidates:
            for direction, pred in (
                (">=", (df[value_col] >= thr).astype(int)),
                ("<=", (df[value_col] <= thr).astype(int)),
            ):
                acc = float((pred == df[f]).mean())
                if acc > best_acc:
                    best_acc, best_thr, best_dir = acc, float(thr), direction
        rows.append({
            "value_column": value_col,
            "flag": f,
            "n_flag_1": int(len(v1)),
            "value_range_flag_1": f"{lo1}..{hi1}",
            "n_flag_0": int(len(v0)),
            "value_range_flag_0": f"{lo0}..{hi0}",
            "classes_overlap": overlap,
            "best_threshold": best_thr,
            "best_threshold_direction": best_dir,
            "threshold_rule_accuracy": best_acc,
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Autocorrelation
# ----------------------------------------------------------------------------

def autocorrelation_by_lag(df: pd.DataFrame, col: str,
                           lags: Iterable[int] = (1, 2, 4, 8, 96)) -> pd.DataFrame:
    """Sample-lag autocorrelation on the canonical series.

    CAVEAT: lags are in samples, not time. The dataset's sampling is not
    strictly uniform (median 15 min, with shorter intervals and long gaps),
    so sample-lag results are indicative only. This is documented wherever
    these numbers are used.
    """
    from .io import canonicalize
    canon = canonicalize(df, policy="first", sort=True)
    s = canon[col]
    rows = []
    for lag in lags:
        rows.append({
            "column": col,
            "lag_samples": int(lag),
            "approx_time_if_15min_cadence_minutes": int(lag) * 15,
            "autocorrelation": float(s.autocorr(lag)) if len(s) > lag else float("nan"),
            "n_pairs": int(len(s) - lag),
        })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# Rates
# ----------------------------------------------------------------------------

def rate_summary(df: pd.DataFrame, value_col: str,
                 high_predicate: Optional[pd.Series] = None) -> Dict:
    """Rate-of-change distribution using ACTUAL delta-t minutes.

    rate[k] = (value[k] - value[k-1]) / (t[k] - t[k-1]) computed only when
    the interval is strictly positive. Duplicate (zero) and out-of-order
    (negative) intervals are excluded from rates and counted separately.

    If ``high_predicate`` is given (a boolean Series aligned to df rows
    after canonical sort), rates are additionally split into
    "excursion-related" (either endpoint flagged) vs "normal-mode".
    """
    from .io import canonicalize
    canon = canonicalize(df, policy="first", sort=True).reset_index(drop=True)
    dt = interval_minutes(canon[PARSED_TS_COLUMN])
    dv = canon[value_col].diff()
    rate = pd.Series(
        [safe_rate(dv.iloc[i], dt.iloc[i]) for i in range(len(canon))],
        index=canon.index,
    )
    valid = rate.dropna()
    out: Dict = {
        "value_column": value_col,
        "n_rates_computed": int(len(valid)),
        "n_intervals_excluded_nonpositive_or_missing": int((dt <= 0).sum() + int(dt.isna().sum())),
        "rate_min_per_min": float(valid.min()) if len(valid) else float("nan"),
        "rate_median_per_min": float(valid.median()) if len(valid) else float("nan"),
        "rate_p95_abs_per_min": float(valid.abs().quantile(0.95)) if len(valid) else float("nan"),
        "rate_p99_abs_per_min": float(valid.abs().quantile(0.99)) if len(valid) else float("nan"),
        "rate_max_per_min": float(valid.max()) if len(valid) else float("nan"),
        "rate_min_abs_per_min": float(valid.abs().min()) if len(valid) else float("nan"),
    }
    if high_predicate is not None:
        hp = high_predicate.reindex(canon.index).fillna(False)
        either = hp | hp.shift(1, fill_value=False)
        normal = rate[~either]
        out["normal_mode_n_rates"] = int(normal.notna().sum())
        out["normal_mode_p99_abs_per_min"] = (
            float(normal.abs().quantile(0.99)) if normal.notna().any() else float("nan")
        )
        out["normal_mode_max_abs_per_min"] = (
            float(normal.abs().max()) if normal.notna().any() else float("nan")
        )
        excursion = rate[either]
        out["excursion_mode_n_rates"] = int(excursion.notna().sum())
        out["excursion_mode_max_abs_per_min"] = (
            float(excursion.abs().max()) if excursion.notna().any() else float("nan")
        )
    return out


def top_rate_transitions(df: pd.DataFrame, value_col: str, n: int = 30,
                         threshold: float = 1.0) -> pd.DataFrame:
    """Rows around the largest |rate| transitions, with actual dt and both
    endpoint values plus raw line numbers for raw-line inspection."""
    from .io import canonicalize
    canon = canonicalize(df, policy="first", sort=True).reset_index(drop=True)
    dt = interval_minutes(canon[PARSED_TS_COLUMN])
    dv = canon[value_col].diff()
    rate = pd.Series(
        [safe_rate(dv.iloc[i], dt.iloc[i]) for i in range(len(canon))],
        index=canon.index,
    )
    big = rate.abs() > threshold
    rows = []
    for i in canon.index[big]:
        rows.append({
            "timestamp": str(canon.loc[i, PARSED_TS_COLUMN]),
            "prev_timestamp": str(canon.loc[i - 1, PARSED_TS_COLUMN]) if i - 1 in canon.index else "",
            "dt_minutes": float(dt.loc[i]),
            "prev_value": float(canon.loc[i - 1, value_col]) if i - 1 in canon.index else float("nan"),
            "value": float(canon.loc[i, value_col]),
            "rate_per_min": float(rate.loc[i]),
            "raw_line": int(canon.loc[i, RAW_LINE_COLUMN]),
            "prev_raw_line": int(canon.loc[i - 1, RAW_LINE_COLUMN]) if i - 1 in canon.index else -1,
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.reindex(out["rate_per_min"].abs().sort_values(ascending=False).index).head(n)


# ----------------------------------------------------------------------------
# Cross-file alignment
# ----------------------------------------------------------------------------

def cross_file_alignment(dfs: Dict[str, pd.DataFrame],
                         tolerance_minutes: float = 15.0) -> pd.DataFrame:
    """Timestamp alignment between every pair of files.

    Reports exact timestamp matches, matches within the declared tolerance
    (nearest-neighbour), and the distribution of nearest-match time deltas.
    Measurements separated by a nonzero delta are never described as
    simultaneous.
    """
    names = sorted(dfs.keys())
    ts_sets = {n: set(pd.Series(d[PARSED_TS_COLUMN].values)) for n, d in dfs.items()}
    ts_sorted = {n: np.array(sorted(ts_sets[n]), dtype="datetime64[ns]") for n in dfs}
    rows = []
    for a, b in combinations(names, 2):
        exact = len(ts_sets[a] & ts_sets[b])
        # nearest-neighbour deltas (both directions, unique pairs)
        if len(ts_sorted[a]) and len(ts_sorted[b]):
            ia = ts_sorted[a]
            ib = ts_sorted[b]
            pos_b = np.searchsorted(ib, ia, side="left")
            best = np.full(len(ia), np.timedelta64("NaT"), dtype="timedelta64[ns]")
            for k, p in enumerate(pos_b):
                cands = []
                if p < len(ib):
                    cands.append(abs(ia[k] - ib[p]))
                if p > 0:
                    cands.append(abs(ia[k] - ib[p - 1]))
                best[k] = min(cands)
            deltas_min = best.astype("timedelta64[s]").astype(float) / 60.0
            within_tol = int((deltas_min <= tolerance_minutes).sum())
            rows.append({
                "file_a": a, "file_b": b,
                "n_timestamps_a": len(ts_sets[a]), "n_timestamps_b": len(ts_sets[b]),
                "exact_matches": exact,
                f"matches_within_{tolerance_minutes:g}min": within_tol,
                "nearest_delta_min_minutes": float(np.nanmin(deltas_min)),
                "nearest_delta_median_minutes": float(np.nanmedian(deltas_min)),
                "nearest_delta_p95_minutes": float(np.nanpercentile(deltas_min, 95)),
                "nearest_delta_max_minutes": float(np.nanmax(deltas_min)),
            })
    return pd.DataFrame(rows)


def all_files_intersection(dfs: Dict[str, pd.DataFrame]) -> int:
    sets = [set(pd.Series(d[PARSED_TS_COLUMN].values)) for d in dfs.values()]
    return len(set.intersection(*sets))
