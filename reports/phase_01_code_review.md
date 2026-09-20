# Phase-1 Code Review (performed during Phase 2)

**Scope:** review of all Phase-1 analysis code and artifacts for assumptions that
depend on the single-physical-transformer premise, and for statistical practices
that could interact badly with repeated-timestamp records.

**Result:** one material defect found and fixed (`mean` duplicate policy);
several documentation-level issues tightened. No Phase-1 headline number changed.

## R1. `canonicalize(..., policy="mean")` averaged conflicting records — FIXED

**File:** `src/transformer_audit/io.py` (Phase-1 version)

**Defect:** The Phase-1 `mean` policy grouped all records sharing a timestamp
and averaged every numeric column — including the binary status channels
(`OTI_A`, `OTI_T`, `WTI`, `MOG_A`) and `OLI`. For a conflicting group with
`OTI_T = {0, 1}` this produces `OTI_T = 0.5`, a state that never physically
existed. Averaging across conflicting branches is only defensible when the
branches are known to be redundant measurements of the same instant — which is
precisely what Phase 2 was charged with determining.

**Phase-1 exposure:** Limited. `phase_01_report.md` used `mean` only as one of
three policies in the duplicate-sensitivity table (`duplicate_policy_sensitivity`),
and all headline Phase-1 numbers (transition counts, rates, event counts,
gaps) were computed on first-occurrence series. The Phase-1 report text did not
present any averaged flag value as a finding. The default policy was `first`
throughout.

**Fix applied in Phase 2:**
- `onset_counts_policy_sensitivity` (audit.py) now uses `("first", "last",
  "identical")` and never `mean`; its docstring states the rule.
- `canonicalize` docstring carries an explicit warning that `mean` can create
  non-physical flag states and is retained only for numeric channels with
  caller awareness.
- New module `records.py` implements the four Phase-2 policies
  (`P1_preserve`, `P2_first`, `P3_last`, `P4_identical`) with no flag
  averaging anywhere, plus `P5` occurrence-stream *diagnostics* (not a
  reduction).
- Regression tests: `TestPolicies::test_no_policy_averages_flags`,
  `test_policy_metrics_never_invent_states`.

## R2. Terminology: "duplicates" → "repeated-timestamp records"

Phase-1 code and reports used `duplicate_timestamp_report`,
`n_duplicate_timestamp_rows`, etc. Phase-2 terminology rule: until the origin
of repeated records is established, they are **repeated-timestamp records**,
not duplicates (calling them duplicates presupposes H2). The Phase-1 function
names are kept for backward compatibility (and their numbers remain correct —
they count groups, not causes); Phase-2 code uses the neutral terms. Noted
here so the naming asymmetry is understood as deliberate.

## R3. `sensor_columns` heuristic

Phase-1 `sensor_columns(df)` returns all columns except the timestamp/raw-line
metadata. In `records.py` this is reused for identity comparison across
repeated groups — correct, since identity must be defined over *all* published
value columns. No change needed; documented.

## R4. Rate computation on repeated records

Phase-1 `rate_summary`/`top_rate_transitions` computed rates on the
first-occurrence canonical series, so repeated records could not inflate
rates. Verified: the Phase-2 `policy_sensitivity` table reproduces max rates
+91.0 / −40.8 OTI-units/min under all four policies
(`reports/generated/duplicate_policy_sensitivity.csv`). The excursion rates
are therefore not artifacts of record handling.

## R5. Event merging across gaps

Phase-1 `merge_events` with gap thresholds (60/360 min) affects WTI/MOG_A
event counts but not the excursion-critical OTI_T events (10 primitive events
stable across merge thresholds; Phase-1 report §7). No single-transformer
assumption is embedded in the merging logic itself (it operates on the
published record sequence). No change.

## R6. Electrical-continuity observations

Phase-1 `electrical.py` computes per-phase apparent power and excursion
electrical context from CurrentVoltage/TotalPower. These computations assume
only that the rows come from the same measurement point *per row* (VL/IL/KW
are per-row quantities); they do not require adjacent rows to be the same
physical asset. The Phase-1 report's *narrative* sometimes said "the
transformer" — reviewed in the Phase-2 claim register; findings retained with
entity-conditioned wording.

## R7. Claims review (single-transformer dependency)

Every Phase-1 claim was re-examined. Disposition summary (details in
`docs/claim_register.md`):

- **Retained as-is** (row-local or distributional facts, no entity premise):
  row counts, hashes, value domains, empty interval (54, 236), 47 rows ≥ 236,
  OTI_T⟺OTI≥236 rule, interval structure, gap structure, per-phase power
  consistency (Σ(VLx·ILx) vs KVA), rate magnitudes, event counts.
- **Retained with entity-conditioned wording** (statistics of the published
  series, valid regardless of how many assets contributed): excursion rate
  summary, WTI/MOG_A/OTI_T event counts, excursion electrical context,
  autocorrelation.
- **Downgraded to conditional**: any sentence beginning "the transformer…"
  in Phase-1 narrative — now read as "the published series" unless an entity
  is established.
- **Withdrawn/never made**: no Phase-1 claim asserted a nameplate rating, oil
  mass, or root cause; none needed withdrawal on those grounds.

## R8. Test-coverage gaps closed in Phase 2

Phase-1 tests had no coverage for repeated-record edge cases (conflicting
branches, flag preservation under reduction policies, occurrence-index
reasoning). Closed by `tests/test_phase2_records_physics.py` (30 tests;
full suite 69 passing).

## Verification after fixes

```
$ python3 -m pytest tests/ -q          # 69 passed
$ python3 scripts/run_phase2_analysis.py   # regenerates all artifacts; provenance gate PASS
$ python3 scripts/independent_raw_verification.py  # 56/56 checks agree (stdlib-only reimplementation)
```

Phase-1 artifacts in `reports/generated/` are unchanged by these fixes except
`duplicate_policy_sensitivity.csv`, which now shows first/last/identical
instead of first/last/mean, with identical numbers for the surviving policies.
