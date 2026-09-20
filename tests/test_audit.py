"""Tests 3, 5, 8: duplicate timestamps, missing intervals, and
OTI/OTI_T threshold separability on synthetic data."""

import pandas as pd

from transformer_audit import (
    PARSED_TS_COLUMN, duplicate_timestamp_report, interval_summary,
    onset_counts, threshold_separability, value_gap_analysis,
)


class TestDuplicateTimestamps:
    def test_report_counts_identical_and_conflicting(self, basic_table):
        rep = duplicate_timestamp_report(basic_table)
        assert len(rep) == 2  # two duplicated timestamps
        by_ts = rep.set_index("timestamp")
        assert by_ts.loc["2019-01-01 00:15:00", "identical_group"] == True  # noqa: E712
        assert by_ts.loc["2019-01-01 01:15:00", "identical_group"] == False  # noqa: E712
        assert by_ts.loc["2019-01-01 01:15:00", "n_conflicting_columns"] == 1

    def test_duplicates_never_silently_dropped_by_report(self, basic_table):
        rep = duplicate_timestamp_report(basic_table)
        # both duplicate groups appear with their raw line numbers
        assert set(rep["n_records"]) == {2, 2}
        assert rep["raw_lines"].str.contains(",").all()

    def test_onset_policy_sensitivity(self, basic_table):
        first = onset_counts(basic_table, ["OTI_T"], policy="first")
        last = onset_counts(basic_table, ["OTI_T"], policy="last")
        assert first["onsets_0_to_1"].iloc[0] == 1
        assert last["onsets_0_to_1"].iloc[0] == 1

    def test_canonical_first_preserves_row_count_minus_dups(self, basic_table):
        from transformer_audit import canonicalize
        c = canonicalize(basic_table, policy="first")
        # 9 raw rows, 7 unique timestamps (two timestamps have 2 records each)
        assert len(c) == 7


class TestMissingIntervals:
    def test_gap_detection(self):
        ts = pd.Series(pd.to_datetime([
            "2019-01-01 00:00", "2019-01-01 00:15", "2019-01-01 00:30",
            "2019-01-02 00:30",  # 24 h gap
            "2019-01-02 00:45",
        ]))
        s = interval_summary(ts)
        assert s["max_minutes"] == 1440.0
        assert s["n_intervals_gt_60min"] == 1
        assert s["n_intervals_gt_1440min"] == 0
        assert s["median_minutes"] == 15.0

    def test_nonpositive_intervals_counted(self, basic_table):
        # canonical series has no dups; raw order does
        s_raw = interval_summary(basic_table[PARSED_TS_COLUMN].sort_values())
        assert s_raw["n_zero_intervals"] == 2

    def test_short_intervals_detected(self):
        # the real dataset contains 1-9 minute intervals; never assume 15
        ts = pd.Series(pd.to_datetime(["2019-01-01 12:39", "2019-01-01 12:41",
                                       "2019-01-01 12:44"]))
        s = interval_summary(ts)
        assert s["min_minutes"] == 2.0
        assert s["median_minutes"] == 2.5  # intervals 2 and 3 min


class TestThresholdSeparability:
    def test_perfectly_separable_synthetic(self):
        df = pd.DataFrame({
            "OTI": [30.0, 31.0, 32.0, 240.0, 245.0, 250.0],
            "OTI_T": [0, 0, 0, 1, 1, 1],
        })
        sep = threshold_separability(df, "OTI", ["OTI_T"])
        row = sep.iloc[0]
        assert row["classes_overlap"] == False  # noqa: E712
        assert row["threshold_rule_accuracy"] == 1.0
        assert row["best_threshold_direction"] == ">="

    def test_overlapping_synthetic(self):
        df = pd.DataFrame({
            "OTI": [29.0, 30.0, 31.0, 30.0, 240.0, 250.0],
            "OTI_A": [0, 0, 1, 1, 1, 1],  # active at low OTI too
        })
        sep = threshold_separability(df, "OTI", ["OTI_A"])
        row = sep.iloc[0]
        assert row["classes_overlap"] == True  # noqa: E712
        assert row["threshold_rule_accuracy"] < 1.0

    def test_value_gap_finds_empty_interval(self):
        vals = pd.Series([30.0, 31.0, 32.0, 240.0, 245.0])
        gaps = value_gap_analysis(vals, min_gap=5.0)
        biggest = gaps.iloc[0]
        assert biggest["lower_observed_value"] == 32.0
        assert biggest["upper_observed_value"] == 240.0
        assert biggest["n_values_in_between_observed"] == 0
