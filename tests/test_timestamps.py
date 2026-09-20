"""Tests 1, 2, 4, 10: timestamp parsing (T vs space), delta-t rates,
zero/negative deltas, division-by-zero guards."""

import pandas as pd
import pytest

from transformer_audit.timestamps import interval_minutes, parse_timestamp, safe_rate


class TestTimestampParsing:
    def test_t_separator(self):
        assert parse_timestamp("2019-06-25T13:06") == pd.Timestamp("2019-06-25 13:06")

    def test_space_separator(self):
        assert parse_timestamp("2019-06-25 13:06") == pd.Timestamp("2019-06-25 13:06")

    def test_space_and_t_are_equal(self):
        assert parse_timestamp("2019-06-25 13:06") == parse_timestamp("2019-06-25T13:06")

    def test_with_seconds(self):
        assert parse_timestamp("2019-06-25T13:06:30") == pd.Timestamp("2019-06-25 13:06:30")

    def test_rejects_garbage(self):
        for bad in ("not-a-time", "13:06", "2019-06-25", "2019-13-45T99:99", ""):
            with pytest.raises(ValueError):
                parse_timestamp(bad)

    def test_rejects_non_string(self):
        with pytest.raises(ValueError):
            parse_timestamp(20190625)


class TestRatesWithActualDeltaT:
    def test_rate_uses_actual_dt(self):
        # 10 units over 5 minutes -> 2.0 per minute
        assert safe_rate(10.0, 5.0) == 2.0

    def test_rate_over_2_minutes(self):
        # the dataset's real excursion: +182 over 2 min -> 91/min
        assert safe_rate(236.0 - 54.0, 2.0) == 91.0

    def test_zero_dt_returns_nan_not_inf(self):
        r = safe_rate(100.0, 0.0)
        assert r != r  # NaN

    def test_negative_dt_returns_nan(self):
        r = safe_rate(100.0, -15.0)
        assert r != r

    def test_nan_dt_returns_nan(self):
        r = safe_rate(100.0, float("nan"))
        assert r != r

    def test_interval_minutes_values(self):
        ts = pd.Series(pd.to_datetime(["2019-01-01 00:00", "2019-01-01 00:15",
                                       "2019-01-01 00:18"]))
        dt = interval_minutes(ts)
        assert dt.iloc[1] == 15.0
        assert dt.iloc[2] == 3.0  # NOT rounded to 15

    def test_nonuniform_dt_not_assumed_15(self):
        # a 3-minute gap must produce a 3-minute interval (real dataset behavior)
        ts = pd.Series(pd.to_datetime(["2019-06-25T13:06", "2019-06-25T13:09"]))
        assert interval_minutes(ts).iloc[1] == 3.0
