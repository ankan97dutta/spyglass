"""ID generation with zero locks.


- span_id(): 64-bit random value encoded as 16-char lowercase hex
"""

from __future__ import annotations

import secrets

__all__ = ["span_id"]


def _rand64() -> int:
    """Fast, cryptographically strong 64-bit random int (no locks).


    secrets uses os.urandom under the hood, which is non-blocking on modern
    platforms once initialized. This avoids any Python-level locks on the hot path.
    """
    return secrets.randbits(64)


def span_id() -> str:
    """Return a 16-char, lowercase hex string representing a 64-bit ID.


    Ensures the ID is non-zero to avoid sentinel collisions in downstream systems.
    """
    n = _rand64()
    # Avoid the rare all-zero value which some systems interpret as "unset"
    while n == 0:
        n = _rand64()
    return f"{n:016x}"
