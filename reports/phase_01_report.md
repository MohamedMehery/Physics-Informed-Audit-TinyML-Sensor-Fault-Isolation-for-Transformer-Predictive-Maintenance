# Phase 1 Report — Evidence-First Repository Bootstrap, Dataset Provenance, Asset-Identity Investigation, and Reproducible Raw-Data Audit

Run date: 2026-09-20 (UTC) · All numerical artifacts regenerate via
`python scripts/run_data_audit.py` into `reports/generated/` (provenance-gated).
Environment: Python 3.13.14, pandas 2.2.3, numpy 2.3.5, Linux 6.1.158+ x86_64.

---

## 1. Repository state on arrival

- Working tree at `/home/user` was **empty** (no files at all).
- **No `README.md` existed** — the unverified AI-generated README draft that
  the Phase-1 instructions expected to archive was **not present**.
- **Not a Git repository** (`git status` → "fatal: not a git repository").

Consequences, executed honestly rather than by fabrication:

- The archive slot `docs/archive/README_initial_unverified.md` was created
  as a factual placeholder documenting the absence (no content invented).
- No unverified claims were inherited; the new `README.md` was written from
  scratch from reproducible evidence only.
- A fresh Git repository was initialized during Phase 1 (commit recorded in
  `reports/phase_01_handoff.md`).

## 2. Dataset acquisition and provenance

- **Source (primary):** official Kaggle dataset
  `sreshta140/ai-transformer-monitoring` ("Distributed Transformer
  Monitoring", owner Sreshta Putchala, version 1 "Initial release",
  created 2020-05-25T10:08:46.673Z, Kaggle id 673798).
- **Acquisition:** anonymous public HTTPS download from the official Kaggle
  API endpoints — metadata `api/v1/datasets/view/...` (HTTP 200, snapshot
  saved and hash-logged) and archive
  `api/v1/datasets/download/sreshta140/ai-transformer-monitoring`
  (HTTP 200, served from Kaggle's signed Google-Storage bucket). No mirror
  was used as a data source. The download was performed twice
  (initial + `scripts/download_dataset.py` re-run) with identical results.
- **Archive:** `ai-transformer-monitoring_v1.zip`, 1,481,162 bytes,
  SHA-256 `b9257e990d480b3486b176bc19304a18b4aa82fd07dc559ec16aaa3ed3fe9c68`.
- **Extracted files** (6,915,767 bytes total; full hashes in
  `provenance/dataset_manifest.json`):

| File | Bytes | SHA-256 (first 16) |
|---|---|---|
| CurrentVoltage.csv | 1,428,576 | `885fad08ecc4fd63` |
| Overview.csv | 1,003,649 | `99c371db6d8fb736` |
| Power.csv | 1,183,477 | `f1aa074386c9d7e7` |
| PowerFactor.csv | 1,739,626 | `cc36cec106b1be03` |
| TotalPower.csv | 1,560,439 | `0e1995281f585743` |

- **Preservation:** raw files are stored under gitignored `data/raw/`;
  the audit pipeline verifies SHA-256 against the manifest **before and
  after every run** and aborts on mismatch (both gates passed on the final
  run). `scripts/download_dataset.py` warns if a future download's hash
  differs (Kaggle version change) so numbers are re-derived deliberately.
- **Mirror check (lead only):** `pythonafroz/transformer-fault-analysis`
  (v3) re-uploads the 5 official CSVs **byte-identical** (SHA-256 match;
  `Overview.csv` renamed `Alarm.csv`) plus a text file copying the original
  description. It adds no provenance information and was not used for
  analysis.

## 3. Dataset license / redistribution status

- Displayed license: **"Data files © Original Authors"**.
- Redistribution conditions: **UNVERIFIED** — this display does not clearly
  grant redistribution rights.
- Actions taken: raw/downloaded data excluded from Git (`.gitignore`);
  only manifest, hashes, scripts, docs committed. Code licensing is
  deliberately left undecided (no LICENSE file created on the owner's
  behalf); the separation is documented in `data/README.md` and the README.

## 4. Source investigation (asset identity)

Registered sources S1–S10 in `provenance/source_register.csv`; full
analysis in `reports/asset_identity_evidence.md`. Summary:

- **Kaggle metadata/description (primary):** column glossary, IoT
  collection 2019-06-25→2020-04-14, "updated every 15 minutes" (contradicted
  in detail by the data, see §7). No asset specifications.
- **Kaggle discussions (3 topics, primary):** a location question with **no
  identifying answer**; a **nameplate-data request (posted 2026-09-19, zero
  replies)**; an unrelated help request. The author has not published asset
  specifications.
- **Author profile (primary for authorship only):** Sreshta Putchala,
  data-science practitioner (profile location Charlotte, NC, USA — the
  *author's* location, not the asset's). Other datasets unrelated.
- **Papers citing the dataset (secondary):** Energies 2022
  (DOI 10.3390/en15217981) describes **its own** monitoring system's
  transformer (three-phase, 1500 kVA, 11→0.4 kV) and adopts the Kaggle data
  as readings from "similar transformers sharing load capacity,
  manufactured age, measuring units, and installed environment conditions"
  — this is the traceable origin of the "1500 kVA" lead, and it is **not an
  attribution to this asset**. Note the paper says **11**→0.4 kV; the
  "10/0.4 kV" variant circulating in secondary material was not found in
  any primary source. IET EPA 2025 (Tamakloe et al., DOI
  10.1049/elp2.70011) cites the dataset without primary asset
  specification.
- **Embedded metadata:** CSVs contain only header + data rows; archive
  entries carry 2020-05-25 timestamps; no comments/worksheets/properties;
  nothing identifying.

## 5. Exact asset facts found (evidence-bounded)

Confirmed/derived/weakly-inferred:

- Three-phase monitoring structure (VL1-3, IL1-3, VL12/23/31, INUT;
  Σ(VLx·ILx) matches reported KVA, median 1.36% error) — [CONFIRMED-DATA]/[DERIVED].
- LV-side monitoring inferred from voltage magnitudes (nonzero VL1 band
  ≈221–261 V, VL12 ≈378–447 V) — [INFERENCE, moderate].
- 50 Hz system (FRQ ∈ [49.6, 50.2] nonzero) — [DERIVED, bounded].
- Observed operating load: record max 142.9 kVA / 142.1 kW; 33.4–103.0 kW
  in ±30-min windows around excursion onsets — [CONFIRMED-DATA]
  ("observed load", never nameplate).
- Oil-immersed transformer with oil temperature/level and winding-related
  indicator channels, per the dataset glossary — [CONFIRMED-SOURCE]
  (glossary wording only).

## 6. Unknown asset parameters

Nameplate kVA rating (1500 kVA = unverified secondary lead), HV/LV ratio
(11/0.4 kV = same lead; not this asset), nominal LV voltage (only bounded
to ~230/400 V class), cooling class, oil volume/mass, oil type, thermal
time constant, sensor types, transmitter range, ADC rail, protection logic,
manufacturer/model, site/country (50 Hz only), time zone, OTI units
(assumed °C, flagged), OLI units, WTI physical semantics. All registered in
`docs/assumption_register.md` as UNKNOWN/UNVERIFIED.

## 7. Complete data-quality results

**(a) Inventory** (`dataset_inventory.csv`, `dataset_columns_dtypes.csv`;
units are not stated in the dataset — "no" for every column):

| File | Rows | Unique ts | Dup-ts rows | Exact dup rows | Range |
|---|---|---|---|---|---|
| CurrentVoltage.csv | 19,352 | 18,915 | 437 | 32 | 2019-06-25 13:06 → 2020-04-14 00:30 |
| Overview.csv | 20,316 | 19,376 | 940 | 574 | 2019-06-25 13:06 → 2020-04-14 00:30 |
| Power.csv | 19,309 | 18,871 | 438 | 429 | 2019-06-25 13:06 → 2020-04-14 00:30 |
| PowerFactor.csv | 19,308 | 18,877 | 431 | 1 | 2019-06-25 12:39 → 2020-04-14 00:30 |
| TotalPower.csv | 19,248 | 18,842 | 406 | 393 | 2019-06-27 10:51 → 2020-04-14 00:30 |

No missing/NaN sensor values; no non-numeric coercions; raw rows are in
non-decreasing timestamp order (no negative intervals; all nonpositive
intervals are exact zero = duplicates).

**(b) Interval irregularity** (`timestamp_interval_summary.csv`): median
15 min and p95 15 min, **but** minimum interval 1 min, p99 22–23 min,
maximum gap 48,398–48,399 min (≈33.6 days), 101–115 intervals >30 min and
17–19 gaps >1 day per file. The metadata's "updated every 15 minutes" is
therefore false in detail — rates must use actual Δt (they do).

**(c) Duplicate timestamps** (`duplicate_timestamp_report.csv`,
`duplicate_timestamp_summary.csv` — analyzed **before** any
canonicalization):

| File | Dup groups | Identical | Conflicting | Max records/ts | Conflicting columns |
|---|---|---|---|---|---|
| CurrentVoltage.csv | 437 | 32 | 405 | 2 | VL*, IL*, INUT |
| Overview.csv | 931 | 568 | 363 | 4 | ATI, OLI, OTI, WTI |
| Power.csv | 438 | 429 | 9 | 2 | WL*, VAL*, RVAL* |
| PowerFactor.csv | 431 | 1 | 430 | 2 | PF*, FRQ, THD* |
| TotalPower.csv | 406 | 393 | 13 | 2 | KW*, KVAR*, KWH* |

Duplicate-policy sensitivity (`alarm_summary.csv`): onset counts for
OTI_A (11), OTI_T (10), MOG_A (5) are stable across first/last/mean
policies; **WTI varies 277–288** (first 285 / last 288 / mean 277).
Canonical active rows: OTI_A 100 (101 raw), OTI_T 47, MOG_A 2,087 (2,153
raw), WTI 5,388 (5,495 raw).

**(d) Value distributions** (`overview_value_distributions.csv`):
OTI 59 distinct values 0–250 (mean 30.06; 42 canonical rows at exactly 0,
Jun–Jul 2019, consistent with telemetry-offline periods); ATI 0–44;
OLI 36–100 (65 distinct; units unstated); **WTI binary {0,1}** (not a
temperature series); OTI_A/OTI_T/MOG_A binary.

**(e) OTI value-gap evidence** (`oti_value_gaps.csv`): no OTI value exists
in the open interval **(54, 236)** (gap size 182; the smaller gap (0,9) also
exists). 47 rows ≥ 236. This is data evidence consistent with a
discontinuous or two-state measurement behavior — considering sampling
frequency, event-triggered samples, missing intervals, and timestamp
irregularity — **not** standalone proof of any mechanism. (Note: the
"70–236 °C gap" figure from the earlier draft instructions is **not
reproduced**; the reproduced empty interval is (54, 236).)

**(f) Threshold separability** (`oti_threshold_analysis.csv`): OTI_T=1 ⟺
OTI ∈ [236, 250] with zero overlap (a `OTI ≥ 236` rule reproduces OTI_T
100% on this dataset — association only, not proven causal logic). OTI_A
classes overlap (flag=1 range 29–250 vs flag=0 range 0–54; best threshold
≥236, accuracy 99.73%): **OTI_A is active at OTI 29–30 during 2019-07-03
→ 07-04 (54 raw rows / 53 canonical), contradicting a simple OTI-threshold
alarm model.** MOG_A=1 ⇒ OLI ≤ 41 without exception, but OLI ≤ 41 occurs
5,334 times with MOG_A=1 only 2,087 times — not a pure OLI threshold
(best single-threshold rule 89.4%, barely above the always-0 baseline).

**(g) Temporal structure:** OTI_T active only 2019-07-16 → 09-03 (Jul 3,
Aug 41, Sep 3 rows); the low-OTI OTI_A episode is 2019-07-03/04; MOG_A
only Jul–Aug 2019; **WTI=1 only 2020-01 → 2020-04** — the winding-related
binary channel's active period is disjoint from the OTI excursion period,
and WTI=0 during all 47 high-OTI rows. OTI autocorrelation (sample lags,
irregular sampling caveat): lag-1 0.859, lag-4 0.497, lag-96 0.395
(`oti_autocorrelation.csv`).

**(h) Rates with actual Δt** (`oti_rate_stats.json`, `oti_rate_summary.csv`,
raw lines in `oti_transition_raw_lines.csv`): 19,375 rates computed;
median 0, p95|r| 0.2, p99|r| 0.4 units/min (°C assumed, A01). Excursion
transitions: 10 rising (+11.1 … **+91.0** units/min over Δt = 2–18 min) and
10 falling (−4.4 … −40.8 units/min over Δt = 5–45 min). Normal-mode
(excluding excursion endpoints): p99|r| 0.333; max 33 units/min — those
maxima are 0→~30 one-sample steps (2019-06-29, 2019-07-08) at
telemetry-return-from-zero boundaries, themselves measurement
discontinuities, not gradual heating.

**(i) Cross-file alignment** (`cross_file_alignment.csv`, tolerance ±15
min declared): pairwise exact matches 18,324–18,729 (e.g., Overview ∩
CurrentVoltage 18,729; Overview ∩ TotalPower 18,370); **all-5 intersection
18,324**. Nearest-delta medians 0 min; p95 ≤ 1 min; max nearest-deltas up
to ~2,772 min (rare one-file-only periods). Measurements are never
described as simultaneous without reporting the actual per-event delta.

**(j) Electrical context** (`excursion_electrical_context.csv`,
`power_formula_crosscheck.json`): for every OTI_T onset, the nearest
CurrentVoltage/TotalPower samples lie 1–12 min away; VL1 stays 219.8–234.2
V; observed load 33.4–103.0 kW (max ~104 kVA). **No coincident disturbance
is visible in the available electrical channels at the dataset's temporal
resolution** (no claim is made about events beyond that resolution or
unmeasured variables). Formula cross-check on 17,243 exactly-matching
nonzero samples: per-phase Σ(VLx·ILx) vs reported KVA — median |err| 1.36%,
p95 5.17%; √3·V_LL·mean(I) — median 1.41%, p95 5.25% (both formulas carry
documented unbalance/phase-angle limitations; unbalance is material here,
e.g., IL up to 46–153 A across phases in excursion windows).

## 8. Event-definition sensitivity

`primitive_events.csv` and `event_merge_sensitivity.csv` (definitions:
primitive = contiguous active run with declared continuity gap; merged =
primitives combined when separated by ≤ merge tolerance):

| Flag | Primitives (gap 15 / 30) | After merge 15' | 30' | 60' | 360' |
|---|---|---|---|---|---|
| OTI_T | 10 / 10 | 10 | 10 | 10 | **8** |
| OTI_A | 13 / 12 | 13/12 | 12 | 12 | **10** |
| MOG_A | 68 / 24 | 68/24 | 24 | 14 | **8** |
| WTI | 378 / 307 | 368/297 | 95 | 36 | **14** |

OTI_T: 10 excursion windows, 2019-07-16 → 2019-09-03, active spans 10–136
min (median 37.5); at a 360-min merge tolerance the two same-day pairs of
2019-08-16 and 2019-08-17 combine to 8 windows. Every count above is
definition-dependent and is reported with its definition; no count is
presented as unique ground truth.

## 9. Preliminary findings directly reproducible

1. Provenance chain complete and hash-verified (official source; mirror
   byte-checked as a lead).
2. The dataset is *not* a clean uniform 15-min series: irregular short
   intervals, ~33.6-day maximum gap, 17–19 multi-hour gaps per file.
3. Duplicate/conflicting timestamps are pervasive (up to 363–430
   conflicting groups per file) and materially affect some statistics
   (WTI onsets ±11 across policies) though not OTI_T/OTI_A/MOG_A onset
   counts.
4. The OTI excursion phenomenon reproduces exactly: 47 high-OTI rows in 10
   windows, empty value interval (54, 236), transition rates up to
   +91 units/min with actual Δt, all co-occurring with OTI_A=1 and
   OTI_T=1.
5. The alarm channel is not a pure function of the shown OTI (Jul 3–4
   low-OTI alarm episode).
6. No visible electrical disturbance around any excursion onset at the
   available resolution; observed load near events 33–103 kW.
7. WTI is binary and temporally disjoint from the excursions.
8. Permitted interpretation (unchanged strength): the observations **may
   be inconsistent with a normal top-oil thermal transient and may be more
   consistent with a measurement-chain or telemetry anomaly; the exact
   hardware root cause remains unknown.**

## 10. Statements from the original README — removals/downgrades

The expected unverified README **did not exist** (§1), so no statement was
inherited. For audit-trail completeness, the following categories from the
Phase-1 instructions (which the draft was said to contain) are confirmed
**absent from the new README** or explicitly downgraded:

| Draft claim (per instructions) | Phase-1 status |
|---|---|
| Fixed 300 kg oil mass | Absent; oil mass = UNKNOWN (A14) |
| Assumed ONAN cooling; 232.7 kW cooling claim | Absent; cooling class = UNKNOWN (A15); no cooling claim |
| Assumed 2–3 h asset-specific thermal time constant | Absent; UNKNOWN (A17); no thermal model fitted |
| PT100 / open-circuit / ADC-rail statements as facts | Absent; sensor/range/mechanism UNKNOWN (A18/A19); only the permitted provisional interpretation is used |
| 100–250 kVA nameplate estimate as fact | Absent; nameplate UNKNOWN (A13); only observed load reported |
| "70–236 °C observation gap" | Corrected: reproduced empty interval is **(54, 236)** (C08) |
| "All 99% ML models are invalid" | Absent; replaced by the task-type distinction (same-timestamp proxy vs causal forecasting vs anomaly detection); no overfitting accusation (C22) |
| "Proven TinyML solution in this repo" | Absent; no ML model exists here; deterministic checks are labeled physics-informed edge rules at most |
| MIT license badge | Absent; no LICENSE file created; code license = owner's decision; dataset license separated (C02) |

## 11. Tests and commands run

```bash
python -m pip install -e ".[test]"     # Python 3.13.14
python scripts/download_dataset.py     # official download; hash verified; manifest written
python scripts/run_data_audit.py       # full audit; pre+post provenance gates PASS
python -m pytest                       # 39 passed
```

Test coverage (39 tests, all synthetic fixtures — no Kaggle dependency):
ISO "T" vs space separators; actual-Δt rates; duplicate timestamps
(identical vs conflicting, policy sensitivity); zero/negative Δt guards;
missing-interval/gap detection; contiguous primitive-event construction;
event merging at 15/30/60/360-min tolerances; OTI/OTI_T separability on
synthetic data (perfect and overlapping cases); cross-file nearest-match
deltas; division-by-zero protection; raw-file preservation (hash
before/after; tamper detection); deterministic reproducibility of summary
tables.

## 12. Unresolved risks

1. **License/redistribution** remains unverified — raw data must stay out
   of Git until clarified by the dataset owner.
2. **OTI units unstated** (°C assumed for rate language; flagged A01).
   Rates and the "implausibility" framing scale with this assumption; the
   discontinuity/separability facts are unit-independent.
3. **Timestamp time zone unknown** — Δt-based results are robust;
   time-of-day interpretations are not.
4. **Conflicting duplicates** (405 in CurrentVoltage, 430 in PowerFactor)
   are re-transmissions with different values; the correct value is
   undeterminable from data alone — policy sensitivity is reported
   instead.
5. **Telemetry-vs-measurement time** (A03) unverified.
6. **Author non-response:** nameplate/location questions on Kaggle remain
   unanswered; asset identity may improve only if the author replies.
7. **Dataset version drift:** a future Kaggle re-publish would change
   hashes; the download script warns, and all numbers must be re-derived.

## 13. Recommended Phase-2 work

1. **Physics-informed edge rule prototyping** (deterministic, *not*
   "TinyML"): e.g., |dOTI/dt| plausibility on actual Δt (normal-mode p99
   0.33 units/min vs excursion ≥11 units/min is a >30× separation);
   include the zero-recovery artifact signature (0→nominal one-sample
   steps) and quantify false-positive/negative rates against the 10
   reproducible excursion windows.
2. **Cross-channel consistency study:** OTI-vs-ATI coupling, WTI's binary
   semantics, MOG_A/OLI relationship and latching/hysteresis hypotheses;
   duplicate-conflict patterns (which channels change on re-transmission).
3. **Author outreach** (Kaggle discussion) for nameplate/location/sensor
   documentation; re-run asset-identity report on any reply.
4. **Task-fair ML baseline design** (if ML is later in scope): strictly
   causal forecasting vs same-timestamp proxy classification, documented
   separately — enabling an evidence-based statement about the ~99%
   notebook results rather than an assumption.
5. **Thermal modelling only after** asset parameters (or justified bounds)
   exist; any model must carry registered assumptions with sensitivity
   analysis (A13–A17).
