# Phase 3R Report — Leakage-Controlled Evaluation and Claim Correction

Repair phase for the Phase-3 plausibility-filter work (commit `cddb031`).
No new research phase; no Phase-1/2 source research repeated; raw-data
hashes and provenance gates preserved (verified before and after every
run). Everything below is reproducible from this repository.

Required standing labels: **entity identity remains unresolved; the OTI
engineering unit is unconfirmed; events are operationally defined from
the export; the hardware root cause is unknown; the full-data sweep is
exploratory; the frozen-threshold replay is internal validation only.**

---

## 1. Scope and method

Independent re-inspection of the Phase-3 code and artifacts (not the
handoff wording) produced `reports/phase_03_acceptance_review.md`
(verdicts PASS/PARTIAL/FAIL per original criterion, with ten documented
errors). This report implements the repairs: strict-inequality
corrections with automated boundary tests; relabeling of the
1,160-configuration sweep as an **exploratory / oracle sensitivity
analysis**; a **leakage-controlled chronological replay** with frozen
thresholds; T1/T2/T3 task separation; horizon analysis at 1/6/24 h;
persistence/duty-cycle alert semantics; event- and row-level metrics
with confidence intervals; a compiling C skeleton with Python/C parity;
and the paper package.

## 2. Boundary corrections (verified against code and data)

- **F2 (rule `OTI > U`, strict):** perfect separation from the normal
  maximum (54 OTI units, 2 samples) and the event minimum (236) holds
  for **U ∈ [54, 236)** — not "(54, 236]" as originally written: at
  U = 236 the strict rule does not flag the OTI = 236 crossing sample
  (the oracle sweep itself recorded 9/10 there).
- **F4 (rule `|ΔOTI| > thr`, strict):** zero-FA perfect step detection
  for **thr ∈ [42, 182)** (max normal |ΔOTI| = 42, second 34; min event
  rise = 182, min fall magnitude 196). No step equals 50, so "jump
  > 50" and "jump ≥ 50" coincide on this export — the distinction is
  now explicit and boundary-tested.
- **F1 rate and the "10 misses 11.1/14.5" statement:** the ten
  crossing-sample rates are [24.75, 65.33, 22.44, 22.89, 14.5, 66.67,
  25.375, 33.33, 11.111, 91.0]. Rate > 10 flags **10/10** (11.1 and
  14.5 both exceed 10); only thresholds **> 14.5** (swept 15, 20) miss
  the two slowest rises. The original handoff statement was factually
  wrong; the original report §4 was correct.
- Automated boundary tests: `tests/test_phase3r_leakage.py` §1 (F2
  interval endpoints, F4 interval, exact-threshold non-flagging, rate
  boundary) plus C-side asserts in the parity driver.

## 3. Exploratory / oracle sensitivity analysis (relabeled)

`scripts/run_filter_evaluation.py` and its artifacts are unchanged in
numbers but relabeled everywhere (script docstring, generated
`phase_03_filter_summary.json` field `analysis_type` =
`exploratory_oracle_sensitivity`, `phase_03_report.md` banner and
section titles, README, old handoff). The sweep selected thresholds
with knowledge of the full dataset (normal max 54, event min 236) and
must not be presented as held-out detector validation. Its verified
boundary facts (separation intervals) remain true within that label.

## 4. Leakage-controlled chronological replay (primary result)

**Calibration** (`src/transformer_audit/replay.py`,
`scripts/run_leakage_replay.py`): records strictly before the first
operational high-band crossing (2019-07-16 13:38). Predefined rules —
F1 rate = calibration q99.9 of |ΔOTI|/dt over valid pairs (0 < dt ≤
60 min); F2 upper = calibration max OTI; F4 jump = calibration q99.9
of |ΔOTI|; F3 = F1 OR F2, independently calibrated. Guards reject any
calibration record at/after the cutoff; tests verify thresholds cannot
depend on test data. Primary calibration includes **all** valid
pre-event records; the alarm-excluded variant (last 60 min removed) is
reported as sensitivity only.

Frozen thresholds (per view): F1 = 13.4545 (P1/P3/P4) / **24.936
(P2_first)**; F2 = **47.0** (all views); F4 = 30.0–33.0. Calibration
facts: 1,649–2,167 records; calibration normal max **47** vs full-data
normal max **54** — the oracle interval [54, 236) is not reachable from
calibration data alone, which is precisely the leakage the sweep
contained. Alarm-excluded sensitivity: F2 max drops to 45.0.

**Replay** (all later records, no retuning; the filter runs
continuously across the boundary so the first event is testable):
post-hoc leakage-controlled replay — internal validation only, not
truly prospective external validation, because the researchers had
already inspected the full dataset.

| filter (frozen) | events detected | event recall, exact 95% CI | row P / R / F1 | FA episodes/day, bootstrap 95% CI | mean delay (min) |
|---|---|---|---|---|---|
| F2 range (U = 47) | 10/10 | 1.00 [0.69, 1.00] | 0.187 / 1.000 / 0.315 | 0.260 [0.181, 0.343] | −11.0 |
| F3 combined | 10/10 | 1.00 [0.69, 1.00] | 0.187 / 1.000 / 0.314 | 0.260 [0.181, 0.343] | −11.0 |
| F4 jump (q99.9) | 10/10 | 1.00 [0.69, 1.00] | 0.500 / 0.213 / 0.298 | 0.0 [0, 0] | 0.0 |
| F1 rate (q99.9, P1/P3/P4) | 9/10 | 0.90 [0.60, 0.998] | 0.692 / 0.192 / 0.300 | 0.0 [0, 0] | 0.0 |
| F1 rate (q99.9, P2_first) | 5/10 | 0.50 [0.19, 0.81] | 0.833 / 0.106 / 0.189 | 0.0 [0, 0] | 23.5* |

\* delay = first in-zone flag − crossing, averaged over events with any
in-zone flag (missed events are caught only by recovery-fall flags).
Row-level ground truth: OTI ≥ 100 rows (47). F4's low row recall is
definitional — it flags transitions (10 crossing rows), not plateau
states. **10/10 recall at n = 10 remains widely uncertain (CI
[0.69, 1.00]).** Denominators (P2 view): 17,624 monitored normal-zone
rows, 103 excluded event-zone rows, 204 normal day-blocks; flagged
samples/test-day: 0.02 (F1) to 0.92 (F2).

**View sensitivity (item 6):** F2/F3/F4 detection is invariant across
P1–P4; **F1 is view-dependent** (9/10 vs 5/10) because P2_first's
calibration rate distribution yields a higher q99.9 (24.94 vs 13.45).
Reset vs continue gap behavior: **identical results everywhere**.

## 5. T1 / T2 / T3 task separation (item 7)

- **T1 — same-sample rule equivalence:** OTI ≥ 236 ⟺ OTI_T = 1 holds
  for every retained record under all views (Phase-2 C30); F2 with
  U ∈ [54, 236) is the same-sample rule family. This is rule
  equivalence, **not prediction**.
- **T2 — operationally defined integrity-event concordance:** event
  labels are derived from OTI band crossings in the export. Reported
  detector-label concordance (§4) is concordance with those operational
  labels. **No field-confirmed sensor-fault labels exist**, so nothing
  here is validated physical-fault detection.
- **T3 — causal early-warning exploration:** restricted to the tested
  variable (OTI only), rules, and horizons; see §6. **No multivariate
  early-warning conclusion is possible** — no other channel was
  evaluated in T3.

## 6. T3 horizons (1 h / 6 h / 24 h; item 8)

OTI-only causal summaries per event window (strictly pre-onset), each
compared one-sided to the calibration q99 (sliding 60-min-step
reference windows; exploratory, no multiple-comparison correction):

| horizon | last | maximum | mean | slope | variability | max-gap | missing-frac |
|---|---|---|---|---|---|---|---|
| 1 h — event windows flagged (of 10) | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| 1 h — normal-window flag rate | 3.3% | 3.6% | 3.5% | 0 | 0 | 0.2% | 0.1% |
| 6 h — event windows flagged | 5 | **8** | 5 | 0 | 2 | 0 | 0 |
| 6 h — normal-window flag rate | 3.5% | 11.6% | 6.2% | 0 | 0 | 0.6% | 0.5% |
| 24 h — event windows flagged | 7 | **9** | 3 | 0 | 4 | 0 | 0 |
| 24 h — normal-window flag rate | 6.8% | **32.0%** | 1.0% | 0 | 0 | 0.1% | 0.1% |

Reading: elevated-normal-band maxima (calibration q99 ≈ 43–44) appear
in most pre-event windows, but also in 12–32% of normal windows at 6–24
h — low specificity; slope, variability, and sampling-gap indicators
flag **zero** event windows at every horizon. Conclusion (allowed
wording): **the tested OTI-only deterministic rules did not demonstrate
robust multi-hour warning.** The Energies 24-hour statement: **Phase 3
did not reproduce that claim** — its exact features, task, split, and
evaluation were not reproduced either; no judgment on its validity is
made.

## 7. Lead-time evaluation corrected (item 9)

Per-event reporting separates: window hit; first alert timestamp;
sustained alert at persistence k = 1, 2, 3 valid samples; detection at
crossing; detection after crossing; pre-window duty cycle
(`phase_03r_per_event.csv`). An isolated earlier false alarm is a
window hit only — never continuous warning. Frozen F2 (P2 view): 3 of
10 events have **sustained (k = 3) pre-crossing alerts** (leads −20,
−48, −42 min; duty cycles 0.67, 1.00, 0.86 — continuous elevated
values, not isolated flags); the other 7 are flagged at the crossing
sample (k = 1; k = 2 completes one sample later). Frozen F4: all 10 at
crossing, k = 1 only. Frozen F1 (P2): 5 at crossing; k ≥ 2 never
sustained before crossing.

## 8. Firmware verification (item 11)

- `firmware_skeleton/mif_filter.h` / `mif_filter.c`: C99, no dynamic
  allocation, mirrors the Python reference exactly (strict
  inequalities; first-sample/NaN/dt ≤ 0/gap contract; range rule
  active only for F2/F3 — a bug caught by the C self-test and fixed).
- `scripts/check_c_python_parity.py`: compiles with
  `cc -std=c99 -Wall -Wextra -Werror -O2` (host gcc 14.2; **not** a
  Cortex-M0 cross-build), runs hand-computed boundary self-tests, then
  replays synthetic boundary vectors (7 filter configs × 2 gap
  behaviors) and the **official replay sequence** (full 19,376-sample
  P2_first series × 4 filters × 2 gap behaviors): **0 mismatches**.
- State measured, not estimated: compiled **sizeof(mif_filter_t) =
  72 bytes** (host double-precision reference; a fixed-point port
  would be smaller; documented).
- Cycle counts remain **illustrative** estimates from documented
  instruction-timing tables; no Cortex-M0 cross-compiler or board was
  used, so nothing is called measured MCU latency.
- MLP/GBDT comparisons moved out of headline results: they are
  hypothetical reference architectures (exact MAC/parameter counts;
  assumed GBDT depth 6, 12 B/node — no trained models, no compilation),
  kept in `computational_cost_comparison.csv` with assumption labels.

## 9. Paper package (item 12)

`paper/outline.md` (evidence map, T1/T2/T3, replay-primary framing),
`paper/abstract_draft_conservative.md` (two lengths; "deterministic
plausibility filter"; no TinyML; no validated-fault-detection claim),
`paper/title_candidates.md`, `paper/figures_tables_inventory.md`,
`paper/limitations.md` (13 numbered limitations incl. all six required
statements). `docs/paper_outline.md` now points to the package.

## 10. README, registers, tests (items 13–15)

README rewritten (Phase-3R section with the six required wordings;
exploratory labeling; corrected Energies wording). Claim register:
C38/C39 corrected in place; C44–C48 added. Assumption register:
A33–A37 added. New tests (`tests/test_phase3r_leakage.py`, 24 tests):
boundaries; calibration/test separation; test-based threshold-selection
prohibition; window-hit vs sustained; persistence; Clopper-Pearson
exact values and coverage; day-block bootstrap determinism; C/Python
parity (boundary-only without raw data; full sequence with raw data);
overclaim scans of README and paper drafts (forbidden phrases; Energies
wording; required wording; exploratory labels; honesty labels).

**Full suite: 137 passed** (113 prior + 24 new), 0 failed. Provenance
gates pass before and after every script run; raw files byte-preserved
and gitignored.

## Remaining blockers

None for Phase-3R scope. Open items: outreach stored, not sent;
paper's related-work sweep [NEEDS WORK]; no external dataset for
external validity; n = 10 events bounds all event-level certainty.
