/* mif_filter.c — see mif_filter.h. Pure C99, no dynamic allocation,
 * no external dependencies. Compiled for the host parity test with
 * -Wall -Wextra -Werror -O2 (scripts/check_c_python_parity.py).
 */
#include "mif_filter.h"

#include <math.h>
#include <stddef.h>

void mif_init(mif_filter_t *f, mif_type_t type,
              double rate_threshold, double upper_threshold,
              double jump_threshold, mif_gap_t gap_behavior)
{
    f->type = type;
    f->rate_threshold = rate_threshold;
    f->upper_threshold = upper_threshold;
    f->jump_threshold = jump_threshold;
    f->gap_minutes = 60.0;
    f->gap_behavior = gap_behavior;
    f->prev_oti = 0.0;
    f->prev_ts = 0.0;
    f->has_prev = 0;
}

size_t mif_state_bytes(void)
{
    return sizeof(mif_filter_t);
}

/* F2: stateless absolute bounds (strict inequalities).
 * Only F2_RANGE and F3_COMBINED evaluate the range rule (mirrors the
 * Python reference, where non-range types have upper_threshold=None).
 * lower_threshold is not used in this project's configurations;
 * the Python reference supports it; parity cases do not exercise it. */
static int mif_eval_range(const mif_filter_t *f, double oti)
{
    if (f->type != MIF_F2_RANGE && f->type != MIF_F3_COMBINED) {
        return 0;
    }
    return oti > f->upper_threshold;
}

mif_decision_t mif_process(mif_filter_t *f, double oti, double ts_min,
                           int oti_valid)
{
    mif_decision_t d;
    d.flagged = 0;
    d.data_anomaly = 0;
    d.state_updated = 0;
    d.rate = NAN;
    d.jump = NAN;

    /* ---- missing input: never flag, never update state -------------- */
    if (!oti_valid || isnan(oti)) {
        d.data_anomaly = 1;
        return d;
    }

    /* ---- stateless range rule --------------------------------------- */
    {
        const int range_flag = mif_eval_range(f, oti);

        /* ---- first sample: no dynamics possible --------------------- */
        if (!f->has_prev) {
            f->prev_oti = oti;
            f->prev_ts = ts_min;
            f->has_prev = 1;
            d.flagged = range_flag;
            d.state_updated = 1;
            return d;
        }

        {
            const double dt = ts_min - f->prev_ts;

            /* ---- non-positive dt: data anomaly, no division ---------- */
            if (dt <= 0.0) {
                d.flagged = range_flag;      /* range still applies */
                d.data_anomaly = 1;
                d.state_updated = 0;         /* keep the older reference */
                return d;
            }

            /* ---- long gap handling ----------------------------------- */
            if (dt > f->gap_minutes && f->gap_behavior == MIF_GAP_RESET) {
                f->prev_oti = oti;
                f->prev_ts = ts_min;
                d.flagged = range_flag;
                d.state_updated = 1;
                return d;
            }

            /* ---- dynamics evaluation ---------------------------------
             * NOTE: this reference computes rate = |dOTI|/dt to match the
             * Python reference exactly. A fixed-point MCU port uses the
             * multiply-form (|dOTI| > thr * dt) to avoid division; the
             * operation counts in computational_cost_comparison.csv
             * assume the multiply-form. */
            {
                const double jump = oti - f->prev_oti;
                const double rate = fabs(jump) / dt;
                int flagged = 0;

                d.rate = rate;
                d.jump = jump;

                if (f->type == MIF_F2_RANGE) {
                    flagged = range_flag;
                }
                if (f->type == MIF_F1_RATE || f->type == MIF_F3_COMBINED) {
                    if (rate > f->rate_threshold) {   /* strict > */
                        flagged = 1;
                    }
                }
                if (f->type == MIF_F4_JUMP) {
                    if (fabs(jump) > f->jump_threshold) { /* strict > */
                        flagged = 1;
                    }
                }
                if (f->type == MIF_F3_COMBINED && range_flag) {
                    flagged = 1;
                }

                d.flagged = flagged;
                d.state_updated = 1;
                f->prev_oti = oti;
                f->prev_ts = ts_min;
                return d;
            }
        }
    }
}
