# Paper Outline (Phase 3)

> **SUPERSEDED by `paper/outline.md` (Phase 3R revision).** The Phase-3R
> package reorders evidence (leakage-controlled replay primary; oracle
> sweep exploratory), adds the T1/T2/T3 task separation, and corrects
> the boundary and early-warning wording. This file is retained for
> history; do not cite it for current claims.

Working title (conservative, no unearned terms):

> **"Auditing a Public Distributed-Transformer-Monitoring Dataset: Record
> Artifacts, Sharp Oil-Temperature-Indicator Excursions, and a Deterministic
> Causal Plausibility Filter"**

Subtitle option: *A reproducibility-first case study on what a 19k-record
Kaggle export can and cannot support.*

Target venue character: engineering-informatics / measurement-integrity
(e.g., a data-quality or instrumentation track). The paper is an AUDIT
paper, not a fault-detection-methods paper.

---

## 1. Story in one paragraph

A widely reused public dataset (19,352-row Kaggle export, reused by a
peer-reviewed Energies 2022 study) contains sharp OTI excursions that no
published analysis has audited. We show the archive carries record-level
artifacts (repeated timestamps), that the OTI channel jumps from ≤54 to
≥236 "OTI units" with an empty interval between, that the excursions are
inconsistent in magnitude and rate with gradual thermal behavior of the
observed load (conditional physics), and that a 1–11 operation-per-sample
deterministic causal filter flags every excursion concurrently with zero
false alarms — but that no multi-hour early warning exists in this export,
contradicting the 24-hour-advance claim attached to the reused data at the
channel level. The value we demonstrate is sensor-integrity flagging at
negligible compute, not prediction.

## 2. Section plan with evidence map

Status labels: **[READY]** = reproducible artifact exists;
**[PARTIAL]** = artifact exists but coverage/verification incomplete;
**[CONDITIONAL]** = result valid only under labeled assumptions;
**[NEEDS WORK]** = required before submission.

| # | Section | Core content | Key artifacts | Status |
|---|---------|--------------|---------------|--------|
| 1 | Introduction: public dataset reuse without audit | Kaggle export reused by Energies 2022 (their Data Availability Statement names it); 30+ public notebooks; none audit the OTI excursions | `source_lineage_report.md`, `source_claim_matrix.csv` | **[READY]** |
| 2 | Dataset and provenance | 19,352 rows; byte-preserved raw files; SHA-256 manifest; single version; uploader = first author of Putchala et al. | `dataset_manifest.json`, C25/C26 | **[READY]** |
| 3 | Record artifacts: repeated timestamps | 406–931 groups/file, cross-file synchronized, near-identical values, deployment-month concentration, never contain high-OTI records; policies P1–P4 | `timestamp_multiplicity.csv`, `repeated_record_conflicts*.csv` | **[READY]** |
| 4 | The excursions (phenomenology) | 10 rising band-crossings, 47 high-OTI rows in 10 windows (16 Jul–3 Sep 2019); empty interval (54,236); step-like rises (+11.1…+91.0 OTI-units/min) and falls; OTI_T ⟺ OTI≥236 rule exact | `excursion_catalog.csv`, C29/C30 | **[READY]** |
| 5 | Entity and scope limits | No identifying metadata; adjacency ≠ same physical transformer; structural tests lean against multi-asset/multi-feeder readings | `asset_scope_and_entity_analysis.md`, C31/C32 | **[READY]** |
| 6 | Conditional physics | Under labeled extreme assumptions (100% power-to-oil, c=1.8–2.1, OTI-units-as-temperature, observed loads): rises need m_eff 32–426 kg; apparent channel time constant 0.5–26 min | `physics_sensitivity.csv`, C34/C35 | **[CONDITIONAL]** — present as bounds, never points |
| 7 | Deterministic causal plausibility filter | F1 rate / F2 range / F3 combined / F4 jump; 1–11 ops/sample; strict thresholds; explicit edge-case contract; stdlib reference implementation | `plausibility_filter.py`, this phase's tests | **[READY]** |
| 8 | Event-based evaluation | 10 events, all 4 policies, 1,160 configurations; detection concurrent 10/10 with 0 FA episodes at many operating points; lead times via actual timestamps | `filter_sweep_summary.csv`, `filter_per_event_detail.csv` | **[READY]** |
| 9 | Baselines and Pareto frontier | B1 trivial threshold (10/10 by construction), B2 seeded random (dominated), B3 static percentile (non-causal; mirrors F2 sub-band); frontier = zero-FA concurrent corner + sub-band lead/FA trade-off | `pareto_frontier.csv` | **[READY]** |
| 10 | Lead-time honesty | Max genuine pre-crossing lead 48 min (1 event, F2 OTI>45); 27–37 min on 2/10 events at 0.055 FA/day; median lead 0; **no evidence of multi-hour warning**; Energies §10 24-h statement not supported by this export at channel level | `filter_per_event_detail.csv` (lead columns) | **[READY]** — wording must stay channel-level |
| 11 | Computational cost | Exact op counts; Cortex-M0 cycle ESTIMATES from documented instruction timings (F3: ~30 fixed-point / ~291 soft-float cycles) vs 28-16-8-1 MLP (584 MACs, 3,529/61,986) and 100-tree GBDT (~600 compares, ~152 KB) | `computational_cost_comparison.csv` | **[READY]** (estimates labeled; no specific-hardware claim) |
| 12 | Related work | Putchala et al. 2022 (system paper), Energies 2022 (IF/GRU results on this data), notebook literature; none audit the channel | `bibliography_register.csv` | **[PARTIAL]** — 2 primary + notebook corpus; a broader related-work pass is **[NEEDS WORK]** |
| 13 | Limitations | Units unknown; entity unknown; single export, no provider logs; sampling cannot exclude sub-interval events; no ground-truth fault labels; "OTI units" throughout | assumption register | **[READY]** |
| 14 | Conclusions | Channel-integrity flagging at negligible cost is reproducible; early warning is absent in this export; dataset reuse should carry the audit's caveats | — | **[READY]** |

## 3. Figures/tables plan (all from existing artifacts)

1. OTI time series with the 10 excursions + empty-band annotation
   (regenerate from Phase-1 artifacts). **[READY]**
2. Filter ROC by type (FA episodes/day vs detection rate) —
   `figures/filter_roc_by_type.png`. **[READY]**
3. Threshold sensitivity panels (F1/F2/F4) —
   `figures/filter_threshold_sensitivity.png`. **[READY]**
4. Lead-time distribution at the balanced operating point —
   `figures/filter_lead_time_distribution.png`. **[READY]**
5. Cost comparison table — `computational_cost_comparison.csv`. **[READY]**
6. Provenance/manifest table (hashes, counts, file inventory). **[READY]**

## 4. Claims NOT made (paper must state these explicitly)

1. **No fault detection.** The filter flags readings inconsistent with
   gradual thermal behavior at the measurement-channel level; the root
   cause of every flagged excursion is unknown.
2. **No sensor-failure diagnosis.** No statement that a sensor failed,
   drifted, or shorted; no ADC/rail/transmitter mechanism claim.
3. **No early-warning claim.** No prediction horizon beyond the measured
   maximum lead (48 min, one event); no "24 hours before" claim — the
   Energies §10 statement is reported as *their* system-level claim and
   marked unsupported *by this export at channel level*.
4. **No asset identity.** No nameplate rating, cooling class, location,
   or manufacturer; no assertion that adjacent rows are the same physical
   transformer.
5. **No units for OTI.** "OTI units" everywhere; never °C or %.
6. **No TinyML / AI / intelligence claims.** The filter is a
   deterministic rule set; no learning, no inference, no "intelligent
   edge".
7. **No deployment claim.** No "runs on Arduino"; at most "within the
   documented computational capabilities of the ARM Cortex-M0 class
   (cycle estimates from public instruction-timing tables)".
8. **No overfitting accusation.** Notebook results are cited as reported,
   with the observation that their tasks were not audited.
9. **No ground truth.** The 10 events are band-crossings, not labeled
   faults; detection rates are against that definition only.
10. **No simultaneous-multichannel claims** (no Δ + tolerance evidence).

## 5. Gaps to close before submission **[NEEDS WORK]**

- Broader related-work sweep (condition-monitoring data audits; dataset
  reproducibility studies) — currently 2 primary sources + notebooks.
- Outreach outcomes (provider/owner contact) — requests stored, NOT sent;
  paper must not cite a response that does not exist.
- Optional: second dataset for external validity of the filter family
  (out of current scope; flagged as future work).
