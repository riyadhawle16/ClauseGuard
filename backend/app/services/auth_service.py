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
    # Password length check
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long",
        )

    print("STEP 2: about to query DB", flush=True)
    existing = get_user_by_email(db, email)
    print("STEP 3: DB query done", flush=True)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    print("STEP 4: about to hash password", flush=True)
    password_hash = hash_password(password)
    print("STEP 5: password hashed", flush=True)

    print("STEP 6: about to commit user", flush=True)
    user = create_user(db, email=email, password_hash=password_hash)
    print("STEP 7: user committed", flush=True)

    print("STEP 8: about to generate JWT", flush=True)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    )
    print("STEP 9: JWT generated, returning response", flush=True)

    return TokenResponse(access_token=access_token, token_type="bearer")


def login_user(db: Session, email: str, password: str) -> TokenResponse:
    user = get_user_by_email(db, email)
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
