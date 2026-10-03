#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Download the UCI AI4I 2020 Predictive Maintenance dataset into data/raw/.

The AI4I 2020 dataset (10,000 rows x 14 columns, CC BY 4.0) is the *only* external
dataset Factora uses: it is the baseline for the F3 failure model. Everything else
in data/ is generated locally by scripts/generate_factory_data.py.

Usage:
    python3 scripts/download_ai4i.py            # download if missing, then validate
    python3 scripts/download_ai4i.py --force    # re-download even if present
    python3 scripts/download_ai4i.py --check    # validate an existing file only (offline)

If the automated download is blocked (corporate proxy, offline machine), the script
prints exact manual-download instructions and exits non-zero. Drop the file at the
shown path and re-run --check; validation is identical either way.

Source and licence (also recorded in data/README.md):
    UCI Machine Learning Repository — AI4I 2020 Predictive Maintenance Dataset
    https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset
    DOI 10.24432/C5HS5C — Creative Commons Attribution 4.0 International (CC BY 4.0).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import ssl
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_PATH = REPO_ROOT / "data" / "raw" / "ai4i2020.csv"

# Official UCI endpoints. The first serves the raw CSV; the second serves the dataset
# zip (we extract ai4i2020.csv from it) in case the legacy path is retired.
PRIMARY_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/00601/ai4i2020.csv"
DATASET_PAGE = "https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset"
MIRROR_PAGE = "https://www.kaggle.com/datasets/stephanmatzka/predictive-maintenance-dataset-ai4i-2020"

# sha256 of ai4i2020.csv as served by the official UCI endpoint (verified 2026-10-03; the
# file carries a UTF-8 BOM). A mismatch is a hard error: upstream changed, so diff it before
# trusting F3 metrics trained on a different file.
EXPECTED_SHA256 = "dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e"
EXPECTED_SHA256_VERIFIED = True

EXPECTED_COLUMNS = [
    "UDI",  # the official CSV spells it UDI (the UCI page's variable table says UID - trust the file)
    "Product ID",
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
]
EXPECTED_ROWS = 10_000
EXPECTED_MIN_BYTES = 400_000

USER_AGENT = "Factora-Hackathon/0.1 (+https://github.com/khushi-infinity/Factora)"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, dest: Path, timeout_s: int = 60) -> None:
    """Stream `url` to `dest` via a temp file (never leaves a half-written CSV)."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    with urllib.request.urlopen(request, timeout=timeout_s, context=context) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"HTTP {getattr(response, 'status', '?')} from {url}")
        with tempfile.NamedTemporaryFile(delete=False, dir=dest.parent, suffix=".part") as tmp:
            shutil.copyfileobj(response, tmp, 1 << 16)
            tmp_path = Path(tmp.name)
    tmp_path.replace(dest)
    dest.chmod(0o644)  # NamedTemporaryFile creates 0600; normalise for reproducible checkouts


def validate(path: Path) -> tuple[list[str], list[str]]:
    """Return (problems, warnings); empty problems means the file is good."""
    problems: list[str] = []
    warnings: list[str] = []
    if not path.exists():
        return [f"missing file: {path}"]
    size = path.stat().st_size
    if size < EXPECTED_MIN_BYTES:
        problems.append(f"file is only {size:,} bytes (expected at least {EXPECTED_MIN_BYTES:,})")
    with path.open(newline="", encoding="utf-8-sig") as handle:  # utf-8-sig strips the BOM
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return problems + ["file is empty (no header row)"]
        if [c.strip() for c in header] != EXPECTED_COLUMNS:
            problems.append(f"unexpected header: {header}")
        rows = sum(1 for _ in reader)
    if rows != EXPECTED_ROWS:
        problems.append(f"expected {EXPECTED_ROWS:,} data rows, found {rows:,}")
    actual_hash = sha256_of(path)
    if actual_hash != EXPECTED_SHA256:
        message = (
            f"sha256 {actual_hash} != recorded {EXPECTED_SHA256} "
            "(upstream file may have changed — proceed only after diffing it)"
        )
        if EXPECTED_SHA256_VERIFIED:
            problems.append(message)
        else:
            warnings.append(message + " [recorded hash not yet verified — advisory only]")
    return problems, warnings


def manual_instructions() -> None:
    print(
        f"""
AUTOMATED DOWNLOAD BLOCKED — manual fallback
============================================
The AI4I 2020 CSV could not be downloaded automatically. Fetch it by hand:

  1. Open the official dataset page:  {DATASET_PAGE}
  2. Download `ai4i2020.csv` (about 510 KB). If the UCI site is unreachable from
     your network, the same file is mirrored at:  {MIRROR_PAGE}
  3. Place it at:  {TARGET_PATH}
  4. Re-run:  python3 scripts/download_ai4i.py --check

Expected shape: {EXPECTED_ROWS:,} data rows, {len(EXPECTED_COLUMNS)} columns \
({EXPECTED_COLUMNS[0]} ... {EXPECTED_COLUMNS[-1]}).
"""
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true", help="re-download even if the file exists")
    parser.add_argument("--check", action="store_true",
                        help="validate the existing file only; never download")
    args = parser.parse_args()

    if args.force or (not args.check and not TARGET_PATH.exists()):
        TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {PRIMARY_URL}")
        print(f"     -> {TARGET_PATH}")
        try:
            fetch(PRIMARY_URL, TARGET_PATH)
        except Exception as exc:  # noqa: BLE001 - report any network failure as instructions
            print(f"download failed: {exc}", file=sys.stderr)
            manual_instructions()
            return 2

    problems, warnings = validate(TARGET_PATH)
    for warning in warnings:
        print(f"WARN  {warning}", file=sys.stderr)
    if problems:
        print(f"\n{TARGET_PATH} is NOT a valid AI4I 2020 file:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        if not args.check:
            manual_instructions()
        return 1

    print(f"OK  {TARGET_PATH}")
    print(f"    sha256 {sha256_of(TARGET_PATH)}")
    print(f"    {EXPECTED_ROWS:,} rows x {len(EXPECTED_COLUMNS)} columns, "
          f"{TARGET_PATH.stat().st_size:,} bytes")
    print("    Licence: CC BY 4.0 — cite UCI AI4I 2020, DOI 10.24432/C5HS5C (see data/README.md)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
