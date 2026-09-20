"""Conditional physical-plausibility calculations (Phase 2).

Every function is explicitly conditional on stated assumptions:

- Temperatures are passed in "OTI units" (unit unconfirmed; °C-consistent
  with source-adjacent usage — see reports/variable_semantics_report.md).
- ``c_oil`` is a parameter, not an assumption of fact: the oil type is
  unknown. Mineral-oil typical specific heat ~1.8-2.1 kJ/(kg·K) is used
  only as a labeled scenario band.
- Active power converted 100% into oil heat is an INTENTIONALLY EXTREME
  upper bound; real transformers convert only losses (~0.5-2% of load)
  into heat.
- Apparent decay constants are "apparent measurement-channel time
  constants", not automatically the transformer oil time constant.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence


# ----------------------------------------------------------------------------
# A. Heating bound
# ----------------------------------------------------------------------------

def energy_kj(power_kw: float, dt_minutes: float) -> float:
    """Electrical energy over an interval, kJ."""
    if dt_minutes < 0:
        raise ValueError("negative interval")
    return power_kw * dt_minutes * 60.0


def critical_mass_kg(energy_kj_: float, c_kj_per_kg_k: float, delta_t_units: float) -> float:
    """m_critical = E_available / (c * delta_T).

    The effective thermal mass that could be heated by delta_T (OTI units)
    if ALL the available energy went into it.
    """
    if c_kj_per_kg_k <= 0:
        raise ValueError("specific heat must be positive")
    if delta_t_units <= 0:
        raise ValueError("delta_T must be positive")
    return energy_kj_ / (c_kj_per_kg_k * delta_t_units)


def required_power_kw(mass_kg: float, c_kj_per_kg_k: float,
                      delta_t_units: float, dt_minutes: float) -> float:
    """Thermal power needed to raise mass_kg by delta_T in dt_minutes."""
    if dt_minutes <= 0:
        raise ValueError("dt must be positive")
    return mass_kg * c_kj_per_kg_k * delta_t_units / (dt_minutes * 60.0)


def achievable_delta_t_units(power_kw: float, mass_kg: float,
                             c_kj_per_kg_k: float, dt_minutes: float) -> float:
    """Delta-T achievable if ALL power goes into the mass."""
    if mass_kg <= 0:
        raise ValueError("mass must be positive")
    return power_kw * dt_minutes * 60.0 / (mass_kg * c_kj_per_kg_k)


# ----------------------------------------------------------------------------
# B. Apparent first-order decay constant
# ----------------------------------------------------------------------------

def apparent_time_constant_minutes(t0: float, t1: float, ta: float,
                                   dt_minutes: float) -> float:
    """tau = -dt / ln((T1 - Ta) / (T0 - Ta)).

    Returns NaN when the log argument is outside (0, 1] — i.e., when the
    pair is not a decaying excess over ambient (already below ambient,
    rising, or already at ambient). The caller must treat NaN as "not a
    valid first-order decay pair", never clip or force it.
    """
    ratio = (t1 - ta) / (t0 - ta)
    if not (0.0 < ratio < 1.0):
        return float("nan")
    if dt_minutes <= 0:
        return float("nan")
    return -dt_minutes / math.log(ratio)


def tau_domain_status(t0: float, t1: float, ta: float) -> str:
    """Explain why a pair is or is not a valid decay pair."""
    if t0 - ta <= 0:
        return "start not above ambient"
    if t1 - ta <= 0:
        return "end at or below ambient"
    ratio = (t1 - ta) / (t0 - ta)
    if ratio >= 1.0:
        return "not decaying (end excess >= start excess)"
    return "valid"


def tau_sensitivity(t0: float, t1: float, ta: float, dt_minutes: float,
                    ta_offsets: Sequence[float] = (-5.0, -2.0, 0.0, 2.0, 5.0),
                    dt_multipliers: Sequence[float] = (0.5, 1.0, 1.5)) -> Dict:
    """Sensitivity of tau to ambient-temperature and timing uncertainty."""
    rows = []
    for dta in ta_offsets:
        for mdt in dt_multipliers:
            tau = apparent_time_constant_minutes(t0, t1, ta + dta, dt_minutes * mdt)
            rows.append({
                "ta_offset_units": dta,
                "ta_used": ta + dta,
                "dt_minutes": dt_minutes * mdt,
                "tau_minutes": tau,
                "domain_status": tau_domain_status(t0, t1, ta + dta),
            })
    return {"base": apparent_time_constant_minutes(t0, t1, ta, dt_minutes),
            "domain_status_base": tau_domain_status(t0, t1, ta),
            "rows": rows}
