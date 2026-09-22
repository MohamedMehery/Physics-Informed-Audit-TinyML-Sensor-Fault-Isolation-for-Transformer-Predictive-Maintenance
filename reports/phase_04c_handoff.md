# Phase 4C Handoff — DOI Propagation and Outreach Finalization

**1. Status.** COMPLETE. DOI `10.5281/zenodo.22904790`
(https://doi.org/10.5281/zenodo.22904790) verified via the Zenodo
record API (record 22904790: title, version v0.1.0, creator, and
license all match this repository; created 2026-09-22). No experiments,
no scientific-content changes, nothing sent.

**2. Commit hashes.** DOI propagation: `68a1d1e` ("Add Zenodo DOI for
v0.1.0 (post-release metadata)"). Outreach finalization + this
handoff: `59f5028173ed844954386399b9a9d5f08494535e` (hash recorded in the follow-up commit,
Phase-3R/4B precedent). Both pushed to origin/main.

**3. Files touched (DOI propagation).** `README.md` (Zenodo badge under
the title; "How to cite" block with an APA-style reference and BibTeX
generated from the updated CITATION.cff via cffconvert — placeholder
key renamed, version line added); `CITATION.cff` (+ `doi`, + `url`; cffconvert-validated, schema
1.2.0); `.zenodo.json` (+ `doi`; valid JSON);
`paper/technical_report_v0_1.md` (header DOI line and §13 citation
updated — placeholders replaced); `docs/release_notes_v0_1.md` (DOI
added to header and How-to-cite; the "DOI pending" bullet removed from
the not-included list). `NOTICE` unchanged (contains no citation line,
per the task's conditional).

**4. Outreach finalization.** `docs/outreach_final.md` holds the four
copy-ready texts, none sent:

1. **Kaggle Discussion post (public)** — factual, non-accusatory title
   ("Audit: OTI_T is a same-sample threshold on OTI (OTI ≥ 236) —
   reproducible code + technical report"); body ≤ 350 words:
   CONFIRMED-DATA findings only, why it matters for anyone training on
   OTI_T, the (54, 236) gap, the leakage-controlled filter result with
   exact CI, unresolved unknowns (units, entity, nameplate), polite
   metadata request, links.
2. **Email to Putchala et al.** ≤ 250 words — inform, thank, four
   metadata questions (entity/IDs, units/semantics incl. OTI_T
   indication-vs-breaker, nameplate, export extraction), correction
   invitation.
3. **Email to Ramesh et al.** ≤ 250 words — scope stated explicitly:
   their Sharjah system and 24-hour-advance claim were NOT reproduced
   or evaluated, no judgment made; asks whether their preprocessing
   (17,207; 14,169 + 3,471 = 17,640 rows vs raw 19,352–20,316) can be
   documented; invites comment.
4. **LinkedIn/community post** ≤ 120 words, conservative wording.

Every text includes the GitHub URL and the DOI; all numbers match
`paper/technical_report_v0_1.md`; no forbidden phrasing, no accusation,
no invalidation of prior work; Phase-3R caveats preserved
(operationally defined events, no field-confirmed labels, post-hoc
internal validation only). Word counts verified programmatically.
KernelSphere and mirror-uploader drafts remain stored unfinalized in
`docs/outreach_requests.md`.

**5. Outreach log.** `docs/outreach_log.md` created with the required
columns (target | channel | date sent | link/DOI included | response |
follow-up date); rows left empty for the owner.

**6. Scan/test results.** Forbidden-claim scan: PASS — full suite
**137 passed** (the scan covers README, technical report, quickstart,
release notes, and paper drafts). A manual pre-scan of
`docs/outreach_final.md` and `docs/outreach_log.md` against the same
FORBIDDEN list found 0 offending lines (both files are outside the
test's scan scope; checked manually).
Programmatic word counts: Kaggle body ≤ 350, Putchala email ≤ 250,
Ramesh email ≤ 250, LinkedIn ≤ 120 — all within limits.

**7. Remaining owner actions.** (a) Review `docs/outreach_final.md`
and send each text from the owner's own accounts/channels; (b) record
sends and responses in `docs/outreach_log.md`; (c) optionally add the
DOI to the GitHub v0.1.0 release description.
