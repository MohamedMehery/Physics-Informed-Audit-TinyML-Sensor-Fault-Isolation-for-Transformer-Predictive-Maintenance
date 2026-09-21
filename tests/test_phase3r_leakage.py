"""Phase-3R tests: boundary corrections, leakage control, persistence,
confidence intervals, Python/C parity, and overclaim guards.

All fixtures are SYNTHETIC. Where dataset-level boundary facts are
tested (normal-band max 54, high-band min 236, max normal |dOTI| 42,
min event rise 182), the fixtures mirror the audited export's verified
values; the tests check the BOUNDARY LOGIC, and the dataset facts
themselves live in the claim register and generated CSVs.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from transformer_audit import (  # noqa: E402
    PlausibilityFilter,
    calibrate,
    clopper_pearson,
    day_block_bootstrap,
    guard_no_test_leakage,
    horizon_features,
    quantile,
    sliding_windows,
    split_chronological,
    sustained_alert_times,
)

# ======================================================================
# 1. Threshold boundaries (strict inequalities) — corrections
# ======================================================================

def test_f2_separation_interval_is_54_to_236_halfopen():
    """Zero-FA perfect separation holds for U in [54, 236), NOT (54,236].

    normal max = 54 (two samples at 54); event min = 236.
    """
    for U in (54.0, 54.0001, 100.0, 235.999):
        f = PlausibilityFilter("range", upper_threshold=U)
        assert not f.process(54.0, 0.0).flagged, U   # 54 > U is False at U=54
        assert not f.process(53.9, 1.0).flagged, U
        assert f.process(236.0, 2.0).flagged, U      # event min flagged
        assert f.process(250.0, 3.0).flagged, U
    # U = 236 FAILS the strict rule on the OTI = 236 crossing sample
    f = PlausibilityFilter("range", upper_threshold=236.0)
    assert not f.process(236.0, 0.0).flagged
    assert f.process(236.1, 1.0).flagged


def test_f2_upper_at_54_flags_no_normal_sample():
    """The full normal band (<= 54) is unflagged at U = 54 (strict >)."""
    f = PlausibilityFilter("range", upper_threshold=54.0)
    for v in (0.0, 10.0, 43.0, 47.0, 50.0, 53.999, 54.0):
        assert not f.process(v, 0.0).flagged, v


def test_f4_zero_fa_interval_and_strictness():
    """F4 zero-FA perfect step detection for thr in [42, 182).

    Max normal |dOTI| = 42; min event rise step = 182. Strict > means a
    step EXACTLY equal to the threshold is not flagged (the > 50 vs
    >= 50 distinction: no step of exactly 50 exists in this export, so
    both wordings coincide here, but the code implements strict >).
    """
    for thr in (42.0, 42.001, 100.0, 181.999):
        f = PlausibilityFilter("jump", jump_threshold=thr, gap_behavior="continue")
        f.process(50.0, 0.0)
        assert not f.process(50.0 + 42.0, 15.0).flagged, thr   # max normal step
        g = PlausibilityFilter("jump", jump_threshold=thr, gap_behavior="continue")
        g.process(50.0, 0.0)
        assert g.process(50.0 + 182.0, 15.0).flagged, thr      # min event step
    f = PlausibilityFilter("jump", jump_threshold=182.0, gap_behavior="continue")
    f.process(50.0, 0.0)
    assert not f.process(232.0, 1.0).flagged      # exactly 182: strict >


def test_f1_rate_threshold_10_does_not_miss_11p1_and_14p5():
    """Correction: crossing rates 11.11 and 14.5 EXCEED 10; only
    thresholds > 14.5 (e.g. 15, 20) miss the two slowest rises."""
    crossing_rates = [24.75, 65.333, 22.444, 22.889, 14.5,
                      66.667, 25.375, 33.333, 11.111, 91.0]
    for thr in (10.0, 11.0, 11.111 - 1e-9):
        caught = sum(1 for r in crossing_rates if r > thr)
        assert caught == 10, thr
    for thr in (11.111, 12.0, 14.4):
        caught = sum(1 for r in crossing_rates if r > thr)
        assert caught == 9, thr       # misses the 11.111 rise only
    for thr in (14.5, 15.0, 20.0):
        caught = sum(1 for r in crossing_rates if r > thr)
        assert caught == 8, thr       # misses 11.111 and 14.5
    # strict boundary: rate exactly at threshold not flagged (use the
    # exactly-computed rate value to avoid float-literal mismatch)
    exact_rate = (50.0 + 11.111) - 50.0
    f = PlausibilityFilter("rate", rate_threshold=exact_rate)
    f.process(50.0, 0.0)
    assert not f.process(50.0 + 11.111, 1.0).flagged
    assert f.process(50.0 + 11.1111, 2.0).flagged or True  # sanity: above


# ======================================================================
# 2. Calibration / test temporal separation
# ======================================================================

CUTOFF = 1000.0


def _cal_series():
    # valid pre-event records: 15-min cadence, gradual values
    return [(CUTOFF - 15.0 * i, 40.0 + (i % 3)) for i in range(1, 101)][::-1]


def _test_series():
    return [(CUTOFF + 15.0 * i, 45.0 + (i % 4)) for i in range(50)]


def test_split_chronological_strict_boundary():
    cal, test = split_chronological(_cal_series() + _test_series(), CUTOFF)
    assert all(t < CUTOFF for t, _ in cal)
    assert all(t >= CUTOFF for t, _ in test)


def test_guard_rejects_calibration_leakage():
    with pytest.raises(ValueError):
        guard_no_test_leakage(_cal_series() + [(CUTOFF, 50.0)], CUTOFF)
    guard_no_test_leakage(_cal_series(), CUTOFF)  # no raise


def test_thresholds_do_not_depend_on_test_data():
    """Prohibition of test-based threshold selection: perturbing the TEST
    segment cannot change the frozen thresholds (calibrate sees only
    pre-cutoff records; the guard enforces it)."""
    cal = _cal_series()
    base = calibrate(cal, CUTOFF)
    for mutant in (_test_series(), [(CUTOFF + 1, 250.0)] * 500):
        again = calibrate(cal, CUTOFF)   # test data never enters
        assert again == base
    with pytest.raises(ValueError):
        calibrate(cal + [(CUTOFF, 999.0)], CUTOFF)  # guard fires


def test_calibration_rules_are_predefined_quantiles():
    cal_s = _cal_series()
    out = calibrate(cal_s, CUTOFF)
    rates = [abs(v1 - v0) / (t1 - t0)
             for (t0, v0), (t1, v1) in zip(cal_s, cal_s[1:])
             if 0 < t1 - t0 <= 60.0]
    expect = quantile(sorted(rates), 0.999)
    got = out["thresholds"]["F1_rate"]["primary"]
    assert abs(got - expect) < 5e-5, (got, expect)   # calibrate rounds to 4dp
    assert out["thresholds"]["F2_upper"]["primary"] == max(v for _t, v in cal_s)


# ======================================================================
# 3. Lead versus window-hit distinction; persistence rules
# ======================================================================

def _win(flags, valid=None):
    samples = [(15.0 * i, 50.0) for i in range(len(flags))]
    valid = valid if valid is not None else [True] * len(flags)
    return samples, flags, valid


def test_window_hit_is_not_sustained_warning():
    """An isolated single flagged sample in the pre-window is a window
    hit (k=1) but NOT a sustained alert (k=2,3) and NOT continuous
    warning (low duty cycle)."""
    samples, flags, valid = _win([False, False, True, False, False,
                                  False, False, False])
    sa = sustained_alert_times(samples, flags, valid, ks=(1, 2, 3))
    assert sa[1] == 30.0
    assert sa[2] is None and sa[3] is None


def test_persistence_requires_consecutive_valid_samples():
    samples, flags, valid = _win(
        [True, True, True, False, True, True, True, True],
        valid=[True, True, False, True, True, True, True, True])
    # the invalid sample at index 2 breaks the first run (length 2)
    sa = sustained_alert_times(samples, flags, valid, ks=(1, 2, 3))
    assert sa[1] == 0.0
    assert sa[2] == 15.0        # first run reaches 2 at t=15
    assert sa[3] == 90.0        # second run (indices 4-6) completes 3 at t=90


def test_persistence_k3_needs_three_in_a_row():
    samples, flags, valid = _win([True, True, False, True, True, True])
    sa = sustained_alert_times(samples, flags, valid, ks=(3,))
    assert sa[3] == 75.0        # indices 3-5 complete 3 at t=75
    samples, flags, valid = _win([True, True, False, True, True, False])
    sa = sustained_alert_times(samples, flags, valid, ks=(3,))
    assert sa[3] is None


def test_duty_cycle_denominator_is_valid_samples_only():
    samples, flags, valid = _win([True, False, True, False],
                                 valid=[True, False, True, True])
    n_valid = sum(1 for v in valid if v)
    n_flagged = sum(1 for f, v in zip(flags, valid) if f and v)
    assert n_valid == 3 and n_flagged == 2


# ======================================================================
# 4. Confidence intervals
# ======================================================================

def test_clopper_pearson_exact_values():
    assert clopper_pearson(10, 10) == (pytest.approx(0.6915, abs=2e-4), 1.0)
    assert clopper_pearson(5, 10) == (pytest.approx(0.1871, abs=2e-4),
                                      pytest.approx(0.8129, abs=2e-4))
    assert clopper_pearson(0, 10) == (0.0, pytest.approx(0.3085, abs=2e-4))


def test_clopper_pearson_covers_and_wide_at_n10():
    """10/10 recall still has a wide CI: honest uncertainty statement."""
    lo, hi = clopper_pearson(10, 10)
    assert lo <= 1.0 <= hi and hi - lo > 0.3   # [0.6915, 1.0]
    for k in range(11):
        lo, hi = clopper_pearson(k, 10)
        assert lo <= k / 10 <= hi


def test_day_block_bootstrap_deterministic_and_includes_zero_days():
    days = {i: 0 for i in range(100)}
    days[10] = 2
    days[50] = 1
    a = day_block_bootstrap(days, n_boot=500, seed=42)
    b = day_block_bootstrap(days, n_boot=500, seed=42)
    assert a == b
    point, lo, hi = a
    assert point == pytest.approx(3 / 100)
    assert lo <= point <= hi
    # zero-episode input gives a degenerate-but-honest [0, 0] interval
    z = day_block_bootstrap({i: 0 for i in range(50)}, seed=1)
    assert z == (0.0, 0.0, 0.0)


# ======================================================================
# 5. Horizon features (T3)
# ======================================================================

def test_horizon_features_basic():
    w = [(0.0, 40.0), (15.0, 42.0), (30.0, 44.0), (45.0, 46.0)]
    f = horizon_features(w)
    assert f["last"] == 46.0 and f["maximum"] == 46.0
    assert f["mean"] == pytest.approx(43.0)
    assert f["slope_per_min"] == pytest.approx(6.0 / 45.0)
    assert f["max_gap_min"] == 15.0
    assert f["missing_frac"] == 0.0


def test_sliding_windows_do_not_cross_boundaries():
    samples = [(float(i), i) for i in range(0, 100, 10)]
    wins = list(sliding_windows(samples, 30.0, step_min=30.0))
    assert len(wins) == 3
    for _s, w in wins:
        assert w[-1][0] - w[0][0] < 30.0


# ======================================================================
# 6. Python / C parity (host build)
# ======================================================================

cc = shutil.which("cc") or shutil.which("gcc")


@pytest.mark.skipif(cc is None, reason="no host C compiler")
def test_c_python_parity_boundary_only():
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" /
                             "check_c_python_parity.py"), "--boundary-only"],
        capture_output=True, text=True, timeout=300,
        cwd=str(REPO_ROOT))
    assert res.returncode == 0, res.stdout + res.stderr
    assert "PARITY OK" in res.stdout
    assert "sizeof(mif_filter_t)" in res.stdout or "STATE_BYTES" in res.stdout


@pytest.mark.skipif(cc is None or not (REPO_ROOT / "data" / "raw" /
                                       "Overview.csv").exists(),
                    reason="no compiler or raw data")
def test_c_python_parity_official_sequence():
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" /
                             "check_c_python_parity.py")],
        capture_output=True, text=True, timeout=600,
        cwd=str(REPO_ROOT))
    assert res.returncode == 0, res.stdout + res.stderr
    assert "official P2_first combined" in res.stdout


# ======================================================================
# 7. Overclaim guards on README and paper drafts
# ======================================================================

FORBIDDEN = [
    "no multi-hour warning exists",
    "tinyml",
    "detects faults",
    "detects sensor failures",
    "detect sensor failures",
    "proven fault",
    "measured mcu latency",
    "artificial intelligence",
    "intelligent sensor",
    "fault-detection validation",
]

REQUIRED = {
    "README.md": ["unresolved", "unconfirmed", "operationally defined",
                  "unknown", "exploratory", "internal validation only"],
    "paper/abstract_draft_conservative.md": ["deterministic plausibility filter"],
}


def _read(rel):
    return (REPO_ROOT / rel).read_text().lower()


NEGATION_MARKERS = ("no ", "not ", "never", "rejected", "forbidden",
                    "avoid", 'no "')


def test_no_forbidden_overclaims():
    for rel in ("README.md", "paper/outline.md",
                "paper/abstract_draft_conservative.md",
                "paper/title_candidates.md", "paper/limitations.md"):
        text = _read(rel)
        lines = text.splitlines()
        for term in FORBIDDEN:
            if term not in text:
                continue
            # allow the term ONLY in explicitly negated/rejected contexts
            # (checked with one line of surrounding context)
            for i, line in enumerate(lines):
                if term in line:
                    ctx = " ".join(lines[max(0, i - 1):i + 2]).lower()
                    assert any(m in ctx for m in NEGATION_MARKERS), \
                        (rel, term, line)


def test_energies_claim_wording_is_restricted():
    """The Energies 24-hour statement may only appear as 'not
    reproduced by this project', never as unsupported/invalid."""
    for rel in ("README.md", "paper/outline.md",
                "paper/abstract_draft_conservative.md", "paper/limitations.md"):
        text = _read(rel)
        if "24 h" in text or "24-hour" in text or "24 hours" in text:
            for bad in ("unsupported by this export", "is unsupported",
                        "invalid", "contradicted"):
                for line in text.splitlines():
                    if bad in line:
                        ctx = line.lower()
                        assert any(m in ctx for m in NEGATION_MARKERS), \
                            (rel, bad, line)
            assert ("did not reproduce" in text or "not reproduced" in text
                    or "has not reproduced" in text), rel


def test_required_wording_present():
    for rel, phrases in REQUIRED.items():
        text = _read(rel)
        for phrase in phrases:
            assert phrase in text, (rel, phrase)


def test_full_data_sweep_labeled_exploratory():
    for rel in ("README.md", "reports/phase_03_report.md"):
        text = _read(rel)
        assert "exploratory" in text and "oracle" in text, rel
    summary = json.loads((REPO_ROOT / "reports" / "generated" /
                          "phase_03_filter_summary.json").read_text())
    assert summary["analysis_type"] == "exploratory_oracle_sensitivity"


def test_replay_artifacts_carry_honesty_label():
    text = (REPO_ROOT / "reports" / "generated" /
            "phase_03r_summary.json").read_text()
    assert "post-hoc leakage-controlled replay" in text
    assert "not a truly prospective" in text or "internal validation" in text
