# Assumption Register

Assumptions are declared, bounded, and sensitivity-tested — never hidden.
Required-UNKNOWN asset parameters (nameplate rating, oil mass, cooling
method, oil type, thermal time constant, sensor type, transmitter range,
exact fault mechanism, site location, time zone) are listed here as
UNKNOWN until a primary source or documented derivation changes them.

| ID | Assumption | Why needed | Range / alternatives | Sensitivity required | Current status |
|---|---|---|---|---|---|
| A01 | OTI (and ATI) values are in degrees Celsius | Reporting rates and temperature comparisons in familiar units | Any linear unit (°C/°F/K); dataset description does not state units | All rate numbers scale linearly with the unit; the discontinuity gap (54→236) and separability results are unit-independent | ASSUMED (unstated in source); flag in every rate statement |
| A02 | Timestamps are tz-naive local wall-clock times | Interval and rate computation | UTC vs local time; any offset shifts daily patterns, not Δt | Δt-based results are offset-invariant; time-of-day patterns would shift | ASSUMED (naive); do not interpret local time-of-day absolutely |
| A03 | `DeviceTimeStamp` is the measurement time (not ingestion/telemetry time) | Event timing and cross-file alignment | Telemetry/ingestion delay would decouple channels | Cross-file nearest-delta medians are 0 min, which supports (but does not prove) synchronized logging | ASSUMED; monitor alignment deltas |
| A04 | Duplicate-timestamp policy "first" for canonical series | Single-series statistics (rates, autocorrelation, onsets) | first / last / mean (all implemented) | Onset counts for OTI_A/OTI_T/MOG_A are policy-stable; WTI varies 277–288; rates use positive-Δt intervals only | DECLARED; sensitivity reported in `alarm_summary.csv` |
| A05 | "High-OTI excursion" defined as OTI ≥ 100 (splitting the 54–236 empty interval) | Separates excursion-band from normal-band statistics | Any threshold in (54, 236) gives identical classification on this data (no values in the gap) | None — the empty interval makes the split unique up to any interior threshold | DECLARED; justified by C08 |
| A06 | WTI/OTI_A/OTI_T/MOG_A are binary status/alarm channels (0/1) | Interpretation as flags, not temperatures | Could be scaled indicators; WTI is {0,1} in data so "winding temperature in °C" is contradicted by observed values | Treating WTI as temperature would be wrong on the data itself | CONFIRMED-DATA (binary); physical semantics UNKNOWN |
| A07 | Sampling cadence is NOT uniformly 15 min | All Δt-based computation | Metadata claims 15 min; observed Δt ∈ {1…9, 15, …, 48399} min | Assuming 15-min uniformity would overestimate excursion transition rates by up to 15× and misplace event boundaries | CONFIRMED-DATA (irregular); never assume uniform |
| A08 | OLI is a percentage-like level indication | Narrative convenience only | Units unstated; could be %, counts, or gauge units | No computation depends on OLI units; only range (36–100) and co-occurrence with MOG_A are used | UNKNOWN units; avoid unit language |
| A09 | Raw file integrity = manifest SHA-256 match | Trust in every downstream number | Any byte change invalidates provenance | Gates abort the audit on mismatch (pre- and post-run) | ENFORCED by `scripts/run_data_audit.py` |
| A10 | Cross-file simultaneity tolerance: exact-timestamp match (declared tolerance ±15 min reported separately) | Joining electrical context to thermal events | ±7.5 / ±15 / ±30 min | Excursion-context joins used nearest sample within the ±30-min window with per-event deltas reported (1–12 min observed) | DECLARED; per-event deltas always shown |
| A11 | LV-side voltage monitoring (phase ~221–261 V, line-line ~378–447 V nonzero bands) | Interpreting voltage magnitudes | HV-side measurement would show kV-range values; PT/VT ratios unknown | Inference from magnitudes only; nominal LV voltage and HV/LV ratio remain UNKNOWN | WEAKLY INFERRED |
| A12 | 50 Hz system (FRQ ∈ [49.6, 50.2] nonzero) | Regional plausibility only | 60 Hz systems excluded; many countries remain possible | Does not identify country/site | DERIVED (bounded) |
| A13 | Nameplate rating | — (future thermal analysis) | Any kVA; observed load peaks at 142.9 kVA (operating load, not nameplate) | Any thermal model scales with rating; 1500 kVA (S7) is an unverified secondary lead | **UNKNOWN / UNVERIFIED** |
| A14 | Oil mass / oil volume | — (future thermal analysis) | Any value | Dominant sensitivity in any oil-thermal model | **UNKNOWN** |
| A15 | Cooling class (ONAN/ONAF/OFAF/…) | — (future thermal analysis) | Any class | Changes heat-transfer model entirely | **UNKNOWN** |
| A16 | Oil type & specific heat | — (future thermal analysis) | Mineral/ester/… | Changes thermal capacity terms | **UNKNOWN** |
| A17 | Thermal time constant | — (future thermal analysis) | Minutes–hours | Determines plausibility of observed rates | **UNKNOWN** (2–3 h asset-specific value from the earlier draft is unsupported and removed) |
| A18 | Sensor type (PT100/thermocouple/…) and transmitter range | — (root-cause reasoning) | Any | Any hardware diagnosis depends on this | **UNKNOWN** |
| A19 | Exact fault/measurement mechanism (open circuit, upscale burnout, ADC rail, RC filter, junction-box effect, relay/breaker action) | — (root-cause reasoning) | Multiple candidate mechanisms | Phase 1 forbids mechanism conclusions | **UNKNOWN** |
| A20 | Site location / country / time zone | Context (weather correlation, etc.) | Any; 50 Hz bounds regions; discussion S4 has no answer | Affects ambient-temperature and load-cycle interpretation | **UNKNOWN** |
