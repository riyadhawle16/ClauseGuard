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


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def register_user(db: Session, email: str, password: str) -> TokenResponse:
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long",
        )
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
