"""init_knowledge_graph

Revision ID: b0509aef577c
Revises: 
Create Date: 2026-07-14 20:57:56.188287

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0509aef577c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_nodes (
            node_id VARCHAR PRIMARY KEY,
            label VARCHAR NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536)
        );
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_edges (
            source_id VARCHAR NOT NULL,
            target_id VARCHAR NOT NULL,
            relationship VARCHAR NOT NULL,
            PRIMARY KEY (source_id, target_id, relationship)
        );
    """)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_edges;")
    op.execute("DROP TABLE IF EXISTS knowledge_nodes;")
