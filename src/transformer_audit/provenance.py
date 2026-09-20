"""Provenance: hashing, manifest building, and raw-file preservation checks."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


def sha256_file(path: str | Path, chunk_size: int = 1 << 20) -> str:
    """SHA-256 of a file, streamed."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_manifest(
    *,
    dataset_slug: str,
    dataset_title: str,
    dataset_owner: str,
    dataset_url: str,
    version: int,
    version_notes: str,
    version_created: str,
    license_displayed: str,
    access_date_utc: str,
    archive_path: str | Path,
    extracted_dir: str | Path,
    metadata_path: Optional[str | Path] = None,
    acquisition_method: str = "",
    extra: Optional[Dict] = None,
) -> Dict:
    """Build a dataset manifest dict with hashes of archive and each file."""
    archive_path = Path(archive_path)
    extracted_dir = Path(extracted_dir)
    files: List[Dict] = []
    for p in sorted(extracted_dir.iterdir()):
        if not p.is_file():
            continue
        files.append({
            "filename": p.name,
            "byte_size": p.stat().st_size,
            "sha256": sha256_file(p),
        })
    manifest = {
        "dataset": {
            "slug": dataset_slug,
            "title": dataset_title,
            "owner": dataset_owner,
            "url": dataset_url,
            "version": version,
            "version_notes": version_notes,
            "version_created_utc": version_created,
            "license_displayed": license_displayed,
            "access_date_utc": access_date_utc,
        },
        "archive": {
            "filename": archive_path.name,
            "byte_size": archive_path.stat().st_size,
            "sha256": sha256_file(archive_path),
        },
        "acquisition_method": acquisition_method,
        "extracted_files": files,
        "notes": extra or {},
    }
    if metadata_path is not None:
        metadata_path = Path(metadata_path)
        manifest["kaggle_metadata_snapshot"] = {
            "filename": metadata_path.name,
            "byte_size": metadata_path.stat().st_size,
            "sha256": sha256_file(metadata_path),
        }
    return manifest


def save_manifest(manifest: Dict, path: str | Path) -> None:
    path = Path(path)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_manifest(path: str | Path) -> Dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def verify_raw_files(manifest: Dict, extracted_dir: str | Path) -> Dict:
    """Verify that extracted raw files still match the manifest hashes.

    Used as a preservation gate before and after every audit run: raw files
    must remain byte-for-byte unmodified.
    """
    extracted_dir = Path(extracted_dir)
    report = {"all_match": True, "files": {}}
    for entry in manifest["extracted_files"]:
        p = extracted_dir / entry["filename"]
        if not p.exists():
            report["files"][entry["filename"]] = {"status": "MISSING"}
            report["all_match"] = False
            continue
        size_ok = p.stat().st_size == entry["byte_size"]
        hash_ok = sha256_file(p) == entry["sha256"]
        ok = size_ok and hash_ok
        report["files"][entry["filename"]] = {
            "status": "OK" if ok else "MISMATCH",
            "size_ok": size_ok,
            "sha256_ok": hash_ok,
        }
        if not ok:
            report["all_match"] = False
    return report


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
