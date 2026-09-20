# Asset Parameter Bounds — Phase 2

**Rules enforced:** observed loading ≠ nameplate; the record load (142.9 kVA)
establishes nothing about rating; 1500 kVA is another paper's own system, not
this asset; no "typical" rating or oil-mass values are asserted; manufacturer
data only from official manufacturer/utility sources (not resellers); rating
remains unbounded above. Machine-readable tables:
`reports/generated/asset_parameter_evidence.csv` (per-parameter),
`reports/generated/manufacturer_spec_envelope.csv` (official envelope).

---

## 1. Identity parameters (all UNKNOWN)

| Parameter | Status | Why it cannot be filled |
|---|---|---|
| # transformers in export | UNKNOWN | no asset column; platform = 52 locations (Putchala Sec. 4) |
| # devices | UNKNOWN | no device column; multiplicity structure (2.3–4.8 % repeats) inconsistent with a constant second stream |
| # feeders | UNKNOWN | one VL/IL triple per timestamp; no feeder ID |
| Location | UNKNOWN (platform: Tripura, India — *platform-level*, not export-level) | Putchala (S11) Sec. 4 describes the live platform, not this export's scope |
| Nameplate rating | UNKNOWN; unbounded above | no primary source; 142.9 kVA observed ≠ rating; 1500 kVA belongs to Energies' own Sharjah system |

## 2. Measured/derived parameters (observed, this export)

| Parameter | Value | Basis |
|---|---|---|
| Window | 2019-06-25 .. 2020-04-14 | timestamps |
| Cadence | 15-min median; observed intervals 1–9 min; gaps >30 min: 101–115/file; largest gap 33.6 days (2019-07/08) | interval summary |
| Secondary voltage | ~220–256 V phase; ~381–443 V line | CurrentVoltage |
| Max load | 142.9 kVA / 142.1 kW (2020-01-27) | TotalPower |
| Load range during excursions | 33.4–103.0 kW (nearest samples ±12 min) | excursion context |
| OTI band | 0–54 normal; 236–250 excursion band; empty (54, 236) | Overview |
| Ambient (ATI) | 0–44, °C-consistent, unit unconfirmed | Overview |

## 3. Official manufacturer/utility envelope (SECONDARY; unrelated to the dataset asset)

Purpose: plausibility ranges for *distribution-class* equipment only. Sources
are official manufacturer pages or a utility procurement specification;
reseller listings and unofficial standard copies were rejected. No per-rating
oil volumes were obtainable from official sources (ETT publishes masses but
not oil volumes; BSES Annexure D oil tables sit beyond the parseable page
limit; Bharat Bijlee publishes only corporate-range material).

| Spec (official) | Data captured | Oil volume |
|---|---|---|
| ETT 200 kVA 11/0.433 kV ONAN (IS 1180/IS 2026) | rating/voltage/cooling | not published |
| ETT 315 kVA 11/0.433 kV ONAN | rating/voltage/cooling | not published |
| ETT 1000 kVA 11 kV/433 V | total mass 4,065 kg | not published |
| ETT 1600 kVA 11/0.433 kV | total mass 6,026 kg | not published |
| BSES Delhi SP-TRDU-02-02 (rev 02, 2019-12-12) | 400/630/1000 kVA, 11/0.433 kV, ONAN, class A, 50 °C design ambient, IS 2026/IS 1180; **WTI/OTI scanner + MOG listed as standard accessories** (approved makes Pecon/Precision) | Annexure D (not parsed) |
| Bharat Bijlee transformers brochure | range up to 200 MVA/400 kV (corporate) | not published |
| IS 1180:2014 Part 1 (scope) | oil-immersed DTs ≤ 2500 kVA, 33 kV class | n/a |

Two envelope facts are used qualitatively elsewhere: (a) WTI/OTI/MOG are
standard DT instrumentation in this market (so the channel set is ordinary
DT telemetry); (b) 11 kV-class DT masses run 1–6 t at 200–1600 kVA — context
for the physics scenario grid, **not** an assertion about the audited asset.

## 4. Parameters used by the conditional physics, and their status

| Parameter | Value used | Status |
|---|---|---|
| Effective thermal mass | scenario grid 50–3,000 kg | parameterized (no asset value asserted) |
| Specific heat c | 1.8 / 2.1 kJ/(kg·K) (mineral-oil typical band) | scenario label only |
| Heat input | timestamp-aligned local max (33–103 kW), global max 142.1 kW, parameterized 500/1500 kW | scenarios; 100 %-to-oil is an explicit extreme bound |
| ΔT | observed 182–206 OTI units | unit-conditional |
| Δt | observed actual intervals 2–18 min | observed |
| Ambient | ATI channel ± 5 units | proxy, unit-unconfirmed |

**Nothing in the parameter table is a claim about the audited asset.** The
rating and oil mass are unknowable from the published data; outreach requests
(docs/outreach_requests.md, NOT sent) ask the provider for exactly these.
