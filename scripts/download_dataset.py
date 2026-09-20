#!/usr/bin/env python3
"""Download the official Kaggle dataset archive and metadata snapshot.

Official source (primary):
  https://www.kaggle.com/datasets/sreshta140/ai-transformer-monitoring
  Kaggle public API endpoints (anonymous access worked at audit time):
    - metadata: https://www.kaggle.com/api/v1/datasets/view/{slug}
    - archive:  https://www.kaggle.com/api/v1/datasets/download/{slug}

The downloaded archive is stored byte-for-byte under data/downloads/ and
extracted under data/raw/ WITHOUT any modification. Hashes are recorded in
provenance/dataset_manifest.json (kept in git; the raw data themselves are
NOT committed — see data/README.md and the license discussion there).

If a KAGGLE_API_TOKEN / kaggle credentials are available, the same official
endpoints are used with authentication; otherwise anonymous public access
is attempted. No mirror is ever substituted silently.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from transformer_audit.provenance import (  # noqa: E402
    build_manifest, save_manifest, sha256_file, utc_now_iso,
)

SLUG = "sreshta140/ai-transformer-monitoring"
DATASET_URL = f"https://www.kaggle.com/datasets/{SLUG}"
VIEW_URL = f"https://www.kaggle.com/api/v1/datasets/view/{SLUG}"
DOWNLOAD_URL = f"https://www.kaggle.com/api/v1/datasets/download/{SLUG}"

EXPECTED_ARCHIVE_SHA256 = (
    # Version 1 archive hash recorded on 2026-09-20 (UTC) during Phase 1.
    "b9257e990d480b3486b176bc19304a18b4aa82fd07dc559ec16aaa3ed3fe9c68"
)
EXPECTED_ARCHIVE_BYTES = 1481162


def fetch(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "transformer-audit/0.1 (evidence audit)"})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            f.write(chunk)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--downloads", default=str(REPO_ROOT / "data" / "downloads"))
    ap.add_argument("--raw", default=str(REPO_ROOT / "data" / "raw"))
    ap.add_argument("--manifest", default=str(REPO_ROOT / "provenance" / "dataset_manifest.json"))
    args = ap.parse_args()

    dl = Path(args.downloads)
    raw = Path(args.raw)
    dl.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)

    meta_path = dl / "kaggle_metadata_v1.json"
    archive_path = dl / "ai-transformer-monitoring_v1.zip"

    print(f"[1/4] Fetching official metadata: {VIEW_URL}")
    try:
        fetch(VIEW_URL, meta_path)
    except Exception as e:  # noqa: BLE001
        print(f"FAILED to fetch metadata: {e!r}", file=sys.stderr)
        return 2
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    print(f"[2/4] Downloading official archive: {DOWNLOAD_URL}")
    try:
        fetch(DOWNLOAD_URL, archive_path)
    except Exception as e:  # noqa: BLE001
        print(f"FAILED to download archive: {e!r}", file=sys.stderr)
        return 2

    size = archive_path.stat().st_size
    digest = sha256_file(archive_path)
    print(f"[3/4] Archive bytes={size} sha256={digest}")
    if size != EXPECTED_ARCHIVE_BYTES or digest != EXPECTED_ARCHIVE_SHA256:
        print(
            "WARNING: archive differs from the Phase-1 recorded hash. If Kaggle "
            "published a new version, re-derive every downstream number and "
            "update the manifest deliberately.",
            file=sys.stderr,
        )

    import zipfile
    with zipfile.ZipFile(archive_path) as zf:
        zf.extractall(raw)
    print(f"[4/4] Extracted to {raw} (raw files unmodified)")

    manifest = build_manifest(
        dataset_slug=SLUG,
        dataset_title=meta.get("title") or "Distributed Transformer Monitoring",
        dataset_owner=meta.get("ownerName") or "Sreshta Putchala",
        dataset_url=DATASET_URL,
        version=int(meta.get("currentVersionNumber") or 1),
        version_notes=(meta.get("versions") or [{}])[0].get("versionNotes", ""),
        version_created=(meta.get("versions") or [{}])[0].get("creationDate", ""),
        license_displayed=meta.get("licenseName") or "Data files © Original Authors",
        access_date_utc=utc_now_iso(),
        archive_path=archive_path,
        extracted_dir=raw,
        metadata_path=meta_path,
        acquisition_method=(
            "Anonymous HTTPS download from official Kaggle API endpoints "
            "(api/v1/datasets/download/sreshta140/ai-transformer-monitoring); "
            "no mirror used."
        ),
        extra={
            "description_excerpt": (meta.get("description") or "")[:500],
            "dataset_id_kaggle": meta.get("id"),
        },
    )
    save_manifest(manifest, args.manifest)
    print(f"Manifest written: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
