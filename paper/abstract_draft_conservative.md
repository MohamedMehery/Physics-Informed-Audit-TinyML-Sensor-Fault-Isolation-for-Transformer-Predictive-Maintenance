# Abstract Draft (conservative) — Phase 3R

## Version A (target ~200 words)

Public datasets that circulate through machine-learning pipelines are
rarely audited at the measurement-channel level. We audit a widely
reused Kaggle export ("Distributed Transformer Monitoring", 19,352 rows,
2019–2020, also used by a peer-reviewed 2022 study) and find that its
oil-temperature-indicator channel (OTI, engineering unit unconfirmed)
exhibits ten sharp excursions: single-step transitions from ≤ 54 to
≥ 236 "OTI units" with no observed values in between, at rates up to
91 units/min. Under labeled bounding assumptions these steps are
inconsistent with gradual thermal behavior of the observed electrical
load; the hardware root cause is unknown, and the dataset provides no
field-confirmed fault labels. We design a family of deterministic,
causal, streaming plausibility filters (rate, range, combined, jump;
1–11 operations per sample; 72-byte host reference state; strict
inequalities), calibrate thresholds only on data preceding the first
excursion using predefined quantile rules, and replay them on all later
records without retuning. Range and jump rules flag every excursion at
or before the crossing sample (10/10; exact 95% CI 0.69–1.00, n = 10)
with zero to 0.26 false-alert episodes per day; rate rules calibrated to
pre-event noise flag 5–9 of 10. The tested OTI-only deterministic rules
did not demonstrate robust multi-hour warning. A 1,160-configuration
full-data sweep is reported separately as exploratory sensitivity
analysis, and a C reference implementation is verified against the
Python reference on the complete replay sequence.

## Version B (short, ~120 words)

We audit the measurement channels of a widely reused public transformer
monitoring dataset. The oil-temperature-indicator channel shows ten
single-step excursions from ≤ 54 to ≥ 236 "OTI units" (unit unconfirmed;
hardware root cause unknown; no field-confirmed labels). A family of
deterministic causal plausibility filters (1–11 operations per sample)
is calibrated only on records preceding the first excursion and replayed
unchanged on all later records: range and jump rules flag all ten
excursions concurrently (95% CI 0.69–1.00) at zero to 0.26 false alerts
per day. The tested OTI-only rules did not demonstrate robust
multi-hour warning. Full-data threshold sweeps are reported as
exploratory analysis; a C skeleton matches the Python reference exactly.

## Wording constraints (checked by tests)

- The filter is described as a **deterministic plausibility filter** —
  never as TinyML, AI, or intelligent.
- No claim of validated physical fault detection (no field-confirmed
  labels exist; event labels are operationally defined from OTI band
  crossings in the export).
- The Energies 24-hour statement is referenced only as "not reproduced
  by this project", never as unsupported or wrong.
- Entity identity remains unresolved; the OTI engineering unit is
  unconfirmed; the hardware root cause is unknown.
