#!/usr/bin/env python3
"""Python/C parity check for the measurement-integrity filter skeleton.

1. Compiles firmware_skeleton/mif_filter.c with a generated driver at
   -Wall -Wextra -Werror -O2 (host build; NOT a Cortex-M0 cross-build).
2. Runs hand-computed boundary self-tests inside the compiled driver
   (independent of Python).
3. Replays (a) synthetic boundary vectors and (b) the OFFICIAL replay
   sequence (P2_first policy series with the frozen leakage-controlled
   F3 thresholds) through BOTH the Python reference and the compiled C
   filter and compares every decision.

Raw files are provenance-gated before use. The C file uses double
arithmetic to match the Python reference exactly; the fixed-point
multiply-form MCU port is documented in computational_cost_comparison.csv.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from transformer_audit import (  # noqa: E402
    PARSED_TS_COLUMN, RAW_LINE_COLUMN, PlausibilityFilter, apply_policy,
    load_manifest, read_table, verify_raw_files,
)

FW = REPO_ROOT / "firmware_skeleton" / "mif_filter.c"
H = REPO_ROOT / "firmware_skeleton" / "mif_filter.h"
RAW_DIR = REPO_ROOT / "data" / "raw"
MANIFEST = REPO_ROOT / "provenance" / "dataset_manifest.json"

DRIVER = r"""
#include "mif_filter.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void selftest(void)
{
    mif_filter_t f;
    mif_decision_t d;

    /* F2 strict boundary: OTI exactly at upper is NOT flagged */
    mif_init(&f, MIF_F2_RANGE, 0, 54.0, 0, MIF_GAP_RESET);
    d = mif_process(&f, 54.0, 0.0, 1);   assert(!d.flagged);
    d = mif_process(&f, 54.0001, 1.0, 1); assert(d.flagged);
    mif_init(&f, MIF_F2_RANGE, 0, 236.0, 0, MIF_GAP_RESET);
    d = mif_process(&f, 236.0, 0.0, 1);  assert(!d.flagged); /* strict > */

    /* F1 strict boundary: rate exactly at threshold is NOT flagged */
    mif_init(&f, MIF_F1_RATE, 10.0, 0, 0, MIF_GAP_RESET);
    (void)mif_process(&f, 50.0, 0.0, 1);
    d = mif_process(&f, 60.0, 1.0, 1);   assert(!d.flagged); /* 10.0/min */
    d = mif_process(&f, 70.001, 2.0, 1); assert(d.flagged);

    /* F4 strict boundary: step exactly at threshold is NOT flagged */
    mif_init(&f, MIF_F4_JUMP, 0, 0, 182.0, MIF_GAP_RESET);
    (void)mif_process(&f, 50.0, 0.0, 1);
    d = mif_process(&f, 232.0, 1.0, 1);  assert(!d.flagged); /* +182 */
    d = mif_process(&f, 432.001, 2.0, 1); assert(d.flagged);

    /* dt == 0: data anomaly, range still evaluated, state kept */
    mif_init(&f, MIF_F3_COMBINED, 5.0, 90.0, 0, MIF_GAP_RESET);
    (void)mif_process(&f, 50.0, 10.0, 1);
    d = mif_process(&f, 250.0, 10.0, 1);
    assert(d.data_anomaly && d.flagged && !d.state_updated);
    d = mif_process(&f, 55.0, 11.0, 1);  /* rate uses kept state 50@10 */
    assert(d.rate > 4.9 && d.rate < 5.1 && !d.flagged);

    /* gap > 60 with reset: range only */
    mif_init(&f, MIF_F1_RATE, 0.5, 0, 0, MIF_GAP_RESET);
    (void)mif_process(&f, 50.0, 0.0, 1);
    d = mif_process(&f, 236.0, 90.0, 1);
    assert(!d.flagged && d.state_updated && isnan(d.rate));
    /* gap > 60 with continue: evaluated across the gap */
    mif_init(&f, MIF_F1_RATE, 0.5, 0, 0, MIF_GAP_CONTINUE);
    (void)mif_process(&f, 50.0, 0.0, 1);
    d = mif_process(&f, 236.0, 90.0, 1);
    assert(d.flagged && d.state_updated);

    /* invalid input: no flag, no state update, data anomaly */
    mif_init(&f, MIF_F4_JUMP, 0, 0, 10.0, MIF_GAP_RESET);
    (void)mif_process(&f, 50.0, 0.0, 1);
    d = mif_process(&f, 0.0, 5.0, 0);
    assert(d.data_anomaly && !d.flagged && !d.state_updated);
    d = mif_process(&f, 60.0, 5.0, 1);   /* rate vs kept 50@0 */
    assert(!d.flagged && d.jump == 10.0);/* exactly at thr: not flagged */

    (void)f; (void)d;
}

int main(int argc, char **argv)
{
    if (argc > 1 && strcmp(argv[1], "selftest") == 0) {
        selftest();
        printf("SELFTEST_OK\n");
        printf("STATE_BYTES %lu\n", (unsigned long)mif_state_bytes());
        return 0;
    }
    if (argc > 2 && strcmp(argv[1], "replay") == 0) {
        FILE *cfg = fopen(argv[2], "r");
        FILE *seq = fopen(argv[3], "r");
        int type; double rt, ut, jt; int gap;
        mif_filter_t f;
        char line[256];
        if (!cfg || !seq) { fprintf(stderr, "open failed\n"); return 2; }
        if (fscanf(cfg, "%d %lf %lf %lf %d", &type, &rt, &ut, &jt, &gap) != 5)
            { fprintf(stderr, "bad config\n"); return 2; }
        fclose(cfg);
        mif_init(&f, (mif_type_t)type, rt, ut, jt, (mif_gap_t)gap);
        while (fgets(line, sizeof line, seq)) {
            double oti, ts; int valid;
            mif_decision_t d;
            if (line[0] == '#' || line[0] == '\n') continue;
            if (sscanf(line, "%lf %lf %d", &oti, &ts, &valid) != 3) continue;
            d = mif_process(&f, oti, ts, valid);
            printf("%d %d %d %.17g %.17g\n", d.flagged, d.data_anomaly,
                   d.state_updated, d.rate, d.jump);
        }
        fclose(seq);
        printf("STATE_BYTES %lu\n", (unsigned long)mif_state_bytes());
        return 0;
    }
    fprintf(stderr, "usage: %s selftest | replay cfg seq\n", argv[0]);
    return 2;
}
"""

C_TYPE = {"rate": 1, "range": 2, "combined": 3, "jump": 4}


def py_decisions(ftype, kwargs, seq):
    f = PlausibilityFilter(ftype, **kwargs)
    out = []
    for oti, ts, valid in seq:
        if not valid:
            d = f.process(None, ts)
        else:
            d = f.process(oti, ts)
        out.append((int(d.flagged), int(d.data_anomaly),
                    int(d.state_updated),
                    None if d.rate is None else float(d.rate),
                    None if d.jump is None else float(d.jump)))
    return out


def c_decisions(binary, ftype, kwargs, seq):
    with tempfile.TemporaryDirectory() as td:
        cfg = Path(td) / "cfg.txt"
        sq = Path(td) / "seq.txt"
        gap = kwargs.get("gap_behavior", "reset")
        cfg.write_text(f"{C_TYPE[ftype]} {kwargs.get('rate_threshold', 0)} "
                       f"{kwargs.get('upper_threshold', 0)} "
                       f"{kwargs.get('jump_threshold', 0)} "
                       f"{0 if gap == 'reset' else 1}\n")
        sq.write_text("".join(f"{o!r} {t!r} {v}\n" for o, t, v in seq))
        res = subprocess.run([str(binary), "replay", str(cfg), str(sq)],
                             capture_output=True, text=True, timeout=300)
        if res.returncode != 0:
            raise RuntimeError(f"C replay failed: {res.stderr}")
    out = []
    state_bytes = None
    for line in res.stdout.strip().splitlines():
        if line.startswith("STATE_BYTES"):
            state_bytes = int(line.split()[1])
            continue
        a, b, c, r, j = line.split()
        out.append((int(a), int(b), int(c),
                    None if r == "nan" else float(r),
                    None if j == "nan" else float(j)))
    return out, state_bytes


def compare(py, c, label):
    assert len(py) == len(c), f"{label}: length mismatch"
    mism = 0
    for i, (p, q) in enumerate(zip(py, c)):
        if p[:3] != q[:3]:
            mism += 1
            print(f"  MISMATCH {label}[{i}]: flags py={p[:3]} c={q[:3]}")
        elif (p[3] is None) != (q[3] is None) or \
             (p[4] is None) != (q[4] is None):
            mism += 1
            print(f"  MISMATCH {label}[{i}]: nan-ness py={p[3:]} c={q[3:]}")
        else:
            for u, v in ((p[3], q[3]), (p[4], q[4])):
                if u is not None and math.isfinite(u):
                    if abs(u - v) > 1e-9 * max(1.0, abs(u)):
                        mism += 1
                        print(f"  MISMATCH {label}[{i}]: value {u} vs {v}")
    assert mism == 0, f"{label}: {mism} mismatches"
    print(f"[ok] {label}: {len(py)} samples, 0 mismatches")


def main() -> int:
    boundary_only = "--boundary-only" in sys.argv
    if not boundary_only:
        manifest = load_manifest(MANIFEST)
        if not verify_raw_files(manifest, RAW_DIR)["all_match"]:
            print("PROVENANCE GATE FAILED.", file=sys.stderr)
            return 2
        print("[0] Provenance gate OK")

    with tempfile.TemporaryDirectory() as td:
        driver = Path(td) / "driver.c"
        driver.write_text(DRIVER)
        binary = Path(td) / "mif_parity"
        cmd = ["cc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2",
               "-I", str(FW.parent), str(FW), str(driver),
               "-lm", "-o", str(binary)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print("COMPILE FAILED:\n" + res.stderr, file=sys.stderr)
            return 3
        print("[1] Compiled with -Wall -Wextra -Werror -O2")

        st = subprocess.run([str(binary), "selftest"], capture_output=True,
                            text=True)
        if st.returncode != 0 or "SELFTEST_OK" not in st.stdout:
            print("C SELFTEST FAILED:\n" + st.stdout + st.stderr,
                  file=sys.stderr)
            return 4
        state_bytes = int(st.stdout.split("STATE_BYTES")[1].split()[0])
        print(f"[2] C boundary self-test OK; compiled sizeof(mif_filter_t) "
              f"= {state_bytes} bytes")

        # ---- synthetic boundary vectors --------------------------------
        nan = float("nan")
        vectors = [
            (50.0, 0.0, 1), (54.0, 15.0, 1), (54.0001, 16.0, 1),
            (47.0, 30.0, 1), (236.0, 32.0, 1), (250.0, 47.0, 1),
            (48.0, 48.0, 1), (nan, 60.0, 0), (50.0, 60.0, 1),
            (250.0, 60.0, 1),          # dt == 0
            (52.0, 45.0, 1),           # dt < 0
            (50.0, 200.0, 1),          # long gap
            (236.0, 260.0, 1),
            (100.0, 261.0, 1),
            (40.0, 262.0, 1),
            (41.5, 263.5, 1),
            (nan, 270.0, 0), (nan, 280.0, 0), (42.0, 281.0, 1),
            (60.0, 340.0, 1), (244.0, 341.0, 1), (246.0, 356.0, 1),
            (44.0, 390.0, 1), (44.0, 390.0, 1), (45.0, 405.0, 1),
        ]
        for ftype, kwargs in [
                ("rate", {"rate_threshold": 10.0}),
                ("range", {"upper_threshold": 54.0}),
                ("range", {"upper_threshold": 47.0}),
                ("range", {"upper_threshold": 236.0}),
                ("combined", {"rate_threshold": 2.0,
                              "upper_threshold": 47.0}),
                ("jump", {"jump_threshold": 182.0}),
                ("jump", {"jump_threshold": 50.0})]:
            for gap in ("reset", "continue"):
                kw = dict(kwargs)
                kw["gap_behavior"] = gap
                py = py_decisions(ftype, kw, vectors)
                c, _ = c_decisions(binary, ftype, kw, vectors)
                compare(py, c, f"boundary {ftype} {gap}")

        if boundary_only:
            print("BOUNDARY-ONLY MODE: official replay sequence skipped "
                  "(no raw data needed)")
            print("PARITY OK")
            return 0

        # ---- official replay sequence ----------------------------------
        calib = json.loads(
            (REPO_ROOT / "reports" / "generated" /
             "phase_03r_calibration.json").read_text())
        thr = calib["P2_first"]["thresholds"]
        ov = read_table(RAW_DIR / "Overview.csv")
        series = apply_policy(ov, "P2_first")
        series = series.sort_values([PARSED_TS_COLUMN, RAW_LINE_COLUMN],
                                    kind="stable").reset_index(drop=True)
        seq = [(float(o), (t - pd_ts0()).total_seconds() / 60.0, 1)
               for t, o in zip(series[PARSED_TS_COLUMN], series["OTI"])]
        for ftype, kwargs in [
                ("combined", {"rate_threshold": thr["F1_rate"]["primary"],
                              "upper_threshold": thr["F2_upper"]["primary"]}),
                ("rate", {"rate_threshold": thr["F1_rate"]["primary"]}),
                ("range", {"upper_threshold": thr["F2_upper"]["primary"]}),
                ("jump", {"jump_threshold": thr["F4_jump"]["primary"]})]:
            for gap in ("reset", "continue"):
                kw = dict(kwargs)
                kw["gap_behavior"] = gap
                py = py_decisions(ftype, kw, seq)
                c, sb = c_decisions(binary, ftype, kw, seq)
                compare(py, c, f"official P2_first {ftype} {gap} "
                        f"(frozen thresholds)")
        print(f"[3] Official replay sequence: full P2_first series "
              f"({len(seq)} samples) x 4 filters x 2 gap behaviors, all "
              f"match; sizeof(mif_filter_t) = {sb} bytes")
    print("PARITY OK")
    return 0


def pd_ts0():
    import pandas as pd
    return pd.Timestamp("1970-01-01")


if __name__ == "__main__":
    raise SystemExit(main())
