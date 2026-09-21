# Release Checklist — v0.1.0

Owner-run release procedure for the Transformer Telemetry Integrity
Audit repository. Phase 4B prepared everything below on 2026-09-21;
items marked [x] are done and verified, [ ] are owner actions.

## A. Pre-release verification (re-run before tagging)

- [x] Raw data absent from git — verify: `git ls-files data/ | grep -v "data/README.md"`
      (expected: no output)
- [x] `.gitignore` protects `data/raw/` and `data/downloads/` — verify:
      `grep -nE "data/(raw|downloads)" .gitignore`
- [x] Provenance gates pass (hash verify before/after every run; part of
      every script and of the test suite)
- [x] Tests pass — `python -m pytest` → **137 passed**
- [x] C/Python parity passes — `python scripts/check_c_python_parity.py`
      → 0 mismatches, sizeof(mif_filter_t) = 72 B
- [x] Forbidden-claim scan passes (part of pytest:
      `test_no_forbidden_overclaims`, `test_required_wording_present`,
      Energies-wording and exploratory-label tests in
      `tests/test_phase3r_leakage.py`)
- [x] README updated (137 tests, Phase-3R commands, parity command,
      not-peer-reviewed statement, corrected OTI-unit wording, archive
      pointers, license section)
- [x] Technical report exists: `paper/technical_report_v0_1.md`
- [x] `LICENSE` exists (Apache-2.0, code)
- [x] `CONTENT_LICENSE.md` exists (CC BY 4.0, docs/reports/figures)
- [x] `NOTICE` exists
- [x] `CITATION.cff` exists (cffconvert-validated, schema 1.2.0)
- [x] `.zenodo.json` exists (valid JSON)
- [x] Release notes exist: `docs/release_notes_v0_1.md`
- [x] Reproducibility quickstart exists: `docs/reproducibility_quickstart.md`
- [x] Phase-3 originals archived: `docs/archive/superseded_phase3/`
- [x] No outreach sent before DOI (`docs/outreach_requests.md` drafts
      stored only)

## B. Tag and push (owner — run manually)

```bash
git status
git log --oneline -5
git tag -a v0.1.0 -m "v0.1.0 reproducible transformer telemetry audit"
git push origin main
git push origin v0.1.0
```

## C. Zenodo archival (owner — manual web steps)

1. **Enable the GitHub repository in Zenodo:** sign in at
   https://zenodo.org with the GitHub account, open Account → GitHub,
   authorize the Zenodo app, and toggle ON
   `MohamedMehery/transformer-telemetry-integrity-audit`.
2. **Create the GitHub release v0.1.0** from the tag (suggested title:
   "v0.1.0 reproducible transformer telemetry audit"; description: see
   `docs/release_notes_v0_1.md`). Zenodo reads `.zenodo.json` at
   release-harvest time (title, creator, license, keywords,
   description, version v0.1.0, open access).
3. **Let Zenodo archive the release** (a new deposit appears; raw
   Kaggle data is not part of the archive since it is not in the
   repository).
4. **Copy the minted DOI** (concept DOI + version DOI).
5. **Update README, CITATION.cff, .zenodo.json, and
   `paper/technical_report_v0_1.md` with the DOI** (replace the
   placeholder lines).
6. **Commit the DOI update** as v0.1.1 or a post-release metadata
   commit (do not rewrite history or move the tag).

## D. After DOI (owner decisions)

- Outreach (Kaggle owner, Putchala authors, Energies authors,
  KernelSphere) may proceed **only after** publication + DOI, and only
  with explicit owner authorization (`docs/outreach_requests.md`).
- Optional: Zenodo community selection; optional preprint of the
  technical report (separate owner decision).
