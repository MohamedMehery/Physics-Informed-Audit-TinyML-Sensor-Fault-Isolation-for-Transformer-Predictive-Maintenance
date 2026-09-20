"""Timestamp parsing utilities.

Rules enforced repository-wide:
- Timestamps are always parsed to pandas Timestamp/datetime before any
  comparison or sorting. Raw text is preserved alongside the parsed value.
- Lexicographic comparison of timestamp strings is forbidden.
- Rates always use actual per-row delta-t in minutes; division by zero,
  negative, or missing delta-t is guarded (returns NaN, never inf).
"""

from __future__ import annotations

import re
from typing import Optional

import pandas as pd

# Accepted formats: 'YYYY-MM-DDTHH:MM', 'YYYY-MM-DD HH:MM', optional ':SS'
# and optional fractional seconds. Both 'T' and ' ' separators are accepted.
_TS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?$"
)


def parse_timestamp(text: object) -> pd.Timestamp:
    """Parse a single dataset timestamp string to a pandas Timestamp.

    Accepts ISO-8601 'T' separators and space separators. Raises ValueError
    for anything else so that malformed timestamps are never silently
    coerced (and never compared as strings).
    """
    if isinstance(text, pd.Timestamp):
        return text
    if not isinstance(text, str):
        raise ValueError(f"timestamp must be a string, got {type(text).__name__}: {text!r}")
    s = text.strip()
    if not _TS_RE.match(s):
        raise ValueError(f"unrecognized timestamp format: {text!r}")
    return pd.Timestamp(s.replace("T", " ", 1))


def parse_timestamp_series(series: pd.Series) -> pd.Series:
    """Vectorised, format-validated parsing of a timestamp column."""
    return series.map(parse_timestamp)


def interval_minutes(ts: pd.Series) -> pd.Series:
    """Consecutive differences of a parsed timestamp series, in minutes.

    The input series is assumed to be in original row order; the caller
    decides whether to sort by parsed time first. The first element is NaN.
    """
    ts = pd.Series(pd.to_datetime(ts.values))
    return ts.diff().dt.total_seconds() / 60.0


def safe_rate(value_delta: float, minutes_delta: float) -> float:
    """Rate of change per minute with explicit guards.

    Returns NaN when minutes_delta is zero, negative, or NaN (duplicate or
    out-of-order timestamps, or missing interval) so that no infinite or
    misleading rate is ever produced.
    """
    try:
        dv = float(value_delta)
        dt = float(minutes_delta)
    except (TypeError, ValueError):
        return float("nan")
    if dt != dt or dt <= 0:  # NaN or non-positive interval
        return float("nan")
    return dv / dt
