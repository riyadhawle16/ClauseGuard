from datetime import timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.repositories.user_repo import get_user_by_email, create_user
from app.utils.jwt_utils import create_access_token
from app.schemas.auth import TokenResponse
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# bcrypt hard limit is 72 bytes (not characters).
# Passwords exceeding this are rejected with a clear validation error
# rather than silently truncated — truncation would mean the stored hash
# doesn't match what the user thinks their password is.
_BCRYPT_MAX_BYTES = 72


def _validate_password_byte_length(password: str) -> None:
    """
    Raise HTTP 422 if the password exceeds bcrypt's 72-byte limit.
    Uses UTF-8 byte length, not character length, because multi-byte
    characters (e.g. accented letters, emoji) each count as multiple bytes.
    """
    if len(password.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Password must not exceed {_BCRYPT_MAX_BYTES} bytes in UTF-8 encoding. "
                "Please choose a shorter password."
            ),
        )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Guard verify_password too — bcrypt raises ValueError on oversized input
    if len(plain_password.encode("utf-8")) > _BCRYPT_MAX_BYTES:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def register_user(db: Session, email: str, password: str) -> TokenResponse:
    # Minimum length check
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long",
        )

    # bcrypt 72-byte limit check
    _validate_password_byte_length(password)

    existing = get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    password_hash = hash_password(password)
    user = create_user(db, email=email, password_hash=password_hash)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )
    return TokenResponse(access_token=access_token, token_type="bearer")


def login_user(db: Session, email: str, password: str) -> TokenResponse:
    user = get_user_by_email(db, email)
    # Deliberately generic error — do not distinguish unknown email from wrong password
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
