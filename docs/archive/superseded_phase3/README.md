# Superseded Phase-3 documents

The two files in this directory are the original Phase-3 filter report
and handoff. They are **superseded by Phase 3R** (leakage-controlled
evaluation and claim correction) and are preserved verbatim (moved,
not modified) for the historical record.

- Authoritative current results: `reports/phase_03r_report.md` and
  `reports/phase_03r_handoff.md`
- Consolidated citable report: `paper/technical_report_v0_1.md`
- Why superseded: the acceptance review
  (`reports/phase_03_acceptance_review.md`) found that the original
  threshold selection used the full dataset (leakage), two boundary
  statements were wrong ("(54, 236]" should be **[54, 236)**; "jump
  ≥ 50" should be |ΔOTI| > thr with thr ∈ **[42, 182)**), and the
  1,160-configuration full-data sweep required explicit
  exploratory/oracle labeling.

Do **not** cite these files as authoritative results. Known-stale
statements inside them are catalogued in
`reports/prepublication_inventory.md` and corrected in the Phase-3R
documents.
