# Phase 2 Handoff — Single-Asset Validity, Source Lineage, Conditional Physics

**Audited object:** the five CSVs of Kaggle `sreshta140/ai-transformer-monitoring`
v1 ("Distributed Transformer Monitoring", 2020-05-25; official API download;
SHA-256-pinned in `provenance/dataset_manifest.json`). Raw files gitignored,
byte-preserved, hash-verified before and after every run.

## What Phase 2 did

1. **Full-text source examination** (not abstracts) with source-role
   separation: Putchala et al. 2022 (PRIMARY — dataset authors) read
   completely; Ramesh et al., Energies 15(21):7981 (SOURCE-ADJACENT) read
   for all relied-upon sections incl. the Data Availability Statement;
   manufacturer/utility envelope from official sources only (ETT, BSES
   Delhi, Bharat Bijlee, IS 1180 scope). Short section-referenced quotes
   only; no copyrighted full text committed.
2. **Lineage triangle closed:** the audited archive was uploaded by
   "Sreshta Putchala" — first author of Putchala et al. 2022 (Springer
   author list verified) — and the Energies study used this same dataset
   (Data Availability Statement names the URL, accessed 2022-06-20; only v1
   exists). The paper's platform statement (KernelSphere, Tripura, 52
   locations, REST APIs, 15-min, from Nov 2020) describes a *later* window
   than the export (2019-06-25…2020-04-14); platform attribution of the
   export window is an inference (uploader + schema + cadence + operating
   ranges), not a primary statement.
3. **Repeated-record analysis** (never "duplicates"; never averaging
   conflicting OTI/flags): multiplicity, cross-file sharing, adjacency,
   conflict magnitudes, occurrence-stream diagnostics, high-OTI
   intersection.
4. **Policy sensitivity** P1/P2/P3/P4: excursion findings invariant;
   Phase-1 `mean` policy removed from all flag statistics (code review
   `phase_01_code_review.md`; no Phase-1 headline number changed).
5. **Variable semantics** per column: OTI in "OTI units" (unconfirmed),
   WTI binary, OLI unit unknown, OTI_T⟺OTI≥236 exact but semantics open;
   near-250 band never called an ADC rail; representation hypotheses with
   falsification tests.
6. **Asset parameter bounds:** identity parameters (#transformers,
   #devices, #feeders, rating, oil volume) all UNKNOWN; observed loading
   (142.9 kVA max) establishes nothing about rating; official envelope =
   market context only; rating unbounded above.
7. **Conditional physics** (after entity/unit/source reviews; every result
   labeled with assumptions; curves not points): heating bounds
   (m_critical = E/(c·ΔT)) and apparent measurement-channel time constants
   (τ with log-domain guards + ambient/Δt sensitivity). No IEC ODE, no ML,
   no edge detector, no hardware root cause.

## Headline results

- **Lineage:** dataset ↔ Putchala et al. 2022 ↔ Energies 2022 = one
  lineage (same archive). The Energies 1500 kVA / 11→0.4 kV description is
  their own Sharjah system, not this dataset. The paper's OTI>65 trip band
  belongs to their live stream; the export's OTI_T aligns with OTI ≥ 236.
- **Required statement (entity unresolved):** *The published dataset does
  not provide enough information to establish that adjacent rows belong to
  the same physical transformer.* Structural tests are consistent with a
  single measurement point but cannot identify one: single contiguous
  voltage regimes (VL1 220–260 V, VL12 381–443 V), no stable occurrence
  streams (repeat share ≤ 4.8 %), branch parity, per-row Σ(VLx·ILx) ≈ KVA.
  H3/H4 find no support in any test.
- **Repeated records:** Overview 931 groups (2.2–4.8 % of timestamps across
  files); synchronized across files (e.g., 420/437 CV↔OV); all raw-line
  adjacent; conflicts tiny (OTI median 1 unit; VL1 median 0.4 V); 448/931
  in the deployment month (2019-06) decaying afterward; **0 of 47 high-OTI
  records in any repeated group** — the excursions are not repetition
  artifacts. Most consistent: ingestion/export re-transmission (H2) for
  the repeats — qualitative best-fit, unconfirmed without provider logs.
- **Policy invariance:** 10 rising band-crossings, OTI_T rule accuracy 1.0
  (0 violations in 20,316 records, all branches), empty interval (54, 236),
  max rates +91.0 / −40.8 OTI-units/min under all of P1–P4.
- **Conditional physics:** under the extreme 100 %-power-to-oil bound with
  observed loads (33–142.1 kW), the observed rises (182–206 OTI units in
  2–18 min) imply effective thermal masses of ~32–426 kg — far below
  distribution-class oil-equivalent masses; masses ≥ 300 kg would need
  sustained 0.1–4.9 MW. With realistic loss fractions the feasible masses
  shrink further. Apparent channel recovery τ = 0.5–26 min (144/150
  sensitivity rows valid; invalid log-domain pairs excluded, never
  clipped). Stated limitation: sampled data cannot exclude unobserved
  sub-interval electrical events; no root cause is claimed.

## Verification & tests

69 tests passing (39 Phase-1 + 30 Phase-2, synthetic fixtures only),
covering conflicting branches, P1–P4 (no flag averaging), high-OTI branch
isolation, occurrence streams, entity-unrecoverability, conditional units,
critical-mass math, τ domain guards, sensitivity, verifier agreement.
Environment: Python 3.13.14, pandas 2.2.3, numpy 2.3.5, matplotlib 3.10.9.
Commands: `run_data_audit.py`, `run_phase2_analysis.py`,
`independent_raw_verification.py` (stdlib-only recompute: 56/56 checks
agree; exits non-zero on disagreement), `pytest` — pre/post provenance
gates PASS.

## Key artifacts

`reports/phase_02_report.md` (13 sections); `source_lineage_report.md`;
`asset_scope_and_entity_analysis.md`; `variable_semantics_report.md`;
`asset_parameter_bounds.md`; `conditional_physics_analysis.md`;
`phase_01_code_review.md`; `docs/outreach_requests.md` (DRAFTS — NOT SENT);
16 new artifacts in `reports/generated/` (multiplicity, conflicts,
policy sensitivity, latent-stream diagnostics, variable semantics,
parameter evidence, physics sensitivity, τ per transition,
alternative explanations, source claim matrix SC01–SC11, bibliography
register, manufacturer envelope, phase_02_summary.json);
`reports/figures/physics_bounds_*.png`; registers updated
(C01–C36, A01–A27, S1–S16).

## Standing constraints preserved

Repeated records never silently discarded; no numeric probabilities; "OTI
units" not °C; near-250 never "ADC rail"; observed loading ≠ nameplate;
manufacturer specs from official sources only; physics conditional with
sensitivity curves; no "proven sensor fault"/"thermal impossibility"/
"TinyML" phrasing; actual Δt rates; entity-unresolved statement mandatory;
outreach drafts stored but not sent.

## Repository status and GitHub merge

- Phase-2 work committed on a clean tree: **`2aab096`** (main Phase-2
  commit) and **`8762ddb`** (spec alignment: claim-matrix columns, outreach
  targets), on top of Phase-1 commits `76b64ab` and `9d73ab2`. Full suite
  re-verified at each commit.
- **GitHub merge: NOT yet performed.** The workspace has no git remote, no
  `gh` CLI, no SSH keys, no stored credentials (verified), so pushing needs
  owner credentials. To merge yourself: `git remote add origin <URL> &&
  git push -u origin main` — or provide the repository URL plus a personal
  access token (repo/push scope) and the merge will be completed.

## Next steps (require owner input)

1. **GitHub merge** — provide the remote URL and credentials, or push with
   the command above.
2. **Authorization** to send any of the outreach drafts
   (`docs/outreach_requests.md`; four required targets + optional mirror
   draft) — the only route to entity scope, channel units, and asset
   parameters.
3. Any provider answers would upgrade variable semantics and the
   conditional physics from parameterized to asset-specific.
4. Optional: byte-comparison with the Energies-reported preprocessing
   (their internal row counts 17,207/17,640 do not match the file row
   counts — their preprocessing is undocumented).
