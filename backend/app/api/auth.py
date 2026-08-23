import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    print("STEP 1: register route hit", flush=True)
    try:
        result = register_user(db, request.email, request.password)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"EXCEPTION CAUGHT: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to an internal error."
        )


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = login_user(db, request.email, request.password)
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"LOGIN EXCEPTION CAUGHT: {type(e).__name__}: {e}", flush=True)
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
