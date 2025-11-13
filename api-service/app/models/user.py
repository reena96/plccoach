"""User model for PLC Coach."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.services.database import Base


class User(Base):
    """User model representing educators, coaches, and administrators."""

    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    role = Column(
        String,
        nullable=False,
        default='educator'
    )
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    sso_provider = Column(String, nullable=True)  # 'google' or 'clever'
    sso_id = Column(String, nullable=True)  # SSO user ID
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    # TODO Epic 3: Uncomment when Conversation model is created
    # conversations = relationship("Conversation", back_populates="user")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('educator', 'coach', 'admin')",
            name='check_user_role'
        ),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
