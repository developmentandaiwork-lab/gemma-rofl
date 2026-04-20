"""add pgvector embeddings for chat messages

Revision ID: 0003_add_message_embeddings_pgvector
Revises: 0002_add_chat_jobs
Create Date: 2026-04-20
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0003_add_message_embeddings_pgvector"
down_revision: Union[str, None] = "0002_add_chat_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("ALTER TABLE chat_messages ADD COLUMN IF NOT EXISTS embedding vector(768)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_chat_messages_embedding_ivfflat "
        "ON chat_messages USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chat_messages_embedding_ivfflat")
    op.drop_column("chat_messages", "embedding")
