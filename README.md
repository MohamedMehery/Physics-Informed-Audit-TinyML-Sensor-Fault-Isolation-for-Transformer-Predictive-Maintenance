# ⚡ Physics-Informed Audit of Transformer Telemetry: 
# Why "OTI Trip" Labels May Reflect Sensor Faults, Not Thermal Events

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Result-Negative%20(documented)-orange.svg)]()

> **Scope note (read first):** This repository documents a *data-centric
> audit* of a public transformer-monitoring dataset. Its core claim is
> narrow and defensible: the high-temperature "trip" labels (`OTI_T`) are
> **inconsistent with a physical top-oil thermal transient** and are most
> plausibly a **measurement-chain / telemetry anomaly**. We deliberately do
> NOT claim a confirmed hardware root cause, because the dataset provides no
> nameplate, thermal-mass, cooling-class, sensor-type, or protection-logic
> metadata.

---

## 1. Evidence Tiering (important)

Every finding below is tagged by how strongly the data supports it:

- **[DATA]** — provable directly from the raw files; independent of transformer specs.
- **[PHYS-COND]** — supported by physics under stated, conservative assumptions.
- **[HYP]** — plausible engineering hypothesis; NOT proven; needs field data.

---

## 2. Findings

### [DATA] Strict separability of the trip flag
`OTI_T = 1` occurs iff `OTI >= 236 °C` across 100% of rows (n = 19,376).
=> Any *same-timestep* classifier that ingests `OTI` (or a direct transform
of it) can reach ~99% accuracy by learning a trivial threshold. This is
target triviality/leakage, not learned thermal dynamics.

### [DATA] Bimodal observation gap
Zero readings exist in the 70–236 °C band (a 166 °C void). Physical heating
would necessarily traverse this band. A complete gap is characteristic of a
two-state / saturating digital behaviour.

### [DATA] No coincident electrical disturbance
During each OTI excursion, VL1–VL3 (~220 V), line-to-line (~380 V), and
IL1–IL3 (~136–170 A) remain stable; WTI and OLI do not move. Only the OTI
channel changes. (Cross-checked against CurrentVoltage.csv.)

### [DATA] High autocorrelation
OTI lag-1 r ≈ 0.86 => random shuffling of train/test causes leakage; only
block/temporal splits are valid.

### [PHYS-COND] Heating is energetically impossible (critical-mass form)
Using the *measured* load only:
  m_crit = P·Δt / (c·ΔT) = 102,969 W × 120 s / (1900 J/kg·K × 182 K) ≈ 35.7 kg
Even assuming 100% of measured electrical power converts to heat inside the
oil (physically impossible), no more than ~35.7 kg of oil could rise 182 °C
in 2 min. Independently sourced specs for 100–250 kVA distribution
transformers indicate oil mass on the order of ~150–370 kg (≈1.4–1.6 L/kVA,
density ≈0.89 kg/L). Since the lower bound (~150 kg) exceeds m_crit by >4×,
the observed rise is energetically impossible across the entire plausible
rating range. (No single oil-mass value is assumed.)

### [PHYS-COND] Cooling implies an impossible time constant (scale-independent)
Fitting an exponential decay to the 248→52 °C drop over 8 min (Ta ≈ 39 °C):
  τ_apparent ≈ 2.9 min
This is ~2 orders of magnitude below the multi-hour oil time constants used
in IEC 60076-7 / reported for ONAN distribution transformers. This argument
does not depend on oil mass at all.

### [HYP] Candidate hardware causes (NOT proven)
Consistent-with, but unconfirmed: RTD/transmitter open-circuit with upscale
burnout; ADC upper-rail saturation near ~250 °C; RC-filtered step response
(236 °C then 248 °C); daytime clustering suggesting an environmental/thermal
covariate at the marshalling box. Confirmation requires device metadata or
physical inspection.

---

## 3. Asset Parameter Estimation (transparent, bounded)

The dataset gives no nameplate. We estimate, with explicit tolerances:

| Parameter          | Estimate            | Basis / Confidence            |
|--------------------|---------------------|-------------------------------|
| Observed load      | ~100 kVA            | [DATA] measured V·I and KVA   |
| Nameplate rating   | 100–250 kVA         | [HYP] IS-1180 sizes + loading |
| Cooling class      | ONAN (likely)       | [HYP] typical for this class  |
| Oil mass           | ~150–370 kg         | [PHYS-COND] mfr specs, ±range |
| Oil c              | ~1900 J/kg·K        | mineral-oil literature value  |
| Oil density        | ~0.89 kg/L          | IEC 60296 typical             |
| Oil time constant  | order of hours      | IEC 60076-7 / literature      |

All physics claims are stated so they hold across these ranges, not at a
single assumed point.

---

## 4. Implication for TinyML

Do NOT train a heavy model to "predict OTI_T". Instead, a Stage-1 sensor-
integrity check flags implausible dynamics on-device:

    |ΔOTI/Δt| > threshold   (calibrated from data; see Section 5)

Empirical calibration (from this dataset):
  - Quiet operation |dOTI/dt|: median 0.067, p99 0.333, p99.9 2.0 °C/min
  - Glitch events: mean 8.2, max 91 °C/min
A threshold near 2.0 °C/min separates the two populations cleanly.
(Note: rate must be computed with the ACTUAL Δt between samples, since
telemetry is event-triggered and Δt varies from 1–15 min.)

---

## 5. Repro

    python audit_transformer_data.py        # sampling, onsets, autocorrelation
    python build_episode_table.py           # NOTE: set gap_tolerance carefully (see below)
    python fit_thermal_model.py             # IEC 60076-7 top-oil ODE on quiet data
    python inspect_raw_oti.py               # raw-line inspection around episodes
    python verify_glitch_authenticity.py    # plain-text + V/I cross-check
    python reviewer_audit_checks.py         # separability, histogram, rate percentiles

---

## 6. Known limitations
- Single dataset; no nameplate/field metadata.
- Root cause is hypothesised, not confirmed.
- Episode counts depend on `gap_tolerance` (see Section 7).

---

## 7. Correction log (transparency)
- Removed fixed oil-mass assumption (300 kg) and the derived 232.7 kW figure;
  replaced with critical-mass (35.7 kg) and time-constant (2.9 min) arguments.
- Reclassified all hardware-specific claims (PT100, ONAN, ADC rail) as [HYP].
- Flagged episode-merge sensitivity (E09/E10 were two glitches merged by a
  6 h tolerance window).
