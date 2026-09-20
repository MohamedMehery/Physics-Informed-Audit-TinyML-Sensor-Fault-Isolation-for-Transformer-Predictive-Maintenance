# Asset Scope and Entity Analysis — Phase 2

**Question (H1–H5):** Do the published rows form a valid time series for ONE
physical transformer? Hypotheses, none pre-selected:

- **H1** single transformer, repeated timestamps are legitimate repeated telemetry
- **H2** export duplication / ingestion re-transmissions
- **H3** multiple transformers/devices combined after asset/device-ID removal
- **H4** multiple feeders, one transformer
- **H5** corrupted/aggregated export, entity unrecoverable

**Ground rules:** repeated records are analyzed, never silently discarded;
no hypothesis is pre-selected; no numeric probabilities are assigned
(likelihood comparisons are qualitative and evidence-based).

---

## 1. What "valid time series for one transformer" would require

1. A single, monotonically increasing time base (yes: verified, no negative
   intervals in any file).
2. Channel values consistent with one measurement point (tested: §3–§5).
3. An identifier or a primary-source statement tying rows to one asset
   (**absent**: no device/location column; no primary statement of export
   scope; provider platform covers 52 locations per Putchala (S11) Sec. 4).

Requirement 3 is unmet, so the single-asset question cannot be answered by
metadata. The rest of this report evaluates the *statistical* evidence.

## 2. Repeated-timestamp structure (all five files)

| File | rows | unique ts | repeated groups | multiplicity |
|------|------|-----------|-----------------|--------------|
| CurrentVoltage | 19,352 | 18,915 | 437 | {1: 18,478, 2: 437} |
| Overview | 20,316 | 19,385 | 931 | {1: 18,454, 2: 923, 3: 7, 4: 1} |
| Power | 19,309 | 18,871 | 438 | {1: 18,433, 2: 438} |
| PowerFactor | 19,308 | 18,877 | 431 | {1: 18,446, 2: 431} |
| TotalPower | 19,248 | 18,842 | 406 | {1: 18,442, 2: 406} |

- Repeats touch only **2.3–4.8 %** of timestamps per file — a constant second
  device stream would repeat at ~100 %.
- **Cross-file sharing:** of Overview's 931 repeated groups, 420 share the
  timestamp with CurrentVoltage repeats (406/438 with Power, 376/431 with
  PowerFactor, 290/406 with TotalPower). Repeats are synchronized across
  files — consistent with a shared ingestion/export layer, not per-channel
  sensor behavior.
- **Raw-line adjacency:** all 931 Overview repeated groups sit on **adjacent
  raw lines** — consistent with re-transmission/retry (H2), and with
  export-stage duplication; inconsistent with two independent devices whose
  messages would interleave arbitrarily.
- **Monthly concentration:** Overview repeats by month — 2019-06: 448 (48 %,
  deployment start), then 20–84/month. A steady second device would not
  decay after deployment.
- **Occurrence-index check (P5 diagnostics):** share of timestamps with
  repeats ≤ 4.8 % << 90 % threshold → reconstructing per-device occurrence
  streams is NOT supported. `verdict_supports_stable_occurrence_streams: false`
  for every file.
- **Conflicts:** 363/931 Overview groups conflict in at least one column;
  magnitudes are tiny: OTI differences 1 unit in 144 groups, 2 in 32, 3 in 9,
  4 in 1, 33 in 1; CurrentVoltage VL1 median conflict 0.4 V (max 3.7 V), IL1
  median 6.4 A (max 25.6 A). Conflicting branches are near-identical
  re-readings, not different assets (a different transformer would not agree
  to 0.4 V).
- **Flag conflicts:** only 17/931 groups (WTI toggles at OTI 25–29,
  Jan–Feb 2020) — flags are not systematically split across branches.
- **High-OTI isolation:** the 47 records with OTI ≥ 236 fall in repeated
  groups **zero times**. The excursions are not created by record repetition.
- **Neighbor fit:** conflicting-group branches fit their time-neighbors
  equally well (first-branch mean |ΔOTI vs neighbors| 4.8 vs last-branch
  4.6) — no branch is consistently "the odd one out," so no branch can be
  assigned to a distinct device by continuity either.

## 3. Multiple-asset signatures (H3): absent

- **Voltage regimes:** VL1 (nonzero rows) p01/median/p99 = 220.1 / 242.7 /
  256.3 V; populated decade bands 220–260 form **one contiguous cluster**
  (no empty gap); VL12 likewise one cluster (381–443 V). Two interleaved
  assets on different feeders/tap positions would typically show separated
  voltage modes. (One cluster does not *prove* one asset — it is consistent
  with H1/H2 and fails to support H3.)
- **Load-current signature:** IL1 distribution is unimodal with a long tail
  (Phase-1 value distributions); no bimodal structure.
- **Multiplicity decay** after June 2019 (§2) contradicts a persistent
  second stream.
- **Electrical consistency per row:** Σ(VLx·ILx) matches published KVA with
  median error 1.36 % (Phase 1) — every row is internally one measurement
  point; mixing assets would not break this, but combined with unimodality
  and adjacency it removes any positive H3 signal.

## 4. Multiple-feeder signature (H4): absent

- One VL/IL triple per timestamp (no feeder index, no parallel channel sets).
- Energies' own multi-feeder system (their Sharjah deployment) presents
  five modules with arbitrary IDs and per-feeder currents (Sec. 6) — a
  different shape from this export's schema.
- No periodic swapping pattern in VL/IL magnitudes that would suggest
  alternating feeder sources.

## 5. Hypothesis assessment (qualitative, evidence-based)

| Hypothesis | Consistent evidence | Contradicting/absent evidence | Verdict |
|---|---|---|---|
| H1 single asset, legitimate repeats | none specific: no telemetry protocol sends two near-identical records under one timestamp | raw-line adjacency + cross-file synchronization + conflict magnitudes (0.4 V) look like re-transmission, not device behavior | **not supported as stated** (H1 without H2 mechanism unexplained) |
| H2 export/ingestion duplication | adjacency, synchronization, tiny conflicts, deployment-month concentration, decay over time, never touching high-OTI rows | cannot be confirmed without provider logs | **most consistent with all observed structure** (for the repeats only) |
| H3 multi-asset mixing | 52-location platform exists (Putchala (S11) Sec. 4); no device column | multiplicity 2.3–4.8 %, single voltage cluster, branch neighbor-fit parity, cross-file sync | **weak; leaned against by every structural test** |
| H4 multi-feeder | Energies system shows feeder-level monitoring exists | export has one channel triple per timestamp; no feeder ID | **not supported in this export's schema** |
| H5 corrupted export | cadence irregularities (1–9 min, 33.6-day gap), repeats | rows are time-ordered and internally consistent; corruption claim would need to specify mechanism | **partially consistent (cadence), otherwise uninformative** |

**Important:** H2 explains the *repeated records*. It does not explain the
OTI excursions (repeats never contain high-OTI rows), and it does not
establish that the non-repeated rows come from one asset — that remains
unverifiable from published metadata.

## 6. Entity conclusion (required statement)

Statistical structure (voltage unimodality, repeat decay, branch parity,
per-row electrical consistency) is *consistent with* a single measurement
point but does not identify one. No device identifier, no primary-source
scope statement, and a 52-location platform upstream mean the entity
question is not resolvable from the published export:

> **The published dataset does not provide enough information to establish
> that adjacent rows belong to the same physical transformer.**

All downstream conclusions in this project are therefore stated as
properties of *the published series*, not of a specific physical asset.
