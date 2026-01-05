import hashlib
from sqlalchemy import text
from sqlalchemy.orm import Session

def acquire_advisory_lock(session: Session, key: int) -> bool:
    """
    Acquires a PostgreSQL advisory lock.
    Returns True if lock was acquired, False otherwise.
    """
    # pg_try_advisory_xact_lock(key) acquires a transaction-level lock
    # that is automatically released at the end of the transaction.
    result = session.execute(text("SELECT pg_try_advisory_xact_lock(:key)"), {"key": key}).scalar()
    return bool(result)

def get_sync_lock_key(experiment_id: int, platform: str) -> int:
    """
    Generates a deterministic 64-bit integer key for advisory locks
    based on experiment_id and platform.
    """
    raw_str = f"sync:{experiment_id}:{platform}"
    # Use SHA256 hash and take first 8 bytes to form a 64-bit integer
    hash_bytes = hashlib.sha256(raw_str.encode('utf-8')).digest()
    # Convert to signed 64-bit integer (Postgres bigint range)
    key = int.from_bytes(hash_bytes[:8], byteorder='big', signed=True)
    return key
