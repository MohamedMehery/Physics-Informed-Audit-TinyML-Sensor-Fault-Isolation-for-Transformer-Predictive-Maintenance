"""Event construction and merge-tolerance sensitivity.

Definitions (explicit, since event counts are definition-dependent):

- A *primitive event* is a maximal contiguous run of samples with the flag
  active (== 1), where consecutive active samples may be separated by at
  most ``max_continuity_gap_minutes`` (declared per analysis). Longer gaps
  split the run into separate primitive events.

- *Merging* combines primitive events separated by an inactive interval of
  at most ``merge_tolerance_minutes``.

No single event count is ground truth: every reported count must state the
flag, the continuity gap, and the merge tolerance.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

import pandas as pd

from .io import PARSED_TS_COLUMN, canonicalize


def primitive_events(
    df: pd.DataFrame,
    flag: str,
    max_continuity_gap_minutes: float = 30.0,
) -> pd.DataFrame:
    """Contiguous runs of flag==1 respecting actual timestamps.

    Returns one row per primitive event with start, end, n_samples,
    duration, and the maximum intra-event gap actually observed.
    """
    canon = canonicalize(df, policy="first", sort=True).reset_index(drop=True)
    active = canon[flag] == 1
    events: List[Dict] = []
    run_idx: List[int] = []

    def flush(run: List[int]) -> None:
        if not run:
            return
        start = canon.loc[run[0], PARSED_TS_COLUMN]
        end = canon.loc[run[-1], PARSED_TS_COLUMN]
        sub = canon.loc[run]
        dt = sub[PARSED_TS_COLUMN].diff().dt.total_seconds() / 60.0
        events.append({
            "flag": flag,
            "start": str(start),
            "end": str(end),
            "n_samples": len(run),
            "duration_minutes": (end - start).total_seconds() / 60.0,
            "max_intra_event_gap_minutes": float(dt.max()) if len(run) > 1 else 0.0,
            "continuity_gap_definition_minutes": max_continuity_gap_minutes,
        })

    for i in range(len(canon)):
        if active.iloc[i]:
            if run_idx:
                prev_t = canon.loc[run_idx[-1], PARSED_TS_COLUMN]
                gap = (canon.loc[i, PARSED_TS_COLUMN] - prev_t).total_seconds() / 60.0
                if gap > max_continuity_gap_minutes:
                    flush(run_idx)
                    run_idx = []
            run_idx.append(i)
        else:
            flush(run_idx)
            run_idx = []
    flush(run_idx)
    return pd.DataFrame(events, columns=[
        "flag", "start", "end", "n_samples", "duration_minutes",
        "max_intra_event_gap_minutes", "continuity_gap_definition_minutes",
    ])


def merge_events(events: pd.DataFrame, merge_tolerance_minutes: float) -> pd.DataFrame:
    """Merge primitive events separated by at most the tolerance.

    Event duration after merging spans first start to last end; member
    primitive events are recorded.
    """
    if events is None or events.empty:
        return events
    ev = events.sort_values("start").reset_index(drop=True)
    merged: List[Dict] = []
    cur = None
    for _, row in ev.iterrows():
        if cur is None:
            cur = {
                "flag": row["flag"],
                "start": row["start"],
                "end": row["end"],
                "n_samples": int(row["n_samples"]),
                "n_primitive_events": 1,
                "duration_minutes": row["duration_minutes"],
                "gap_definitions": f"cont<= {row['continuity_gap_definition_minutes']}min; merge<= {merge_tolerance_minutes}min",
            }
            continue
        gap = (
            pd.Timestamp(row["start"]) - pd.Timestamp(cur["end"])
        ).total_seconds() / 60.0
        if gap <= merge_tolerance_minutes:
            cur["end"] = row["end"]
            cur["n_samples"] += int(row["n_samples"])
            cur["n_primitive_events"] += 1
            cur["duration_minutes"] = (
                pd.Timestamp(cur["end"]) - pd.Timestamp(cur["start"])
            ).total_seconds() / 60.0
        else:
            merged.append(cur)
            cur = {
                "flag": row["flag"],
                "start": row["start"],
                "end": row["end"],
                "n_samples": int(row["n_samples"]),
                "n_primitive_events": 1,
                "duration_minutes": row["duration_minutes"],
                "gap_definitions": f"cont<= {row['continuity_gap_definition_minutes']}min; merge<= {merge_tolerance_minutes}min",
            }
    if cur is not None:
        merged.append(cur)
    return pd.DataFrame(merged, columns=[
        "flag", "start", "end", "n_samples", "n_primitive_events",
        "duration_minutes", "gap_definitions",
    ])


DEFAULT_MERGE_TOLERANCES_MIN = [15.0, 30.0, 60.0, 360.0]


def event_sensitivity(
    df: pd.DataFrame,
    flags: Iterable[str],
    continuity_gaps_minutes: Iterable[float] = (15.0, 30.0),
    merge_tolerances_minutes: Iterable[float] = (0.0,) + tuple(DEFAULT_MERGE_TOLERANCES_MIN),
) -> pd.DataFrame:
    """Event counts / durations under every (flag, continuity-gap,
    merge-tolerance) combination. A merge tolerance of 0 means primitive
    events are reported unmerged."""
    rows = []
    for flag in flags:
        for gap in continuity_gaps_minutes:
            prim = primitive_events(df, flag, max_continuity_gap_minutes=gap)
            for tol in merge_tolerances_minutes:
                if tol <= 0:
                    m = prim
                    n_prim_report = len(prim)
                else:
                    m = merge_events(prim, tol)
                    n_prim_report = len(prim)
                rows.append({
                    "flag": flag,
                    "continuity_gap_minutes": gap,
                    "merge_tolerance_minutes": tol,
                    "n_primitive_events": n_prim_report,
                    "n_events_after_merge": len(m),
                    "total_active_samples": int(prim["n_samples"].sum()) if len(prim) else 0,
                    "median_event_duration_minutes": (
                        float(m["duration_minutes"].median()) if len(m) else float("nan")
                    ),
                    "max_event_duration_minutes": (
                        float(m["duration_minutes"].max()) if len(m) else float("nan")
                    ),
                })
    return pd.DataFrame(rows)
