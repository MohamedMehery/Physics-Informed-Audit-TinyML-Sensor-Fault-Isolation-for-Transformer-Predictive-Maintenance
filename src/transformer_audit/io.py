"""File I/O that preserves raw provenance: original timestamp text,
parsed timestamps, and raw file line numbers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from .timestamps import parse_timestamp_series

RAW_TS_COLUMN = "DeviceTimeStamp"      # original text, byte-faithful
PARSED_TS_COLUMN = "_ts"               # parsed pandas Timestamp
RAW_LINE_COLUMN = "_raw_line"          # 1-based line number in the raw CSV (header = line 1)

TS_FORMAT_NOTE = (
    "Dataset timestamps use minute resolution with an ISO-8601 'T' separator "
    "(e.g. 2019-06-25T13:06). A space separator is accepted for robustness; "
    "all comparisons use parsed datetimes, never strings."
)


def read_table(path: str | Path) -> pd.DataFrame:
    """Read one dataset CSV, preserving provenance columns.

    Returns a DataFrame with:
      - all original columns (sensor columns converted to numeric, coercion
        failures counted by the caller via ``coercion_failures``);
      - DeviceTimeStamp: original text exactly as in the file;
      - _ts: parsed timestamp (format-validated);
      - _raw_line: 1-based file line number (header = line 1, first data
        row = line 2).
    Row order is the raw file order; no sorting happens here.
    """
    path = Path(path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False)
    df[RAW_LINE_COLUMN] = df.index + 2  # header on line 1
    df[PARSED_TS_COLUMN] = parse_timestamp_series(df[RAW_TS_COLUMN])
    for col in df.columns:
        if col in (RAW_TS_COLUMN, PARSED_TS_COLUMN, RAW_LINE_COLUMN):
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def coercion_failures(df: pd.DataFrame) -> Dict[str, int]:
    """Count of non-numeric sensor values coerced to NaN, per column."""
    sensor_cols = [
        c for c in df.columns
        if c not in (RAW_TS_COLUMN, PARSED_TS_COLUMN, RAW_LINE_COLUMN)
    ]
    return {c: int(df[c].isna().sum()) for c in sensor_cols if df[c].isna().any()}


def sensor_columns(df: pd.DataFrame) -> list[str]:
    return [
        c for c in df.columns
        if c not in (RAW_TS_COLUMN, PARSED_TS_COLUMN, RAW_LINE_COLUMN)
    ]


def canonicalize(
    df: pd.DataFrame,
    policy: str = "first",
    sort: bool = True,
) -> pd.DataFrame:
    """Reduce duplicate timestamps to one canonical record per timestamp.

    Policies:
      - 'first': keep the first raw-line occurrence (default);
      - 'last': keep the last raw-line occurrence;
      - 'mean': mean of numeric sensor values across the group
        (flags rounded to the group mean, reported as a fractional value).

    The duplicate analysis (duplicate_timestamp_report) must be run and
    reported BEFORE any canonicalization is used for downstream statistics.
    """
    if policy not in ("first", "last", "mean"):
        raise ValueError(f"unknown duplicate policy: {policy}")
    df = df.copy()
    if sort:
        df = df.sort_values(PARSED_TS_COLUMN, kind="stable")
    if policy in ("first", "last"):
        keep = "first" if policy == "first" else "last"
        return df.drop_duplicates(subset=[PARSED_TS_COLUMN], keep=keep).reset_index(drop=True)
    # mean policy
    cols = sensor_columns(df)
    agg = {c: "mean" for c in cols}
    agg[RAW_TS_COLUMN] = "first"
    agg[RAW_LINE_COLUMN] = "min"
    out = df.groupby(PARSED_TS_COLUMN, as_index=False).agg(agg)
    return out
