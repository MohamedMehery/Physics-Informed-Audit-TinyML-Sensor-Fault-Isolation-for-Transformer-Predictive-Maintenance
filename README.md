# Transformer Monitoring Dataset — Evidence-First Audit

**Status: Phase 1 — data and provenance audit** (complete; see
`reports/phase_01_handoff.md`)

An evidence-first investigation of the public Kaggle dataset
**"Distributed Transformer Monitoring"**, focused on data quality,
provenance, asset identity, and reproducible characterization of the
recorded alarm/excursion behavior. This repository deliberately separates
what is *known* from what is *unknown*, and does not claim any hardware
root cause.

## Dataset (primary source)

| Field | Value |
|---|---|
| Title | Distributed Transformer Monitoring |
| URL | https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring |
| Slug | `sreshta140/ai-transformer-monitoring` |
| Owner | Sreshta Putchala (`sreshta140`) |
| Version | 1 — "Initial release" (created 2020-05-25T10:08:46.673Z, per Kaggle metadata) |
| Accessed | 2026-09-20 (UTC), official Kaggle API download endpoint (anonymous public access; no mirror) |
| License displayed | "Data files © Original Authors" — **redistribution conditions unverified** |
| Archive | 1,481,162 bytes, SHA-256 `b9257e990d480b3486b176bc19304a18b4aa82fd07dc559ec16aaa3ed3fe9c68` |
| Files | `CurrentVoltage.csv`, `Overview.csv`, `Power.csv`, `PowerFactor.csv`, `TotalPower.csv` (per-file hashes: `provenance/dataset_manifest.json`) |

Citation (dataset): Sreshta Putchala, "Distributed Transformer Monitoring",
Kaggle, version 1 (2020), https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring
(accessed Sep. 20, 2026).

> **License caution:** the raw dataset files are **not** redistributed in
> this repository (gitignored). The repository code license is a separate
> decision that the repository owner has not yet made; no license file is
> created on the owner's behalf, and no code license would permit
> redistribution of the Kaggle dataset.

## Research questions

1. **Provenance:** What exactly was downloaded, from where, and can it be
   verified byte-for-byte? (Done — manifest + provenance gates.)
2. **Asset identity:** Can the monitored transformer be identified beyond
   "an oil-immersed three-phase distribution transformer monitored on its
   LV side in a 50 Hz system"? (Phase 1 result: no — see
   `reports/asset_identity_evidence.md`.)
3. **Data quality:** How irregular is the timestamp cadence, how many
   duplicate/conflicting records exist, and how much do duplicate-handling
   policies and event definitions change the reported counts?
4. **Excursion behavior:** What exactly do the OTI alarm/trip channels and
   the OTI value discontinuity look like, at what rates (using *actual*
   Δt), and is anything visible in the electrical channels around them?
5. **Interpretation discipline:** Which conclusions are permitted by the
   evidence, and which popular claims (specific nameplates, cooling classes,
   sensor failures, "TinyML" labels) are unsupported?

## Evidence classification

Every claim is labeled (see `docs/research_protocol.md`):

- `[CONFIRMED-DATA]` — directly reproducible from the official raw dataset
  (artifacts under `reports/generated/`)
- `[CONFIRMED-SOURCE]` — explicitly stated by an identifiable primary source
- `[DERIVED]` — mathematically derived from confirmed measurements, with
  equations, units, assumptions, uncertainty documented
- `[INFERENCE]` — plausible but not uniquely established
- `[UNKNOWN]` — not available from current evidence (never guessed)

Registers: `docs/claim_register.md` (claims), `docs/assumption_register.md`
(assumptions; required-UNKNOWN parameters listed there).

## Reproducibility

Tested environment (recorded in `reports/generated/phase_01_summary.json`):
Python 3.13.14, pandas 2.2.3, numpy 2.3.5, Linux x86_64.

```bash
python -m pip install -e ".[test]"   # install package + pytest
python scripts/download_dataset.py   # official Kaggle download; verifies hash;
                                     # extracts raw/ (gitignored); writes manifest
python scripts/run_data_audit.py     # full audit -> reports/generated/*.csv|json
python -m pytest                     # 39 synthetic-fixture unit tests
```

`run_data_audit.py` verifies raw-file SHA-256 hashes against the manifest
**before and after** the run and aborts on any mismatch (raw files are never
modified). All rates use actual timestamp differences, never an assumed
15-minute cadence.

## Repository structure

```
README.md                     this file
pyproject.toml                package config (transformer-audit)
data/                         gitignored raw+download data; policy in data/README.md
docs/
  research_protocol.md        evidence rules, prohibitions, event definitions
  claim_register.md           every claim + evidence class
  assumption_register.md      every assumption + required-UNKNOWN parameters
  archive/                    archive slot for the prior README (none existed; see file)
provenance/
  dataset_manifest.json       dataset metadata, archive+file hashes
  source_register.csv         all sources (S1–S10), primary/secondary
src/transformer_audit/        io, timestamps, provenance, audit, events, electrical
scripts/                      download_dataset.py, run_data_audit.py
tests/                        39 unit tests (synthetic fixtures only)
reports/
  asset_identity_evidence.md  asset-identity investigation
  phase_01_report.md          detailed Phase-1 report
  phase_01_handoff.md         compact handoff
  generated/                  machine-readable audit outputs (CSV/JSON)
```

## Confirmed findings (Phase 1) — all reproducible

Full lists with artifacts: `docs/claim_register.md`, `reports/phase_01_report.md`.
Highlights (numbers: `reports/generated/`):

- **Provenance:** official archive obtained from Kaggle and hash-verified;
  a third-party mirror was checked and its shared files are byte-identical
  (it adds no provenance information).
- **Files:** 19,352 / 20,316 / 19,309 / 19,308 / 19,248 rows
  (CurrentVoltage / Overview / Power / PowerFactor / TotalPower);
  coverage 2019-06-25 → 2020-04-14.
- **Cadence is irregular** despite the "every 15 minutes" description:
  median interval 15 min, but intervals of 1–9 min occur, and the largest
  gap is 48,399 min (≈33.6 days); 17–19 gaps exceed 1 day per file.
- **Duplicate timestamps in every file** (e.g., Overview: 931 duplicate
  groups — 568 identical, 363 conflicting in ATI/OLI/OTI/WTI). Analyzed
  before canonicalization; onset counts for OTI_A/OTI_T/MOG_A are stable
  across duplicate policies, WTI varies (277–288 onsets).
- **OTI discontinuity:** OTI spans 0–250 with *no observed value between
  54 and 236*; 47 rows ≥ 236 (10 excursion windows, 2019-07-16 → 2019-09-03,
  active spans 10–136 min; 8 windows at a 360-min merge tolerance).
  Rising transitions reach +91 and falling −40.8 units/min over 2–8 min
  (actual Δt), vs a normal-mode p99 |rate| of 0.33 units/min.
- **Flags:** `OTI_T=1` ⟺ OTI ∈ [236, 250] in this dataset (a ≥236 threshold
  reproduces it 100% — association, not proven causality); `OTI_A=1` also
  occurs at OTI 29–30 during 2019-07-03/04, contradicting a simple
  OTI-threshold alarm model; `WTI` is binary {0,1} (not a temperature
  series; active only in 2020-01→04; 0 during all high-OTI rows);
  `MOG_A=1` ⇒ OLI ≤ 41 but not conversely (Jul–Aug 2019 only); OLI units
  are unstated.
- **Electrical context:** around every excursion onset the nearest
  electrical samples (within 1–12 min) show normal band voltages
  (VL1 219.8–234.2 V) and observed loads of 33.4–103.0 kW — *no coincident
  disturbance is visible in the available electrical channels at the
  dataset's temporal resolution* (this does not exclude events beyond that
  resolution/those variables). Observed apparent power over the whole
  record peaks at 142.9 kVA (operating load, not a nameplate rating);
  reported KVA cross-checks with Σ(VLx·ILx) to 1.36% median error.

### Permitted interpretation (current strength)

> The observations may be inconsistent with a normal top-oil thermal
> transient and may be more consistent with a measurement-chain or
> telemetry anomaly. The exact hardware root cause remains unknown.

## Unknowns and limitations (explicit)

**Unknown:** nameplate rating (the circulating "1500 kVA, 11/0.4 kV" figure
comes from a secondary paper describing *its own* system and is an
unverified lead for this asset), oil mass/volume, cooling class, oil type,
thermal time constant, sensor types, transmitter range, protection logic,
manufacturer/model, site/country (50 Hz system only), time zone, OTI units
(assumed °C for rate statements — flagged), OLI units, WTI's physical
semantics.

**Limitations:** sampling irregular and gappy; duplicate/conflicting
records present (quantified, with policy sensitivity); event counts are
definition-dependent (flag + continuity gap + merge tolerance always
stated); cross-file joins rely on timestamp equality (median nearest-delta
0 min, per-event deltas always reported); no thermal model was fitted in
Phase 1 by design.

**Not claimed anywhere in this repository:** any specific hardware root
cause (ADC railing, sensor open-circuit, etc.), any transformer
specification beyond the confirmed data structure, any "TinyML" solution
(no ML model is trained here — deterministic checks would be
physics-informed edge rules at most), and any invalidation of third-party
published ML results (none was independently reproduced here).

## History note

This repository's working tree arrived **empty** (no README, no Git
history) on 2026-09-20; the "unverified AI-generated README" that Phase 1
was asked to archive did not exist, so nothing was inherited and nothing is
fabricated. See `docs/archive/README_initial_unverified.md` and
`reports/phase_01_report.md` §1.
