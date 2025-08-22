"""
Hashing provider protocol and implementations for fractal-down.

Provides a pluggable hashing system with a default blake2s implementation
and optional CHARM integration if available.
"""

import hashlib
from typing import Protocol


class HashProvider(Protocol):
    """Protocol for hash providers used in fractal-down."""

    def digest(self, data: bytes) -> bytes:
        """Compute hash digest for the given data."""
        ...


class Blake2sProvider:
    """Default hash provider using blake2s from stdlib."""

    def digest(self, data: bytes) -> bytes:
        """Compute blake2s digest for the given data."""
        return hashlib.blake2s(data).digest()


class CharmProvider:
    """Optional CHARM hash provider if available."""

    def __init__(self, charm_hash_func):
        self._charm_hash = charm_hash_func

    def digest(self, data: bytes) -> bytes:
        """Compute CHARM digest for the given data."""
        return self._charm_hash(data)


def get_default_provider() -> HashProvider:
    """
    Get the default hash provider.

    Returns CharmProvider if CHARM is available and provides charm_hash_bytes,
    otherwise returns Blake2sProvider.
    """
    try:
        # Try to import CHARM and use its hash function if available
        import CHARM  # type: ignore

        if hasattr(CHARM, "charm_hash_bytes"):
            return CharmProvider(CHARM.charm_hash_bytes)
    except ImportError:
        pass

    # Fallback to blake2s
    return Blake2sProvider()
