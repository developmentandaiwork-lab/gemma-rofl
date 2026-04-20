"""normalize pgvector schema for chat message embeddings

Revision ID: 0004_normalize_pgvector_schema
Revises: 0003_msg_embed_vec
Create Date: 2026-04-20
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0004_normalize_pgvector_schema"
down_revision: Union[str, None] = "0003_msg_embed_vec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension exists.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Ensure embedding column exists with expected dimension.
    op.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS embedding vector(768)")
    op.execute("ALTER TABLE chat_messages ALTER COLUMN embedding TYPE vector(768)")

    # Rebuild ANN index in a deterministic way.
    op.execute("DROP INDEX IF EXISTS ix_chat_messages_embedding_ivfflat")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chat_messages_embedding_ivfflat "
        "ON chat_messages USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    # Keep extension/column for safety; only drop index created by this migration chain.
    op.execute("DROP INDEX IF EXISTS ix_chat_messages_embedding_ivfflat")
