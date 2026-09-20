# Corrections Relative to the Archived Remote README (4ab4b02)

The file `remote_readme_4ab4b02.md` is the GitHub repository's original
README (commits 6b81c65 → 7793576 → 4ab4b02), preserved verbatim when the
audit repository was merged in. It is the owner's earlier project write-up.
Several of its statements were corrected during the Phase-1/Phase-2 audit;
the current README.md and the reports under `reports/` supersede it. The
specific corrections:

| Remote README statement | Audit finding (supersedes) | Where |
|---|---|---|
| "OTI >= 236 °C" (and all °C units for OTI) | OTI unit is **unconfirmed** by any primary source; the audit uses "OTI units" throughout | `variable_semantics_report.md`; claim C33 |
| "Zero readings exist in the 70–236 °C band (a 166 °C void)" | The empty interval is **(54, 236)** — normal band tops out at 54, not 70; width 182 units | Phase-1 gap analysis; claim C08 |
| "heating is energetically impossible" / "energetically impossible across the entire plausible rating range" | Forbidden phrasing. The audit states a **conditional** bound: under an explicit extreme assumption (100 % power-to-oil, c = 1.8–2.1, OTI-units-as-temperature), observed-power causes imply effective masses of ~32–426 kg; sampled data cannot exclude unobserved sub-interval events; no root cause claimed | `conditional_physics_analysis.md` §A; claims C34, A21–A24 |
| Single-point m_crit ≈ 35.7 kg | Superseded by **curves/ranges** (m_crit 32–426 kg at observed loads; required-power table for candidate masses), all assumption-labeled | `physics_sensitivity.csv`; figures |
| "Independently sourced specs for 100–250 kVA distribution transformers indicate oil mass ~150–370 kg (≈1.4–1.6 L/kVA)" | No official manufacturer/utility source publishes per-rating oil volumes for the relevant class (reseller tables rejected); oil mass stays **UNKNOWN and parameterized** (50–3,000 kg scenario grid); the 100–250 kVA class estimate is not imposed | `asset_parameter_bounds.md`; A14 |
| "sensor faults" (title) / "most plausibly a measurement-chain / telemetry anomaly" | The audit's permitted strength: abrupt transitions **may be inconsistent with a normal top-oil transient**; measurement-chain/telemetry anomaly remains a **hypothesis**; no hardware root cause claimed; "proven sensor fault"/"ADC railing" never used | claim C23; `alternative_explanations.csv` |
| "n = 19,376" for the OTI_T rule | Precisely: the rule holds on all **20,316 raw** Overview records (and on the 19,376 unique timestamps); 0 violations | claim C30; `high_oti_duplicate_intersection.csv` |
| "event-triggered" telemetry, Δt 1–15 min | Cadence is 15-min **median** with observed intervals 1–9 min and multi-week gaps; the ingestion trigger is unknown | Phase-1 interval summary |
| Scripts in §5 (`audit_transformer_data.py`, `fit_thermal_model.py`, …) | Those files are not part of this repository's codebase; the audit pipeline is `scripts/run_data_audit.py`, `scripts/run_phase2_analysis.py`, `scripts/independent_raw_verification.py` (and no IEC thermal ODE is fit, per Phase-2 constraints) | README |
| MIT license badge | The audit repository intentionally ships **no LICENSE file** (license is the owner's decision; none created on the owner's behalf). The badge in the archived README is the owner's prior assertion. | README license caution |

The archived README's own §7 correction log (removing the fixed 300 kg oil
mass, reclassifying PT100/ONAN/ADC-rail claims as hypotheses, flagging
episode-merge sensitivity) is consistent in direction with the audit and is
acknowledged — the table above completes that process.
