"""Phase-2 tests: repeated-record analysis, policies, latent-entity
diagnostics, and conditional-physics math.

All fixtures are SYNTHETIC — no real dataset rows are embedded.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from transformer_audit import (  # noqa: E402
    PARSED_TS_COLUMN, RAW_TS_COLUMN,
    apply_policy, apparent_time_constant_minutes, conflict_summary,
    critical_mass_kg, energy_kj, high_oti_repeated_intersection,
    multiplicity_table, neighbor_continuity_fit, occurrence_report,
    per_record_flag_consistency, policy_metrics, policy_sensitivity,
    read_table,
    repeated_group_report, repeated_timestamps_shared, required_power_kw,
    sensor_columns, tau_domain_status, tau_sensitivity,
    achievable_delta_t_units, value_band_unimodality, canonicalize,
)
from transformer_audit.timestamps import parse_timestamp


def make_table(rows, columns, tmp_path):
    """rows: list of (ts_string, *values) matching columns order."""
    df = pd.DataFrame(
        [{"DeviceTimeStamp": r[0], **dict(zip(columns, r[1:]))} for r in rows]
    )
    p = tmp_path / "fixture.csv"
    df.to_csv(p, index=False)
    return read_table(p)


OV_COLS = ["OTI", "WTI", "ATI", "OLI", "OTI_A", "OTI_T", "MOG_A"]


# --------------------------------------------------------------------------
# 1. separate synthetic devices -> NOT what this export looks like
# --------------------------------------------------------------------------
class TestSyntheticDevices:
    def test_two_devices_constant_multiplicity_two(self, tmp_path):
        # two devices reporting every interval -> every timestamp doubled
        rows = []
        for i in range(10):
            ts = f"2019-07-01T{i:02d}:00"
            rows.append((ts, 40 + i, 0, 30, 100, 0, 0, 0))
            rows.append((ts, 55 + i, 0, 30, 100, 0, 0, 0))  # second device, offset values
        df = make_table(rows, OV_COLS, tmp_path)
        m = multiplicity_table(df)
        assert m.loc[m["records_per_timestamp"] == 2, "n_timestamps"].sum() == 10
        rep = repeated_group_report(df)
        assert len(rep) == 10
        # conflicts everywhere (values differ by 15 units)
        assert rep["identical_group"].sum() == 0

    def test_real_export_is_not_two_devices(self):
        # in the real data only ~4.6% of Overview timestamps repeat
        ov = read_table(REPO_ROOT / "data" / "raw" / "Overview.csv")
        m = multiplicity_table(ov)
        frac = (m.loc[m["records_per_timestamp"] > 1, "n_timestamps"].sum()
                / m["n_timestamps"].sum())
        assert frac < 0.10  # a persistent second stream would be ~100%


# --------------------------------------------------------------------------
# 2. conflicting branches
# --------------------------------------------------------------------------
class TestConflictingBranches:
    def test_conflict_summary_flags_value_columns(self, tmp_path):
        rows = [
            ("2019-07-01T00:00", 40, 0, 30, 100, 0, 0, 0),
            ("2019-07-01T00:00", 41, 0, 30, 100, 0, 0, 0),  # OTI conflict
            ("2019-07-01T00:15", 42, 0, 30, 100, 0, 0, 0),
        ]
        df = make_table(rows, OV_COLS, tmp_path)
        s = conflict_summary(df)
        assert s["conflicting_groups"] == 1
        assert s["identical_groups"] == 0
        # the OTI column is the one that conflicts
        rep = repeated_group_report(df)
        assert "OTI" in rep["conflicting_columns"].iloc[0].split(";")

    def test_identical_repeats_not_conflicts(self, tmp_path):
        rows = [
            ("2019-07-01T00:00", 40, 0, 30, 100, 0, 0, 0),
            ("2019-07-01T00:00", 40, 0, 30, 100, 0, 0, 0),
        ]
        df = make_table(rows, OV_COLS, tmp_path)
        rep = repeated_group_report(df)
        assert len(rep) == 1 and rep["identical_group"].iloc[0]


# --------------------------------------------------------------------------
# 3. policies P1–P4
# --------------------------------------------------------------------------
class TestPolicies:
    @pytest.fixture()
    def conflict_df(self, tmp_path):
        rows = [
            ("2019-07-01T00:00", 40, 0, 30, 100, 0, 0, 0),
            ("2019-07-01T00:00", 40, 0, 30, 100, 0, 0, 0),  # exact repeat
            ("2019-07-01T00:15", 42, 0, 30, 100, 0, 0, 0),
            ("2019-07-01T00:15", 43, 0, 30, 100, 0, 0, 0),  # conflicting
        ]
        return make_table(rows, OV_COLS, tmp_path)

    def test_p1_preserves_all(self, conflict_df):
        out = apply_policy(conflict_df, "P1_preserve")
        assert len(out) == 4

    def test_p2_first(self, conflict_df):
        out = apply_policy(conflict_df, "P2_first")
        assert len(out) == 2
        oti = out.set_index(PARSED_TS_COLUMN)["OTI"]
        assert oti.iloc[0] == 40 and oti.iloc[1] == 42

    def test_p3_last(self, conflict_df):
        out = apply_policy(conflict_df, "P3_last")
        assert len(out) == 2
        oti = out.set_index(PARSED_TS_COLUMN)["OTI"]
        assert oti.iloc[0] == 40 and oti.iloc[1] == 43

    def test_p4_identical_only(self, conflict_df):
        out = apply_policy(conflict_df, "P4_identical")
        # exact-repeat group collapses to 1; conflicting group keeps both
        assert len(out) == 3

    def test_no_policy_averages_flags(self, conflict_df):
        # binary/flag columns must never be averaged by any record policy
        for p in ("P1_preserve", "P2_first", "P3_last", "P4_identical"):
            out = apply_policy(conflict_df, p)
            assert set(out["OTI_T"].unique()) <= {0, 1}, p

    def test_policy_metrics_never_invent_states(self, conflict_df):
        for pol in ("P1_preserve", "P2_first", "P3_last", "P4_identical"):
            m = policy_metrics(conflict_df, policy=pol)
            assert m["oti_t_rule_accuracy"] in (0.0, 1.0)


# --------------------------------------------------------------------------
# 4. high-OTI confined to one branch only
# --------------------------------------------------------------------------
class TestHighOtiOneBranch:
    def test_high_oti_in_single_branch_detected(self, tmp_path):
        rows = [
            ("2019-07-01T00:00", 40, 0, 30, 100, 0, 0, 0),
            ("2019-07-01T00:15", 245, 0, 30, 100, 1, 1, 0),   # branch A: high
            ("2019-07-01T00:15", 41, 0, 30, 100, 0, 0, 0),    # branch B: low
        ]
        df = make_table(rows, OV_COLS, tmp_path)
        inter = high_oti_repeated_intersection(df)
        # the high-OTI record IS in a repeated group in this synthetic case
        assert inter["n_high_oti_records_in_repeated_groups"] == 1

    def test_real_export_high_oti_never_in_repeated_groups(self):
        ov = read_table(REPO_ROOT / "data" / "raw" / "Overview.csv")
        inter = high_oti_repeated_intersection(ov, threshold=236)
        assert inter["n_high_oti_records_in_repeated_groups"] == 0
        assert inter["n_high_oti_records"] == 47

    def test_real_export_per_record_flag_rule(self):
        ov = read_table(REPO_ROOT / "data" / "raw" / "Overview.csv")
        fc = per_record_flag_consistency(ov)
        assert fc["violations"] == 0


# --------------------------------------------------------------------------
# 5. occurrence-index matching
# --------------------------------------------------------------------------
class TestOccurrenceIndex:
    def test_occurrence_report_matches_streams(self, tmp_path):
        rows = []
        for i in range(12):
            ts = f"2019-07-01T{i:02d}:00"
            rows.append((ts, 40 + i, 0, 30, 100, 0, 0, 0))
        rows.append(("2019-07-01T05:00", 45.0, 0, 30, 100, 0, 0, 0))  # k=2 blip
        df = make_table(rows, OV_COLS, tmp_path)
        occ = occurrence_report(df)
        # a single blip in an otherwise single stream is NOT a stable 2nd stream
        assert occ["share_of_timestamps_with_repeats"] < 0.5
        assert not occ["verdict_supports_stable_occurrence_streams"]

    def test_persistent_second_stream_detected(self, tmp_path):
        rows = []
        for i in range(12):
            ts = f"2019-07-01T{i:02d}:00"
            rows.append((ts, 40 + i, 0, 30, 100, 0, 0, 0))
            rows.append((ts, 60 + i, 0, 30, 100, 0, 0, 0))
        df = make_table(rows, OV_COLS, tmp_path)
        occ = occurrence_report(df)
        assert occ["share_of_timestamps_with_repeats"] > 0.9
        assert occ["max_records_per_timestamp"] == 2
        assert occ["verdict_supports_stable_occurrence_streams"]


# --------------------------------------------------------------------------
# 6. device identity unrecoverable from the published export
# --------------------------------------------------------------------------
class TestEntityUnrecoverable:
    def test_no_device_columns_in_export(self):
        ov = read_table(REPO_ROOT / "data" / "raw" / "Overview.csv")
        cols = set(ov.columns) - {RAW_TS_COLUMN, PARSED_TS_COLUMN, "raw_line"}
        assert not any(
            c.lower() in {"device", "device_id", "transformer_id", "asset_id",
                          "location", "location_id", "site", "site_id", "feeder"}
            for c in cols
        )

    def test_voltage_single_regime(self):
        cv = read_table(REPO_ROOT / "data" / "raw" / "CurrentVoltage.csv")
        vb = value_band_unimodality(cv, "VL1")
        assert vb["n_contiguous_band_clusters"] == 1


# --------------------------------------------------------------------------
# 7. conditional units: OTI is not confirmed °C anywhere in the pipeline
# --------------------------------------------------------------------------
class TestConditionalUnits:
    def test_tau_function_is_unit_agnostic(self):
        # tau math must work on raw channel values without any °C conversion
        tau = apparent_time_constant_minutes(246.0, 49.0, 36.0, 15.0)
        assert 0 < tau < 30
        # identical result when values are merely rescaled affinely? No —
        # tau is invariant to affine shifts (offset), sensitive to scale:
        tau_shift = apparent_time_constant_minutes(246.0 + 10, 49.0 + 10, 36.0 + 10, 15.0)
        assert abs(tau - tau_shift) < 1e-9  # offset-invariant

    def test_variable_semantics_has_no_confirmed_units(self):
        sem = pd.read_csv(REPO_ROOT / "reports" / "generated" / "variable_semantics.csv")
        assert (sem["confirmed_unit"] == "none").all()


# --------------------------------------------------------------------------
# 8. critical mass math
# --------------------------------------------------------------------------
class TestCriticalMass:
    def test_energy_identity(self):
        # 2 kW sustained for 60 min = 7200 kJ
        assert abs(energy_kj(2.0, 60.0) - 7200.0) < 1e-9

    def test_critical_mass_formula(self):
        # E=1000 kJ, c=2, dT=100 -> m = 5 kg
        assert abs(critical_mass_kg(1000.0, 2.0, 100.0) - 5.0) < 1e-9

    def test_required_power_roundtrip(self):
        m = required_power_kw(300.0, 1.9, 180.0, 10.0)  # returns kW... check scale
        # roundtrip: energy from that power over 10 min -> same critical mass
        E = energy_kj(m, 10.0)
        assert abs(critical_mass_kg(E, 1.9, 180.0) - 300.0) < 1e-6

    def test_achievable_delta_t_monotone_in_power(self):
        low = achievable_delta_t_units(50.0, 500.0, 2.0, 15.0)
        high = achievable_delta_t_units(500.0, 500.0, 2.0, 15.0)
        assert high > low > 0


# --------------------------------------------------------------------------
# 9–10. apparent tau + invalid log domains
# --------------------------------------------------------------------------
class TestApparentTau:
    def test_tau_positive_for_cooling(self):
        tau = apparent_time_constant_minutes(246.0, 49.0, 36.0, 15.0)
        assert tau > 0

    def test_tau_nan_when_ratio_outside_unit_interval(self):
        # T1 above T0 (heating through the fall) -> log domain invalid
        assert np.isnan(apparent_time_constant_minutes(49.0, 246.0, 36.0, 15.0))
        # ambient above T1 -> ratio < 0 -> NaN
        assert np.isnan(apparent_time_constant_minutes(246.0, 49.0, 60.0, 15.0))
        # ratio == 1 exactly -> zero information -> NaN
        assert np.isnan(apparent_time_constant_minutes(246.0, 246.0, 36.0, 15.0))
        # non-positive dt -> NaN
        assert np.isnan(apparent_time_constant_minutes(246.0, 49.0, 36.0, 0.0))

    def test_tau_domain_status_labels(self):
        assert tau_domain_status(246.0, 49.0, 36.0) == "valid"
        assert tau_domain_status(49.0, 246.0, 36.0) != "valid"


# --------------------------------------------------------------------------
# 11. sensitivity
# --------------------------------------------------------------------------
class TestSensitivity:
    def test_tau_sensitivity_spans_perturbations(self):
        s = tau_sensitivity(246.0, 49.0, 36.0, 15.0)
        assert "base" in s and "rows" in s
        assert set(s["rows"][0]) >= {"ta_offset_units", "dt_minutes", "tau_minutes", "domain_status"}
        taus = [r["tau_minutes"] for r in s["rows"] if r["domain_status"] == "valid"]
        assert len(taus) > 0
        assert max(taus) >= min(taus) > 0

    def test_policy_sensitivity_invariant_across_policies(self):
        ov = read_table(REPO_ROOT / "data" / "raw" / "Overview.csv")
        m = policy_sensitivity(ov)  # rows: P1..P4
        assert set(m["high_oti_rising_transitions"]) == {10}
        assert set(m["oti_t_rule_accuracy"]) == {1.0}
        assert set(m["policy"]) == {"P1_preserve", "P2_first", "P3_last", "P4_identical"}


# --------------------------------------------------------------------------
# 12. verifier agreement (runs the stdlib-only script)
# --------------------------------------------------------------------------
class TestVerifierAgreement:
    def test_independent_verifier_passes(self):
        r = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "independent_raw_verification.py")],
            capture_output=True, text=True, timeout=300,
        )
        assert r.returncode == 0, r.stdout + r.stderr
        assert "INDEPENDENT VERIFICATION PASSED" in r.stdout

    def test_neighbor_fit_symmetric_for_synthetic_noise(self, tmp_path):
        rows = []
        base = 40.0
        for i in range(20):
            ts = f"2019-07-01T{i:02d}:00"
            rows.append((ts, base + i, 0, 30, 100, 0, 0, 0))
        # conflicting second branch with symmetric noise around trend
        rows.append(("2019-07-01T05:00", base + 5 - 1, 0, 30, 100, 0, 0, 0))
        rows.append(("2019-07-01T06:00", base + 6 + 1, 0, 30, 100, 0, 0, 0))
        df = make_table(rows, OV_COLS, tmp_path)
        fit = neighbor_continuity_fit(df)
        assert "mean_fit_error_first_branch" in fit
        assert "mean_fit_error_last_branch" in fit
