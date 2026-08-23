import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    logger.warning("=== REGISTER REQUEST RECEIVED ===")
    logger.warning("Email provided: %s", request.email)

    try:
        logger.warning("Calling register_user service...")
        result = register_user(db, request.email, request.password)
        logger.warning("register_user completed successfully for: %s", request.email)
        return result
    except HTTPException as http_exc:
        # These are expected business errors (duplicate email, short password)
        logger.warning(
            "register_user raised HTTPException: status=%d detail=%s",
            http_exc.status_code, http_exc.detail
        )
        raise
    except Exception as exc:
        # Unexpected error — log full traceback for diagnosis, return generic 500
        logger.exception(
            "UNEXPECTED ERROR in /register for %s: %s",
            request.email, type(exc).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to an internal error."
        )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    logger.warning("=== LOGIN REQUEST RECEIVED ===")
    logger.warning("Email provided: %s", request.email)

    try:
        result = login_user(db, request.email, request.password)
        logger.warning("login_user completed successfully for: %s", request.email)
        return result
    except HTTPException as http_exc:
        logger.warning(
            "login_user raised HTTPException: status=%d detail=%s",
            http_exc.status_code, http_exc.detail
        )
        raise
    except Exception as exc:
        logger.exception(
            "UNEXPECTED ERROR in /login for %s: %s",
            request.email, type(exc).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to an internal error."
        )


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
    )
