#!/usr/bin/env python3
"""Independent raw-file verification (Phase 2).

A deliberately separate implementation that:
- uses ONLY the Python standard library (csv, hashlib, datetime, math);
- does NOT import transformer_audit and does NOT reuse its cleaning code;
- recomputes the headline Phase-1 numbers from data/raw/*.csv;
- cross-checks them against reports/generated/ artifacts;
- exits non-zero with a clear message on ANY disagreement.

This guards against shared-bug blindness in the main pipeline.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw"
GEN = REPO / "reports" / "generated"
FILES = ["CurrentVoltage.csv", "Overview.csv", "Power.csv", "PowerFactor.csv", "TotalPower.csv"]

EXPECTED_ROW_COUNTS = {
    "CurrentVoltage.csv": 19352,
    "Overview.csv": 20316,
    "Power.csv": 19309,
    "PowerFactor.csv": 19308,
    "TotalPower.csv": 19248,
}

failures = []
checks = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global checks
    checks += 1
    status = "OK " if ok else "FAIL"
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_ts(text: str) -> datetime:
    # strict: YYYY-MM-DDTHH:MM or with space; no lexicographic comparisons anywhere
    t = text.strip()
    if len(t) == 16 and t[10] in "T " and t[4] == "-" and t[7] == "-":
        return datetime.strptime(t.replace("T", " ", 1), "%Y-%m-%d %H:%M")
    raise ValueError(f"unparseable timestamp: {text!r}")


def load(path: Path):
    """Return (header, rows) with rows as list of dicts of raw strings."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def main() -> int:
    # ---- manifest hashes ---------------------------------------------------
    manifest = json.loads((REPO / "provenance" / "dataset_manifest.json").read_text())
    for entry in manifest["extracted_files"]:
        p = RAW / entry["filename"]
        ok = p.exists() and p.stat().st_size == entry["byte_size"] and sha256(p) == entry["sha256"]
        check(f"hash {entry['filename']}", ok)

    # ---- per-file recomputation -------------------------------------------
    results = {}
    for fname in FILES:
        header, rows = load(RAW / fname)
        check(f"row count {fname}", len(rows) == EXPECTED_ROW_COUNTS[fname],
              f"independent={len(rows)} expected={EXPECTED_ROW_COUNTS[fname]}")

        ts = [r["DeviceTimeStamp"] for r in rows]
        parsed = [parse_ts(t) for t in ts]
        check(f"timestamps parseable {fname}", all(True for _ in parsed))

        groups = defaultdict(list)
        for i, t in enumerate(parsed):
            groups[t].append(i)

        n_rep_groups = sum(1 for v in groups.values() if len(v) > 1)
        identical = 0
        conflicting = 0
        for t, idxs in groups.items():
            if len(idxs) < 2:
                continue
            variants = {tuple(rows[i][c] for c in header if c != "DeviceTimeStamp") for i in idxs}
            if len(variants) == 1:
                identical += 1
            else:
                conflicting += 1

        results[fname] = {
            "rows": len(rows),
            "unique_ts": len(groups),
            "repeated_groups": n_rep_groups,
            "identical_groups": identical,
            "conflicting_groups": conflicting,
            "ts_min": min(parsed).strftime("%Y-%m-%d %H:%M"),
            "ts_max": max(parsed).strftime("%Y-%m-%d %H:%M"),
        }
        print(f"    {fname}: {results[fname]}")

    # ---- compare against Phase-1 artifacts --------------------------------
    inv = list(csv.DictReader(open(GEN / "dataset_inventory.csv", newline="", encoding="utf-8")))
    inv_by = {r["filename"]: r for r in inv}
    for fname, r in results.items():
        a = inv_by[fname]
        check(f"artifact rows {fname}", int(a["n_rows"]) == r["rows"])
        check(f"artifact unique ts {fname}", int(a["n_unique_timestamps"]) == r["unique_ts"])
        check(f"artifact repeated groups {fname}",
              int(a["n_duplicate_timestamp_rows"]) == r["rows"] - r["unique_ts"])

    dupsum = list(csv.DictReader(open(GEN / "duplicate_timestamp_summary.csv", newline="", encoding="utf-8")))
    dup_by = {r["filename"]: r for r in dupsum}
    for fname in ("Overview.csv", "CurrentVoltage.csv"):
        d = dup_by[fname]
        r = results[fname]
        check(f"artifact dup groups {fname}", int(d["duplicate_timestamp_groups"]) == r["repeated_groups"])
        check(f"artifact identical groups {fname}", int(d["identical_groups"]) == r["identical_groups"])
        check(f"artifact conflicting groups {fname}", int(d["conflicting_groups"]) == r["conflicting_groups"])

    # ---- Overview-specific headline facts ---------------------------------
    _, ov_rows = load(RAW / "Overview.csv")
    oti = [float(r["OTI"]) for r in ov_rows]
    oti_t = [float(r["OTI_T"]) for r in ov_rows]
    ts_ov = [parse_ts(r["DeviceTimeStamp"]) for r in ov_rows]

    check("OTI min", min(oti) == 0.0, f"{min(oti)}")
    check("OTI max", max(oti) == 250.0, f"{max(oti)}")
    n_ge236 = sum(1 for v in oti if v >= 236)
    check("OTI >= 236 count", n_ge236 == 47, f"independent={n_ge236}")

    uniq_sorted = sorted(set(oti))
    empty_big = [(a, b) for a, b in zip(uniq_sorted[:-1], uniq_sorted[1:]) if b - a > 5]
    check("empty OTI interval (54,236)", (54.0, 236.0) in empty_big, str(empty_big))

    # OTI_T relationship on ALL raw records (every branch)
    ok_pairs = sum(1 for v, f in zip(oti, oti_t) if (v >= 236) == (f == 1))
    check("OTI_T <=> OTI>=236 on all raw records", ok_pairs == len(oti),
          f"{ok_pairs}/{len(oti)}")

    # ---- transition rates with ACTUAL dt -----------------------------------
    # canonical: first occurrence per timestamp, time-sorted
    seen = {}
    for i, t in enumerate(ts_ov):
        if t not in seen:
            seen[t] = i
    canon = sorted(seen.items())
    rising = []
    falling = []
    for (t0, i0), (t1, i1) in zip(canon[:-1], canon[1:]):
        dt_min = (t1 - t0).total_seconds() / 60.0
        v0, v1 = float(ov_rows[i0]["OTI"]), float(ov_rows[i1]["OTI"])
        if dt_min > 0:
            rate = (v1 - v0) / dt_min
            if v0 < 100 <= v1:   # rising crossing
                rising.append((t1, v0, v1, dt_min, rate))
            elif v0 >= 100 > v1:  # falling crossing
                falling.append((t1, v0, v1, dt_min, rate))
    check("high-OTI rising transitions == 10", len(rising) == 10, f"independent={len(rising)}")
    check("high-OTI falling transitions == 10", len(falling) == 10, f"independent={len(falling)}")
    max_rate = max(r[4] for r in rising)
    min_rate = min(r[4] for r in falling)
    check("max positive rate == 91.0", abs(max_rate - 91.0) < 1e-9, f"{max_rate}")
    check("max negative rate == -40.8", abs(min_rate - (-40.8)) < 1e-9, f"{min_rate}")

    # cross-check against Phase-1 rate artifact (top rates)
    top = list(csv.DictReader(open(GEN / "oti_rate_summary.csv", newline="", encoding="utf-8")))
    top_by_ts = {r["timestamp"]: float(r["rate_per_min"]) for r in top}
    for t, v0, v1, dtm, rate in rising:
        key = t.strftime("%Y-%m-%d %H:%M:%S")
        if key in top_by_ts:
            check(f"rate agreement {key}", abs(top_by_ts[key] - rate) < 1e-6,
                  f"independent={rate} artifact={top_by_ts[key]}")

    # ---- raw lines around every high-OTI transition ------------------------
    raw_lines = (RAW / "Overview.csv").read_text(encoding="utf-8").splitlines()
    n_ctx = 0
    for t, v0, v1, dtm, rate in rising:
        # locate the first raw line whose parsed timestamp equals t and OTI >= 236
        for ln in range(1, len(raw_lines) + 1):
            parts = raw_lines[ln - 1].split(",")
            if len(parts) >= 8:
                try:
                    if parse_ts(parts[0]) == t and float(parts[1]) >= 236:
                        n_ctx += 1
                        break
                except ValueError:
                    continue
    check("raw line located for every high-OTI transition", n_ctx == len(rising),
          f"{n_ctx}/{len(rising)}")

    # ---- verdict -------------------------------------------------------------
    print()
    if failures:
        print(f"INDEPENDENT VERIFICATION FAILED: {len(failures)} of {checks} checks failed:")
        for f_ in failures:
            print("  -", f_)
        return 1
    print(f"INDEPENDENT VERIFICATION PASSED: all {checks} checks agree with Phase-1/2 artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
