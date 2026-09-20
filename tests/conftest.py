"""Shared synthetic fixtures. Tests never depend on the Kaggle download."""

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from transformer_audit import PARSED_TS_COLUMN, RAW_LINE_COLUMN, RAW_TS_COLUMN  # noqa: E402


def make_table(rows):
    """rows: list of (timestamp_text, OTI, OTI_A, OTI_T, MOG_A, WTI)."""
    df = pd.DataFrame(
        rows,
        columns=[RAW_TS_COLUMN, "OTI", "OTI_A", "OTI_T", "MOG_A", "WTI"],
    )
    from transformer_audit.timestamps import parse_timestamp_series
    df[PARSED_TS_COLUMN] = parse_timestamp_series(df[RAW_TS_COLUMN])
    df[RAW_LINE_COLUMN] = df.index + 2
    return df


@pytest.fixture
def basic_table():
    """Regular 15-min cadence, one excursion, one duplicate (identical),
    one duplicate (conflicting)."""
    return make_table([
        ("2019-01-01T00:00", 30.0, 0.0, 0.0, 0.0, 0.0),
        ("2019-01-01T00:15", 31.0, 0.0, 0.0, 0.0, 0.0),
        ("2019-01-01T00:15", 31.0, 0.0, 0.0, 0.0, 0.0),  # identical duplicate
        ("2019-01-01T00:30", 32.0, 0.0, 0.0, 0.0, 0.0),
        ("2019-01-01T00:45", 240.0, 1.0, 1.0, 0.0, 0.0),  # excursion onset
        ("2019-01-01T01:00", 245.0, 1.0, 1.0, 0.0, 0.0),
        ("2019-01-01T01:15", 33.0, 0.0, 0.0, 0.0, 0.0),   # excursion end
        ("2019-01-01T01:15", 34.0, 0.0, 0.0, 0.0, 0.0),   # conflicting duplicate
        ("2019-01-01T01:30", 33.0, 0.0, 0.0, 0.0, 0.0),
    ])


@pytest.fixture
def tiny_raw_csv(tmp_path):
    """A tiny raw CSV file on disk for I/O + preservation tests."""
    p = tmp_path / "Overview.csv"
    p.write_text(
        "DeviceTimeStamp,OTI,WTI,ATI,OLI,OTI_A,OTI_T,MOG_A\r\n"
        "2019-01-01T00:00,30.0,0.0,25.0,100.0,0.0,0.0,0.0\r\n"
        "2019-01-01T00:15,31.0,0.0,25.0,100.0,0.0,0.0,0.0\r\n"
        "2019-01-01T00:30,32.0,0.0,25.0,100.0,0.0,0.0,0.0\r\n",
        encoding="utf-8",
    )
    return p
