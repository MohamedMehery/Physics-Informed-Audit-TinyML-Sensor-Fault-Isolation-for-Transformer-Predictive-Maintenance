# Release Notes — v0.1.0 (2026-09-21)

**Transformer Telemetry Integrity Audit** — first public release.
Author: Mohamed Mehery (Independent Researcher).

This release is a **technical report / research software artifact** —
an evidence-first audit of the public Kaggle dataset "Distributed
Transformer Monitoring" plus a deterministic plausibility filter with
leakage-controlled evaluation. **It is not peer reviewed.**

- **DOI:** 10.5281/zenodo.22904790 (https://doi.org/10.5281/zenodo.22904790)

## What is included

- **Phase 1 — data audit:** provenance verification (official Kaggle
  archive, SHA-256 pinned), per-file row counts, cadence/gap analysis,
  duplicate-timestamp analysis, flag semantics (OTI_T/OTI_A/WTI/MOG_A),
  electrical context around excursion onsets
  (`reports/phase_01_report.md`, `reports/generated/`).
- **Phase 2 — validity, lineage, conditional physics:** source-lineage
  triangle (uploader = first author of Putchala et al.; the Energies
  15(21):7981 study used this dataset), entity-identity analysis
  (unresolved), repeated-record policy sensitivity (P1–P4),
  assumption-labeled conditional physics bounds
  (`reports/phase_02_report.md`, supporting reports).
- **Phase 3 / 3R — deterministic plausibility filters:** four causal
  streaming filters (rate, range, combined, jump; 1–11 operations per
  sample) with a leakage-controlled frozen-threshold chronological
  replay as the primary result, plus a clearly separated 1,160-
  configuration **exploratory / oracle** sweep
  (`reports/phase_03r_report.md` — authoritative; the original Phase-3
  report is archived under `docs/archive/superseded_phase3/`).
- **C reference implementation:** C99 filter skeleton with Python/C
  parity on the full official replay sequence (19,376 samples × 4
  filters × 2 gap behaviors, 0 mismatches; `firmware_skeleton/`).
- **Consolidated citable technical report:** `paper/technical_report_v0_1.md`.
- **Test suite:** 137 tests, including provenance gates, replay/parity
  checks, and automated overclaim guards
  (`tests/`, `python -m pytest` → 137 passed).
- **Figures:** 6 PNGs; the 3 full-data-sweep figures carry in-image
  "EXPLORATORY / ORACLE SWEEP" labels; physics figures are
  assumption-labeled (`reports/figures/`,
  `paper/figures_tables_inventory.md`).
- **Documentation:** README, `docs/reproducibility_quickstart.md`,
  `docs/release_checklist.md`, claim/assumption registers,
  documentation map, `paper/references.bib` + `references.md`.
- **Citation and license metadata:** `CITATION.cff`, `.zenodo.json`,
  `LICENSE` (Apache-2.0, code), `CONTENT_LICENSE.md` (CC BY 4.0,
  documentation/reports/figures), `NOTICE`.

## What is NOT included

- **Raw Kaggle data.** The dataset ("Data files © Original Authors",
  redistribution conditions unverified) is NOT redistributed: raw and
  downloaded files are gitignored; only hashes, manifests, code, and
  documentation are tracked (`data/README.md`).
- **Trained ML models.** No ML model is trained anywhere in this
  project; the filters are deterministic plausibility checks, not a
  validated physical-fault detector, and no fault-detection validation
  is claimed (no field-confirmed labels exist).
- **Measured MCU benchmarks.** Cortex-M0 cycle counts are illustrative
  estimates from documented instruction-timing tables; no cross-build
  or board was used. Only `sizeof(mif_filter_t) = 72 B` is measured
  (host reference).
- **Figures F1–F3** (OTI series, replay alert classes, T3 horizons):
  not generated in v0.1.0; the technical report presents their content
  as tables instead (`paper/figures_tables_inventory.md`).
- **Peer review.** None has occurred.
- **Outreach.** None has been sent (`docs/outreach_requests.md` drafts
  are stored only; outreach waits until after publication + DOI).

## Key results (conservative wording)

- Ten operationally defined high-band OTI excursions (single-step
  ≤ 54 → ≥ 236 OTI units, no values observed in between; rates up to
  91 OTI-units/min). Entity identity remains unresolved; OTI
  engineering unit unconfirmed; no field-confirmed hardware root cause.
- Post-hoc leakage-controlled replay (internal validation only) with
  thresholds frozen on pre-event calibration data: range/jump/combined
  rules flag 10/10 events at or before the crossing sample (exact 95%
  CI [0.6915, 1.0]; n = 10) at 0–0.26 false-alert episodes/day
  (bootstrap CI [0.181, 0.343] for the range rule); the rate rule flags
  9/10 (P1/P3/P4) or 5/10 (P2_first) — view-dependent.
- The tested OTI-only deterministic rules did not demonstrate robust
  multi-hour warning.

## Limitations (summary)

Single dataset; n = 10 events (wide CIs); sampling irregular with gaps
up to 33.6 days; events operationally defined, not field-confirmed
faults; full-data sweep is exploratory/oracle; replay is internal
validation only; cycle counts illustrative; the Energies 24-hour-advance
statement was not reproduced by this project (its evaluation was not
reproduced either; no judgment on its validity). Full list:
`paper/limitations.md`.

## Licensing

- Code: Apache License 2.0 (`LICENSE`).
- Documentation, reports, figures, technical-report text: CC BY 4.0
  (`CONTENT_LICENSE.md`).
- The Kaggle dataset is © Original Authors, is not owned by the
  repository author, and is not redistributed; neither license applies
  to it (`NOTICE`).

## How to cite

See `CITATION.cff` (or the GitHub "Cite this repository" button):
Mohamed Mehery, *Transformer Telemetry Integrity Audit*, v0.1.0,
2026-09-21. https://doi.org/10.5281/zenodo.22904790. The dataset must be cited separately (see
`README.md`).
