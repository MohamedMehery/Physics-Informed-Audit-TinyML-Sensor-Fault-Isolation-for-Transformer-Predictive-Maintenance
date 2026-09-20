# Phase 2 Report — Single-Asset Validity, Source Lineage, and Conditional Physics

**Audited object:** the five published CSV files of Kaggle
`sreshta140/ai-transformer-monitoring` v1 ("Distributed Transformer
Monitoring", uploaded by the Putchala et al. first author; hash-pinned in
`provenance/dataset_manifest.json`; raw files gitignored and
byte-preserved).

---

## 1. Executive summary

Phase 2 asked whether the published rows form a valid time series for one
physical transformer, and what can be said about the abrupt OTI transitions
under explicit, condition-labeled assumptions. Findings:

1. **Lineage closed, entity open.** The export is verified to be the same
   data the Energies 15(21):7981 authors used (their Data Availability
   Statement points at the upload by the first author of Putchala et al.
   2022; row counts match ours exactly). No primary source states the
   export's entity scope.
2. **Required statement (entity unresolved):** *The published dataset does
   not provide enough information to establish that adjacent rows belong to
   the same physical transformer.*
3. **Repeated records** (931 Overview groups; 2.2–4.8 % of timestamps) are
   synchronized across files, raw-line adjacent, near-identical in value,
   concentrated in the deployment month, and **never contain the 47
   high-OTI rows** — most consistent with ingestion/export re-transmission
   (H2) for the repeats specifically. Multi-asset (H3) and multi-feeder
   (H4) structures find no support in any test performed (single contiguous
   voltage regime, no stable occurrence streams, branch parity).
4. **The excursion findings are policy-invariant:** under P1 (preserve all),
   P2 (first), P3 (last), P4 (identical-only) the series always shows 10
   rising band-crossings, the empty interval (54, 236), max rates +91.0 /
   −40.8 OTI-units/min, and a perfect per-record (OTI ≥ 236) ⟺ (OTI_T = 1)
   rule.
5. **Conditional physics:** under an extreme 100 %-conversion upper bound
   with observed power (33–142.1 kW), only effective thermal masses of
   ~32–426 kg could rise by the observed 182–206 OTI units in the observed
   2–18 min — far below distribution-class oil-equivalent masses; plausible
   masses (≥300 kg) would require sustained 0.1–4.9 MW. The channel's
   apparent recovery time constant is 0.5–26 min. No root cause is claimed;
   sampling cannot exclude unobserved sub-interval electrical events.

## 2. Questions and hypotheses

Core question: do the rows form a valid time series for ONE physical
transformer? Hypotheses H1 (single asset, legitimate repeats), H2 (export
duplication/retries), H3 (multiple assets after ID removal), H4 (multiple
feeders), H5 (corrupted export) — none pre-selected; no numeric
probabilities assigned anywhere in this phase (qualitative evidence
comparison only).

## 3. Data, provenance, and gates

- Raw files verified by SHA-256 before and after every run
  (`verify_raw_files`; pre/post gates in `run_phase2_analysis.py`).
- Independent stdlib-only verifier
  (`scripts/independent_raw_verification.py`) recomputed row counts, hashes,
  ranges, repeated-timestamp counts, identical-vs-conflicting groups, OTI
  min/max, #≥236, empty interval, OTI_T⟺OTI, actual-Δt rates, and raw-line
  location of every high-OTI transition: **56/56 checks agree**; exits
  non-zero on any disagreement.
- Environment: Python 3.13.14, pandas 2.2.3, numpy 2.3.5, matplotlib
  3.10.9. Tests: **69 passed** (39 Phase-1 + 30 Phase-2).

## 4. Source examination (full texts) and lineage

Full texts examined — not abstracts — with source-role separation and short
verbatim quotes (section-referenced) recorded in
`source_lineage_report.md` and `reports/generated/source_claim_matrix.csv`:

- **Putchala et al. 2022** (PRIMARY, S11; complete full text read): data
  "provided by a private company, KernelSphere Technologies … REST APIs
  recorded from November 2020 up to date at 52 different locations at the
  State, Tripura, India … updated for every 15 min" (Sec. 4). Their paper
  analyzes ≈237,687 rows of the live stream (Sec. 4.4), not this export's
  window. Their thresholds (OTI > 65 etc., Sec. 4.2) belong to their
  pipeline on that stream.
- **Energies 15(21):7981** (SOURCE-ADJACENT, S7; all relied-upon sections read
  incl. Data Availability Statement and Sec. 10): used the Kaggle upload by
  the paper's first author (`sreshta140/ai-transformer-monitoring`,
  accessed 20 June 2022) — the same data audited here (CurrentVoltage
  19,352 rows, identical window/schema). Their 1500 kVA / 11/0.4 kV
  description is their own Sharjah system (Sec. 5.1/6), not this dataset.
  Their OTT "shuts off electrical flow" description conflicts with this
  export's electrical continuity during OTI_T=1 windows, so OTI_T semantics
  remain open.
- **Kaggle pages**: audited copy published 2020-05-25 (re-upload);
  sreshta140 copy uploaded by "Sreshta Putchala" = first author of the
  Springer paper (author list verified on the Springer chapter page).

## 5. Repeated-record analysis

Terminology: **repeated-timestamp records** — never "duplicates" (origin
unknown). No conflicting OTI or binary flag is ever averaged.

- Multiplicity: Overview {1: 18,445, 2: 923, 3: 7, 4: 1}; other files
  {1: ~18.4k, 2: ~0.4k}.
- Cross-file sharing: 420/437 (CV↔OV) … 290/406 (TP↔OV) of repeated
  timestamps repeat across files → synchronized ingestion layer.
- 931/931 Overview groups raw-line adjacent; monthly counts 448 (Jun 2019,
  48 %) decaying to 20–84/month.
- Conflicts: 363/931 groups; OTI magnitude 1 unit (144), 2 (32), 3 (9),
  4 (1), 33 (1); VL1 median 0.4 V; flags conflict in only 17 groups.
- High-OTI (≥236) rows in repeated groups: **0 of 47**.
- Per-record (OTI ≥ 236) ⟺ (OTI_T = 1): **0 violations in 20,316 records**
  (including every branch).
- Occurrence-stream check: share of timestamps with repeats ≤ 4.8 % — no
  stable per-device streams; P5 reconstruction unsupported.
- Branch continuity parity: 4.8 vs 4.6 mean |ΔOTI| to neighbors — no branch
  stands out as a separate device.

## 6. Policy sensitivity (P1–P4)

`reports/generated/duplicate_policy_sensitivity.csv`: across
P1_preserve / P2_first / P3_last / P4_identical — 10 high-OTI rising
transitions; OTI_T rule accuracy 1.0; empty interval (54, 236) present;
max rates +91.0 / −40.8 units/min; 10 OTI_T primitive events. The
excursion-related conclusions are invariant to record handling. The Phase-1
`mean` policy was removed from all flag statistics (code review R1).

## 7. Entity and asset scope

Statistical evidence is consistent with a single measurement point (single
contiguous VL1 220–260 V and VL12 381–443 V regimes; unimodal currents;
per-row Σ(VLx·ILx) ≈ KVA) but does not identify one: no device column, no
primary scope statement, 52-location platform upstream. H3/H4 unsupported by
every structural test; H2 explains the repeats but not the excursions and
does not establish entity. Required statement issued (§1 item 2). Full
analysis: `asset_scope_and_entity_analysis.md`.

## 8. Variable semantics

Per-column table: `variable_semantics.csv`; narrative:
`variable_semantics_report.md`. OTI in "OTI units" (unit unconfirmed);
WTI binary (not treated as a temperature); OLI unit unknown; OTI_A active
at both 29–30 and 236–250; OTI_T ⟺ OTI ≥ 236 exactly (semantics open);
near-250 values are NOT called an ADC rail (no hardware metadata) — the
leading representation hypotheses (error/status code; converted/saturated
representation; genuine excursion; export artifact) are listed with
falsification tests, none established.

## 9. Asset parameter bounds

`asset_parameter_evidence.csv` + `manufacturer_spec_envelope.csv`;
narrative: `asset_parameter_bounds.md`. Identity parameters (#transformers,
#devices, #feeders, rating, oil volume) all UNKNOWN; observed loading
(142.9 kVA max) establishes nothing about rating; official envelope
(ETT/BSES/Bharat Bijlee/IS 1180 scope) used only for distribution-class
plausibility; no typical oil volumes asserted (none obtainable from official
sources); rating unbounded above.

## 10. Conditional physics

`conditional_physics_analysis.md` + `physics_sensitivity.csv` +
`apparent_tau_per_transition.csv` + three figures. Summary in §1 item 5.
Every result is labeled with its assumptions (100 %-to-oil as extreme bound;
c = 1.8–2.1; OTI-unit conditionality; observed-power bounds; sampling
limitation stated rather than claimed away). Required thermal power vs mass,
achievable ΔT vs mass, and critical mass vs power are given as curves/tables,
not single points.

## 11. Alternative explanations

9-row matrix (`alternative_explanations.csv`) with supporting evidence,
contradicting evidence, missing metadata, qualitative confidence, and a
falsification test per cause. No hardware root cause asserted.

## 12. Independent verification, code review, tests

- Stdlib-only verifier: 56/56 agreement (§3).
- Phase-1 code review (`phase_01_code_review.md`): one material defect
  (mean-policy flag averaging) found, fixed, regression-tested; Phase-1
  artifacts regenerated; no Phase-1 headline number changed.
- Test suite: 69 passed (synthetic fixtures only; no dataset rows embedded);
  new coverage includes conflicting branches, P1–P4 behavior, high-OTI
  branch isolation, occurrence streams, entity-unrecoverability, conditional
  units, critical-mass math, τ log-domain guards, sensitivity, and verifier
  agreement.
- Commands/environment recorded in §3 and `phase_02_summary.json`.

## 13. Limitations and next steps

Limitations: entity unresolvable from published data; OTI/OLI units
unconfirmed; no provider/ingestion logs; no hardware metadata; sampled data
cannot exclude unobserved sub-interval electrical events; manufacturer
envelope is market-context, not asset-specific.

Next steps (require owner authorization or credentials): send outreach
drafts (docs/outreach_requests.md — currently DRAFTS ONLY), and any provider
answers that fill identity/unit parameters would upgrade §8–§10 from
conditional to asset-specific.
