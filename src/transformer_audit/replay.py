"""Phase 3R: leakage-controlled chronological replay for the plausibility
filter family (pure stdlib).

Purpose
-------
The Phase-3 full-dataset sweep (1,160 configurations) is an
EXPLORATORY / ORACLE sensitivity analysis: thresholds were chosen with
knowledge of the whole export (including the full-data normal maximum
54 and the event minimum 236). This module implements the repair:

1. CALIBRATION on records strictly before the first operational
   high-band crossing only, with PREDEFINED rules (quantiles / max of
   calibration-only statistics). No test data, no later maxima, no test
   metrics influence the thresholds. A guard enforces the temporal
   separation.
2. FROZEN-THRESHOLD replay on all later records without retuning.
3. Persistence-based alert logic (k = 1, 2, 3 valid samples), window
   hits vs sustained alerts, duty cycle, and row-level metrics.
4. Exact binomial (Clopper-Pearson) confidence intervals for event
   recall and a day-block bootstrap interval for false-alert rates.
5. T3 horizon exploration (1 h / 6 h / 24 h) with OTI-only causal
   summaries.

Honesty label (required on every output): this is a POST-HOC
LEAKAGE-CONTROLLED REPLAY, not a truly prospective external
validation, because the researchers have already inspected the full
dataset.
"""

from __future__ import annotations

import math
import random

from .plausibility_filter import PlausibilityFilter

# First operational high-band crossing in the export (Phase-1 excursion
# catalog; the first of the 10 rising band-crossings).
FIRST_CROSSING_ISO = "2019-07-16 13:38:00"

GAP_MINUTES = 60.0

# Predefined calibration rules. Chosen as standard tail quantiles of the
# calibration distribution BEFORE looking at replay outcomes; variants
# are reported as sensitivity only.
CAL_RULES = {
    "F1_rate": {
        "primary": ("quantile", 0.999),
        "sensitivity": [("quantile", 0.99), ("quantile", 0.9999), ("max", None)],
    },
    "F2_upper": {
        "primary": ("max", None),
        "sensitivity": [("quantile", 0.99), ("quantile", 0.999)],
    },
    "F4_jump": {
        "primary": ("quantile", 0.999),
        "sensitivity": [("quantile", 0.99), ("quantile", 0.9999), ("max", None)],
    },
    # F3 = F1(primary) OR F2(primary), each calibrated independently.
}


# ----------------------------------------------------------------------
# Calibration
# ----------------------------------------------------------------------

def split_chronological(samples, cutoff_min):
    """calibration = ts < cutoff; test = ts >= cutoff (frozen boundary)."""
    cal = [(t, v) for t, v in samples if t < cutoff_min]
    test = [(t, v) for t, v in samples if t >= cutoff_min]
    return cal, test


def guard_no_test_leakage(cal_samples, cutoff_min):
    """Raise if any calibration record is at/after the cutoff."""
    for t, _v in cal_samples:
        if t >= cutoff_min:
            raise ValueError(
                "calibration leakage: record at/after cutoff "
                f"(ts={t} >= cutoff={cutoff_min})")


def valid_pairs(cal_samples):
    """Consecutive pairs with 0 < dt <= GAP_MINUTES (predefined rule).

    Pairs spanning larger gaps are excluded from the calibration
    distribution: they do not represent gradual-behavior sampling.
    """
    rates, jumps = [], []
    for i in range(1, len(cal_samples)):
        t0, v0 = cal_samples[i - 1]
        t1, v1 = cal_samples[i]
        dt = t1 - t0
        if not (0 < dt <= GAP_MINUTES):
            continue
        if v0 != v0 or v1 != v1:  # NaN guard
            continue
        rates.append(abs(v1 - v0) / dt)
        jumps.append(abs(v1 - v0))
    return rates, jumps


def quantile(sorted_vals, p):
    """Linear-interpolation quantile of an ascending list."""
    if not sorted_vals:
        raise ValueError("empty")
    if len(sorted_vals) == 1:
        return float(sorted_vals[0])
    rank = p * (len(sorted_vals) - 1)
    lo = int(math.floor(rank))
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = rank - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


def calibrate(cal_samples, cutoff_min):
    """Apply the predefined rules; returns thresholds + calibration stats.

    The result depends ONLY on cal_samples. A guard enforces that no
    calibration record is at/after the cutoff.
    """
    guard_no_test_leakage(cal_samples, cutoff_min)
    rates, jumps = valid_pairs(cal_samples)
    rates_s, jumps_s = sorted(rates), sorted(jumps)
    oti_vals = sorted(v for _t, v in cal_samples if v == v)
    out = {"n_records": len(cal_samples), "n_valid_pairs": len(rates),
           "oti_max": oti_vals[-1] if oti_vals else None}
    thr = {}
    for name, rule in CAL_RULES.items():
        variants = {"primary": rule["primary"],
                    "sensitivity": rule["sensitivity"]}
        thr[name] = {}
        for kind, spec in [("primary", rule["primary"])] + \
                [("sensitivity:" + str(s[0]) + ("" if s[1] is None else f":{s[1]}"), s)
                 for s in rule["sensitivity"]]:
            mode, p = spec
            if name == "F1_rate":
                base = rates_s
            elif name == "F4_jump":
                base = jumps_s
            else:  # F2_upper uses OTI values
                base = oti_vals
            if mode == "max":
                val = base[-1]
            else:
                val = quantile(base, p)
            thr[name][kind] = round(float(val), 4)
    out["thresholds"] = thr
    return out


# ----------------------------------------------------------------------
# Persistence and alert logic
# ----------------------------------------------------------------------

def sustained_alert_times(samples, flags, valid, ks=(1, 2, 3)):
    """First timestamp at which a run of >= k consecutive VALID flagged
    samples completes, for each k in ks.

    valid[i] marks successfully processed samples (not NaN; dt > 0).
    Data-anomaly samples break a persistence run (they are not valid).
    Returns {k: ts or None}.
    """
    out = {}
    for k in ks:
        run = 0
        first = None
        for i in range(len(samples)):
            if flags[i] and valid[i]:
                run += 1
                if run >= k and first is None:
                    first = samples[i][0]
            else:
                run = 0
        out[k] = first
    return out


def pre_window_stats(samples, flags, valid, zone_idx, event, pre_window=60.0):
    """Window-hit / first alert / duty cycle inside one event's pre-window.

    window_hit        : any valid flagged sample inside the pre-window
    first_alert_ts    : its timestamp (None if no hit)
    duty_cycle        : flagged valid samples / valid samples in window
    NOTE: a window hit is NOT sustained warning; see persistence.
    """
    start = event["crossing_ts"] - pre_window
    prev_rec = event.get("prev_recovery_ts")
    if prev_rec is not None:
        start = max(start, prev_rec)
    n_valid = n_flagged = 0
    first = None
    for i, (ts, _v) in enumerate(samples):
        if start < ts <= event["crossing_ts"]:
            if valid[i]:
                n_valid += 1
                if flags[i]:
                    n_flagged += 1
                    if first is None:
                        first = ts
    return {"window_hit": first is not None,
            "first_alert_ts": first,
            "duty_cycle": (n_flagged / n_valid) if n_valid else float("nan"),
            "n_valid_samples": n_valid}


# ----------------------------------------------------------------------
# Confidence intervals
# ----------------------------------------------------------------------

def _binom_cdf(k, n, p):
    """P(X <= k) for X ~ Bin(n, p). Exact, pure python."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    total = 0.0
    for i in range(0, k + 1):
        total += math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i))
    return total


def clopper_pearson(k, n, alpha=0.05):
    """Exact binomial 95% CI (default) for k successes of n trials."""
    if n <= 0:
        return (float("nan"), float("nan"))
    if k == 0:
        lo = 0.0
    else:
        # lower bound: solve P(X <= k-1 | p) = 1 - alpha/2
        # (cdf is decreasing in p: cdf > target -> p too small -> raise lo)
        lo, hi_p = 0.0, 1.0
        for _ in range(200):
            mid = 0.5 * (lo + hi_p)
            if _binom_cdf(k - 1, n, mid) > 1 - alpha / 2:
                lo = mid
            else:
                hi_p = mid
    if k == n:
        hi = 1.0
    else:
        # upper bound: solve P(X <= k | p) = alpha/2
        # (cdf < target -> p too large -> lower hi)
        lo_p, hi = 0.0, 1.0
        for _ in range(200):
            mid = 0.5 * (lo_p + hi)
            if _binom_cdf(k, n, mid) < alpha / 2:
                hi = mid
            else:
                lo_p = mid
    return (round(lo, 4), round(hi, 4))


def day_block_bootstrap(episodes_per_day, n_boot=1000, seed=42,
                        alpha=0.05):
    """Percentile CI for the false-alert rate by resampling DAY BLOCKS.

    episodes_per_day: {date_or_day_index: n_episodes}. Days with zero
    episodes must be included as explicit zeros (they are resampleable).
    """
    days = sorted(episodes_per_day)
    counts = [episodes_per_day[d] for d in days]
    n = len(days)
    if n == 0:
        return (float("nan"),) * 3
    rng = random.Random(seed)
    rates = []
    for _ in range(n_boot):
        tot = sum(counts[rng.randrange(n)] for _ in range(n))
        rates.append(tot / n)
    rates.sort()
    lo = rates[int(math.floor((alpha / 2) * n_boot))]
    hi = rates[min(n_boot - 1, int(math.floor((1 - alpha / 2) * n_boot)))]
    point = sum(counts) / n
    return (round(point, 6), round(lo, 6), round(hi, 6))


# ----------------------------------------------------------------------
# T3: OTI-only causal horizon summaries (exploratory)
# ----------------------------------------------------------------------

def horizon_features(window):
    """OTI-only causal summaries over [(ts, oti), ...] inside a horizon
    window STRICTLY before onset. window must be time-ordered.

    Returns dict: last, maximum, mean, slope (endpoint), variability
    (population std), max_gap_min, missing_frac (vs 15-min cadence).
    """
    if not window:
        return None
    vals = [v for _t, v in window]
    n = len(vals)
    t0, t1 = window[0][0], window[-1][0]
    span = t1 - t0
    gaps = [window[i][0] - window[i - 1][0] for i in range(1, n)]
    max_gap = max(gaps) if gaps else 0.0
    expected = (span / 15.0) + 1 if span > 0 else 1
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / n
    slope = (vals[-1] - vals[0]) / span if span > 0 else 0.0
    return {"last": vals[-1], "maximum": max(vals), "mean": mean,
            "slope_per_min": slope, "variability": math.sqrt(var),
            "max_gap_min": max_gap,
            "missing_frac": max(0.0, 1.0 - n / expected) if span > 0 else 0.0}


def sliding_windows(samples, length_min, step_min=60.0):
    """Yield [(ts, oti)...] windows of length_min over a time-ordered
    sample list, stepping by step_min. Windows keep samples with
    start <= ts < start + length."""
    if not samples:
        return
    t0 = samples[0][0]
    t1 = samples[-1][0]
    start = t0
    while start + length_min <= t1:
        lo, hi = start, start + length_min
        w = [(t, v) for t, v in samples if lo <= t < hi]
        if w:
            yield (start, w)
        start += step_min
