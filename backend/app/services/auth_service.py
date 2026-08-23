import logging
from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.repositories.user_repo import get_user_by_email, create_user
from app.utils.jwt_utils import create_access_token
from app.schemas.auth import TokenResponse
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def register_user(db: Session, email: str, password: str) -> TokenResponse:
    logger.warning("register_user: start | email=%s", email)

    # Password length check
    if len(password) < 8:
        logger.warning("register_user: password too short")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long",
        )

    # Check for existing user
    logger.warning("register_user: checking for existing user in DB...")
    try:
        existing = get_user_by_email(db, email)
    except Exception as exc:
        logger.exception("register_user: DB query failed checking existing user: %s", type(exc).__name__)
        raise

    if existing:
        logger.warning("register_user: email already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    # Hash password
    logger.warning("register_user: hashing password...")
    try:
        password_hash = hash_password(password)
        logger.warning("register_user: password hashed OK")
    except Exception as exc:
        logger.exception("register_user: password hashing failed: %s", type(exc).__name__)
        raise

    # Create user record
    logger.warning("register_user: creating user in DB...")
    try:
        user = create_user(db, email=email, password_hash=password_hash)
        logger.warning("register_user: user created OK | user_id type=%s", type(user.id).__name__)
    except Exception as exc:
        logger.exception("register_user: DB user creation failed: %s", type(exc).__name__)
        raise

    # Generate JWT
    logger.warning("register_user: generating JWT...")
    try:
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        )
        logger.warning("register_user: JWT generated OK")
    except Exception as exc:
        logger.exception("register_user: JWT generation failed: %s", type(exc).__name__)
        raise

    logger.warning("register_user: completed successfully")
    return TokenResponse(access_token=access_token, token_type="bearer")


def login_user(db: Session, email: str, password: str) -> TokenResponse:
    logger.warning("login_user: start | email=%s", email)

    try:
        user = get_user_by_email(db, email)
        logger.warning("login_user: DB query OK | user_found=%s", user is not None)
    except Exception as exc:
        logger.exception("login_user: DB query failed: %s", type(exc).__name__)
        raise

    # Generic error — do not distinguish unknown email from wrong password
    if not user or not verify_password(password, user.password_hash):
        logger.warning("login_user: authentication failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    try:
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
        )
        logger.warning("login_user: JWT generated OK")
    except Exception as exc:
        logger.exception("login_user: JWT generation failed: %s", type(exc).__name__)
        raise

    logger.warning("login_user: completed successfully")
    return TokenResponse(access_token=access_token, token_type="bearer")
