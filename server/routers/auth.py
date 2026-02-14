"""
Authentication endpoints - register and login
"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session

from database import SessionLocal, User
from models.schemas import RegisterRequest, LoginRequest, TokenResponse
from services.auth import get_password_hash, verify_password, create_access_token

router = APIRouter()


@router.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new user"""
    db: Session = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user with hashed password
        hashed_password = get_password_hash(request.password)
        new_user = User(
            name=request.name,
            email=request.email,
            password_hash=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Create access token
        access_token = create_access_token(data={"sub": new_user.email})

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            name=new_user.name,
            email=new_user.email
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        )
    finally:
        db.close()


@router.post("/api/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    db: Session = SessionLocal()
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Create access token
        access_token = create_access_token(data={"sub": user.email})

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            name=user.name,
            email=user.email
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}",
        )
    finally:
        db.close()
