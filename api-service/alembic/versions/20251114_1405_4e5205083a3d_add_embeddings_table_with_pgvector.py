"""add embeddings table with pgvector

Revision ID: 4e5205083a3d
Revises: 001_initial_schema
Create Date: 2025-11-14 14:05:18.033227+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '4e5205083a3d'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Install pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create embeddings table
    op.create_table(
        'embeddings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(3072), nullable=False),
        sa.Column('metadata', JSONB, nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'))
    )

    # Create ivfflat index for fast similarity search
    # Note: Index must be created after data is loaded for best performance
    # We'll create it in the upload script after bulk insert
    op.execute("""
        CREATE INDEX IF NOT EXISTS embeddings_embedding_idx
        ON embeddings
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # Create index on metadata for filtering
    op.create_index(
        'ix_embeddings_metadata_book_id',
        'embeddings',
        [sa.text("(metadata->>'book_id')")],
        postgresql_using='btree'
    )

    op.create_index(
        'ix_embeddings_metadata_primary_domain',
        'embeddings',
        [sa.text("(metadata->>'primary_domain')")],
        postgresql_using='btree'
    )


def downgrade() -> None:
    op.drop_index('ix_embeddings_metadata_primary_domain')
    op.drop_index('ix_embeddings_metadata_book_id')
    op.execute('DROP INDEX IF EXISTS embeddings_embedding_idx')
    op.drop_table('embeddings')
    # Note: We don't drop the vector extension as other tables might use it
