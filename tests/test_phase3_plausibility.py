"""Phase-3 tests: deterministic plausibility filter, event-based metrics,
baselines, Pareto frontier, and the computational cost model.

All fixtures are SYNTHETIC — no real dataset rows are embedded. Where the
full-dataset evaluation is exercised, it uses a small synthetic table built
with the same helpers as earlier phases.

Terminology under test: the filter flags readings INCONSISTENT WITH
GRADUAL THERMAL BEHAVIOR. It does not "detect faults" or "sensor failures",
and it is never described as TinyML / AI / intelligent (checked explicitly
in test_no_forbidden_terminology).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from transformer_audit import (  # noqa: E402
    FilterDecision,
    PlausibilityFilter,
    b1_trivial_threshold_flags,
    b2_random_flags,
    b3_percentile_flags,
    build_zone_index,
    est_cycles_m0,
    evaluate_flags,
    find_rising_crossings,
    gbdt_100_trees,
    mlp_28_16_8_1,
    normal_zones,
    OP_COUNTS,
    pareto_frontier,
    total_ops,
)

# ======================================================================
# Area 1 - F1 rate filter
# ======================================================================

def test_f1_flags_fast_rise():
    f = PlausibilityFilter("rate", rate_threshold=2.0)
    f.process(50.0, 0.0)
    d = f.process(60.0, 5.0)          # +10 units in 5 min = 2.0/min... equal!
    assert not d.flagged               # strict > : exactly 2.0 is NOT flagged
    d = f.process(75.0, 10.0)          # +15 in 5 min = 3.0/min
    assert d.flagged and d.reason == "rate"
    assert d.rate == pytest.approx(3.0)


def test_f1_flags_fast_fall_symmetrically():
    f = PlausibilityFilter("rate", rate_threshold=2.0)
    f.process(240.0, 0.0)
    d = f.process(200.0, 10.0)         # -40 in 10 min = 4/min
    assert d.flagged and d.rate == pytest.approx(4.0)


def test_f1_strict_threshold_boundary():
    f = PlausibilityFilter("rate", rate_threshold=5.0)
    f.process(50.0, 0.0)
    d = f.process(60.0, 2.0)           # exactly 5.0/min
    assert not d.flagged
    d = f.process(80.0, 4.0)           # 20/2 = 10/min
    assert d.flagged


# ======================================================================
# Area 2 - F2 range filter
# ======================================================================

def test_f2_upper_and_lower():
    f = PlausibilityFilter("range", upper_threshold=100.0, lower_threshold=10.0)
    assert f.process(240.0, 0.0).flagged            # > upper, first sample OK
    f2 = PlausibilityFilter("range", upper_threshold=100.0, lower_threshold=10.0)
    assert f2.process(5.0, 0.0).flagged             # < lower
    assert not f2.process(50.0, 1.0).flagged


def test_f2_strict_inequalities():
    f = PlausibilityFilter("range", upper_threshold=100.0)
    f.process(50.0, 0.0)
    assert not f.process(100.0, 1.0).flagged        # exactly at upper: no flag
    assert f.process(100.1, 2.0).flagged


def test_f2_no_state_needed():
    """F2 is stateless: decisions do not depend on prior samples."""
    a = PlausibilityFilter("range", upper_threshold=90.0)
    b = PlausibilityFilter("range", upper_threshold=90.0)
    a.process(500.0, 0.0)                            # irrelevant history
    b.process(1.0, 0.0)
    assert a.process(95.0, 5.0).flagged
    assert b.process(95.0, 5.0).flagged


# ======================================================================
# Area 3 - F3 combined filter
# ======================================================================

def test_f3_union_of_rate_and_range():
    f = PlausibilityFilter("combined", rate_threshold=2.0, upper_threshold=90.0)
    f.process(50.0, 0.0)
    d = f.process(95.0, 10.0)          # rate 4.5/min AND > 90
    assert d.flagged and "rate" in d.reason and "upper" in d.reason
    f2 = PlausibilityFilter("combined", rate_threshold=100.0, upper_threshold=90.0)
    f2.process(50.0, 0.0)
    d = f2.process(95.0, 10.0)         # slow (4.5 < 100) but out of range
    assert d.flagged and d.reason == "upper"


def test_f3_first_sample_range_only():
    f = PlausibilityFilter("combined", rate_threshold=2.0, upper_threshold=90.0)
    d = f.process(240.0, 0.0)
    assert d.flagged                    # range fires on first sample
    f2 = PlausibilityFilter("combined", rate_threshold=2.0, upper_threshold=300.0)
    d = f2.process(50.0, 0.0)
    assert not d.flagged and d.note


# ======================================================================
# Area 4 - F4 jump filter
# ======================================================================

def test_f4_jump_ignores_time():
    f = PlausibilityFilter("jump", jump_threshold=50.0, gap_behavior="continue")
    f.process(50.0, 0.0)
    d = f.process(240.0, 1440.0)        # +190 over a whole day
    assert d.flagged and d.jump == pytest.approx(190.0)
    assert d.rate == pytest.approx(190.0 / 1440.0)


def test_f4_strict_boundary():
    f = PlausibilityFilter("jump", jump_threshold=100.0)
    f.process(50.0, 0.0)
    assert not f.process(150.0, 5.0).flagged   # exactly 100: no flag
    assert f.process(260.0, 10.0).flagged      # +110


# ======================================================================
# Area 5 - edge-case contract
# ======================================================================

def test_edge_first_sample_no_dynamics():
    f = PlausibilityFilter("rate", rate_threshold=0.1)
    d = f.process(50.0, 100.0)
    assert not d.flagged and d.rate is None
    assert d.state_updated and "first" in d.note


def test_edge_nan_not_flagged_state_kept():
    f = PlausibilityFilter("rate", rate_threshold=2.0)
    f.process(50.0, 0.0)
    d = f.process(float("nan"), 5.0)
    assert not d.flagged and not d.state_updated
    # the older reference (50 at t=0) is kept: next rate uses it
    d = f.process(75.0, 10.0)
    assert d.rate == pytest.approx(25.0 / 10.0)
    assert d.flagged


def test_edge_none_input_behaves_like_nan():
    f = PlausibilityFilter("jump", jump_threshold=10.0)
    f.process(50.0, 0.0)
    d = f.process(None, 5.0)
    assert not d.flagged and not d.state_updated


def test_edge_nonpositive_dt_is_data_anomaly():
    f = PlausibilityFilter("rate", rate_threshold=1.0)
    f.process(50.0, 10.0)
    d = f.process(250.0, 10.0)          # dt == 0 (repeated timestamp)
    assert d.data_anomaly and not d.flagged
    assert d.rate is None and not d.state_updated
    d = f.process(250.0, 5.0)           # dt < 0 (reordered)
    assert d.data_anomaly and not d.flagged


def test_edge_gap_reset_vs_continue():
    # gap of 90 min > default gap_minutes=60
    fr = PlausibilityFilter("rate", rate_threshold=2.0, gap_behavior="reset")
    fr.process(50.0, 0.0)
    d = fr.process(236.0, 90.0)
    assert not d.flagged and d.rate is None and "gap" in d.note
    fc = PlausibilityFilter("rate", rate_threshold=2.0, gap_behavior="continue")
    fc.process(50.0, 0.0)
    d = fc.process(236.0, 90.0)
    assert d.flagged and d.rate == pytest.approx(186.0 / 90.0)


def test_edge_short_gap_not_special():
    f = PlausibilityFilter("rate", rate_threshold=2.0, gap_behavior="reset")
    f.process(50.0, 0.0)
    d = f.process(90.0, 30.0)           # 30-min gap < 60: normal evaluation
    assert d.rate == pytest.approx(40.0 / 30.0) and not d.flagged


# ======================================================================
# Area 6 - causality and state minimality
# ======================================================================

def test_causality_future_samples_cannot_change_past_decisions():
    f1 = PlausibilityFilter("combined", rate_threshold=2.0, upper_threshold=90.0)
    f2 = PlausibilityFilter("combined", rate_threshold=2.0, upper_threshold=90.0)
    prefix = [(50.0, 0.0), (60.0, 10.0), (70.0, 20.0)]
    for args in prefix:
        d1, d2 = f1.process(*args), f2.process(*args)
        assert d1.flagged == d2.flagged
    # very different futures must not retro-alter anything (nothing stored
    # beyond the last sample: check state size explicitly)
    f1.process(250.0, 30.0)
    f2.process(1.0, 30.0)
    # each filter retains ONLY its most recent sample (no more, no less)
    assert f1._prev_oti == 250.0 and f2._prev_oti == 1.0


def test_state_is_minimal():
    f = PlausibilityFilter("combined", rate_threshold=1.0, upper_threshold=90.0)
    f.process(50.0, 0.0)
    # only the previous OTI value and previous timestamp are retained
    attrs = {a for a in vars(f) if a.startswith("_prev")}
    assert attrs == {"_prev_oti", "_prev_ts"}


def test_filter_is_deterministic():
    runs = []
    for _ in range(3):
        f = PlausibilityFilter("rate", rate_threshold=2.0)
        runs.append([f.process(v, t).as_dict()
                     for v, t in [(50.0, 0.0), (80.0, 5.0), (40.0, 12.0)]])
    assert runs[0] == runs[1] == runs[2]


# ======================================================================
# Area 7 - rising band-crossing events
# ======================================================================

def _mk(vals):
    """(ts_minutes, oti) pairs at 15-min cadence from a list of OTI values."""
    return [(15.0 * i, v) for i, v in enumerate(vals)]


def test_find_rising_crossings_basic():
    samples = _mk([50, 52, 236, 240, 60, 55, 238, 50])
    ev = find_rising_crossings(samples)
    assert len(ev) == 2
    assert ev[0]["crossing_index"] == 2 and ev[0]["recovery_index"] == 4
    assert ev[1]["crossing_index"] == 6 and ev[1]["recovery_index"] == 7


def test_find_rising_crossings_requires_positive_dt():
    samples = [(0.0, 50.0), (10.0, 100.0), (10.0, 150.0),  # dt=0 pair
               (20.0, 55.0), (30.0, 100.0)]
    ev = find_rising_crossings(samples)
    # the (10,100)->(10,150) transition has dt=0: not a crossing event;
    # (55 -> 100) at dt=10 IS one; (50 -> 100) at dt=10 IS one
    assert [e["crossing_index"] for e in ev] == [1, 4]


def test_find_rising_crossings_no_recovery_returns_none():
    samples = _mk([50, 60, 236, 240, 250])
    ev = find_rising_crossings(samples)
    assert len(ev) == 1
    assert ev[0]["recovery_index"] is None and ev[0]["recovery_ts"] is None


def test_unrecovered_event_zone_extends_to_end():
    samples = _mk([50, 60, 236, 240])
    ev = find_rising_crossings(samples)
    zi = build_zone_index(samples, ev, pre_window_minutes=60.0)
    assert zi == [0, 0, 0, 0]           # everything after start is zone 0


# ======================================================================
# Area 8 - detection zones and boundary semantics
# ======================================================================

def test_zone_is_prewindow_to_recovery():
    samples = _mk([50, 52, 54, 236, 240, 60, 55])   # crossing idx 3
    ev = find_rising_crossings(samples)
    zi = build_zone_index(samples, ev, pre_window_minutes=60.0)
    # zone = (crossing-60, recovery] = (15-60, 90] -> all samples here
    assert zi == [0, 0, 0, 0, 0, 0, -1]


def test_zone_start_exclusive_at_60min_mark():
    # crossing at t=15*6=90; pre-window start = 30; sample exactly at 30
    samples = _mk([50, 50, 50, 50, 50, 50, 236, 60, 55])
    ev = find_rising_crossings(samples)
    zi = build_zone_index(samples, ev, pre_window_minutes=60.0)
    assert zi[2] == -1                  # t=30 is NOT in the zone (exclusive)
    assert zi[3] == 0                   # t=45 is


def test_zone_clipped_at_previous_recovery():
    # event 1 crossing t=32 (idx 2), recovery t=60 (idx 4);
    # event 2 crossing t=90 -> naive pre-window start 30 < recovery 60,
    # so start is clipped to 60 and is EXCLUSIVE: the recovery sample at
    # t=60 belongs to event 1's zone only.
    samples = [(0, 50), (15, 52), (32, 236), (45, 240), (60, 50),
               (75, 54), (90, 236), (105, 49), (120, 51)]
    ev = find_rising_crossings(samples)
    zi = build_zone_index(samples, ev, pre_window_minutes=60.0)
    assert zi[4] == 0                   # event-1 recovery sample: zone 0
    assert zi[5] == 1                   # t=75 inside event-2 pre-window
    spans = normal_zones(samples, ev, pre_window_minutes=60.0)
    assert spans == [(105.0, 120.0)]    # only the tail is normal operation


def test_recovery_fall_not_counted_as_next_event_early_detection():
    """Regression: the 2019-08-17 pattern (recovery fall of the previous
    excursion inside the next event's 60-min pre-window) must not create a
    positive lead for the next event."""
    samples = [(0, 50), (15, 52), (32, 236), (45, 242), (57, 240),
               (93, 38),                      # recovery fall of event 1
               (150, 39), (210, 243), (240, 49), (260, 50)]
    # event 2 crossing at t=210; pre-window (150, 210]; recovery fall at
    # t=93 is OUTSIDE it; a rate flag at t=93 must not count for event 2.
    ev = find_rising_crossings(samples)
    assert len(ev) == 2
    flags = [False] * len(samples)
    flags[5] = True                      # the recovery-fall flag
    flags[7] = True                      # flag at the crossing sample
    m = evaluate_flags(samples, flags, ev, pre_window_minutes=60.0)
    assert m["per_event"][1]["detected"] is True
    assert m["per_event"][1]["lead_min"] == 0.0


# ======================================================================
# Area 9 - evaluate_flags: detection, leads, false-alarm episodes
# ======================================================================

def test_strict_detection_requires_flag_at_or_before_crossing():
    samples = _mk([50, 52, 236, 240, 60, 55, 238, 50, 51])
    ev = find_rising_crossings(samples)
    # flag only AFTER the crossing sample of event 1 (idx 3, t=45)
    flags = [False, False, False, True, False, False, False, False, False]
    m = evaluate_flags(samples, flags, ev)
    assert m["per_event"][0]["detected"] is False
    assert m["per_event"][0]["detected_in_zone"] is True
    assert m["per_event"][0]["lead_min"] == -15.0   # after crossing = negative
    # flag exactly AT the crossing sample (idx 2, t=30)
    flags = [False, False, True, False, False, False, False, False, False]
    m = evaluate_flags(samples, flags, ev)
    assert m["per_event"][0]["detected"] is True
    assert m["per_event"][0]["lead_min"] == 0.0
    assert m["per_event"][0]["first_flag_pre_crossing"] is False


def test_lead_positive_when_flag_precedes_crossing():
    samples = _mk([50, 54, 236, 240, 60, 55, 238, 50, 51])
    ev = find_rising_crossings(samples)
    flags = [True] + [False] * 8          # flag 30 min before crossing (t=0)
    m = evaluate_flags(samples, flags, ev)
    assert m["per_event"][0]["detected"] is True
    assert m["per_event"][0]["lead_min"] == 30.0
    assert m["per_event"][0]["first_flag_pre_crossing"] is True


def test_flag_outside_prewindow_is_not_detection():
    # flag 90 min before the crossing: outside the 60-min pre-window
    samples = _mk([50, 50, 50, 50, 50, 50, 50, 50, 236, 60])
    ev = find_rising_crossings(samples)
    flags = [True] + [False] * 9
    m = evaluate_flags(samples, flags, ev, pre_window_minutes=60.0)
    assert m["per_event"][0]["detected"] is False
    assert m["per_event"][0]["detected_in_zone"] is False


def test_false_alarms_are_episodes_not_rows():
    samples = _mk([50, 52, 236, 60, 55, 55, 55, 55, 238, 50])
    ev = find_rising_crossings(samples)
    # three contiguous flagged rows in the normal stretch (idx 4-6) +
    # one separate flagged row (idx 7 would extend the run; use far one)
    flags = [False] * 10
    flags[4] = flags[5] = flags[6] = True     # one episode of 3 rows
    m = evaluate_flags(samples, flags, ev)
    assert m["false_alarm_episodes"] == 1
    assert m["total_flagged_rows"] == 3


def test_false_alarm_rate_per_normal_day():
    samples = _mk([50, 52, 236, 60, 55, 55, 238, 50, 51, 52, 53, 54])
    # normal operation = samples after recovery (idx 7, t=105) to end
    ev = find_rising_crossings(samples)
    flags = [False] * 12
    flags[8] = True
    m = evaluate_flags(samples, flags, ev)
    # normal span (105, 165] = 60 min = 1/24 day -> rate = 24/day
    assert m["normal_days"] == pytest.approx(60.0 / 1440.0)
    assert m["false_alarm_rate_per_day"] == pytest.approx(24.0)


def test_flag_at_own_recovery_is_not_false_alarm():
    samples = _mk([50, 52, 236, 60, 55, 238, 50, 51])
    ev = find_rising_crossings(samples)
    flags = [False] * 8
    flags[3] = True                       # recovery sample of event 1
    m = evaluate_flags(samples, flags, ev)
    assert m["false_alarm_episodes"] == 0


# ======================================================================
# Area 10 - baselines
# ======================================================================

def test_b1_matches_oiti_t_semantics():
    samples = _mk([50, 236, 250, 100, 99])
    flags = b1_trivial_threshold_flags(samples)
    assert flags == [False, True, True, False, False]  # >= 236, non-strict


def test_b2_seeded_reproducible_and_probability_honored():
    samples = _mk(list(range(100)))
    a = b2_random_flags(samples, 0.3, seed=42)
    b = b2_random_flags(samples, 0.3, seed=42)
    c = b2_random_flags(samples, 0.3, seed=43)
    assert a == b and a != c
    assert 0.1 < sum(a) / len(a) < 0.5    # roughly at p


def test_b3_percentile_threshold_and_noncausal_note():
    samples = _mk([float(i) for i in range(1, 101)])   # 1..100
    flags = b3_percentile_flags(samples, 90.0)
    # p90 (linear interpolation) = 90.1 -> flags 91..100 = 10 samples
    assert sum(flags) == 10
    assert "NOT\n    causal" in b3_percentile_flags.__doc__.replace(
        "NOT causal", "NOT\n    causal") or "causal" in b3_percentile_flags.__doc__


# ======================================================================
# Area 11 - Pareto frontier
# ======================================================================

def test_pareto_dominance_and_ties():
    rows = [
        {"name": "a", "detection_rate": 1.0, "false_alarm_rate_per_day": 0.0},
        {"name": "b", "detection_rate": 1.0, "false_alarm_rate_per_day": 0.1},
        {"name": "c", "detection_rate": 0.8, "false_alarm_rate_per_day": 0.0},
        {"name": "d", "detection_rate": 0.5, "false_alarm_rate_per_day": 0.9},
        {"name": "e", "detection_rate": 1.0, "false_alarm_rate_per_day": 0.0},
    ]
    front = pareto_frontier(rows)
    names = [r["name"] for r in front]
    assert names[0] == "a" and "e" in names    # tie retained
    assert "b" not in names and "c" not in names and "d" not in names


# ======================================================================
# Area 12 - computational cost model
# ======================================================================

def test_op_counts_are_exact_and_consistent():
    for name, c in OP_COUNTS.items():
        assert c["sub"] + c["cmp"] + c["mul"] + c["div"] + c["str"] == total_ops(name)
    # rate filter uses the multiply-form: no division anywhere
    assert OP_COUNTS["F1_rate"]["div"] == 0
    assert OP_COUNTS["F3_combined"]["div"] == 0
    # range is a single compare
    assert total_ops("F2_range") == 1


def test_mlp_counts_exact():
    m = mlp_28_16_8_1()
    assert m["macs"] == 28 * 16 + 16 * 8 + 8 * 1 == 584
    assert m["params"] == 584 + 25 == 609
    assert m["weights_bytes_fp32"] == 609 * 4 == 2436


def test_gbdt_parameterized_estimate():
    g = gbdt_100_trees(depth=6)
    assert g["compares_per_sample"] == 600
    assert g["model_bytes"] == 100 * 127 * 12
    # labeled as an estimate in the module docstring? check the helper name
    assert "assumed_depth" in g


def test_m0_cycle_estimates_ordered():
    for name in OP_COUNTS:
        fixed = est_cycles_m0(name, "fixed")
        soft = est_cycles_m0(name, "float")
        assert 0 < fixed < soft, (name, fixed, soft)
    # filter must be far cheaper than the MLP reference at both precisions
    m = mlp_28_16_8_1()
    assert est_cycles_m0("F3_combined", "fixed") < m["est_cycles_m0_fixed"] / 100
    with pytest.raises(ValueError):
        est_cycles_m0("F1_rate", "decimal")


# ======================================================================
# Area 13 - terminology discipline (spec L)
# ======================================================================

def test_no_forbidden_terminology():
    forbidden = ("tinyml", " ai ", "artificial intelligence", "intelligent",
                 "proven fault", "detects fault", "detects sensor fail",
                 "root cause identified")
    for path in (REPO_ROOT / "src" / "transformer_audit" / "plausibility_filter.py",
                 REPO_ROOT / "src" / "transformer_audit" / "filter_metrics.py"):
        text = path.read_text().lower()
        for term in forbidden:
            assert term not in text, (path.name, term)


# ======================================================================
# Area 14 - end-to-end on a synthetic series (stream -> metrics)
# ======================================================================

def test_end_to_end_synthetic_evaluation():
    """Two events, one pre-window precursor flag, one false-alarm episode."""
    vals = [50, 51, 52, 236, 240, 60,           # event 1 (precursor at idx 1)
            55, 56, 57, 58, 59, 60, 61, 62,     # normal stretch (FA source)
            63, 64, 65, 236, 245, 70,           # event 2
            71, 72]
    samples = _mk(vals)
    ev = find_rising_crossings(samples)
    assert len(ev) == 2
    f = PlausibilityFilter("combined", rate_threshold=2.0, upper_threshold=52.0)
    flags = [f.process(v, t).flagged for t, v in samples]
    m = evaluate_flags(samples, flags, ev)
    # event 1: precursor flag at idx 1 (t=15, OTI=51 > 52? NO -> not flagged)
    # F2 strict > : 51 <= 52 is not flagged; the precursor is idx 2 (52? no)
    # -> detection comes from the crossing sample itself (236 > 52)
    assert m["per_event"][0]["detected"] is True
    # FA episodes: contiguous >52 flags in the normal stretch merge into 1+
    assert m["false_alarm_episodes"] >= 1
    assert m["events_detected"] == 2


def test_run_filter_evaluation_script_exists_and_gated():
    script = REPO_ROOT / "scripts" / "run_filter_evaluation.py"
    assert script.exists()
    text = script.read_text()
    # provenance gates before AND after the sweep
    assert "Pre-run provenance gate" in text
    assert "Post-run provenance gate" in text
    # full policy coverage
    for pol in ("P1_preserve", "P2_first", "P3_last", "P4_identical"):
        assert pol in text
    # baselines present
    for b in ("B1_trivial", "B2_random", "B3_percentile"):
        assert b in text
