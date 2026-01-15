"""encrypt existing credentials

Revision ID: 0016_encrypt_existing_credentials
Revises: 0015_org_invites_send_tracking
Create Date: 2025-01-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0016_encrypt_existing_credentials"
down_revision = "0015_org_invites_send_tracking"
branch_labels = None
depends_on = None


def encrypt_existing_credentials(bind) -> int:
    from app.security.credentials_crypto import encryption_enabled, encrypt_credentials, is_encrypted
    if not encryption_enabled():
        print("CREDENTIALS_ENC_KEYS not set; skipping credentials encryption.")
        return 0

    connections = sa.table(
        "connections",
        sa.column("id", sa.Integer),
        sa.column("credentials_json", sa.JSON),
    )

    updated = 0
    last_id = 0
    while True:
        rows = bind.execute(
            sa.select(connections.c.id, connections.c.credentials_json)
            .where(connections.c.id > last_id)
            .order_by(connections.c.id)
            .limit(500)
        ).fetchall()
        if not rows:
            break
        for row in rows:
            last_id = row.id
            creds = row.credentials_json or {}
            if is_encrypted(creds):
                continue
            encrypted = encrypt_credentials(creds)
            bind.execute(
                sa.update(connections)
                .where(connections.c.id == row.id)
                .values(credentials_json=encrypted)
            )
            updated += 1
    return updated


def upgrade() -> None:
    bind = op.get_bind()
    encrypt_existing_credentials(bind)


def downgrade() -> None:
    pass
