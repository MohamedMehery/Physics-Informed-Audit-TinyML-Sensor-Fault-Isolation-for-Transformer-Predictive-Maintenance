# Source Lineage Report — Phase 2

**Question:** What is the verifiable provenance chain of the audited Kaggle
dataset (`sreshta140/ai-transformer-monitoring`, "Distributed Transformer
Monitoring"), and which statements about it can be traced to primary sources?

**Method:** full-text examination (not abstracts) of the two candidate sources,
verbatim-quote capture with section numbers, verification of dataset-page
metadata against the pinned archive, and strict source-role separation
(PRIMARY/ORIGINAL = dataset authors or provider; SOURCE-ADJACENT = researchers
using the same data; SECONDARY = later repeats or unrelated envelope
material). No copyrighted full text is committed to this repository; only
short quotes with section references.

---

## 1. The lineage picture established this phase

```
KernelSphere Technologies (Hyderabad, India)          [platform provider]
   │  IoT devices, REST APIs, 15-min cadence, 52 locations, Tripura
   │  (PRIMARY statement: Putchala et al. 2022, Sec. 4 — about their
   │   LIVE stream, recorded from November 2020 "up to date")
   ▼  (platform attribution of the export window = INFERENCE:
      uploader identity + identical schema + 15-min cadence +
      overlapping operating ranges; no primary statement covers
      the 2019-2020 window)
Kaggle "Distributed Transformer Monitoring"           [S1; THE AUDITED DATASET]
   sreshta140/ai-transformer-monitoring, v1, 2020-05-25
   ("Initial release" — the only version)
   owner: Sreshta Putchala — FIRST AUTHOR of Putchala et al. 2022
   official Kaggle API download; 5 CSVs SHA-256-pinned in
   provenance/dataset_manifest.json (acquisition: Phase 1)
   │
   ├─ byte-identical mirror: pythonafroz/transformer-fault-analysis v3
   │  (five files sha256-identical; Overview.csv renamed Alarm.csv; S9)
   │
   ▲  Data Availability Statement (verbatim, verified in full text):
   │  "The dataset adopted in this research is openly available in [Kaggle]
   │   at https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring
   │   (accessed on 20 June 2022)."
   │
Energies 15(21):7981                                  [S7; SOURCE-ADJACENT]
   Ramesh, Shahriar, Al-Ali, Osman, Shaaban (AUS Sharjah), CC BY
   GRU forecasting + Isolation Forest anomaly detection run on THIS
   dataset (the same v1 archive audited here — only version 1 exists,
   so the copy they accessed on 2022-06-20 is that archive)
```

**Key facts, each traceable:**

1. **The audited archive is the authors' original upload.** Phase 1
   downloaded `ai-transformer-monitoring_v1.zip` from the official Kaggle
   API (byte size 1,481,162; SHA-256
   `b9257e…ed3fe9c68`; per-file hashes pinned). The dataset has a single
   version ("Initial release", 2020-05-25T10:08:46Z). Owner name:
   "Sreshta Putchala".

2. **The uploader is the ICCCE paper's first author.** The Springer author
   list for 10.1007/978-981-16-7389-4_21 (S11) reads "Putchala, S.R., Kotha, R.,
   Guda, V., Ramadevi, Y." (Chaitanya Bharathi Institute of Technology,
   Hyderabad) [verified on the Springer chapter page]. The paper is
   therefore the dataset authors' own analysis — of their LIVE stream, not
   of this export (next point).

3. **The paper's data statement describes a different window.** Sec. 4,
   verbatim: "The data set is provided by a private company, KernelSphere
   Technologies. This live data is obtained from the REST APIs recorded
   from November 2020 up to date at 52 different locations at the State,
   Tripura, India, with IoT devices and is updated for every 15 min."
   Their paper's analyses (≈237,687 rows per Sec. 4.4 counts; Fig. 2 June
   2021) postdate the export window (2019-06-25..2020-04-14) by seven
   months. The schema (their Table 2) matches the export exactly, and
   their live KW forecasts (28–97) / VL1 (≈241) overlap the export's
   ranges (33–103 kW; median 242.7 V) — same-platform consistency signals.
   **Attribution of the export window to the KernelSphere platform is an
   inference (uploader + schema + cadence + ranges), not a primary
   statement.**

4. **The Energies study used the same archive we audit.** Their Data
   Availability Statement names the sreshta140 URL (accessed 20 June
   2022); only version 1 exists, so they analyzed the same v1 files. Their
   system description — 1500 kVA, 11/0.4 kV at University City Sharjah,
   PSCAD five-module simulation (Sec. 5.1, Sec. 6) — is their OWN
   monitoring system and is **not** a description of this dataset's
   source. The 1500 kVA rating cannot be transferred to the audited
   asset; their "similar transformers sharing load capacity…" phrasing is
   generic. Their internal row-count reporting (17,207 vs 14,169+3,471 =
   17,640) does not match the file row counts (19,352/20,316) — their
   preprocessing is undocumented; noted, not resolved.

5. **The paper's modelling thresholds do not transfer.** OTI > 65 trip
   band, VL < 220, KW > 115 etc. (Sec. 4.2) were tuned on the Nov-2020+
   live stream. In the export, OTI_T aligns exactly with OTI ≥ 236 — a
   different threshold — so even the flag semantics of OTI_T stay open
   (Energies' "OTT shuts off electrical flow" description conflicts with
   the export's electrical continuity during OTI_T=1 windows).

## 2. What remains unknown (and why it matters)

- **Entity scope of the export**: no device, location, or asset column;
  the provider platform serves 52 locations. Whether the export is one
  transformer, one location, or several is not stated by any primary
  source.
- **Origin of the export window**: who extracted the 2019–2020 window
  from the platform, and how, is undocumented (the paper describes its
  own Nov-2020+ capture only).
- **Channel units and semantics** (OTI unit, WTI binary meaning, OTI_T
  indication vs command): see variable_semantics_report.md.

## 3. Source roles (final classification)

| ID | Source | Role | Full text accessed |
|----|--------|------|-------------------|
| S1 | Kaggle `sreshta140/ai-transformer-monitoring` v1 (audited archive) | PRIMARY (the data under audit; uploaded by the paper's first author) | files + description page + API metadata snapshot |
| S11 | Putchala et al. 2022, ICCCE/ICACES, Springer AIS pp. 217–230, DOI 10.1007/978-981-16-7389-4_21 | PRIMARY (dataset authors' platform statements; their modelling on the live stream) | **complete** (all sections incl. Tables 2, 8, 9; author-shared copy) |
| S7 | Ramesh et al., Energies 15(21):7981, DOI 10.3390/en15217981 (CC BY) | SOURCE-ADJACENT (uses the same archive; own system described separately) | **complete for all relied-upon sections** (incl. Data Availability Statement, Sec. 5.1, 6, 7.1, 8, 9.2, 10) |
| S9 | Kaggle mirror `pythonafroz/transformer-fault-analysis` v3 | SECONDARY (byte-identical re-upload; no new provenance) | files verified by hash (Phase 1) |
| S16 | KernelSphere Technologies (kernelsphere.com; CIN U72200TG2013PTC085215) | PRIMARY-adjacent (platform provider identity; public registry/contact pages) | public pages |
| S12–S15 | ETT, BSES Delhi spec, Bharat Bijlee, IS 1180 scope | SECONDARY (manufacturer/utility envelope for parameter plausibility; unrelated to dataset) | official pages/specs only |

## 4. Legal/excerpt compliance

- Putchala et al.: Springer copyright. Quotes in this repository are short
  (single sentences), attributed with section numbers, and used for
  verification/lineage purposes. The author-shared ResearchGate copy was
  read via its public link; no copy of the PDF is stored in this
  repository.
- Ramesh et al.: CC BY 4.0 — quoting with attribution is licensed; we
  still quote only what is needed, with section numbers.
- Kaggle dataset pages: quoted fragments (parameter list, date-window
  sentence, Data Availability sentence) are factual metadata excerpts.

## 5. Verdict

The audited archive is the original upload by the Putchala et al. first
author, and the Energies study used that same archive — the three
artifacts (dataset, ICCCE paper, Energies paper) are verified to be one
lineage. However, **no primary source establishes the entity scope of the
export** (one transformer vs many), and the paper's platform statement
covers a later data window. The required entity-unresolved statement
therefore stands: *The published dataset does not provide enough
information to establish that adjacent rows belong to the same physical
transformer.*
