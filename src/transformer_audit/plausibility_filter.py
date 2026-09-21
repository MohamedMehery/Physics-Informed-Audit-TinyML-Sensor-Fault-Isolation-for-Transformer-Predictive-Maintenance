"""Deterministic causal plausibility filter for the OTI measurement channel.

Phase-3 reference implementation. Design constraints (enforced by tests):

- DETERMINISTIC: no randomness, no learned parameters.
- CAUSAL: at time k the filter uses only values at times <= k
  (current sample + its own retained previous sample).
- STREAMING: one sample per call, O(1) time, minimal state.
- PURE STDLIB: no third-party imports, so the logic can be
  transliterated to C without ambiguity.

Terminology discipline: the filter flags readings that are INCONSISTENT
WITH GRADUAL THERMAL BEHAVIOR at the measurement-channel level. It does
NOT "detect faults" or "detect sensor failures"; the root cause of the
flagged behavior remains unknown. Values are in "OTI units" (unit
unconfirmed by any primary source — Phase 2).

Filter family
-------------
F1 "rate"     : |OTI[k] - OTI[k-1]| / dt_minutes > rate_threshold
F2 "range"    : OTI[k] > upper_threshold  OR  OTI[k] < lower_threshold
F3 "combined" : F1 OR F2
F4 "jump"     : |OTI[k] - OTI[k-1]| > jump_threshold  (time ignored)

All comparisons are strict (>) so that a value exactly at the threshold is
NOT flagged; the boundary behavior is unit-tested.

Edge-case contract (unit-tested)
--------------------------------
- first sample            : no dynamics flag (no previous value); range is
                             still evaluated; state initialized.
- NaN / None OTI          : never flagged; state NOT updated.
- dt <= 0 (repeat/reorder): never divide; reported as a DATA ANOMALY
                             (separate from plausibility flags); state NOT
                             updated (the older reference is kept).
- gap > gap_minutes       : "reset"  -> treat next sample as first (no
                             rate/jump evaluation; range still evaluated);
                             "continue" -> evaluate normally across the gap.
                             Both behaviors are unit-tested and both are
                             swept in the evaluation script.

Timestamps are passed as float minutes since an arbitrary epoch (caller
converts); the module never parses date strings.
"""

from __future__ import annotations

import math

FILTER_TYPES = ("rate", "range", "combined", "jump")

# Sentinel: filters out of order/duplicate timestamps as data anomalies.
_GAP_BEHAVIORS = ("reset", "continue")


class FilterDecision:
    """Result of processing one sample.

    Attributes
    ----------
    flagged : bool
        True when a PLAUSIBILITY rule fired (rate / range / jump).
        Data anomalies (non-positive dt, NaN input) are NOT "flagged";
        see ``data_anomaly``.
    reason : str
        "" | "rate" | "upper" | "lower" | "jump" | "rate+upper" | ...
    rate : float | None
        Computed |dOTI|/dt in OTI-units/minute when dynamics were evaluated.
    jump : float | None
        Signed dOTI (OTI units) when dynamics were evaluated.
    data_anomaly : bool
        True for non-positive dt or missing input (transport/export problem,
        not a plausibility verdict).
    state_updated : bool
        Whether the retained previous sample was replaced.
    note : str
        Human-readable explanation (for logs and tests).
    """

    __slots__ = ("flagged", "reason", "rate", "jump", "data_anomaly",
                 "state_updated", "note")

    def __init__(self, flagged=False, reason="", rate=None, jump=None,
                 data_anomaly=False, state_updated=False, note=""):
        self.flagged = flagged
        self.reason = reason
        self.rate = rate
        self.jump = jump
        self.data_anomaly = data_anomaly
        self.state_updated = state_updated
        self.note = note

    def as_dict(self):
        return {
            "flagged": self.flagged, "reason": self.reason, "rate": self.rate,
            "jump": self.jump, "data_anomaly": self.data_anomaly,
            "state_updated": self.state_updated, "note": self.note,
        }

    def __repr__(self):  # pragma: no cover - debug helper
        return ("FilterDecision(flagged=%r, reason=%r, rate=%r, jump=%r, "
                "data_anomaly=%r, state_updated=%r)" %
                (self.flagged, self.reason, self.rate, self.jump,
                 self.data_anomaly, self.state_updated))


class PlausibilityFilter:
    """Streaming deterministic plausibility filter (see module docstring)."""

    def __init__(self, filter_type, *, rate_threshold=None,
                 upper_threshold=None, lower_threshold=None,
                 jump_threshold=None, gap_minutes=60.0,
                 gap_behavior="reset"):
        if filter_type not in FILTER_TYPES:
            raise ValueError(f"unknown filter_type: {filter_type!r}")
        if gap_behavior not in _GAP_BEHAVIORS:
            raise ValueError(f"unknown gap_behavior: {gap_behavior!r}")

        needs_rate = filter_type in ("rate", "combined")
        needs_jump = filter_type == "jump"
        needs_range = filter_type in ("range", "combined")

        if needs_rate and rate_threshold is None:
            raise ValueError("rate filter requires rate_threshold")
        if needs_jump and jump_threshold is None:
            raise ValueError("jump filter requires jump_threshold")
        if needs_range and (upper_threshold is None and lower_threshold is None):
            raise ValueError("range filter requires upper_threshold or lower_threshold")
        for name, v in (("rate_threshold", rate_threshold),
                        ("upper_threshold", upper_threshold),
                        ("lower_threshold", lower_threshold),
                        ("jump_threshold", jump_threshold)):
            if v is not None and not (isinstance(v, (int, float)) and
                                      math.isfinite(v)):
                raise ValueError(f"{name} must be a finite number")

        self.filter_type = filter_type
        self.rate_threshold = rate_threshold
        self.upper_threshold = upper_threshold
        self.lower_threshold = lower_threshold
        self.jump_threshold = jump_threshold
        self.gap_minutes = gap_minutes
        self.gap_behavior = gap_behavior

        # ---- minimal retained state: exactly two values ----
        self._prev_oti = None      # float or None
        self._prev_ts = None       # float minutes or None
        self._samples_seen = 0

    # -- state inspection (for tests/debug; not needed in deployment) --
    @property
    def state(self):
        return (self._prev_oti, self._prev_ts)

    def reset(self):
        """Clear retained state (used after long gaps when reset behavior)."""
        self._prev_oti = None
        self._prev_ts = None

    # ------------------------------------------------------------------
    def _eval_range(self, oti):
        """F2: absolute bounds. Stateless; independent of gap handling."""
        if self.upper_threshold is not None and oti > self.upper_threshold:
            return True, "upper"
        if self.lower_threshold is not None and oti < self.lower_threshold:
            return True, "lower"
        return False, ""

    def process(self, oti, ts_minutes):
        """Process one sample; returns a FilterDecision.

        Parameters
        ----------
        oti : float or None
            Current OTI value in OTI units (None/NaN = missing).
        ts_minutes : float
            Timestamp of the sample in minutes since an arbitrary epoch.
        """
        # ---- missing input: never flag, never update state -------------
        if oti is None or (isinstance(oti, float) and math.isnan(oti)):
            return FilterDecision(
                flagged=False, reason="", data_anomaly=True,
                state_updated=False,
                note="missing/NaN OTI: not evaluated; state unchanged")

        self._samples_seen += 1

        # ---- stateless range rule (F2 part) -----------------------------
        range_flag, range_reason = self._eval_range(oti)

        # ---- first sample: no dynamics possible ------------------------
        if self._prev_oti is None:
            self._prev_oti = oti
            self._prev_ts = ts_minutes
            return FilterDecision(
                flagged=range_flag, reason=range_reason,
                state_updated=True,
                note="first sample: range only")

        dt = ts_minutes - self._prev_ts

        # ---- non-positive dt: data anomaly, no division ----------------
        if dt <= 0:
            return FilterDecision(
                flagged=range_flag, reason=range_reason,
                data_anomaly=True, state_updated=False,
                note=f"non-positive dt ({dt:g} min): dynamics not evaluated; "
                     "state unchanged")

        # ---- long gap handling (both behaviors supported) --------------
        if dt > self.gap_minutes and self.gap_behavior == "reset":
            self._prev_oti = oti
            self._prev_ts = ts_minutes
            return FilterDecision(
                flagged=range_flag, reason=range_reason,
                state_updated=True,
                note=f"gap {dt:g} min > {self.gap_minutes:g} min: state reset; "
                     "range only")

        # ---- dynamics evaluation ---------------------------------------
        jump = oti - self._prev_oti          # signed, OTI units
        rate = abs(jump) / dt                # OTI units per minute

        flagged = False
        reasons = []
        if self.filter_type == "range":
            flagged = range_flag
            if range_flag:
                reasons.append(range_reason)
        if self.filter_type in ("rate", "combined"):
            if rate > self.rate_threshold:   # strict >
                flagged = True
                reasons.append("rate")
        if self.filter_type == "jump":
            if abs(jump) > self.jump_threshold:  # strict >
                flagged = True
                reasons.append("jump")
        if self.filter_type == "combined" and range_flag:
            flagged = True
            reasons.append(range_reason)

        # ---- update retained state -------------------------------------
        self._prev_oti = oti
        self._prev_ts = ts_minutes

        return FilterDecision(
            flagged=flagged, reason="+".join(reasons),
            rate=rate, jump=jump, state_updated=True)
