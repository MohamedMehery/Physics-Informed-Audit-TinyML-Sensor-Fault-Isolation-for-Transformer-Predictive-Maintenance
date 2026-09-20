"""Electrical context: apparent-power cross-checks and excursion context.

Caution (repository rule): measured kW/kVA is *operating load*, never a
nameplate rating. For unbalanced three-phase data the per-phase sum
sum(V_phase * I_phase) and the approximation sqrt(3) * V_LL * mean(I) can
disagree; both are computed and compared against the dataset's reported
total KVA. All formula limitations are documented in the outputs.
"""

from __future__ import annotations

from typing import Dict, Optional

import numpy as np
import pandas as pd

from .io import PARSED_TS_COLUMN, canonicalize

FORMULA_NOTES = (
    "per_phase_sum = VL1*IL1 + VL2*IL2 + VL3*IL3 (valid for per-phase "
    "magnitudes, ignores phase-angle differences); "
    "sqrt3_approx = sqrt(3) * mean(VL12,VL23,VL31) * mean(IL1,IL2,IL3) "
    "(assumes balanced sinusoidal three-phase; biased under unbalance); "
    "both compared to reported KVA column."
)


def apparent_power_estimates(cv_row: Dict | pd.Series) -> Dict[str, float]:
    """Two independent apparent-power estimates (kVA) from one
    CurrentVoltage record. Returns NaN when inputs are missing/zero."""
    def f(col):
        v = cv_row.get(col, np.nan)
        try:
            v = float(v)
        except (TypeError, ValueError):
            return np.nan
        return v

    vl = [f("VL1"), f("VL2"), f("VL3")]
    il = [f("IL1"), f("IL2"), f("IL3")]
    vll = [f("VL12"), f("VL23"), f("VL31")]

    per_phase = sum(v * i for v, i in zip(vl, il))
    vll_mean = np.nanmean(vll) if not all(np.isnan(x) for x in vll) else np.nan
    il_mean = np.nanmean(il) if not all(np.isnan(x) for x in il) else np.nan
    sqrt3 = np.sqrt(3.0) * vll_mean * il_mean
    return {
        "per_phase_sum_kva": per_phase / 1000.0,
        "sqrt3_approx_kva": sqrt3 / 1000.0,
    }


def power_approximation_errors(cv: pd.DataFrame, tp: pd.DataFrame) -> Dict:
    """Compare both estimates against reported KVA (TotalPower) on exactly
    matching canonical timestamps, nonzero voltage and KVA only."""
    a = canonicalize(cv, policy="first", sort=True)
    b = canonicalize(tp, policy="first", sort=True)
    m = pd.merge(a, b, on=PARSED_TS_COLUMN, suffixes=("_cv", "_tp"))
    m = m[(m["VL12"] > 0) & (m["KVA"] > 0)]
    if m.empty:
        return {"n_compared": 0}
    est = m.apply(lambda r: pd.Series(apparent_power_estimates(r)), axis=1)
    err_pp = (est["per_phase_sum_kva"] - m["KVA"]).abs() / m["KVA"] * 100.0
    err_s3 = (est["sqrt3_approx_kva"] - m["KVA"]).abs() / m["KVA"] * 100.0
    return {
        "n_compared": int(len(m)),
        "per_phase_sum_median_abs_err_pct": float(err_pp.median()),
        "per_phase_sum_p95_abs_err_pct": float(err_pp.quantile(0.95)),
        "sqrt3_median_abs_err_pct": float(err_s3.median()),
        "sqrt3_p95_abs_err_pct": float(err_s3.quantile(0.95)),
        "notes": FORMULA_NOTES,
    }


def excursion_electrical_context(
    excursion_times: list,
    cv: pd.DataFrame,
    tp: pd.DataFrame,
    pf: Optional[pd.DataFrame] = None,
    window_minutes: int = 30,
) -> pd.DataFrame:
    """Electrical channel context around OTI excursion onset timestamps.

    For each onset time: nearest CurrentVoltage / TotalPower rows within the
    window, their time deltas, and the observed ranges of voltage, current,
    kW, kVA. Neutral wording only: this describes what is visible in the
    available channels at the dataset's temporal resolution.
    """
    a = canonicalize(cv, policy="first", sort=True)
    b = canonicalize(tp, policy="first", sort=True)
    rows = []
    win = pd.Timedelta(minutes=window_minutes)
    for t in excursion_times:
        t = pd.Timestamp(t)
        wcv = a[(a[PARSED_TS_COLUMN] >= t - win) & (a[PARSED_TS_COLUMN] <= t + win)]
        wtp = b[(b[PARSED_TS_COLUMN] >= t - win) & (b[PARSED_TS_COLUMN] <= t + win)]
        cv_delta = (
            (wcv[PARSED_TS_COLUMN] - t).abs().min().total_seconds() / 60.0
            if len(wcv) else np.nan
        )
        tp_delta = (
            (wtp[PARSED_TS_COLUMN] - t).abs().min().total_seconds() / 60.0
            if len(wtp) else np.nan
        )
        rows.append({
            "excursion_onset": str(t),
            "window_minutes": window_minutes,
            "n_cv_rows_in_window": int(len(wcv)),
            "nearest_cv_delta_minutes": float(cv_delta) if cv_delta == cv_delta else np.nan,
            "n_tp_rows_in_window": int(len(wtp)),
            "nearest_tp_delta_minutes": float(tp_delta) if tp_delta == tp_delta else np.nan,
            "VL1_min": float(wcv["VL1"].min()) if len(wcv) else np.nan,
            "VL1_max": float(wcv["VL1"].max()) if len(wcv) else np.nan,
            "VL12_min": float(wcv["VL12"].min()) if len(wcv) else np.nan,
            "VL12_max": float(wcv["VL12"].max()) if len(wcv) else np.nan,
            "IL1_min": float(wcv["IL1"].min()) if len(wcv) else np.nan,
            "IL1_max": float(wcv["IL1"].max()) if len(wcv) else np.nan,
            "IL2_max": float(wcv["IL2"].max()) if len(wcv) else np.nan,
            "IL3_max": float(wcv["IL3"].max()) if len(wcv) else np.nan,
            "KW_min": float(wtp["KW"].min()) if len(wtp) else np.nan,
            "KW_max": float(wtp["KW"].max()) if len(wtp) else np.nan,
            "KVA_min": float(wtp["KVA"].min()) if len(wtp) else np.nan,
            "KVA_max": float(wtp["KVA"].max()) if len(wtp) else np.nan,
        })
    return pd.DataFrame(rows)
