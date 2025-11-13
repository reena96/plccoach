"""Initial database schema with users, sessions, conversations, and messages tables.

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-11-13 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema: users, sessions, conversations, messages tables with indexes."""

    # Install pgvector extension for vector embeddings (required for future AI features)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False, server_default='educator'),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sso_provider', sa.String(), nullable=True),
        sa.Column('sso_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.CheckConstraint(
            "role IN ('educator', 'coach', 'admin')",
            name='check_user_role'
        ),
    )

    # Create index on users.email for login lookups
    op.create_index('idx_users_email', 'users', ['email'])

    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='fk_sessions_user_id',
            ondelete='CASCADE'
        ),
    )

    # Create index on sessions.user_id for user session lookups
    op.create_index('idx_sessions_user_id', 'sessions', ['user_id'])

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('share_token', sa.String(), nullable=True),
        sa.Column('share_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            name='fk_conversations_user_id'
        ),
        sa.UniqueConstraint('share_token', name='uq_conversations_share_token'),
    )

    # Create index on conversations.user_id for user's conversation list
    op.create_index('idx_conversations_user', 'conversations', ['user_id'])

    # Create index on share_token for public sharing lookups
    op.create_index('idx_conversations_share_token', 'conversations', ['share_token'])

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('domains', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('feedback_score', sa.Integer(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.DECIMAL(precision=10, scale=6), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(
            ['conversation_id'],
            ['conversations.id'],
            name='fk_messages_conversation_id',
            ondelete='CASCADE'
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name='check_message_role'
        ),
    )

    # Create compound index on messages for conversation message retrieval (ordered by time)
    op.create_index('idx_messages_conversation', 'messages', ['conversation_id', 'created_at'])


def downgrade() -> None:
    """Drop all tables and pgvector extension."""

    # Drop indexes first
    op.drop_index('idx_messages_conversation', table_name='messages')
    op.drop_index('idx_conversations_share_token', table_name='conversations')
    op.drop_index('idx_conversations_user', table_name='conversations')
    op.drop_index('idx_sessions_user_id', table_name='sessions')
    op.drop_index('idx_users_email', table_name='users')

    # Drop tables (foreign keys handled by CASCADE)
    op.drop_table('messages')
    op.drop_table('conversations')
    op.drop_table('sessions')
    op.drop_table('users')

    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
