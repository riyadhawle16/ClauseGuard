from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(db, request.email, request.password)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, request.email, request.password)


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
    )
