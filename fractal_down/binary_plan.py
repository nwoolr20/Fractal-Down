"""
Binary plan serialization format for fractal-down.

Provides save/load functionality with magic header, versioning, and hash verification.
"""

import pickle
import struct
from pathlib import Path
from typing import Optional

from fractal_down.treelift import Plan
from fractal_down.hashing import HashProvider, get_default_provider


# Binary format constants
MAGIC = b"FPLAN"
VERSION = 1
HEADER_SIZE = len(MAGIC) + 4 + 4  # magic + version + payload_size
DIGEST_SIZE = 32  # Assuming 32-byte digests (blake2s default)


def save_plan(plan: Plan, path: str, hp: Optional[HashProvider] = None) -> str:
    """
    Save plan to binary format.

    Format: [magic][u32_be version][u32_be nbytes][payload][digest]

    Args:
        plan: Plan to save
        path: File path to save to
        hp: Hash provider (uses default if None)

    Returns:
        Absolute path of saved file

    Raises:
        IOError: If unable to write file
    """
    if hp is None:
        hp = get_default_provider()

    # Serialize plan using pickle with highest protocol
    payload = pickle.dumps(plan, protocol=pickle.HIGHEST_PROTOCOL)
    payload_size = len(payload)

    # Compute digest of payload
    digest = hp.digest(payload)

    # Build binary data
    header = MAGIC + struct.pack(">II", VERSION, payload_size)
    binary_data = header + payload + digest

    # Write to file
    file_path = Path(path).resolve()
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, "wb") as f:
            f.write(binary_data)
    except Exception as e:
        raise IOError(f"Failed to save plan to {file_path}: {e}")

    return str(file_path)


def load_plan(path: str, hp: Optional[HashProvider] = None) -> Plan:
    """
    Load plan from binary format.

    Args:
        path: File path to load from
        hp: Hash provider (uses default if None)

    Returns:
        Loaded Plan object

    Raises:
        ValueError: If file format is invalid or digest verification fails
        IOError: If unable to read file
    """
    if hp is None:
        hp = get_default_provider()

    file_path = Path(path).resolve()

    try:
        with open(file_path, "rb") as f:
            data = f.read()
    except Exception as e:
        raise IOError(f"Failed to read plan from {file_path}: {e}")

    if len(data) < HEADER_SIZE + DIGEST_SIZE:
        raise ValueError(
            f"File too small: {len(data)} bytes, need at least {HEADER_SIZE + DIGEST_SIZE}"
        )

    # Parse header
    magic = data[: len(MAGIC)]
    if magic != MAGIC:
        raise ValueError(f"Invalid magic: expected {MAGIC!r}, got {magic!r}")

    version, payload_size = struct.unpack(">II", data[len(MAGIC) : HEADER_SIZE])
    if version != VERSION:
        raise ValueError(f"Unsupported version: expected {VERSION}, got {version}")

    # Extract payload and digest
    payload_start = HEADER_SIZE
    payload_end = payload_start + payload_size
    digest_start = payload_end

    if len(data) < digest_start + DIGEST_SIZE:
        # Handle variable digest sizes - use remaining bytes for digest
        digest_size = len(data) - digest_start
        if digest_size <= 0:
            raise ValueError("No digest found in file")
    else:
        digest_size = DIGEST_SIZE

    payload = data[payload_start:payload_end]
    stored_digest = data[digest_start : digest_start + digest_size]

    # Verify digest
    computed_digest = hp.digest(payload)
    if computed_digest != stored_digest:
        raise ValueError(
            f"Digest verification failed. Expected {stored_digest.hex()}, "
            f"computed {computed_digest.hex()}"
        )

    # Deserialize plan
    try:
        plan = pickle.loads(payload)
    except Exception as e:
        raise ValueError(f"Failed to deserialize plan: {e}")

    if not isinstance(plan, Plan):
        raise ValueError(f"Invalid plan type: expected Plan, got {type(plan)}")

    return plan
