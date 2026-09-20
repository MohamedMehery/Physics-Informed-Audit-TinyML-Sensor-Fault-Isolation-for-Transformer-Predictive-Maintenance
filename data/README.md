# data/ — dataset storage policy

## Layout

- `downloads/` — official Kaggle archive and metadata snapshot, byte-for-byte
  as downloaded (**gitignored, not committed**).
- `raw/` — extracted raw CSVs, byte-for-byte unmodified (**gitignored, not
  committed**). The audit pipeline verifies their SHA-256 hashes against
  `provenance/dataset_manifest.json` before and after every run and aborts
  on any mismatch.

## Source (primary)

- Dataset: **Distributed Transformer Monitoring**
- URL: https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring
- Slug: `sreshta140/ai-transformer-monitoring`
- Owner: Sreshta Putchala (`sreshta140`)
- Version 1 ("Initial release"), created 2020-05-25T10:08:46.673Z (Kaggle metadata)
- Downloaded/accessed: 2026-09-20 (UTC) from the official Kaggle API download
  endpoint (anonymous public access); no mirror used.
- Archive: `ai-transformer-monitoring_v1.zip`, 1,481,162 bytes,
  SHA-256 `b9257e990d480b3486b176bc19304a18b4aa82fd07dc559ec16aaa3ed3fe9c68`
- Extracted files (6,915,767 bytes total): `CurrentVoltage.csv`,
  `Overview.csv`, `Power.csv`, `PowerFactor.csv`, `TotalPower.csv`
  — per-file sizes and SHA-256 hashes: see `provenance/dataset_manifest.json`.

## License / redistribution (IMPORTANT)

- License displayed on Kaggle: **"Data files © Original Authors"**.
- Redistribution conditions are **UNVERIFIED**. This license display does
  not clearly grant redistribution rights.
- Therefore the raw and downloaded data are **not committed** to this
  repository. Only hashes, manifests, code, and documentation are tracked.
- The code in this repository is licensed separately (license decision
  pending repository owner — no license is created on the owner's behalf).
- Nothing in this repository's code license permits redistribution of the
  Kaggle dataset files.

## Reproduction

```bash
python scripts/download_dataset.py   # re-downloads official archive + metadata,
                                     # verifies hash, extracts to data/raw/,
                                     # writes provenance/dataset_manifest.json
```

If Kaggle changes the archive (new version), `download_dataset.py` prints a
hash-mismatch warning — every downstream number must then be re-derived
deliberately.
