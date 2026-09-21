/* mif_filter.h — Measurement-Integrity Filter (deterministic plausibility
 * filter) for the OTI measurement channel. C reference skeleton, Phase 3R.
 *
 * Mirrors src/transformer_audit/plausibility_filter.py EXACTLY:
 *   F1 rate      : |OTI[k]-OTI[k-1]| / dt  >  rate_threshold   (strict >)
 *   F2 range     : OTI[k] > upper_threshold                  (strict >)
 *   F3 combined  : F1 OR F2
 *   F4 jump      : |OTI[k]-OTI[k-1]| > jump_threshold        (strict >)
 *
 * Edge-case contract (verified by scripts/check_c_python_parity.py):
 *   - first sample            : range only; state initialized
 *   - invalid OTI (missing)   : no flag, no state update, data_anomaly
 *   - dt <= 0                 : range still evaluated; data_anomaly; no
 *                               division; state NOT updated
 *   - dt > gap_minutes        : reset  -> range only, state replaced
 *                               continue -> evaluate normally
 *
 * This is a deterministic rule set. It flags readings INCONSISTENT WITH
 * GRADUAL THERMAL BEHAVIOR at the measurement-channel level; it does not
 * detect faults or sensor failures, and the root cause of flagged
 * behavior is unknown. Values are in "OTI units" (unit unconfirmed).
 *
 * Cycle counts quoted anywhere in the project are ILLUSTRATIVE estimates
 * from documented instruction-timing tables; no Cortex-M0 cross-compiler
 * or physical board was used in this project, so nothing here is a
 * measured MCU latency.
 */
#ifndef MIF_FILTER_H
#define MIF_FILTER_H

#include <stddef.h>

typedef enum {
    MIF_F1_RATE = 1,
    MIF_F2_RANGE = 2,
    MIF_F3_COMBINED = 3,
    MIF_F4_JUMP = 4
} mif_type_t;

typedef enum {
    MIF_GAP_RESET = 0,
    MIF_GAP_CONTINUE = 1
} mif_gap_t;

typedef struct {
    mif_type_t type;         /* filter family selector                */
    double     rate_threshold;  /* OTI-units/min (F1/F3)              */
    double     upper_threshold; /* OTI units (F2/F3)                  */
    double     jump_threshold;  /* OTI units (F4)                     */
    double     gap_minutes;     /* long-gap boundary, default 60      */
    mif_gap_t  gap_behavior;
    /* ---- retained state: previous sample only (causal) ---- */
    double     prev_oti;      /* OTI units                            */
    double     prev_ts;       /* minutes since caller's epoch         */
    int        has_prev;      /* 0 until the first valid state        */
} mif_filter_t;

typedef struct {
    int    flagged;        /* a plausibility rule fired               */
    int    data_anomaly;   /* invalid input or non-positive dt        */
    int    state_updated;  /* retained previous sample replaced       */
    double rate;           /* |dOTI|/dt if evaluated, else NaN        */
    double jump;           /* signed dOTI if evaluated, else NaN      */
} mif_decision_t;

/* Initialize a filter. Unused thresholds are ignored per type. */
void mif_init(mif_filter_t *f, mif_type_t type,
              double rate_threshold, double upper_threshold,
              double jump_threshold, mif_gap_t gap_behavior);

/* Process one sample. oti_valid == 0 models a missing/NaN OTI value. */
mif_decision_t mif_process(mif_filter_t *f, double oti, double ts_min,
                           int oti_valid);

/* Compiled state size (measured, not estimated). */
size_t mif_state_bytes(void);

#endif /* MIF_FILTER_H */
