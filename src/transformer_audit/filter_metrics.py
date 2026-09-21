"""Event-based evaluation metrics for plausibility filters (pure stdlib).

Phase-3 evaluation contract:

- Detection is measured on BAND-CROSSING EVENTS (rising transitions of OTI
  from below 100 to >= 100 OTI units with strictly positive dt), not rows.
- A filter DETECTS an event (strict, headline metric) if it flags at least
  one sample at or before the first OTI >= 236 sample of that event, within
  a bounded pre-crossing window (``pre_window_minutes``, default 60) so
  that unrelated earlier flags cannot count as detection.
- LEAD TIME = crossing_timestamp - first_flag_timestamp (actual timestamps,
  minutes): positive = flagged before the crossing sample; zero = at the
  crossing sample; negative = first in-zone flag only after the crossing
  (recorded, but such events are NOT counted in the headline detection
  rate; they are reported as ``detected_in_zone``).
- FALSE ALARMS are contiguous flag runs inside NORMAL operation zones
  (outside event zones), counted as EPISODES, not rows. The normal zones
  exclude the ``pre_window_minutes`` stretch immediately before each
  crossing, which belongs to the event's detection zone.
- False-alarm rate = episodes per day of normal operation (actual
  timestamps).
"""

from __future__ import annotations

import random

BAND_LOW = 100.0          # rising crossing: prev < 100 <= curr
HIGH_BAND = 236.0         # "first OTI >= 236 sample" of an event


# ----------------------------------------------------------------------
# Events
# ----------------------------------------------------------------------

def find_rising_crossings(samples):
    """Find rising band-crossing events in an ordered sample stream.

    Parameters
    ----------
    samples : sequence of (ts_minutes, oti)

    Returns
    -------
    list of dicts with keys:
        crossing_index : index of the first sample with OTI >= BAND_LOW
        crossing_ts    : its timestamp
        recovery_index : index of the first later sample with OTI < BAND_LOW
                         (None if the series ends inside the excursion)
        recovery_ts    : its timestamp (None likewise)
    """
    events = []
    n = len(samples)
    for i in range(1, n):
        ts_prev, oti_prev = samples[i - 1]
        ts_cur, oti_cur = samples[i]
        if ts_cur <= ts_prev:
            continue  # repeated/reordered timestamp: not a time transition
        if oti_prev < BAND_LOW <= oti_cur:
            events.append({"crossing_index": i, "crossing_ts": ts_cur})
    # recoveries
    for ev in events:
        rec_idx = None
        for j in range(ev["crossing_index"] + 1, n):
            ts_j, oti_j = samples[j]
            if oti_j < BAND_LOW:
                rec_idx = j
                break
        ev["recovery_index"] = rec_idx
        ev["recovery_ts"] = samples[rec_idx][0] if rec_idx is not None else None
    return events


def _detection_start(ev, prev_ev, pre_window_minutes):
    """Pre-window start, clipped at the previous event's recovery.

    Without clipping, a rate/jump flag on the recovery fall of the previous
    excursion can land inside the next event's pre-window and be miscounted
    as early detection of the next event. Clipping makes the pre-window
    consist of normal operation only.

    Zone semantics (enforced in build_zone_index, unit-tested):
    the detection zone of event k is
        (start_k, recovery_k]   -- start EXCLUSIVE, recovery INCLUSIVE --
    where start_k = max(crossing_k - pre_window, recovery_{k-1}).
    The previous event's recovery sample itself therefore belongs to the
    PREVIOUS event's zone (its recovery fall flags there, not as early
    detection of the next event).
    """
    start = ev["crossing_ts"] - pre_window_minutes
    if prev_ev is not None and prev_ev["recovery_ts"] is not None:
        start = max(start, prev_ev["recovery_ts"])
    return start


def event_zones(events, pre_window_minutes=60.0, horizon_minutes=None):
    """Detection zone [clipped pre-window start, recovery] for each event."""
    zones = []
    for k, ev in enumerate(events):
        start = _detection_start(ev, events[k - 1] if k else None,
                                 pre_window_minutes)
        end = ev["recovery_ts"]
        if end is None:
            end = float("inf") if horizon_minutes is None else horizon_minutes
        zones.append((start, end, ev))
    return zones


def normal_zones(samples, events, pre_window_minutes=60.0):
    """Normal-operation zones: timeline minus event detection zones."""
    if not samples:
        return []
    t0 = samples[0][0]
    t1 = samples[-1][0]
    spans = []
    cursor = t0
    for k, ev in enumerate(events):
        det_start = _detection_start(ev, events[k - 1] if k else None,
                                     pre_window_minutes)
        rec = ev["recovery_ts"] if ev["recovery_ts"] is not None else t1
        if det_start > cursor:
            spans.append((cursor, det_start))
        cursor = max(cursor, rec)
    if cursor < t1:
        spans.append((cursor, t1))
    return [(a, b) for a, b in spans if b > a]


# ----------------------------------------------------------------------
# Evaluation of a flag sequence
# ----------------------------------------------------------------------

def build_zone_index(samples, events, pre_window_minutes=60.0):
    """Per-sample zone membership in one sweep: O(n) after sorting boundaries.

    Returns zone_idx where zone_idx[i] = k (event-k detection zone) or -1
    (normal operation). Detection zone = [crossing - pre_window, recovery].
    """
    boundaries = []
    for k, ev in enumerate(events):
        start = _detection_start(ev, events[k - 1] if k else None,
                                 pre_window_minutes)
        boundaries.append((start, 0, k))                                    # start
        end = ev["recovery_ts"]
        if end is not None:
            boundaries.append((end, 1, k))                                  # end
    boundaries.sort()  # by time, starts before ends at equal time
    zone_idx = []
    bi = 0
    active = -1
    for ts, _oti in samples:
        while bi < len(boundaries) and boundaries[bi][0] < ts:
            _t, kind, k = boundaries[bi]
            if kind == 0:
                active = k
            else:
                if active == k:
                    active = -1
            bi += 1
        zone_idx.append(active)
    return zone_idx


def evaluate_flags(samples, flags, events, pre_window_minutes=60.0,
                   data_anomalies=None, zone_idx=None):
    """Compute event-based metrics for a parallel flag sequence.

    Returns a dict:
        per_event : list (one per event) of
                    {event_id, crossing_index, crossing_ts, detected (strict),
                     detected_in_zone, first_flag_ts, lead_min,
                     first_flag_pre_crossing}
        false_alarm_episodes : int   (contiguous flagged runs in normal zones)
        normal_days : float
        false_alarm_rate_per_day : float
        total_flagged_rows : int
        data_anomaly_rows : int
    """
    if zone_idx is None:
        zone_idx = build_zone_index(samples, events, pre_window_minutes)

    n = len(samples)
    first_flag_ts = [None] * len(events)
    first_pre_ts = [None] * len(events)
    episodes = 0
    in_episode = False
    total_flagged = 0
    for i in range(n):
        if not flags[i]:
            in_episode = False
            continue
        total_flagged += 1
        k = zone_idx[i]
        ts = samples[i][0]
        if k >= 0:
            if first_flag_ts[k] is None:
                first_flag_ts[k] = ts
            if ts <= events[k]["crossing_ts"] and first_pre_ts[k] is None:
                first_pre_ts[k] = ts
        else:
            if not in_episode:
                episodes += 1
                in_episode = True

    per_event = []
    for k, ev in enumerate(events):
        detected = first_pre_ts[k] is not None
        in_zone = first_flag_ts[k] is not None
        lead = (ev["crossing_ts"] - first_flag_ts[k]) if in_zone else None
        per_event.append({
            "event_id": k + 1,
            "crossing_index": ev["crossing_index"],
            "crossing_ts": ev["crossing_ts"],
            "detected": detected,
            "detected_in_zone": in_zone,
            "first_flag_ts": first_flag_ts[k],
            "lead_min": lead,
            "first_flag_pre_crossing": detected and first_pre_ts[k] < ev["crossing_ts"],
        })

    nspan = normal_zones(samples, events, pre_window_minutes)
    normal_days = sum((b - a) / (60.0 * 24.0) for a, b in nspan)

    leads = [p["lead_min"] for p in per_event if p["detected"]]
    return {
        "per_event": per_event,
        "events_detected": sum(1 for p in per_event if p["detected"]),
        "events_detected_in_zone": sum(1 for p in per_event if p["detected_in_zone"]),
        "lead_times_min": leads,
        "false_alarm_episodes": episodes,
        "normal_days": normal_days,
        "false_alarm_rate_per_day": (episodes / normal_days) if normal_days > 0 else float("nan"),
        "total_flagged_rows": total_flagged,
        "data_anomaly_rows": sum(1 for d in (data_anomalies or []) if d),
    }


# ----------------------------------------------------------------------
# Baselines
# ----------------------------------------------------------------------

def b1_trivial_threshold_flags(samples, threshold=HIGH_BAND):
    """B1: flag if OTI >= threshold (what OTI_T already encodes)."""
    return [oti is not None and not _isnan(oti) and oti >= threshold
            for _ts, oti in samples]


def b2_random_flags(samples, p, seed):
    """B2: flag each sample independently with probability p (seeded)."""
    rng = random.Random(seed)
    return [rng.random() < p for _ in samples]


def b3_percentile_flags(samples, percentile_x):
    """B3: flag if OTI > percentile_X of the OTI distribution.

    NOTE: the percentile is computed from the FULL series, so B3 is NOT
    causal; it is a baseline only (documented limitation).
    """
    vals = sorted(v for _ts, v in samples if v is not None and not _isnan(v))
    if not vals:
        return [False] * len(samples)
    thr = _percentile(vals, percentile_x)
    return [v is not None and not _isnan(v) and v > thr for _ts, v in samples]


def _isnan(v):
    return v != v  # True only for NaN


def _percentile(sorted_vals, pct):
    """Linear-interpolation percentile of a sorted list (0..100)."""
    if not sorted_vals:
        raise ValueError("empty")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    rank = (pct / 100.0) * (len(sorted_vals) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = rank - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


# ----------------------------------------------------------------------
# Pareto frontier
# ----------------------------------------------------------------------

def pareto_frontier(rows, det_key="detection_rate", fa_key="false_alarm_rate_per_day"):
    """Rows not dominated on (detection_rate max, false_alarm_rate min).

    A row r is dominated if some other row o satisfies
    det(o) >= det(r) and fa(o) <= fa(r) and (det(o) > det(r) or fa(o) < fa(r)).
    Ties (identical det and fa) are all retained (all non-dominated).
    """
    frontier = []
    for r in rows:
        dominated = False
        for o in rows:
            if o is r:
                continue
            if (o[det_key] >= r[det_key] and o[fa_key] <= r[fa_key]
                    and (o[det_key] > r[det_key] or o[fa_key] < r[fa_key])):
                dominated = True
                break
        if not dominated:
            frontier.append(r)
    # sort: best detection first, then lowest false alarms
    frontier.sort(key=lambda r: (-r[det_key], r[fa_key]))
    return frontier


# ----------------------------------------------------------------------
# Computational cost model (EXACT op counts; cycle counts are documented
# estimates for ARM Cortex-M0 — see computational_cost_comparison.csv)
# ----------------------------------------------------------------------

# Documented Cortex-M0 integer timings (ARMv6-M): SUB/CMP/MOV/ADD = 1 cycle,
# MULS (32x32 low) = 1 cycle, LDR/STR = 2 cycles, taken branch ~3 cycles.
# Documented typical GCC libgcc soft-float routine costs (arm-none-eabi):
# __aeabi_fsub ~50, __aeabi_fmul ~50, __aeabi_fdiv ~140, __aeabi_fcmp ~20
# cycles (ranges vary by compiler version; labeled ESTIMATE everywhere).
M0_INT_BASIC = 1
M0_INT_MUL = 1
M0_MEM = 2
M0_BRANCH_TAKEN = 3
SOFT_FLOAT = {"add": 50, "sub": 50, "mul": 50, "div": 140, "cmp": 20, "cvt": 50}

# Exact per-sample operation counts (steady state, dt>0, no gap reset).
# "mul-form" replaces the division a/dt > thr with a > thr*dt.
OP_COUNTS = {
    #                sub cmp mul div str
    "F1_rate":       {"sub": 2, "cmp": 5, "mul": 1, "div": 0, "str": 2},
    "F2_range":      {"sub": 0, "cmp": 1, "mul": 0, "div": 0, "str": 0},
    "F3_combined":   {"sub": 2, "cmp": 6, "mul": 1, "div": 0, "str": 2},
    "F4_jump":       {"sub": 2, "cmp": 5, "mul": 0, "div": 0, "str": 2},
    "B1_threshold":  {"sub": 0, "cmp": 1, "mul": 0, "div": 0, "str": 0},
}


def total_ops(name):
    c = OP_COUNTS[name]
    return sum(c.values())


def est_cycles_m0(name, arithmetic="fixed"):
    """Estimated Cortex-M0 cycles for one sample.

    fixed  : integer/fixed-point multiply-form (exact op counts priced at
             documented integer cycle counts + loads/stores/branches).
    float  : float32 software emulation (documented libgcc routine costs).
    """
    c = OP_COUNTS[name]
    if arithmetic == "fixed":
        core = (c["sub"] * M0_INT_BASIC + c["cmp"] * M0_INT_BASIC
                + c["mul"] * M0_INT_MUL + c["str"] * M0_MEM)
        loads = 4 * M0_MEM            # prev_oti, prev_ts, oti, ts
        branches = 3 * M0_BRANCH_TAKEN  # dt<=0 / gap / flag exits
        return core + loads + branches
    if arithmetic == "float":
        core = (c["sub"] * SOFT_FLOAT["sub"] + c["cmp"] * SOFT_FLOAT["cmp"]
                + c["mul"] * SOFT_FLOAT["mul"] + c["div"] * SOFT_FLOAT["div"]
                + c["str"] * M0_MEM)
        loads = 4 * M0_MEM
        branches = 3 * M0_BRANCH_TAKEN
        return core + loads + branches
    raise ValueError(arithmetic)


# Reference models for the comparison table
def mlp_28_16_8_1():
    """28-16-8-1 MLP: exact MAC/parameter counts."""
    layers = [(28, 16), (16, 8), (8, 1)]
    macs = sum(i * o for i, o in layers)
    biases = sum(o for _i, o in layers)
    params = macs + biases
    acts = 28 + 16 + 8 + 1
    return {"macs": macs, "adds": macs + biases, "params": params,
            "weights_bytes_fp32": params * 4, "activation_bytes_fp32": acts * 4,
            "acts": acts,
            "est_cycles_m0_fixed": macs * (M0_INT_MUL + M0_INT_BASIC + 2 * M0_MEM)
            + biases * M0_INT_BASIC,
            "est_cycles_m0_float": macs * (SOFT_FLOAT["mul"] + SOFT_FLOAT["add"]
                                           + 2 * M0_MEM) + biases * SOFT_FLOAT["add"]}


def gbdt_100_trees(depth=6, node_bytes=12):
    """100-tree gradient boosting (assumed depth 6, 8-12B/node): estimates.

    Storage/compare counts are ESTIMATES parameterized by depth; the MLP and
    filter counts are exact. Assumptions recorded in the cost CSV.
    """
    nodes_per_tree = 2 ** (depth + 1) - 1
    return {"trees": 100, "assumed_depth": depth,
            "compares_per_sample": 100 * depth,
            "est_cycles_m0_fixed": 100 * depth * (M0_INT_BASIC + 2 * M0_MEM),
            "model_bytes": 100 * nodes_per_tree * node_bytes}
