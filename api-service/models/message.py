"""Message model for PLC Coach."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DECIMAL, DateTime, ForeignKey, ARRAY, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from db_config import Base


class Message(Base):
    """Message model representing individual messages within conversations."""

    __tablename__ = 'messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey('conversations.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(String, nullable=False)
    citations = Column(JSONB, nullable=True)  # Flexible JSON structure for citations
    domains = Column(ARRAY(String), nullable=True)  # Knowledge domains
    feedback_score = Column(Integer, nullable=True)  # User feedback (-1, 0, 1)
    input_tokens = Column(Integer, nullable=True)  # For cost tracking
    output_tokens = Column(Integer, nullable=True)  # For cost tracking
    cost_usd = Column(DECIMAL(10, 6), nullable=True)  # Actual cost in USD
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name='check_message_role'
        ),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, conversation_id={self.conversation_id}, role='{self.role}')>"
