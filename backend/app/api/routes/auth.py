from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from datetime import timedelta
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCredentials(BaseModel):
    username: str = "admin"
    hashed_password: str = get_password_hash("changeme")


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    user = UserCredentials()
    
    if credentials.username != user.username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    return LoginResponse(access_token=access_token)


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(token_data: dict = None):
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    access_token = create_access_token(
        data={"sub": token_data.get("sub")},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    return LoginResponse(access_token=access_token)
