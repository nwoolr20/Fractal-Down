"""Simple license key and contract tracking for Fractal-Down.

This module provides minimal utilities for issuing and verifying
license keys. License data is stored in a JSON file on disk and can
optionally be redirected via the ``FRACTAL_DOWN_LICENSE_FILE``
environment variable.
"""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


# Resolve license file path, allowing override through environment variable.
DEFAULT_PATH = Path.home() / ".fractal_down" / "licenses.json"
LICENSE_FILE = Path(os.environ.get("FRACTAL_DOWN_LICENSE_FILE", DEFAULT_PATH))


@dataclass
class LicenseRecord:
    """A stored license key tied to a contract identifier."""

    key: str
    contract: str
    features: Optional[List[str]] = None


def _ensure_storage() -> None:
    """Ensure the storage directory exists."""
    LICENSE_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_licenses() -> List[dict]:
    """Load all license records from disk."""
    if not LICENSE_FILE.exists():
        return []
    with LICENSE_FILE.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_licenses(records: List[dict]) -> None:
    """Persist license records to disk."""
    _ensure_storage()
    with LICENSE_FILE.open("w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)


def generate_license(contract: str, features: Optional[List[str]] = None) -> LicenseRecord:
    """Generate and store a new license key for ``contract``.

    Parameters
    ----------
    contract:
        Identifier for the customer contract.
    features:
        Optional list of enabled feature flags.

    Returns
    -------
    LicenseRecord
        The generated record containing the new license key.
    """
    records = load_licenses()
    key = secrets.token_hex(16)
    record = {"key": key, "contract": contract, "features": features or []}
    records.append(record)
    save_licenses(records)
    return LicenseRecord(key=key, contract=contract, features=features or [])


def verify_license(key: str) -> bool:
    """Check whether ``key`` exists in stored licenses."""
    return any(rec.get("key") == key for rec in load_licenses())


def license_has_feature(key: str, feature: str) -> bool:
    """Return ``True`` if ``key`` is valid and ``feature`` is enabled."""
    rec = next((rec for rec in load_licenses() if rec.get("key") == key), None)
    if rec is not None:
        return feature in rec.get("features", [])
    return False
