# Phase-3 Acceptance Review (Phase 3R)

Independent re-inspection of commit `cddb031` (Phase 3) against the
original Phase-3 acceptance criteria, performed before any repair.
Verdicts refer to the state AT `cddb031`; the "3R action" column states
what Phase 3R did about each gap. Evidence paths are repo-relative.

## Verdict summary

| # | Original criterion (Phase-3 spec) | Verdict at cddb031 | 3R action |
|---|-----------------------------------|--------------------|-----------|
| B | Filter family F1/F2/F3/F4: streaming, causal, pure stdlib, minimal state, explicit edge cases, clean reference implementation | **PASS** | unchanged; C skeleton added (F) |
| C | Full-dataset evaluation under P1–P4: sweeps, event-based metrics (10 band-crossings; detection = flag at/before first ≥236 sample), leads via actual timestamps, FA as episodes/day, 2 CSVs + 3 figures | **PARTIAL** — all artifacts produced, but thresholds were selected with full-dataset knowledge (oracle/leakage); no persistence, duty cycle, or confidence intervals | sweep relabeled **exploratory/oracle sensitivity analysis**; leakage-controlled replay added; persistence/duty cycle/CIs added |
| D | Baselines B1/B2/B3, same metrics, B3 non-causal labeled | **PASS** | unchanged (reported only in exploratory context) |
| E | Pareto frontier CSV; operating-point families; honest statement if no early warning | **PARTIAL** — frontier and families exist; "no early warning" was OVERCLAIMED ("No multi-hour early warning exists in this export") and pre-window hits were counted as leads without persistence/duty-cycle qualification | wording corrected to tested-rules scope; persistence k=1/2/3, window-hit vs sustained separation, duty cycle added; T3 horizons 1/6/24 h added |
| F | Exact op counts; state bytes; Cortex-M0 cycle estimates vs MLP/GBDT; no Arduino claim | **PARTIAL** — op counts exact and cycle estimates labeled; but NO C implementation existed, state bytes were theoretical only, and MLP/GBDT comparisons sat in headline results with an assumed GBDT depth | `firmware_skeleton/mif_filter.{h,c}` + host parity added; compiled `sizeof(mif_filter_t)` = 72 B measured; MLP/GBDT moved to clearly-labeled hypothetical references |
| G | Paper outline with evidence map + claims NOT made | **PARTIAL** — `docs/paper_outline.md` existed; no T1/T2/T3 task separation; no abstract/title/limitations package | `paper/` package created (5 files); T1/T2/T3 separation explicit |
| H | README Phase-3 section keeping Phase-2 caveats | **PARTIAL** — section existed with caveats, but carried "No multi-hour early warning exists in this export" and the "not supported by this export" Energies wording | rewritten with required wording; overclaim test added |
| I | Registers updated with evidence classes | **PARTIAL** — C37–C43/A28–A32 added, but C38 asserted the WRONG separation interval "(54, 236]" and C39 carried the overclaim | C38/C39 corrected; C44–C48, A33–A37 added |
| J | Tests for the 9 spec areas; full suite | **PARTIAL** — 44 tests, 113 passing; but no boundary tests for [54,236), no leakage/persistence/CI/parity tests | 24 new tests (`test_phase3r_leakage.py`); suite now 137 passing |
| K | `phase_03_report.md` (10 sections) + `phase_03_handoff.md` (10 items) | **PARTIAL** — both existed; handoff item 4 contained a factual error (below) | report relabeled; error documented here and in `phase_03r_report.md` |
| L | No forbidden terms anywhere | **PARTIAL** — code/test terminology clean; README/report/handoff carried overclaim wording (see errors 4–5) | corrected; automated overclaim test guards README + paper drafts |
| M | Final response = handoff only, <1000 words | **PASS** | maintained in 3R |

## Errors found in the original Phase-3 handoff/report (verified against code and data)

1. **Handoff item 4 (factual error).** "F1 > 10/min misses exactly the
   two slowest rises (11.1, 14.5 OTI-units/min)." FALSE: both rates
   exceed 10, so rate > 10 detects 10/10 at the crossing sample; only
   thresholds **> 14.5** (the swept 15 and 20) miss those two events.
   The report §4 stated this correctly; the handoff contradicted it.
   Evidence: `filter_sweep_summary.csv` (rate>10 → 10/10; rate>15 →
   8/10); crossing-sample rates
   [24.75, 65.33, 22.44, 22.89, 14.5, 66.67, 25.375, 33.33, 11.111, 91.0].
2. **Wrong separation interval (report §4, §7, README, C38).** "F2 with
   any upper threshold in (54, 236] … 10/10, 0 FA". The upper endpoint
   is wrong: at U = 236 the strict rule `OTI > 236` does NOT flag the
   event-10 crossing sample (OTI = 236 exactly) — the sweep itself
   recorded 9/10 there. Correct interval: **[54, 236)** (normal max 54,
   with two samples at 54 that a strict rule correctly leaves unflagged).
3. **Ambiguous jump wording.** "F4 with jump threshold ≥ 50" conflated
   the threshold sweep value with the rule's strict inequality. The rule
   is |ΔOTI| > thr; no step equals 50 in this export (normal max |Δ| =
   42, min event step = 182), so "> 50" and "≥ 50" coincide here, and
   the zero-FA perfect-detection interval is thr ∈ **[42, 182)**.
4. **Overclaim (report §5, README, handoff item 5, C39).** "No
   multi-hour warning exists in this export" — stated as a property of
   the export rather than of the tested rules. Corrected to: "The
   tested OTI-only deterministic rules did not demonstrate robust
   multi-hour warning."
5. **Energies wording (report §5, README, C39).** "marked not supported
   by this export at channel level" — the Energies 24-hour claim's
   features, task, split, and evaluation were never reproduced, so no
   such judgment is permissible. Corrected to: "Phase 3 did not
   reproduce that claim."
6. **Lead-time conflation.** Mean leads (6.4 / 15.4 min) counted any
   pre-window flag without persistence or duty-cycle qualification; an
   isolated single-sample flag is not continuous warning. 3R adds
   persistence k = 1/2/3, window-hit vs sustained distinction, and
   duty cycles (`phase_03r_per_event.csv`).
7. **Leakage (design-level).** All headline detection numbers came from
   thresholds chosen on the full dataset (normal max 54, event min 236
   known). The sweep is retained but relabeled exploratory/oracle; the
   leakage-controlled replay is now the primary quantitative result.
8. **Cost claims without an implementation.** "Transliterable to C" was
   asserted but no C code existed; state sizes were theoretical. 3R adds
   the compiling, parity-tested C skeleton and the measured
   `sizeof(mif_filter_t)` = 72 bytes.
9. **No uncertainty.** 10/10 recall was reported without confidence
   intervals (exact 95% CI [0.69, 1.00] at n = 10) and no row-level
   precision/recall/F1. Added in 3R.
10. **Implementation bug found and fixed during 3R development** (before
    any commit): the `range` filter type never set `flagged` from its
    range rule; and a zone-boundary artifact counted the previous
    excursion's recovery-fall flag as early detection of the next event
    (2019-08-17 pattern). Both are regression-tested
    (`test_phase3_plausibility.py`).

## Verification method

Code paths re-read directly (`src/transformer_audit/plausibility_filter.py`,
`filter_metrics.py`, `scripts/run_filter_evaluation.py`); CSV/JSON
artifacts re-computed and cross-checked (`reports/generated/`); boundary
values re-derived from the raw export through the policy pipeline
(normal max 54 at 2 samples; high min 236; max normal |ΔOTI| 42; min
event rise 182; crossing rates as above). Raw-file hashes verified
before and after every run.
