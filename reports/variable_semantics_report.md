# Variable Semantics Report — Phase 2

**Method:** per-column examination of raw domain, unique values, behavior,
zero-coding, source definitions (Kaggle description + Putchala Table 2 +
Energies Sec. 7.1), confirmed units, and residual ambiguity. Machine-readable
table: `reports/generated/variable_semantics.csv`.

**Global rule adopted:** OTI values are reported in **"OTI units"** — the unit
is not confirmed by any primary source. WTI stays a **binary status channel**.
No channel is treated as °C, %, or any engineering unit without confirmation.

---

## Overview channels

| Column | Raw domain | n unique | Behavior (this export) | Source definition | Confirmed unit | Open ambiguity |
|---|---|---|---|---|---|---|
| OTI | 0–250 (integers) | 59 | normal band 0–54; **empty interval (54, 236)**; 47 rows at 236–250 in 10 windows 16 Jul–3 Sep 2019; 42 canonical zeros | "Oil Temperature Indicator" (all three sources, no unit) | **none** | unit unknown; band 236–250 far above any documented operating band (Energies (S7) overheat marker ≈90 on a C-scale; Putchala (S11) trip rule OTI>65 on their stream) — **near-250 values are NOT called an ADC rail** (no hardware metadata) |
| WTI | {0, 1} | 2 | 0 during all 47 high-OTI rows; active only Jan–Apr 2020 | "Winding Temperature Indicator" | none (binary) | binary here; sources do not explain why a *temperature* indicator is binary in this export; treated as a status flag, **not a temperature** |
| ATI | 0–44 | 34 | tracks diurnal cycle; correlates r=0.94 with OTI in the normal band (0.55 including excursions) | "Ambient Temperature Indicator" | none (°C-consistent range) | used as ambient proxy in τ analysis with ±5-unit sensitivity |
| OLI | 36–100 | 65 | discrete levels; mode 100; MOG_A=1 ⇒ OLI ≤ 41 | "Oil Level Indicator" | **none** (percent-like) | unit/zero-point unknown; do not read as % |
| OTI_A | {0, 1} | 2 | 1 on all 47 high-OTI rows **and** at OTI 29–30 on 3–4 Jul 2019 (53 rows) | "OTI Alarm" | none | not a pure function of shown OTI (29–30 activation unexplained) |
| OTI_T | {0, 1} | 2 | 1 exactly when OTI ≥ 236 (100 % of records, all branches); holds 1871/1871 inside repeated groups | "OTI Trip" | none | **indication vs command unknown**: Energies (S7) describes OTT as shutting off flow, but voltage/current continue through OTI_T=1 windows in this export → semantics unresolved |
| MOG_A | {0, 1} | 2 | active Jul–Aug 2019 only; implies OLI ≤ 41 | "Magnetic Oil Gauge (alarm)" | none | latch/hysteresis unknown |

## CurrentVoltage / Power / PowerFactor / TotalPower channels

| Column | Raw domain (this export) | Notes |
|---|---|---|
| VL1/VL2/VL3 | ~219.8–256.3 V (nonzero) | phase voltages; p01–p99 220–256; small counts of low outliers |
| VL12/VL23/VL31 | ~381–443 V | line voltages ≈ √3 × phase (consistent) |
| IL1/IL2/IL3 | 0–~250 A | long-tailed; zero runs overnight |
| INUT | 0–~65 A | neutral current; sources give no threshold for this export |
| KW / KVA / PF | KW 0–142.1; KVA 0–142.9; PF 0–1 | Σ(VLx·ILx) vs KVA median error 1.36 % (Phase 1) |

Units for VL/IL/KW/KVA are conventional (V/A/kW/kVA) and internally
consistent (line/phase ratio, power identity), so they are used; the
temperature/level channels carry no such internal check and remain
unit-unconfirmed.

## Representation hypotheses for the OTI 236–250 band (no root-cause claim)

1. **Error/status code** (values 236–250 encode a device state, not a
   temperature): supported by integer quantization, empty interval below,
   tight clustering, and threshold-perfect OTI_T alignment; falsified by an
   error-code table (not available).
2. **Saturated/converted representation** (sensor chain saturating or a
   conversion/status layer): not distinguishable from (1) without transmitter
   metadata; the values 236–250 are NOT uniform (they vary smoothly within
   the band), which a hard rail would not necessarily do.
3. **Genuine fast thermal excursion**: contradicted by energy bounds under
   observed loads (conditional_physics_analysis.md §A) but not excludable for
   unobserved sub-interval power; sampling cannot rule out what it does not
   see.
4. **Processed/aggregated artifact of the export pipeline**: consistent with
   H2-type ingestion effects elsewhere in the export; no direct evidence.

None of these is established. The project's standing wording remains:
"abrupt transitions into a band of 236–250 OTI units with an empty interval
(54, 236) below it," with no hardware root-cause claim.

## Consequences enforced in code

- `physics.py` operates on "OTI units" — no °C conversion anywhere; τ is
  offset-invariant (test-verified) so an unknown zero-point shift does not
  change τ; an unknown *scale* would scale ΔT and propagate into the
  conditional masses/powers exactly as the assumption tables state.
- No analysis averages OTI or binary flags across conflicting repeated
  records (P1–P4 policies; test-enforced).
- `variable_semantics.csv` records `confirmed_unit = none` for all Overview
  channels (test-enforced).
