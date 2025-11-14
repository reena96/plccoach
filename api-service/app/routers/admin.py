"""Admin router for user management and administrative functions."""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.services.database import get_db
from app.services.auth_service import get_user_by_id, list_users, update_user_role
from app.dependencies.rbac import require_admin
from app.models.session import Session as UserSession
from app.schemas.user import UserListResponse, UserListItem, UpdateRoleRequest, UserProfileResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/users", response_model=UserListResponse, tags=["Admin"])
async def list_all_users(
    page: int = 1,
    limit: int = 50,
    session: UserSession = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all users with pagination (admin only).

    **AC3: Admin User List Endpoint**
    - Returns 200 with paginated user list
    - Default limit=50, page=1
    - Ordered by created_at descending (newest first)

    **AC4: Admin-Only Access**
    - Returns 403 for non-admin users (enforced by require_admin dependency)

    Args:
        page: Page number (1-indexed)
        limit: Number of users per page (default 50)

    Returns:
        UserListResponse: Paginated list of users with metadata
    """
    # Validate pagination parameters
    if page < 1:
        raise HTTPException(status_code=400, detail="Page number must be >= 1")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    # Calculate offset
    offset = (page - 1) * limit

    # Get users from database
    users = list_users(db, offset=offset, limit=limit)

    # Get total count for pagination metadata
    from app.models.user import User
    total = db.query(User).count()

    # Convert to response schema
    user_items = [UserListItem.model_validate(user) for user in users]

    return UserListResponse(
        users=user_items,
        total=total,
        page=page,
        limit=limit
    )


@router.patch("/users/{user_id}", response_model=UserProfileResponse, tags=["Admin"])
async def update_user_role_endpoint(
    user_id: uuid.UUID,
    request_body: UpdateRoleRequest,
    request: Request,
    session: UserSession = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user's role (admin only).

    **AC5: Admin Role Update Endpoint**
    - Updates user role in database
    - Returns 200 with updated user object
    - Logs change with admin info, target user, old/new role

    **AC6: Role Validation**
    - Returns 400 for invalid role (Pydantic validates enum)
    - Returns 404 if user not found

    **AC10: Audit Logging**
    - Logs role change with admin ID/email, target user ID/email, old/new role, timestamp, IP

    Args:
        user_id: UUID of user to update
        request_body: UpdateRoleRequest with new role

    Returns:
        UserProfileResponse: Updated user profile
    """
    # Get admin user for audit logging
    admin_user = get_user_by_id(db, session.user_id)
    if not admin_user:
        logger.error(f"Admin user not found for valid session - session_id: {session.id}")
        raise HTTPException(status_code=403, detail="Admin user not found")

    # Get target user
    target_user = get_user_by_id(db, user_id)
    if not target_user:
        logger.warning(f"Role update failed: User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")

    # Store old role for audit log
    old_role = target_user.role
    new_role = request_body.role

    # Check if role is actually changing
    if old_role == new_role:
        logger.info(f"Role update skipped: User {user_id} already has role '{new_role}'")
        return UserProfileResponse.model_validate(target_user)

    # Update role in database
    updated_user = update_user_role(db, user_id, new_role)

    if not updated_user:
        # This should not happen if user exists, but handle gracefully
        logger.error(f"Role update failed: Could not update user {user_id}")
        raise HTTPException(status_code=500, detail="Failed to update user role")

    # Get client IP address for audit log
    client_ip = request.client.host if request.client else "unknown"

    # AC10: Audit log role change with structured JSON logging
    logger.info(
        f"Role change - "
        f"admin_id: {admin_user.id}, admin_email: {admin_user.email}, "
        f"target_user_id: {updated_user.id}, target_user_email: {updated_user.email}, "
        f"old_role: {old_role}, new_role: {new_role}, "
        f"ip_address: {client_ip}",
        extra={
            "event": "role_change",
            "admin_id": str(admin_user.id),
            "admin_email": admin_user.email,
            "target_user_id": str(updated_user.id),
            "target_user_email": updated_user.email,
            "old_role": old_role,
            "new_role": new_role,
            "ip_address": client_ip
        }
    )

    return UserProfileResponse.model_validate(updated_user)
