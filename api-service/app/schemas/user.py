"""Pydantic schemas for user-related requests and responses."""
from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, UUID4, EmailStr


class UserProfileResponse(BaseModel):
    """User profile response schema (excludes sensitive fields like sso_id)."""
    id: UUID4
    email: EmailStr
    name: str
    role: Literal["educator", "coach", "admin"]
    organization_id: Optional[UUID4] = None
    sso_provider: Literal["google", "clever"]
    created_at: datetime
    last_login: datetime

    class Config:
        from_attributes = True  # Allows ORM mode (SQLAlchemy models)


class UserListItem(BaseModel):
    """User list item schema for admin endpoints."""
    id: UUID4
    email: EmailStr
    name: str
    role: Literal["educator", "coach", "admin"]
    organization_id: Optional[UUID4] = None
    created_at: datetime
    last_login: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list response."""
    users: list[UserListItem]
    total: int
    page: int
    limit: int


class UpdateRoleRequest(BaseModel):
    """Request body for updating user role."""
    role: Literal["educator", "coach", "admin"]
