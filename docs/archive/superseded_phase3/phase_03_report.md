# Phase 3 Report — Deterministic Plausibility Filter: Design, Evaluation, Baselines, Cost

Phase 3 of the transformer-monitoring dataset audit. All results are
reproducible from this repository (`scripts/run_filter_evaluation.py`,
provenance-gated before and after the run). Raw files are byte-preserved
and gitignored; every number below comes from a committed artifact.

> **PHASE-3R STATUS LABEL (supersedes the original framing).** The
> 1,160-configuration sweep in this report is an **exploratory / oracle
> sensitivity analysis**: thresholds were selected with knowledge of the
> full dataset (normal maximum 54, event minimum 236) and it is **not**
> held-out detector validation. The leakage-controlled chronological
> replay with frozen calibration-derived thresholds is in
> `reports/phase_03r_report.md`. Corrections verified in Phase 3R: the
> F2 zero-false-alarm separation interval is **[54, 236)** (not
> (54, 236] — at U = 236 the strict rule misses the OTI = 236 crossing
> sample), the F4 interval is [42, 182), and F1 misses the two slowest
> rises only for thresholds > 14.5 (not > 10: 11.1 and 14.5 both exceed
> 10).

Standing terminology: the filter flags readings **inconsistent with
gradual thermal behavior** at the measurement-channel level. It does not
"detect faults" or "detect sensor failures," the root cause of every
flagged excursion is unknown, and OTI values are in **"OTI units"**
(unit unconfirmed by any primary source).

---

## 1. Executive summary

- Four deterministic, causal, streaming filters (F1 rate, F2 range,
  F3 combined, F4 jump) were implemented as a pure-stdlib reference
  (`src/transformer_audit/plausibility_filter.py`) with an explicit
  edge-case contract, and evaluated over the **full dataset under all
  four record policies (P1–P4)** in **1,160 configurations**
  (threshold sweeps × gap behaviors × policies) plus three baselines.
- Evaluation is **event-based**: 10 rising band-crossings into OTI ≥ 236
  (the OTI_T rule), not rows. Detection = flag at or before the event's
  first OTI ≥ 236 sample, inside a bounded 60-min pre-window. False
  alarms are contiguous **episodes** during normal operation
  (292.6 normal days), reported per day. Lead times use actual
  timestamps.
- **Concurrent detection with zero false alarms is trivially achievable**
  (F2 with any upper threshold in (54, 236], F4 with jump threshold ≥ 50,
  and baseline B1 all give 10/10 events, lead 0, 0 FA episodes) — these
  filters flag exactly the 47 excursion samples (F2) or the 10 rise + 10
  recovery steps (F4).
- **No multi-hour early warning exists in this export.** The maximum
  genuine pre-crossing lead is **48 min on one event** (F2, OTI>45,
  0.23 FA episodes/day); at the low-FA operating point OTI>50 two of ten
  events are preceded by 27–37 minutes by **elevated-normal-band values
  (50–54 OTI units, the top 0.4 % of normal operation)** at 0.055 FA
  episodes/day. The median event lead is 0 at every practical threshold.
  Nothing in any 60-min pre-window exceeds 54 OTI units.
- Baselines: B1 (trivial OTI ≥ 236 threshold) detects 10/10 by
  construction at lead 0; B2 (seeded random) needs p ≥ 0.01
  (≥ 0.63 FA/day) to detect anything (mean 0.33/10) — dominated by every
  filter family; B3 (static percentile, **non-causal**) reproduces the
  F2 sub-band operating points (p99.5 ≈ OTI>50: identical 10/10, 6.4-min
  mean lead, 0.055 FA/day).
- Computational cost: **exact** operation counts (1 op/sample for F2/B1,
  9 for F4, 10 for F1, 11 for F3 — multiply-form, no division), state of
  2–10 bytes. Cortex-M0 cycle **estimates** from documented instruction
  timings: ~18–30 cycles/sample fixed-point, ~37–291 soft-float — versus
  584-MAC/609-parameter MLP (3,529 / 61,986 cycles, 2,436 B weights) and
  an assumption-parameterized 100-tree GBDT (~600 compares, ~152 KB).
  No claim beyond "within the documented computational capabilities of
  the Cortex-M0 class" is made.

## 2. Filter family design (spec B)

One class, four instantiations, all sharing one streaming loop
(`PlausibilityFilter.process(oti, ts_minutes) -> FilterDecision`):

| id | rule (strict `>` throughout) | ops/sample | state |
|----|------------------------------|-----------:|-------|
| F1 rate | `|OTI[k]−OTI[k−1]|/dt > rate_threshold` | 10 | prev OTI, prev ts, threshold |
| F2 range | `OTI[k] > upper` (or `< lower`, optional) | 1 | threshold only |
| F3 combined | F1 OR F2 | 11 | union of both |
| F4 jump | `|OTI[k]−OTI[k−1]| > jump_threshold` (time ignored) | 9 | prev OTI, prev ts, threshold |

Design constraints (unit-tested): **deterministic** (no randomness, no
learned parameters), **causal** (uses only the current sample and its
retained predecessor), **streaming** (O(1) per sample), **pure stdlib**
(transliterable to C without ambiguity). The rate filter is implemented
in multiply-form on microcontrollers (`|ΔOTI| > thr·dt`) — zero
divisions in op counts.

Edge-case contract (each case unit-tested):
- first sample → range only, no dynamics, state initialized;
- NaN/None OTI → never flagged, state **not** updated;
- dt ≤ 0 (repeated/reordered timestamps) → **data anomaly**, never
  divide, state not updated (older reference kept);
- gap > 60 min → `reset` (treat next sample as first) or `continue`
  (evaluate across the gap); both behaviors swept.

## 3. Evaluation protocol (spec C) — exploratory / oracle sensitivity

- **Series**: each policy's retained records, ordered by
  (timestamp, raw line); timestamps as float minutes.
- **Events**: `find_rising_crossings` — transitions with dt > 0 from
  OTI < 100 to OTI ≥ 100 that lead into the high band (all 10 land
  directly at 236–250, the empty interval (54, 236)). Recovery = first
  later sample < 100. All four policies yield **the same 10 events**
  (0 high-OTI records occur in repeated groups).
- **Detection zone**: `(max(crossing−60 min, previous recovery), recovery]`
  — start **exclusive**, recovery **inclusive**. The clip ensures a
  recovery-fall flag of the previous excursion cannot be counted as
  early detection of the next event (this exact artifact occurred on
  2019-08-17 during development and is now a regression test).
- **Detection (headline, strict)**: a flag at ts ≤ crossing inside the
  zone. In-zone-only flags (after the crossing sample) are recorded
  separately with negative lead.
- **Lead time**: `crossing_ts − first_flag_ts` (positive = before the
  crossing sample; 0 = at the crossing sample).
- **False alarms**: contiguous flagged runs inside normal-operation
  zones (the timeline outside detection zones; 292.625 days), counted as
  episodes; rate = episodes per normal day.
- **Sweeps**: F1 rate ∈ {0.5,1,2,3,5,10,15,20} OTI-units/min; F2 upper ∈
  {45,48,50,52,54,60,70,80,90,100,150,200,236} (sub-band thresholds
  45–54 added after observing pre-crossing values in the
  elevated-normal band); F4 jump ∈ {5,10,20,30,50,100,150} OTI units;
  F3 = full 8×13 grid; × {reset, continue} × {P1,P2,P3,P4}.
- **Provenance gates** before and after the run: all raw-file SHA-256
  hashes match the manifest.

## 4. Results — detection and false alarms (full sweep; exploratory / oracle sensitivity, not held-out validation)

`reports/generated/filter_sweep_summary.csv` (1,160 rows);
`filter_per_event_detail.csv` (11,600 event evaluations).

**Detection is policy-invariant**: all 132 real-filter configurations at
gap=reset have identical detection counts under P1/P2/P3/P4 (0 vary).
False-alarm rates differ by at most one episode (P3_last occasionally
differs by fractions of an episode/day). Gap behavior reset vs continue
changes neither detection nor FA for the rate filters.

Reference policy P2_first, gap=reset:

- **F1**: 10/10 up to rate>10 (FA 0.010/day = 3 episodes); 8/10 at
  rate>15 and >20 — exactly the two slowest rises (11.1 and
  14.5 OTI-units/min at the crossing sample) escape, confirming the
  sweep is governed by the measured rise rates. Leads: 0 (mean 0.3 min
  at rate>0.5 from one 3-min pre-crossing rise).
- **F2**: upper ∈ (54, 236] → **10/10, lead 0, 0 FA episodes, exactly
  47 flagged rows** (the excursion samples). At OTI>236 (strict) → 9/10
  (event 10's crossing sample is exactly 236; documented contrast with
  B1's non-strict ≥ 236). Sub-band: OTI>45: 10/10, mean lead 15.4 min
  (median 3), 0.229 FA/day; OTI>48: 10/10, 9.5 min, 0.140/day; OTI>50:
  10/10, 6.4 min, 0.0547/day; OTI>52: 10/10, 0.7 min, 0.010/day.
- **F4**: 10/10 at every threshold 5–150; ≥ 50 → 0 FA episodes (20
  flagged rows = 10 rises + 10 recovery falls). Leads 0 everywhere.
- **F3**: 10/10 across the entire grid (union); leads = the F2
  component's; FA = union of both components'.

## 5. Lead-time analysis — the early-warning question

Per-event leads (P2_first, reset), the only positive values anywhere in
the real-filter sweep:

| operating point | per-event leads (min) | mean | median |
|---|---|---:|---:|
| F2 OTI>45 | 48, 42, 35, 23, 6, 0×5 | 15.4 | 3.0 |
| F2 OTI>48 | 48, 27, 20, 0×7 | 9.5 | 0.0 |
| F2 OTI>50 | 37, 27, 0×8 | 6.4 | 0.0 |
| F2 OTI>52 | 7, 0×9 | 0.7 | 0.0 |
| F1 rate>0.5 | 3, 0×9 | 0.3 | 0.0 |

Facts behind these numbers:

- The pre-crossing samples of the 10 events sit in the **top of the
  normal band** (33–54 OTI units); ≥ 50 is 0.38 % and ≥ 53 is 0.03 % of
  normal-band samples. Five events start from 33–47 and show no
  precursor at any swept threshold; five show elevated-normal values
  20–48 min ahead.
- **The rise itself is a single step**: last pre-crossing value ≤ 54,
  crossing value 236–250, 2–18 min later — the empty interval (54, 236)
  holds at sample resolution. No rate/range/jump filter can flag the
  transition before the crossing sample unless a pre-existing
  elevated-normal value crosses a sub-band threshold first.
- **No evidence of multi-hour warning.** Nothing above 54 OTI units
  appears in any 60-min pre-window, and pre-crossing values are
  ordinary normal-band readings. The Energies 2022 §10 statement that
  their Isolation-Forecast pipeline "predicts anomalies 24 h before"
  is therefore **not supported by this export at the measurement-channel
  level** (their claim concerns their pipeline on this data; we make no
  claim about their experiments beyond this channel-level observation).
- The value of these filters is **concurrent flagging** (integrity
  checking at negligible cost), not prediction. The sub-band leads
  (minutes) are a weak, event-dependent precursor, not a warning system.

`figures/filter_lead_time_distribution.png` shows the balanced operating
point (F3 rate>2; OTI>50): 8 events at lead 0, one at 27, one at 37 min.

## 6. Baseline comparison (spec D)

Same metrics, same zones, P2_first:

| baseline | config | detected | mean lead | FA/day | note |
|---|---|---:|---:|---:|---|
| B1 trivial | OTI ≥ 236 | 10/10 | 0.0 | 0.0 | equals the OTI_T rule by construction (C30) |
| B2 random | p=1e-5…5e-2, seeds 42/43/44 | 0/10 up to p=0.005; 0.33/10 at p=0.01; 3/10 at p=0.05 | (chance flags) | 0.002–3.06 | dominated by every filter family |
| B3 percentile | >p95 / p99 / p99.5 / p99.9 | 10 / 10 / 10 / 5 | 24 / 9.5 / 6.4 / 0 min | 0.465 / 0.140 / 0.055 / 0.0 | **non-causal** (full-dataset percentile); p99.5 lands at ≈ OTI>50 and exactly reproduces F2's numbers |

Interpretation: B1 shows the detection task is trivial *given the
definition of events as band-crossings* — any threshold in (54, 236)
suffices; the filters' added value over B1 is (a) independence from the
high-band threshold, (b) fall/jump/recovery flagging, (c) data-anomaly
reporting, and (d) the sub-band precursor trade-off. B2 shows the
filter families are far from chance. B3 shows the sub-band operating
points are what a distribution-based rule would also choose — the
signal is in the data, not in filter cleverness.

## 7. Pareto frontier and operating-point families (spec E)

`reports/generated/pareto_frontier.csv` (88 non-dominated points; B1
attached as reference). The frontier has two regimes:

1. **Zero-FA corner** (det 10/10, FA 0): F2 upper ∈ (54, 200], F4 jump
   ∈ [50, 150]. 11 configurations.
2. **Sub-band lead/FA trade-off** (det 10/10, FA > 0, mean lead > 0):
   F2/F3 sub-band thresholds 45–52.

Recommended operating-point **families** (not single "best" points):

- **Conservative** — F4 jump>50 (or F2 OTI>100): 10/10 concurrent, 0 FA
  episodes, flags only the excursion steps; no reliance on sub-band
  statistics.
- **Balanced** — F3 combined rate>2 & OTI>50: 10/10, mean lead 6.4 min
  (37/27 min on the two events with elevated-normal precursors), 0.099
  FA episodes/day (one episode per ~10 days).
- **Aggressive** — F2 OTI>45 (or F3 rate>0.5 & OTI>45): 10/10, mean
  lead 15.4 min, median 3 min, 0.23–0.54 FA episodes/day.

Honest summary: all families detect every event **concurrently**; the
families differ only in how much false-alarm budget they spend for
minute-scale leads on the subset of events that have elevated-normal
precursors.

## 8. Computational cost (spec F)

`reports/generated/computational_cost_comparison.csv`. Operation counts
are **exact** (from the reference implementation); cycle counts are
**estimates** from documented Cortex-M0 (ARMv6-M) integer instruction
timings (1-cycle ALU/MULS, 2-cycle LDR/STR, ~3-cycle taken branch) and
typical GCC libgcc soft-float routine costs (~20 cmp, ~50 add/mul,
~140 div) — labeled as estimates everywhere:

| approach | ops/sample | M0 cycles (fixed-pt) | M0 cycles (soft-float) | state/storage |
|---|---:|---:|---:|---|
| F2 range / B1 | 1 | ~18 | ~37 | 2 B |
| F4 jump | 9 | ~28 | ~221 | 8 B |
| F1 rate | 10 | ~29 | ~271 | 8 B |
| F3 combined | 11 | ~30 | ~291 | 10 B |
| MLP 28-16-8-1 (reference) | 609 (584 MACs + 25 adds) | ~3,529 | ~61,986 | 2,436 B weights |
| GBDT 100×depth-6 (reference) | ~600 compares | ~3,000 | — | ~152 KB |

State: float32 (prev OTI, prev ts, thresholds) is 4–16 B; fixed-point
(u16 OTI 0–250, u32 ts-min, s16 thresholds) is 2–10 B. The filter
family is within the documented computational capabilities of the
Cortex-M0 class by 2–3 orders of magnitude relative to the reference
models. **No claim is made about any specific board or vendor**, and no
"runs on Arduino" statement appears anywhere.

## 9. Robustness checks (policies, gaps, determinism)

- **Policy invariance**: detection counts identical across P1–P4 for
  all 132 real-filter configurations (the 47 excursion records never
  occur in repeated groups, so retained-set composition cannot change
  the events). FA episodes differ by ≤ 1 across policies.
- **Gap behavior**: reset vs continue change neither detection nor FA
  at any swept threshold (the largest gaps in the export are ~days;
  rate flags across such gaps would be meaningless, and `continue`
  simply evaluates them).
- **Determinism**: the entire evaluation is single-threaded, seeded
  where randomness exists (B2 only), and byte-reproducible; three
  repeated runs produce identical CSVs.
- **Terminology gate**: `test_no_forbidden_terminology` scans the two
  new modules for forbidden terms ("TinyML", "AI", "intelligent",
  "proven fault", …).

## 10. Tests, artifacts, limitations

**Tests** — `tests/test_phase3_plausibility.py` (44 tests) covers: F1/F2/
F3/F4 semantics incl. strict boundaries; the full edge-case contract
(first sample, NaN, dt ≤ 0, gap reset/continue); causality and state
minimality; event extraction incl. dt=0 and unrecovered events; zone
boundary semantics (exclusive start, recovery clip — with the
2019-08-17 regression case); strict vs in-zone detection, lead signs,
FA episodes-vs-rows, FA rate per normal day; B1/B2/B3; Pareto dominance
and ties; exact op counts, MLP/GBDT counts, cycle-order sanity;
terminology discipline; end-to-end synthetic evaluation; script
provenance-gate and policy-coverage checks. Full suite: **113 passed**
(69 prior + 44 new).

**Artifacts** (all under `reports/`): `generated/filter_sweep_summary.csv`,
`generated/filter_per_event_detail.csv`, `generated/pareto_frontier.csv`,
`generated/computational_cost_comparison.csv`,
`generated/phase_03_filter_summary.json`,
`figures/filter_roc_by_type.png`, `figures/filter_threshold_sensitivity.png`,
`figures/filter_lead_time_distribution.png`.

**Limitations** (unchanged from Phases 1–2, plus new ones):
- OTI/WTI/ATI/OLI units unknown ("OTI units" throughout); entity scope
  unknown (adjacency ≠ same physical transformer); no ground-truth
  fault labels — the "events" are band-crossings by definition.
- The 60-min pre-window, its clipping rule, and episode-based FA
  counting are methodology choices (documented, unit-tested) — other
  conventions would shift FA rates and lead attribution slightly.
- Single export; sampling cannot exclude sub-interval excursions.
- Cortex-M0 cycle numbers are estimates from documented tables, not
  measurements on hardware; the GBDT reference is parameterized by an
  assumed depth (no source fixes an architecture).
- The sub-band precursor (5 of 10 events, 20–48 min) is an observation
  in this export, not a general property of transformer channels.

**Next steps**: outreach outcomes (stored, not sent); optional external
validity on a second dataset; paper assembly per
`docs/paper_outline.md`.
