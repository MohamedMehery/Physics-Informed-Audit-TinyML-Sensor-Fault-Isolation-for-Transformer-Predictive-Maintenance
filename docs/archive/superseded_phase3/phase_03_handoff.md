# Phase 3 Handoff — Deterministic Plausibility Filter

**Audited object:** unchanged — the five CSVs of Kaggle
`sreshta140/ai-transformer-monitoring` v1, SHA-256-pinned, gitignored,
byte-preserved, hash-verified before and after every run.

**Phase-3 commit:** `cddb031` (all code, tests, artifacts, and docs
below; raw files remain gitignored).

## What Phase 3 did

1. **Filter family (reference implementation).**
   `src/transformer_audit/plausibility_filter.py` — four deterministic,
   causal, streaming, pure-stdlib filters: F1 rate (|ΔOTI|/dt > thr),
   F2 range (OTI > upper), F3 combined, F4 jump (|ΔOTI| > thr, time
   ignored). Strict `>` throughout; state = previous OTI + previous
   timestamp + thresholds (2–16 B); multiply-form avoids division.
   Edge-case contract unit-tested: first sample → range only; NaN → no
   flag, no state update; dt ≤ 0 → data anomaly, never divide, state
   kept; gap > 60 min → reset | continue (both swept). Terminology
   enforced by test: flags readings *inconsistent with gradual thermal
   behavior*; never "faults"/"sensor failures"/TinyML/AI/intelligent.

2. **Event-based evaluation protocol.**
   `src/transformer_audit/filter_metrics.py`: 10 rising band-crossings
   (prev < 100 ≤ curr, dt > 0) per policy — all four policies yield the
   same 10 events; detection zone = (max(crossing−60 min, previous
   recovery), recovery], start exclusive; strict detection = flag at or
   before the first OTI ≥ 236 sample; lead = crossing_ts − first_flag_ts
   (actual timestamps); false alarms = contiguous episodes in normal
   operation (292.625 days), per day.

3. **Systematic sweep, full dataset, all policies — relabeled in
   Phase 3R as an EXPLORATORY / ORACLE SENSITIVITY ANALYSIS (thresholds
   chosen with full-dataset knowledge; not held-out validation; see
   `reports/phase_03r_handoff.md`).**
   `scripts/run_filter_evaluation.py`: 1,160 configurations (F1 × 8
   thresholds, F2 × 13, F4 × 7, F3 8×13 grid, × reset/continue ×
   P1–P4) + baselines; provenance gates pre/post. Outputs:
   `filter_sweep_summary.csv`, `filter_per_event_detail.csv`,
   `pareto_frontier.csv`, `computational_cost_comparison.csv`,
   `phase_03_filter_summary.json`, 3 figures.

4. **Main result — detection.** Concurrent detection of 10/10 events
   with zero false alarms is achievable by simple means: F2 upper ∈
   (54, 236] flags exactly the 47 excursion samples; F4 jump ≥ 50 flags
   the 10 rise + 10 recovery steps. Detection is policy-invariant
   (all 132 gap=reset configs identical). F1 > 10/min misses exactly
   the two slowest rises (11.1, 14.5 OTI-units/min).

5. **Main result — no early warning.** Maximum genuine pre-crossing
   lead: 48 min on one event (F2 OTI>45, 0.23 FA episodes/day); at
   OTI>50, 2/10 events preceded by 27–37 min; median lead 0 everywhere;
   nothing above 54 OTI units in any 60-min pre-window; the rise is a
   single step ≤54 → 236–250. No multi-hour warning exists in this
   export. The Energies §10 "24 h before" statement is their
   system-level claim, marked not supported by this export at channel
   level. Filter value = concurrent sensor-integrity flagging, not
   prediction. A weak precursor exists: elevated-normal-band values
   (50–54, top 0.4 % of normal samples) precede 2–5 of 10 events by
   20–48 min depending on threshold.

6. **Baselines.** B1 (OTI ≥ 236): 10/10, lead 0, 0 FA by construction
   (≡ OTI_T rule). B2 (seeded random, seeds 42–44): dominated — needs
   p ≥ 0.01 (≥ 0.63 FA/day) to detect anything (mean 0.33/10). B3
   (static percentile, **non-causal**): p99.5 reproduces F2 OTI>50
   exactly (10/10, lead 6.4 min, 0.055 FA/day).

7. **Pareto frontier & operating points.** 88 non-dominated points;
   two regimes: zero-FA concurrent corner (11 configs) and the sub-band
   lead/FA trade-off. Recommended families: **conservative** F4 jump>50
   (10/10, 0 FA); **balanced** F3 rate>2 & OTI>50 (10/10, mean lead
   6.4 min, 0.099 FA/day); **aggressive** F2 OTI>45 (10/10, mean lead
   15.4 min, median 3, 0.23 FA/day).

8. **Computational cost.** Exact op counts/sample: 1 (F2/B1), 9 (F4),
   10 (F1), 11 (F3); state 2–16 B. Cortex-M0 cycle **estimates** from
   documented instruction timings: ~18–30 fixed-point / ~37–291
   soft-float per sample vs 584-MAC 609-param MLP (~3,529/~61,986
   cycles, 2,436 B) and assumed depth-6 100-tree GBDT (~600 compares,
   ~152 KB). Wording ceiling: "within the documented computational
   capabilities of the Cortex-M0 class"; no board/vendor claim.

9. **Tests & docs.** 44 new tests (`tests/test_phase3_plausibility.py`)
   covering all spec areas incl. the 2019-08-17 recovery-fall
   regression and a terminology gate; full suite **113 passed**.
   `reports/phase_03_report.md` (10 sections);
   `docs/paper_outline.md` (evidence map + claims-NOT-made);
   README Phase-3 section (Phase-2 caveats retained); registers
   extended (C37–C43, A28–A32).

10. **Open items.** Outreach stored, NOT sent. No ground-truth fault
    labels (events are band-crossings by definition). Zone/episode
    conventions are methodology choices (documented, tested). Cycle
    counts are estimates, not hardware measurements. Paper [NEEDS
    WORK]: broader related-work sweep; optional second dataset for
    external validity. **Push to GitHub pending:** three device-flow
    authorization codes expired unused while the turn was held open;
    commit `cddb031` is local and intact — re-run the device flow in
    the next session to push.
