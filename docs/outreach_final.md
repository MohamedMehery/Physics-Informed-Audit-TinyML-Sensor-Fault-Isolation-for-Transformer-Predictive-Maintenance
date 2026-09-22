# Outreach — Final Copy-Ready Texts (Phase 4C)

**Status: COPY-READY, NOT SENT.** Nothing here has been sent. Sending is
an owner action, from the owner's own accounts, after owner review
(standing constraint: outreach requires explicit owner authorization;
publication + DOI are now in place).

Compliance: every text includes the GitHub URL and the DOI; every
number matches `paper/technical_report_v0_1.md` and its cited artifacts;
no forbidden phrasing (no proven-fault claim, no "TinyML", no
accusation, no invalidation of prior work); Phase-3R caveats preserved
(operationally defined events, no field-confirmed labels, post-hoc
internal validation only, unresolved units/entity/nameplate). Word
counts verified programmatically (see `reports/phase_04c_handoff.md`).

- GitHub: https://github.com/MohamedMehery/transformer-telemetry-integrity-audit
- DOI: https://doi.org/10.5281/zenodo.22904790

---

## 1. Kaggle Discussion post (public)

**Title:** Audit: OTI_T is a same-sample threshold on OTI (OTI ≥ 236) — reproducible code + technical report

**Body:**

Hello — I audited this dataset end-to-end (code, tests, and a technical
report, all public) and wanted to share findings that matter if you
train on OTI_T, plus a request for metadata.

What I found — all reproducible from the raw files:

1. **OTI_T is a same-sample threshold:** OTI_T = 1 exactly when
   OTI ≥ 236 (100% of retained records; the flag never leads or lags
   OTI). A model that "predicts" OTI_T from OTI is learning a
   threshold, not an early-warning signal.
2. **OTI jumps from ≤ 54 to ≥ 236 with no observed values in between**
   (47 rows ≥ 236 in 10 windows, Jul–Sep 2019; rise rates up to
   91 OTI-units/min over 2–8 min, using actual Δt). The OTI
   engineering unit is unconfirmed, so everything is reported in
   "OTI units".
3. **Housekeeping:** timestamps are irregular (gaps up to ≈ 33.6 days),
   and every file has 406–931 repeated-timestamp groups (2.2–4.8% of
   timestamps), near-identical in value — most consistent with
   re-transmissions, not multiple devices.

As a check, I calibrated four simple deterministic streaming rules
(rate, range, combined, jump) **only on data before the first
excursion**, then replayed them unchanged on all later records:
range/jump/combined flag 10/10 excursions at or before the crossing
sample (exact 95% CI [0.6915, 1.0]; n = 10) at 0–0.26 false-alert
episodes/day; the rate rule flags 9/10 or 5/10 depending on
duplicate-handling policy. This is post-hoc internal validation, not
prospective testing. These are operationally defined events, **not
field-confirmed faults** — no ground-truth fault labels exist in this
dataset, and I claim no hardware root cause.

Still unresolved — I'd appreciate the uploader's or community's help:

- Units of OTI/ATI/OLI, and why WTI is binary in this export
- Whether the export represents one physical transformer (I could not
  establish this from the data)
- Any nameplate/rating metadata (the "1500 kVA" figure in papers
  describes a different system)

Everything is here (not peer reviewed):

- GitHub: https://github.com/MohamedMehery/transformer-telemetry-integrity-audit
- DOI: https://doi.org/10.5281/zenodo.22904790

Happy to be corrected on any point.

---

## 2. Email — Putchala et al. (dataset authors)

**Subject:** Questions about the 2019–2020 Kaggle export of your transformer monitoring data

Dear Prof. Putchala and co-authors,

I audited the public Kaggle export "Distributed Transformer Monitoring"
(sreshta140/ai-transformer-monitoring, v1) and read your ICCCE/ICACES
paper with interest. Thank you for making the data public — the audit
builds directly on it.

The audit (code, hashes, and a technical report; not peer reviewed) is
archived at https://doi.org/10.5281/zenodo.22904790 — GitHub:
https://github.com/MohamedMehery/transformer-telemetry-integrity-audit.
Headline observations: OTI_T = 1 exactly when OTI ≥ 236 (same sample,
100% of records); OTI steps from ≤ 54 to ≥ 236 with no values in
between (10 windows, Jul–Sep 2019); repeated-timestamp groups in every
file.

May I ask:

1. Does the export represent one physical transformer, and were
   device/asset IDs removed before publishing?
2. What are the units and semantics of OTI, ATI, OLI, WTI (binary in
   this export), OTI_A, OTI_T, and MOG_A? Was OTI_T an indication or a
   breaker status?
3. Is any nameplate rating available for the monitored unit?
4. How was the export extracted? (Your paper's live KernelSphere
   stream covers a later window than the 2019–2020 export.)

If anything in the audit mischaracterizes your work, please tell me
and I will correct it; answers will be credited.

With thanks,
Mohamed Mehery, Independent Researcher

---

## 3. Email — Ramesh et al. (Energies 15(21):7981)

**Subject:** The Kaggle dataset used in your Energies 15(21):7981 study — documentation question

Dear Prof. Ramesh and co-authors,

Your Data Availability Statement cites the Kaggle dataset
sreshta140/ai-transformer-monitoring (accessed 20 June 2022), which I
have audited end-to-end. The audit (code + technical report; not peer
reviewed) is archived at https://doi.org/10.5281/zenodo.22904790 —
GitHub: https://github.com/MohamedMehery/transformer-telemetry-integrity-audit.

To be clear about scope: the audit covers only the shared Kaggle
export. Your own Sharjah installation and your 24-hour-advance
anomaly statement were not reproduced or evaluated in any way, and the
audit makes no judgment about them.

In the export I found that OTI_T = 1 exactly when OTI ≥ 236 (same
sample), that OTI steps from ≤ 54 to ≥ 236 with no values in between,
and that every file contains repeated-timestamp groups. These affect
preprocessing choices, so I would be grateful if you could document:

1. What preprocessing produced your reported row counts (17,207;
   14,169 + 3,471 = 17,640)? The raw files contain 19,352–20,316 rows.
2. How you handled repeated timestamps and the OTI 236–250 band.

Any comment is welcome and will be credited; if anything
mischaracterizes your study I will correct it promptly.

With thanks,
Mohamed Mehery, Independent Researcher

---

## 4. LinkedIn / community post (short)

Public audit of a widely reused Kaggle transformer-monitoring dataset:
the OTI_T flag is a same-sample threshold (OTI ≥ 236), and OTI steps
from ≤ 54 to ≥ 236 with nothing in between — 10 excursions, no
field-confirmed fault labels, engineering unit unconfirmed, entity
identity unresolved. I built a deterministic plausibility filter
calibrated only on pre-event data: 10/10 excursions flagged at or
before the crossing sample (exact 95% CI [0.6915, 1.0]; n = 10),
0–0.26 false alerts/day — post-hoc internal validation only. Code,
137 tests, and a technical report (not peer reviewed):
https://github.com/MohamedMehery/transformer-telemetry-integrity-audit
DOI: https://doi.org/10.5281/zenodo.22904790

---

*KernelSphere and mirror-uploader drafts remain stored, unfinalized, in
`docs/outreach_requests.md` (owner decision whether to finalize).*
