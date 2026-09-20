# Conditional Physics Analysis — Phase 2

**Status:** performed ONLY after the entity, unit, and source reviews. Every
number below is conditional on the assumptions listed with it. Curves, not
points. No hardware root cause is claimed anywhere. OTI values are in
**OTI units** (unit unconfirmed) — results scale with whatever the true unit
is, and that is stated per table.

**Inputs:** 10 rising and 10 falling band-crossing transitions on the
canonical (first-occurrence) series; identical counts under P1–P4
(`duplicate_policy_sensitivity.csv`). Rising: ΔT = 182–206 OTI units over
Δt = 2–18 min (median 200 units / 8 min). Artifacts:
`physics_sensitivity.csv`, `apparent_tau_per_transition.csv`,
`oti_transitions_phase2.csv`, figures `reports/figures/physics_bounds_*.png`.

---

## A. Heating bound — m_critical = E_available / (c·ΔT)

**Question:** with the electrical energy actually observable in the export,
how much effective thermal mass could be driven through the observed ΔT —
and conversely, what power would plausible masses require?

**Assumptions (all stated, all conditional):**
- A1: 100 % of the electrical power flowing at the transformer converts to
  heat in the measured oil body — an **extreme upper bound**; realistic
  conversion is losses-only (typically a small fraction of load), which makes
  every required-power number below larger and every feasible mass smaller.
- A2: c = 1.8–2.1 kJ/(kg·K) (mineral-oil typical band; oil type unknown).
- A3: OTI units behave like temperature differences for ΔT (unit unconfirmed).
- A4: power during the transition is bounded by what the export shows around
  it (local max within ±30 min = 33–103 kW; global max 142.1 kW; scenarios
  500/1500 kW parameterize unobserved supply).
- A5: sampled data cannot exclude an unobserved high-power sub-interval event
  between samples — this bound constrains *observable* causes only.

**Result — critical effective thermal mass (kg) that could rise by the
observed ΔT within the observed Δt:**

| Power scenario | m_crit range across the 10 rises |
|---|---|
| local max within ±30 min (33–103 kW) | 32 – 271 kg |
| global max observed (142.1 kW) | 45 – 426 kg |
| parameterized 500 kW | 157 – 1,500 kg |
| parameterized 1500 kW | 471 – 4,500 kg |

**Result — required sustained power (MW) for candidate masses, c = 1.9:**

| Mass | fastest rise (206 units / 2 min) | median rise (200 / 8 min) | slowest rise (182 / 18 min) |
|---|---|---|---|
| 300 kg | 0.98 MW | 0.24 MW | 0.10 MW |
| 700 kg | 2.28 MW | 0.55 MW | 0.22 MW |
| 1,500 kg | 4.89 MW | 1.19 MW | 0.48 MW |

**Reading (conditional on A1–A5):** under the *extreme* 100 %-conversion
assumption, only effective masses of tens-to-hundreds of kg are compatible
with the observed power — far below the oil-equivalent mass of any
distribution-class transformer (11 kV-class DT total masses run into tonnes
per the official envelope; oil alone is typically hundreds of kg or more).
Conversely, masses of hundreds of kg or more would require sustained
0.1–5 MW through the measured point, versus a maximum observed 0.142 MW —
even before replacing A1 with a realistic loss fraction, which shrinks the
feasible masses by another 1–2 orders of magnitude. **Within observed-power
causes, the rises are not energetically consistent with bulk-oil heating of
a distribution-transformer-scale thermal mass.** This does NOT exclude an
unobserved electrical event between samples (A5) — the export simply cannot
test that — and it does not identify a root cause for the OTI band itself.

Figures: `physics_bounds_power_vs_mass.png` (required power vs mass, log
scale, observed-load line), `physics_bounds_achievable_dT.png` (achievable
ΔT vs mass at observed/parameterized loads), `physics_bounds_critical_mass.png`
(m_crit at extreme-bound scenarios).

## B. Cooling bound — apparent time constant τ

**Definition:** for each falling transition, τ_apparent = −Δt / ln((T1−Ta)/
(T0−Ta)) using ATI as ambient. This is the **apparent measurement-channel
time constant** — the first-order-decay constant of the *channel as
published*, which conflates oil thermal response, sensor response, and any
processing/quantization in the chain. It is NOT asserted to be the oil
thermal time constant (typical top-oil constants are ~1–3 h; the values
below are far smaller, which is itself informative about the channel).

**Domain guard:** pairs whose excess ratio leaves (0, 1) — rising through the
transition, ambient above the endpoint, zero excess — return NaN and are
excluded (never clipped): 144/150 sensitivity rows valid; 6/150 invalid.

**Results (base cases, ATI ambient, actual Δt):** per-transition τ ranges
0.73–22.9 min; representative values 1.5–15 min at the observed Δt. Across
the sensitivity grid (ambient ±5 units, Δt ×{0.5, 1, 1.5}) the valid range is
**0.5–26 min**. Details: `apparent_tau_per_transition.csv`.

**Sensitivity structure:** τ is offset-invariant in the temperature channels
(test-verified) — an unknown common zero-point shift does not change it; an
unknown scale factor in OTI units scales ΔT and the derived masses in §A
linearly, which is why §A reports ranges against ΔT rather than points.
Ambient mis-estimation of ±5 units moves τ by roughly a factor of two at the
smallest Δt; record-policy choice (P1–P4) does not change any transition
pair (high-OTI rows never occur in repeated groups).

**Reading (conditional):** the channel returns from the 236–250 band to the
normal band with an apparent first-order constant of minutes, not hours.
Whatever physical or representational process produced the band, the
*measured channel* relaxes on a minute scale.

## C. Alternative-explanation matrix

Full matrix with supporting/contradicting evidence, missing metadata,
confidence, and falsification tests: `reports/generated/alternative_explanations.csv`
(9 candidate causes). Summary of standing:

1. physical top-oil transient (single asset) — weakly supported; energetically
   inconsistent under observed-power assumptions (§A) but not excludable for
   unobserved sub-interval events;
2. measurement-chain anomaly — moderate as a *category*, not as a root cause
   (no hardware metadata);
3. telemetry/ingestion re-transmission (H2) — explains the repeated records
   (not the excursions);
4. multiple-asset mixing (H3) — leaned against (asset_scope report);
5. multiple feeders (H4) — not supported by schema;
6. device error/status encoding at 236–250 — a representation hypothesis
   with threshold-perfect OTI_T alignment; unfalsified and unconfirmed;
7. export duplication — subsumed by 3;
8. timestamp/order corruption — cadence irregularities confirmed but they do
   not create the OTI steps;
9. unobserved short electrical event between samples — cannot be excluded by
   sampled data (standing limitation, stated, not a finding).

## What this analysis does NOT do

- No IEC thermal ODE, no thermal-network fitting, no ML training, no edge
  detection (per Phase-2 constraints).
- No claim that sampling excludes unobserved transients (A5 states the
  opposite).
- No nameplate, oil volume, or rating inference — all such parameters are
  either observed, scenario-labeled, or absent.
