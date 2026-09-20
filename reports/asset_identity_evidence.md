# Asset-Identity Evidence Report (Phase 1)

**Question:** Can the monitored transformer be identified more precisely
than "an oil-immersed distribution transformer" from verifiable evidence?

**Method:** targeted investigation of (1) official Kaggle metadata and the
downloaded archive; (2) all Kaggle discussion topics on the dataset;
(3) the dataset author's Kaggle profile and other datasets; (4) exact
searches on the distinctive column combination OTI, WTI, ATI, OLI, OTI_A,
OTI_T, MOG_A (+ VL12/INUT); (5) papers citing the dataset; (6) potential
originating IoT projects; (7) metadata embedded in files/archive.
Sources are registered in `provenance/source_register.csv` (S1–S10).

## 1. Evidence table

| Candidate claim | Value | Evidence class | Source | Primary/secondary | Exact support | Confidence | Allowed wording |
|---|---|---|---|---|---|---|---|
| Dataset exists, v1, 5 CSVs, IoT-collected, 2019-06-25→2020-04-14, "updated every 15 minutes", column glossary (OTI=Oil Temperature Indicator, WTI=Winding Temperature Indicator, ATI=Ambient, OLI=Oil Level, OTI_A=Alarm, OTI_T=Trip, MOG_A=Magnetic oil gauge indicator, VL/IL/INUT) | as stated | [CONFIRMED-SOURCE] | Kaggle dataset page + API metadata (S1, S2) | Primary | Verbatim in description; metadata JSON hash-logged | High | "The dataset description states …" (the 15-min claim is contradicted in detail by the data — C05) |
| Three-phase asset | three phase voltages VL1–VL3, three currents IL1–IL3, line-line voltages VL12/23/31, neutral current INUT | [DERIVED] | Raw data structure (C18) | Primary (data) | Columns + plausible three-phase electrical values; Σ(VLx·ILx) matches reported KVA to 1.36% median | High (structure) | "The monitoring is three-phase" |
| Monitored voltage side | LV side | [INFERENCE] | Voltage magnitudes: VL1 nonzero band ≈221–261 V, VL12 ≈378–447 V (C18) | Primary (data) | Phase voltages ~230 V class; HV side would show kV-class values | Moderate | "Consistent with LV-side monitoring; not confirmed" |
| Nominal LV voltage | ~0.4 kV class (230/400 V class system) | [INFERENCE] | Observed bands (C18); secondary paper's "0.4 kV" (S7) | Mixed | Data shows 221–261 V phase; nominal not stated anywhere | Moderate-weak | "Consistent with a 400 V-class LV system; nominal unverified" |
| HV/LV voltage ratio | 11/0.4 kV or 10/0.4 kV | [UNKNOWN] | S7 says 11→0.4 kV **for its own system**, not this asset; 10/0.4 variant found in no primary source during Phase 1 | Secondary only | No primary attribution | Low | "Unknown; a secondary paper's own system used 11/0.4 kV" |
| Nameplate kVA rating | 1500 kVA | [UNKNOWN] (lead: [INFERENCE]) | S7 (Energies 2022) describes its system's transformer as 1500 kVA and adopts the Kaggle data as from "similar transformers sharing load capacity, manufactured age, measuring units, and installed environment conditions" | Secondary | The paper never states the Kaggle asset itself is 1500 kVA | Low | "Unverified research lead; do not state as fact" |
| Observed electrical loading | max 142.9 kVA / 142.1 kW over the record; 33.4–103.0 kW in ±30-min windows around OTI_T onsets | [CONFIRMED-DATA]/[DERIVED] | `excursion_electrical_context.csv`, TotalPower | Primary (data) | Reproducible numbers | High | "Observed load near the event" — never nameplate |
| Cooling class (ONAN etc.) | any | [UNKNOWN] | No source | — | None | — | "Unknown" |
| Oil volume / mass | any | [UNKNOWN] | No source | — | None | — | "Unknown" |
| Manufacturer / model | any | [UNKNOWN] | No source | — | None | — | "Unknown" |
| Sensor type (PT100/thermocouple/…) | any | [UNKNOWN] | No source; dataset says only "IoT devices" | — | None | — | "Unknown" |
| Transmitter measurement range | any (note: OTI observed max 250, an integer, with no values in (54,236) — see C08) | [UNKNOWN] | No source; data shows quantized integers | — | Range/rail not established | — | "Unknown; the 0–250 observed span and the (54,236) gap are data facts, not range facts" |
| Site / country | any (50 Hz system per FRQ∈[49.6,50.2]) | [UNKNOWN] | Discussion S4 (location question) has no identifying answer; author profile location is the *author's*, not the asset's | — | None for the asset | — | "Unknown; 50 Hz excludes 60 Hz regions only" |
| Time zone | any | [UNKNOWN] | No source; timestamps are tz-naive | — | None | — | "Unknown" |
| Protection logic (what OTI_A/OTI_T/MOG_A actuate, relay/breaker behavior) | any | [UNKNOWN] | No source; flags exist in data only | — | OTI_T=1 co-occurs with OTI≥236 and OTI_A=1 (C09); OTI_A also active at OTI 29–30 (C10) — the *logic* is not documented | — | "Unknown; observed co-occurrences are data facts" |
| The dataset is also re-uploaded as `pythonafroz/transformer-fault-analysis` | mirror with byte-identical shared files (Overview.csv renamed Alarm.csv; description copied into a .txt) | [CONFIRMED-DATA] (identity) | S9; SHA-256 comparison | Secondary (mirror) | 5/5 shared files hash-identical to official archive | High (identity) | "A verified mirror; adds no provenance information" |

## 2. Parameter conclusions

| Parameter | Conclusion |
|---|---|
| Number of phases | **Confirmed (three-phase monitoring structure)** — from data |
| Monitored voltage side | **Weakly inferred (LV)** — from voltage magnitudes |
| Nominal LV voltage | **Bounded (~230/400 V class)** — not confirmed nominal |
| HV/LV ratio | **Unknown** (secondary 11/0.4 kV lead does not attribute to this asset) |
| Observed electrical loading | **Confirmed (data)** — max 142.9 kVA; event-window 33–104 kW |
| Nameplate kVA rating | **Unknown** (1500 kVA = unverified secondary lead) |
| Cooling class | **Unknown** |
| Oil volume / mass | **Unknown** |
| Manufacturer / model | **Unknown** |
| Sensor type | **Unknown** |
| Transmitter range | **Unknown** (observed 0–250 span is not a range specification) |
| Site / country | **Unknown** (50 Hz only) |
| Time zone | **Unknown** |
| Protection logic | **Unknown** (flag co-occurrences are documented as data facts) |

## 3. Investigation notes

1. **Kaggle discussions (3 topics)**: (a) "Anybody knows the location of
   distributed transformer" — no identifying answer (last comment asks the
   same question back); (b) "Request for Transformer Nameplate Data and
   Specifications" (posted 2026-09-19, i.e., one day before this audit) —
   zero replies; (c) an unrelated help request. The dataset author has not
   published asset specifications in discussions.
2. **Author profile**: Sreshta Putchala (Notebooks Master; data-science
   practitioner). Other datasets (COVID genome sample, diabetes) are
   unrelated. No originating IoT project or paper by the author was found.
3. **Papers citing the dataset**: Energies 2022 (10.3390/en15217981) —
   origin of the 1500 kVA / 11→0.4 kV description **for the authors' own
   system**, with the Kaggle data described as from "similar transformers";
   IET EPA 2025 (Tamakloe et al., 10.1049/elp2.70011) — cites the dataset.
   Neither is a primary source for this asset's identity.
4. **Embedded metadata**: CSVs contain only the header + data rows; the
   archive stores plain deflate entries with 2020-05-25 timestamps; no
   comments/worksheets/extra properties. Nothing identifying.
5. **The "10/0.4 kV" variant** of the lead claim was not found in any
   primary source during Phase 1; the originating paper says 11→0.4 kV for
   its own system. Both variants remain unattributable to this asset.

## 4. Bottom line

The asset is identifiable only as **an oil-immersed, three-phase
distribution transformer monitored on its LV side in a 50 Hz system, with
IoT telemetry from 2019-06-25 to 2020-04-14**. Every nameplate, thermal,
sensor, protection, and geographic parameter remains UNKNOWN on current
evidence. The 1500 kVA / 11(10)/0.4 kV figures circulating in secondary
literature describe *another paper's system* and must not be presented as
facts about this asset.
