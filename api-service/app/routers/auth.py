"""Authentication router for OAuth and session management."""
import uuid
import logging
from fastapi import APIRouter, Request, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.services.database import get_db
from app.services.auth_service import oauth, get_or_create_user, create_session, delete_session, get_user_by_id
from app.dependencies.session import get_current_session
from app.models.session import Session as UserSession
from app.schemas.user import UserProfileResponse
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/google/login")
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow.

    Generates CSRF state token, stores in cookie, and redirects to Google consent screen.
    """
    # Generate random state parameter for CSRF protection
    state = str(uuid.uuid4())

    # Build redirect URI
    redirect_uri = settings.google_redirect_uri

    # Create redirect response to Google OAuth authorization
    # Note: authlib will automatically add state parameter
    redirect_url = await oauth.google.authorize_redirect(
        request,
        redirect_uri,
        state=state
    )

    # Set state cookie for validation in callback
    response = RedirectResponse(url=str(redirect_url.headers['location']))
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=600  # 10 minutes
    )

    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.

    Validates state parameter, exchanges authorization code for tokens,
    verifies JWT, creates/updates user, creates session, and redirects to dashboard.
    """
    # Get state from cookie
    state_cookie = request.cookies.get("oauth_state")

    # Get state from query parameter
    state_param = request.query_params.get("state")

    # Validate state parameter (CSRF protection)
    if not state_cookie or not state_param or state_cookie != state_param:
        raise HTTPException(status_code=403, detail="Invalid state parameter")

    try:
        # Exchange authorization code for tokens
        token = await oauth.google.authorize_access_token(request)

        # Parse ID token (includes user profile data)
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=401, detail="Failed to get user info")

        # Extract user profile data
        email = user_info.get('email')
        name = user_info.get('name')
        google_user_id = user_info.get('sub')  # Google's unique user ID

        if not email or not google_user_id:
            raise HTTPException(status_code=401, detail="Invalid user info from Google")

        # Create or update user (JIT provisioning)
        user = get_or_create_user(
            db=db,
            email=email,
            name=name,
            sso_provider='google',
            sso_id=google_user_id
        )

        # Create session
        user_session = create_session(db=db, user_id=user.id)

        # Create redirect response to dashboard
        response = RedirectResponse(url="/dashboard", status_code=302)

        # Set session cookie
        response.set_cookie(
            key=settings.session_cookie_name,
            value=str(user_session.id),
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax",
            max_age=settings.session_max_age
        )

        # Delete state cookie (no longer needed)
        response.delete_cookie(key="oauth_state")

        return response

    except Exception as e:
        # Log error details for debugging (server-side only)
        logger.error(f"OAuth authentication failed: {str(e)}", exc_info=True)
        # Return generic error message to client (security best practice)
        raise HTTPException(status_code=401, detail="Authentication failed. Please try again.")


@router.get("/clever/login")
async def clever_login(request: Request):
    """
    Initiate Clever OAuth login flow.

    Generates CSRF state token, stores in cookie, and redirects to Clever consent screen.
    """
    # Generate random state parameter for CSRF protection
    state = str(uuid.uuid4())

    # Build redirect URI
    redirect_uri = settings.clever_redirect_uri

    # Create redirect response to Clever OAuth authorization
    # Note: authlib will automatically add state parameter
    redirect_url = await oauth.clever.authorize_redirect(
        request,
        redirect_uri,
        state=state
    )

    # Set state cookie for validation in callback
    response = RedirectResponse(url=str(redirect_url.headers['location']))
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=600  # 10 minutes
    )

    return response


@router.get("/clever/callback")
async def clever_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Clever OAuth callback.

    Validates state parameter, exchanges authorization code for tokens,
    maps Clever roles to application roles, creates/updates user, creates session,
    and redirects to dashboard.
    """
    # Get state from cookie
    state_cookie = request.cookies.get("oauth_state")

    # Get state from query parameter
    state_param = request.query_params.get("state")

    # Validate state parameter (CSRF protection)
    if not state_cookie or not state_param or state_cookie != state_param:
        raise HTTPException(status_code=403, detail="Invalid state parameter")

    try:
        # Exchange authorization code for tokens
        token = await oauth.clever.authorize_access_token(request)

        # Parse ID token (includes user profile data)
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(status_code=401, detail="Failed to get user info")

        # Extract user profile data
        email = user_info.get('email')
        name = user_info.get('name')
        clever_user_id = user_info.get('sub')  # Clever's unique user ID

        if not email or not clever_user_id:
            raise HTTPException(status_code=401, detail="Invalid user info from Clever")

        # Map Clever role to application role
        # Clever roles: district_admin, school_admin, teacher, student
        clever_type = user_info.get('type', 'teacher')
        if clever_type in ['district_admin', 'school_admin']:
            role = 'admin'
        else:
            role = 'educator'

        # Extract organization_id from Clever district data
        # Clever provides district ID in various formats, try common fields
        organization_id = None
        district_id = user_info.get('district')
        if district_id:
            try:
                organization_id = uuid.UUID(district_id) if isinstance(district_id, str) else None
            except (ValueError, AttributeError):
                # If district_id is not a valid UUID, log and continue without organization
                logger.warning(f"Could not parse district_id as UUID: {district_id}")

        # Create or update user (JIT provisioning with role mapping)
        user = get_or_create_user(
            db=db,
            email=email,
            name=name,
            sso_provider='clever',
            sso_id=clever_user_id,
            role=role,
            organization_id=organization_id
        )

        # Create session
        user_session = create_session(db=db, user_id=user.id)

        # Create redirect response to dashboard
        response = RedirectResponse(url="/dashboard", status_code=302)

        # Set session cookie
        response.set_cookie(
            key=settings.session_cookie_name,
            value=str(user_session.id),
            httponly=True,
            secure=settings.environment == "production",
            samesite="lax",
            max_age=settings.session_max_age
        )

        # Delete state cookie (no longer needed)
        response.delete_cookie(key="oauth_state")

        return response

    except Exception as e:
        # Log error details for debugging (server-side only)
        logger.error(f"Clever OAuth authentication failed: {str(e)}", exc_info=True)
        # Return generic error message to client (security best practice)
        raise HTTPException(status_code=401, detail="Authentication failed. Please try again.")


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Log out user by deleting session and clearing cookie.

    Handles logout gracefully - always returns 200 OK even if session is invalid/missing.
    This prevents information leakage about session validity.

    AC1: Logout Functionality
    - Deletes session from database
    - Clears session cookie
    - Returns 200 OK
    - Subsequent requests with old cookie will be rejected (by session validation middleware)
    """
    # Extract session ID from cookie
    session_cookie = request.cookies.get(settings.session_cookie_name)

    if session_cookie:
        try:
            session_id = uuid.UUID(session_cookie)
            # Delete session from database
            delete_session(db=db, session_id=session_id)
        except (ValueError, AttributeError) as e:
            # Invalid session ID format - log but continue gracefully
            logger.warning(f"Invalid session ID format during logout: {session_cookie}")

    # Clear session cookie (set max_age=-1 to delete)
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax"
    )

    # Always return 200 OK, even if session was invalid/missing (AC1)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserProfileResponse, tags=["Authentication"])
async def get_me(
    session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """
    Get current user profile.

    Returns the authenticated user's profile information.
    Requires valid session cookie (validated by get_current_session dependency).

    **AC1: GET /auth/me Endpoint**
    - Returns 200 with user profile for valid session
    - Excludes sensitive fields (sso_id) from response

    **AC2: Unauthenticated Access**
    - Returns 401 if session is invalid/expired (handled by get_current_session)

    **AC8: Session Dependency Validation**
    - Uses get_current_session() dependency from Story 1.6
    - Session validation checks expiry and inactivity timeout
    - Updates last_accessed_at on each request

    Returns:
        UserProfileResponse: User profile with id, email, name, role, organization, sso_provider, created_at, last_login
    """
    # Get user from database using session's user_id
    user = get_user_by_id(db, session.user_id)

    if not user:
        # This should not happen if session is valid, but handle gracefully
        logger.error(f"User not found for valid session - session_id: {session.id}, user_id: {session.user_id}")
        raise HTTPException(status_code=401, detail="User not found")

    # Return user profile (Pydantic automatically excludes sso_id field)
    return UserProfileResponse.model_validate(user)
