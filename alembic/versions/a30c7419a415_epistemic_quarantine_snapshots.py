"""epistemic_quarantine_snapshots

Revision ID: a30c7419a415
Revises: b0509aef577c
Create Date: 2026-07-14 20:58:10.495024

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a30c7419a415'
down_revision: Union[str, None] = 'b0509aef577c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS epistemic_quarantine_snapshots (
            snapshot_id VARCHAR PRIMARY KEY,
            raw_payload TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS epistemic_quarantine_snapshots;")
