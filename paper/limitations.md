# Limitations (Phase 3R)

Required standing statements (each must survive review):

1. **Entity identity remains unresolved.** The published dataset does
   not provide enough information to establish that adjacent rows
   belong to the same physical transformer.
2. **OTI engineering unit is unconfirmed.** All values are reported in
   "OTI units"; no °C/% conversion is made anywhere.
3. **Events are operationally defined from the export** (rising
   band-crossings of OTI into ≥ 236, the OTI_T rule). They are not
   field-confirmed physical faults; no ground-truth sensor-fault labels
   exist.
4. **Hardware root cause is unknown.** No mechanism (ADC rail, sensor,
   transmitter, telemetry) is claimed.
5. **The full-data sweep (1,160 configurations) is exploratory** — an
   oracle sensitivity analysis with thresholds chosen using full-dataset
   knowledge; it is not held-out validation.
6. **The frozen-threshold replay is internal validation only**: a
   post-hoc leakage-controlled replay, not a truly prospective external
   validation, because the researchers had already inspected the full
   dataset before defining the replay.

Additional limitations:

7. **Small event count.** n = 10 events: 10/10 recall carries an exact
   95% CI of [0.69, 1.00]; all event-level conclusions are
   correspondingly uncertain.
8. **Single export, irregular sampling.** Gaps up to 33.6 days; the
   sampling cannot exclude sub-interval excursions; view policies
   P1–P4 and reset/continue gap behaviors are reported for every
   frozen-threshold result (rate-filter recall is view-dependent:
   9/10 under P1/P3/P4 vs 5/10 under P2_first).
9. **T3 horizon exploration is OTI-only.** No other channel was
   evaluated as a precursor; no multivariate early-warning conclusion
   is possible. Windows are compared to calibration-period quantiles
   without multiple-comparison correction.
10. **Cycle counts are illustrative**, from documented ARMv6-M integer
    instruction timings and typical GCC soft-float routine costs; no
    Cortex-M0 cross-compiler or physical board was used, so no measured
    MCU latency is reported. State size is measured on the compiled host
    reference (sizeof = 72 B, double-precision); a fixed-point port
    would be smaller.
11. **Reference-model comparisons (MLP 28-16-8-1, 100-tree GBDT) are
    hypothetical**: exact MAC/parameter counts for the stated
    architectures, but no trained models, no compilation, and assumed
    GBDT depth — kept out of headline results.
12. **The Energies 24-hour-advance statement was not reproduced by this
    project**; its exact features, task, split, and evaluation were not
    reproduced either, so no judgment on its validity is made.
13. **Outreach is stored, not sent**; no provider clarification of
    units, entity, or export process is available yet.
