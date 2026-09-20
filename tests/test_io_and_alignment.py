"""Tests 9, 11, 12: cross-file nearest-timestamp matching, raw-file
preservation, and reproducibility of summary tables."""

import pandas as pd

from conftest import make_table
from transformer_audit import (
    PARSED_TS_COLUMN, cross_file_alignment, read_table, sha256_file,
    value_distribution,
)


class TestCrossFileAlignment:
    def test_exact_and_nearest_matches(self):
        a = make_table([
            ("2019-01-01T00:00", 30.0, 0, 0, 0, 0),
            ("2019-01-01T00:15", 31.0, 0, 0, 0, 0),
        ])
        b = make_table([
            ("2019-01-01T00:00", 30.0, 0, 0, 0, 0),   # exact match
            ("2019-01-01T00:19", 31.0, 0, 0, 0, 0),   # 4 min from 00:15
        ])
        rep = cross_file_alignment({"a.csv": a, "b.csv": b}, tolerance_minutes=15.0)
        row = rep.iloc[0]
        assert row["exact_matches"] == 1
        assert row["matches_within_15min"] == 2
        assert row["nearest_delta_median_minutes"] == 2.0  # (0, 4) median
        assert row["nearest_delta_max_minutes"] == 4.0

    def test_out_of_tolerance_counted_separately(self):
        a = make_table([("2019-01-01T00:00", 30.0, 0, 0, 0, 0)])
        b = make_table([("2019-01-01T05:00", 30.0, 0, 0, 0, 0)])  # 300 min away
        rep = cross_file_alignment({"a.csv": a, "b.csv": b}, tolerance_minutes=15.0)
        row = rep.iloc[0]
        assert row["exact_matches"] == 0
        assert row["matches_within_15min"] == 0
        assert row["nearest_delta_max_minutes"] == 300.0

    def test_nonzero_delta_not_called_simultaneous(self):
        # the summary must carry the delta, never assert simultaneity
        a = make_table([("2019-01-01T00:00", 30.0, 0, 0, 0, 0)])
        b = make_table([("2019-01-01T00:10", 30.0, 0, 0, 0, 0)])
        rep = cross_file_alignment({"a.csv": a, "b.csv": b}, tolerance_minutes=15.0)
        assert rep.iloc[0]["nearest_delta_min_minutes"] == 10.0


class TestRawPreservation:
    def test_read_table_preserves_raw_text_and_lines(self, tiny_raw_csv):
        df = read_table(tiny_raw_csv)
        assert df["DeviceTimeStamp"].iloc[0] == "2019-01-01T00:00"  # exact text
        assert df["_raw_line"].tolist() == [2, 3, 4]                # file lines
        assert df["_ts"].iloc[1] == pd.Timestamp("2019-01-01 00:15")

    def test_hash_unchanged_after_reading(self, tiny_raw_csv):
        before = sha256_file(tiny_raw_csv)
        read_table(tiny_raw_csv)
        read_table(tiny_raw_csv)
        after = sha256_file(tiny_raw_csv)
        assert before == after

    def test_verify_raw_files_detects_tampering(self, tiny_raw_csv, tmp_path):
        from transformer_audit import build_manifest, verify_raw_files
        manifest = build_manifest(
            dataset_slug="x/y", dataset_title="t", dataset_owner="o",
            dataset_url="u", version=1, version_notes="", version_created="",
            license_displayed="", access_date_utc="",
            archive_path=tiny_raw_csv, extracted_dir=tmp_path,
        )
        assert verify_raw_files(manifest, tmp_path)["all_match"] is True
        tiny_raw_csv.write_text(tiny_raw_csv.read_text() + "tampered\r\n")
        report = verify_raw_files(manifest, tmp_path)
        assert report["all_match"] is False
        assert report["files"]["Overview.csv"]["status"] == "MISMATCH"


class TestReproducibility:
    def test_summary_tables_deterministic(self, basic_table):
        d1 = value_distribution(basic_table, ["OTI", "OTI_A"])
        d2 = value_distribution(basic_table, ["OTI", "OTI_A"])
        pd.testing.assert_frame_equal(d1, d2)

    def test_duplicate_report_deterministic(self, basic_table):
        from transformer_audit import duplicate_timestamp_report
        pd.testing.assert_frame_equal(
            duplicate_timestamp_report(basic_table),
            duplicate_timestamp_report(basic_table),
        )

    def test_rate_summary_deterministic(self, basic_table):
        from transformer_audit import rate_summary, top_rate_transitions
        pd.testing.assert_frame_equal(
            top_rate_transitions(basic_table, "OTI", n=10, threshold=0.5),
            top_rate_transitions(basic_table, "OTI", n=10, threshold=0.5),
        )
        assert rate_summary(basic_table, "OTI") == rate_summary(basic_table, "OTI")
