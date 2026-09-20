# Phase 1 Handoff — Data & Provenance Audit

**1. Status: COMPLETE** (one scope deviation, documented: the README to
archive never existed — see item 10).

**2. Git:** repository initialized during Phase 1; initial commit hash
recorded in the repository log (first commit: "Phase 1 — evidence-first
bootstrap, provenance, asset identity, data audit").

**3. Official dataset acquisition: SUCCESS.** Downloaded anonymously from
the official Kaggle API endpoint (no mirror, no credentials needed):
"Distributed Transformer Monitoring", `sreshta140/ai-transformer-monitoring`,
version 1 (2020-05-25), owner Sreshta Putchala, accessed 2026-09-20 (UTC).
Archive 1,481,162 B, SHA-256 `b9257e990d480b3486b176bc19304a18b4aa82fd07dc559ec16aaa3ed3fe9c68`;
5 CSVs hashed in `provenance/dataset_manifest.json`. Displayed license
"Data files © Original Authors"; redistribution unverified → raw files
gitignored, never committed.

**4. Confirmed facts** (artifacts in `reports/generated/`, claims in
`docs/claim_register.md`): 5 files, 19,352/20,316/19,309/19,308/19,248 rows,
2019-06-25→2020-04-14; irregular cadence (median 15 min but 1–9-min
intervals present; max gap 48,399 min ≈ 33.6 days); duplicates in every
file (Overview: 931 groups, 568 identical, 363 conflicting); OTI spans
0–250 with an empty observed interval **(54, 236)** — the "70–236" figure
does not reproduce; 47 OTI ≥ 236 rows in 10 windows (Jul 16–Sep 3, 2019);
OTI_T=1 ⟺ OTI ∈ [236, 250] (threshold rule reproduces it 100%); OTI_A
also active at OTI 29–30 (Jul 3–4) — not a pure OTI-threshold alarm; WTI
binary {0,1}, active only Jan–Apr 2020, zero during all high-OTI rows;
MOG_A=1 ⇒ OLI ≤ 41 (not conversely); excursion transition rates +11.1 to
+91.0 units/min on actual Δt (normal-mode p99 0.33); no coincident
electrical disturbance visible at ±30-min resolution (VL1 219.8–234.2 V;
observed load 33.4–103.0 kW; record max 142.9 kVA — operating load, not
nameplate); all-5-file timestamp intersection 18,324.

**5. Important unknowns:** nameplate rating, HV/LV ratio, nominal LV
voltage (only ~230/400 V class inferred), cooling class, oil mass/volume,
oil type, thermal time constant, sensor type, transmitter range, ADC rail,
protection logic, manufacturer/model, site/country (50 Hz only), time
zone, OTI units (°C assumed, flagged), OLI units, WTI semantics.

**6. Asset-identification result:** identifiable only as an oil-immersed
three-phase distribution transformer monitored on its LV side in a 50 Hz
system. The "1500 kVA, 11(10)/0.4 kV" figure is traced to Energies 2022
(DOI 10.3390/en15217981), which describes **its own** system and calls the
Kaggle data "similar transformers" — unverified lead, not fact. Kaggle
discussions (location question; nameplate request posted 2026-09-19) have
no answers. Mirror `pythonafroz/transformer-fault-analysis` verified
byte-identical; adds nothing.

**7. Reproduced audit numbers:** see item 4; full tables:
`dataset_inventory.csv`, `timestamp_interval_summary.csv`,
`duplicate_timestamp_report.csv` (+summary), `alarm_summary.csv`,
`oti_threshold_analysis.csv`, `oti_rate_summary.csv`/`oti_rate_stats.json`,
`primitive_events.csv`, `event_merge_sensitivity.csv`,
`cross_file_alignment.csv`, `excursion_electrical_context.csv`,
`power_formula_crosscheck.json`, `phase_01_summary.json`.
Event-definition sensitivity: OTI_T 10 windows (continuity gap 15/30 min;
merge 15/30/60 min) → 8 at 360-min merge; OTI_A 13/12 → 10; MOG_A 68/24 →
8; WTI 378/307 → 14. All counts stated with their definitions.

**8. Tests: 39 passed, 0 failed** (`python -m pytest`; synthetic fixtures
only). Pipeline commands: `python scripts/download_dataset.py`,
`python scripts/run_data_audit.py` (pre+post provenance gates PASS — raw
files unmodified). Environment: Python 3.13.14, pandas 2.2.3, numpy 2.3.5.

**9. Files created:** `README.md` (new, conservative), `pyproject.toml`,
`.gitignore`, `data/README.md`, `docs/research_protocol.md`,
`docs/claim_register.md`, `docs/assumption_register.md`,
`docs/archive/README_initial_unverified.md` (placeholder),
`provenance/dataset_manifest.json`, `provenance/source_register.csv`,
`src/transformer_audit/` (io, timestamps, provenance, audit, events,
electrical), `scripts/download_dataset.py`, `scripts/run_data_audit.py`,
`tests/` (39 tests), `reports/asset_identity_evidence.md`,
`reports/phase_01_report.md`, this handoff, and 20 generated artifacts in
`reports/generated/`. Raw data in gitignored `data/`.

**10. Differences from old README:** none possible — the working tree
arrived empty (no README, no Git history); nothing was archived because
nothing existed, nothing was inherited, nothing fabricated. The archive
slot documents this. Had the draft existed, these would have been removed
per protocol: 300 kg oil mass, ONAN/232.7 kW cooling, 2–3 h time constant,
PT100/open-circuit/ADC-rail claims, 100–250 kVA nameplate, "all 99% models
invalid", "proven TinyML", MIT badge. The new README contains none of
these; "70–236 °C gap" is corrected to the reproduced (54, 236).

**11. Exact blockers:** none for Phase-1 scope. Open items: dataset
license/redistribution clarification; author answers to nameplate/location
questions; OTI unit confirmation.

**12. Recommended Phase 2:** (a) deterministic physics-informed edge-rule
prototyping on actual Δt (excursion ≥11 vs normal p99 0.33 units/min —
>30× separation; include zero-recovery artifact signature); (b)
cross-channel consistency study (WTI semantics, MOG_A/OLI logic,
duplicate-conflict patterns); (c) author outreach via Kaggle discussion;
(d) task-fair causal-forecasting vs same-timestamp-proxy baseline design
before any statement about published ~99% results; (e) thermal modelling
only after asset parameters or justified bounds exist, with registered
assumptions and sensitivity analysis. Hardware root cause remains
unestablished: current permitted wording — the observations may be
inconsistent with a normal top-oil thermal transient and may be more
consistent with a measurement-chain or telemetry anomaly; the exact
hardware root cause remains unknown.
