# Phase 3R Handoff — Leakage-Controlled Evaluation and Claim Correction

## 1. Status

**COMPLETE.** Phase 3 repaired at every point raised: boundary
corrections verified against code, oracle sweep relabeled, frozen-
threshold chronological replay added, T1/T2/T3 separated, horizons
1/6/24 h analyzed, persistence/duty-cycle semantics added, CIs added,
C skeleton with parity added, paper package created, registers/README
corrected. No new research phase; raw hashes and provenance gates
preserved (verified before/after every run).

## 2. Commit hash

Phase-3R content commit: `79e06e6` (this handoff's hash line is a
follow-up commit). Prior Phase-3 commits `cddb031`, `ffa60e2`.

## 3. Errors found in the old Phase-3 handoff

1. "F1 > 10/min misses the two slowest rises (11.1, 14.5)" — FALSE;
   both exceed 10 (rate > 10 → 10/10). Only thresholds > 14.5 miss them.
2. F2 separation interval "(54, 236]" — wrong endpoint; correct
   **[54, 236)** (at U = 236 the strict rule misses the OTI = 236
   crossing sample; the sweep itself showed 9/10 there).
3. "F4 jump threshold ≥ 50" conflated sweep value with rule strictness;
   rule is |ΔOTI| > thr, zero-FA interval **[42, 182)**; no step equals
   50, so > and ≥ coincide on this export.
4. "No multi-hour early warning exists in this export" — overclaim;
   corrected to tested-rules scope.
5. Energies §10 "marked not supported by this export" — overclaim;
   corrected to "Phase 3 did not reproduce that claim."
6. Leads counted pre-window hits without persistence/duty-cycle
   qualification.
7. All headline detection numbers came from full-data threshold
   selection (leakage).
8. "Transliterable to C" asserted with no C code; state bytes
   theoretical only.
9. No confidence intervals (10/10 at n = 10) and no row-level
   precision/recall/F1.

Full list: `reports/phase_03_acceptance_review.md`.

## 4. Frozen calibration rules and thresholds

Calibration = records strictly before 2019-07-16 13:38 (first
high-band crossing); predefined rules only: F1 = calibration q99.9 of
|ΔOTI|/dt (valid pairs, 0 < dt ≤ 60 min); F2 = calibration max OTI;
F4 = calibration q99.9 of |ΔOTI|; F3 = F1 OR F2. Guards + tests
prohibit test-data influence; alarm-excluded calibration reported as
sensitivity only (F2 max 47 → 45).

Frozen: F1 = 13.4545 (P1/P3/P4), **24.936 (P2_first)**; F2 = **47.0**;
F4 = 30.0–33.0. Calibration normal max 47 vs full-data 54 — the
leakage the oracle sweep contained.

## 5. Held-out chronological replay metrics (primary result)

Post-hoc leakage-controlled replay (internal validation only; not
prospective external validation), all later records, no retuning:

- **F2 range (U=47): 10/10 events**, row P/R/F1 = 0.187/1.000/0.315,
  FA 0.260 episodes/day [0.181, 0.343], mean delay −11 min (3 events
  sustained-before at −20/−48/−42 min, duty 0.67–1.00; 7 at crossing).
- **F4 jump: 10/10**, row P/R/F1 = 0.500/0.213/0.298 (flags
  transitions, not plateau), FA 0.0.
- **F3 combined: 10/10**, FA 0.260/day.
- **F1 rate: 9/10 (P1/P3/P4); 5/10 (P2_first)** — view-dependent.
- Denominators (P2): 17,624 monitored normal-zone rows vs 103 excluded
  event-zone rows; 204 normal day-blocks.

## 6. Oracle-sweep metrics (clearly separated)

The 1,160-configuration full-data sweep is retained but relabeled
**exploratory/oracle sensitivity analysis** everywhere (script, JSON
field `analysis_type`, reports, README). Verified boundary facts
within that label: F2 separation [54, 236); F4 [42, 182); F1 > 10 →
10/10. Not held-out validation; not comparable to §5 numbers (its
thresholds used full-data knowledge).

## 7. T1/T2/T3 conclusions

- **T1:** OTI ⟺ OTI_T same-sample rule equivalence (all views) — rule
  equivalence, not prediction.
- **T2:** detector-label concordance with operationally defined
  band-crossing events. **No field-confirmed sensor-fault labels
  exist**; no validated physical-fault detection is claimed.
- **T3:** the tested OTI-only deterministic rules did not demonstrate
  robust multi-hour warning (slope/variability/gap features flagged
  0/10 event windows at 1/6/24 h; elevated-max features flagged 5–9/10
  but 12–32% of normal windows — low specificity). **No multivariate
  early-warning conclusion is possible** (only OTI evaluated). The
  Energies 24-hour claim: Phase 3 did not reproduce it (its features,
  task, split, and evaluation were not reproduced either).

## 8. Confidence intervals

Exact binomial (Clopper-Pearson) 95% CI on event recall: 10/10 →
[0.6915, 1.00]; 9/10 → [0.555, 0.9975]; 5/10 → [0.187, 0.813].
Day-block bootstrap (1000 resamples, seed 42) on FA rate: F2 0.260
[0.181, 0.343]; zero-episode filters give degenerate [0, 0] (204
day-blocks; bootstrap cannot exclude small rates). **10/10 at n = 10
remains widely uncertain.**

## 9. View sensitivity

F2/F3/F4 detection invariant across P1–P4; **F1 view-dependent**
(9/10 vs 5/10; P2_first calibration yields q99.9 = 24.94 vs 13.45).
Reset vs continue gap behavior: identical everywhere.

## 10. C implementation / parity status

`firmware_skeleton/mif_filter.{h,c}` compiles at
-std=c99 -Wall -Wextra -Werror -O2 (host gcc 14.2; no Cortex-M0
cross-compiler or board used). C self-test asserts hand-computed
boundaries. Parity vs Python: boundary vectors (7 configs × 2 gaps)
and the official replay sequence (19,376 P2_first samples × 4 filters
× 2 gap behaviors) — **0 mismatches**. Compiled
`sizeof(mif_filter_t)` = **72 bytes** (host double reference).
Cycle counts remain illustrative; no measured MCU latency claimed.
MLP/GBDT moved to assumption-labeled hypothetical references.

## 11. Paper package status

`paper/{outline, abstract_draft_conservative, title_candidates,
figures_tables_inventory, limitations}.md` — complete; abstract says
"deterministic plausibility filter", no TinyML, no validated-fault
claim. `docs/paper_outline.md` superseded with pointer.

## 12. Tests passed / failed

**137 passed, 0 failed** (24 new in `tests/test_phase3r_leakage.py`:
boundaries, temporal separation, threshold-selection prohibition,
window-hit vs sustained, persistence, CIs, parity, overclaim scans).
Provenance gates pass before/after every run.

## 13. Remaining blockers

None in 3R scope. Open: outreach stored not sent; paper related-work
sweep [NEEDS WORK]; no external-dataset validation; n = 10 events
bounds certainty; GitHub push pending device-flow authorization.

## 14. Phase 4 recommendation

**Recommended, conditional:** only after outreach outcomes or a second
dataset — the export's internal evidence is now characterized to its
limits. Within-dataset work is exhausted; further phases would recycle
the same leakage constraints.
