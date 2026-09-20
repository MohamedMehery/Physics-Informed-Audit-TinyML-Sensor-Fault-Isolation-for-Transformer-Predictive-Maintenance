# Research Protocol — Phase 1 (data and provenance audit)

This protocol governs all work in this repository. It exists to keep every
statement traceable to evidence, and to prevent unverifiable engineering
assumptions from entering the record.

## 1. Evidence classes

Every claim is labeled with exactly one class:

| Class | Meaning |
|---|---|
| `[CONFIRMED-DATA]` | Directly reproducible from the official raw dataset (scripts + generated artifacts under `reports/generated/`). |
| `[CONFIRMED-SOURCE]` | Explicitly stated by an identifiable primary source (official Kaggle metadata/page, dataset-author statement, original paper, official standard page, manufacturer datasheet). |
| `[DERIVED]` | Mathematically derived from confirmed measurements, with equations, units, assumptions, and uncertainty documented. |
| `[INFERENCE]` | Plausible but not uniquely established by current evidence. |
| `[UNKNOWN]` | Not available from the current evidence. Never filled with an engineering guess. |

## 2. Standing prohibitions

1. **No assumed asset specifications.** Nameplate rating, voltage ratio, oil
   mass/volume, cooling class (ONAN/ONAF/OFAF/…), manufacturer, model,
   location, time zone, oil type, thermal time constant, sensor type
   (PT100/thermocouple/…), transmitter range, ADC rail — all `UNKNOWN`
   unless a primary source or a documented derivation establishes them.
2. **No hardware root-cause claims.** Phrases like "proved ADC railing" or
   "proved PT100 open circuit" are forbidden. The strongest permitted
   conclusion until evidence strengthens it:

   > "The observations may be inconsistent with a normal top-oil thermal
   > transient and may be more consistent with a measurement-chain or
   > telemetry anomaly. The exact hardware root cause remains unknown."

3. **No "TinyML" branding for deterministic rules.** Rate/range/plausibility
   rules are *edge sensor-integrity checks* / *physics-informed edge rules* /
   *deterministic plausibility filters*. "TinyML" is reserved for an actual
   trained, evaluated, deployed ML model on constrained hardware (none
   exists in this repository).
4. **No blanket invalidation of published ML results.** The dataset's
   public notebooks report up to ~99% accuracy/metrics. We do not claim
   overfitting unless a specific study is cited, its task understood, and
   the result independently reproduced. Distinguish: (a) same-timestamp
   classification of `OTI_T` using `OTI` (a trivial direct proxy exists:
   `OTI ≥ 236` reproduces `OTI_T` perfectly in this dataset); (b) future
   forecasting using only causal past data; (c) anomaly detection without
   `OTI_T` as a label. (a) being easy does not invalidate (b) or (c).
5. **The OTI observation gap is not "proof" of anything.** It is reported as
   data evidence consistent with a discontinuous or two-state measurement
   behavior, alongside sampling-frequency, event-trigger, missing-interval,
   and timestamp-irregularity considerations.
6. **No silent discards.** Duplicate timestamps, missing intervals, and
   conflicting records are quantified and documented *before* any
   canonicalization policy is applied; policy sensitivity is reported.
7. **Actual delta-t everywhere.** `rate[k] = (OTI[k] − OTI[k−1]) / Δt_min[k]`
   with the *actual* time difference. The metadata's "every 15 minutes" is
   not assumed (observed intervals include 1–9 min and gaps up to 33.6 days).
8. **Timestamps are parsed, never compared as strings.** Raw text is
   preserved alongside parsed values; raw file line numbers are retained.
9. **Electrical load ≠ nameplate.** Measured kW/kVA is operating load.
   Values near 100 kVA are described only as "observed load near the event".
10. **Code license ≠ dataset license.** The Kaggle display license
    ("Data files © Original Authors") is unverified for redistribution;
    raw data stays out of Git; no repository license is created without the
    owner's explicit choice.

## 3. Event definitions (definition-dependent counts)

- **Primitive event**: a maximal contiguous run of active-flag samples
  where consecutive active samples are separated by at most a declared
  *continuity gap* (analyzed at 15 and 30 minutes).
- **Merged event**: primitive events combined when separated by at most a
  declared *merge tolerance* (analyzed at 0/15/30/60/360 minutes).
- Every published event count must state flag + continuity gap + merge
  tolerance. No single count is ground truth.

## 4. Provenance gates

- Raw files' SHA-256 hashes are checked against
  `provenance/dataset_manifest.json` **before and after** every audit run;
  any mismatch aborts the run (raw files are never modified in place).
- The official Kaggle source is the only primary data source. Mirrors may
  be examined as leads and used only after byte-level verification.

## 5. Phase boundaries

- **Phase 1 (this)**: provenance, asset-identity evidence, data-quality
  audit, event-definition sensitivity. No thermal model fitting, no assumed
  masses/cooling/constants.
- **Phase 2 (future)**: only if Phase-1 outputs are judged reliable enough —
  candidate physics-informed edge rules (deterministic, not "TinyML"),
  cross-channel consistency studies, and — only with independent evidence —
  any thermal modelling with explicitly registered assumptions.

## 6. Tested environment

Recorded in `reports/generated/phase_01_summary.json` (`environment` key);
see README "Reproducibility".
