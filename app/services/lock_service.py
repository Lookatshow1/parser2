import hashlib
from sqlalchemy import text
from sqlalchemy.orm import Session

def acquire_advisory_lock(session: Session, key: int) -> bool:
    """
    Acquires a PostgreSQL advisory lock.
    Returns True if lock was acquired, False otherwise.
    """
    held = session.info.setdefault("advisory_locks", set())
    if key in held:
        return False

    # pg_try_advisory_xact_lock(key) acquires a transaction-level lock
    # that is automatically released at the end of the transaction.
    result = session.execute(text("SELECT pg_try_advisory_xact_lock(:key)"), {"key": key}).scalar()
    acquired = bool(result)
    if acquired:
        held.add(key)
    return acquired

def _normalize_platform(platform: object) -> str:
    value = getattr(platform, "value", None)
    return str(value if value is not None else platform)


def get_sync_lock_key(experiment_id: int, platform: str) -> int:
    """
    Generates a deterministic 64-bit integer key for advisory locks
    based on experiment_id and platform.
    """
    raw_str = f"sync:{experiment_id}:{_normalize_platform(platform)}"
    # Use SHA256 hash and take first 8 bytes to form a 64-bit integer
    hash_bytes = hashlib.sha256(raw_str.encode('utf-8')).digest()
    # Convert to signed 64-bit integer (Postgres bigint range)
    key = int.from_bytes(hash_bytes[:8], byteorder='big', signed=True)
    return key


def get_connection_sync_lock_key(connection_id: int, platform: str) -> int:
    raw_str = f"sync:connection:{connection_id}:{_normalize_platform(platform)}"
    hash_bytes = hashlib.sha256(raw_str.encode("utf-8")).digest()
    return int.from_bytes(hash_bytes[:8], byteorder="big", signed=True)


def get_auto_sync_lock_key(connection_id: int) -> int:
    raw_str = f"auto_sync:{connection_id}"
    hash_bytes = hashlib.sha256(raw_str.encode("utf-8")).digest()
    return int.from_bytes(hash_bytes[:8], byteorder="big", signed=True)
