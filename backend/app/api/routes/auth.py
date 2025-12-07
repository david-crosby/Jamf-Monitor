import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.security import (
    create_access_token, 
    verify_password, 
    get_password_hash,
    verify_token
)
from app.core.config import get_settings
from app.core.database import get_db
from app.core.repositories import UserRepository

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


async def _authenticate_user(
    username: str, 
    password: str,
    db: Optional[AsyncSession] = None
) -> bool:
    """
    Authenticate user against database or environment configuration.
    Returns True if authentication successful.
    """
    if db:
        user_repo = UserRepository(db)
        user = await user_repo.get_user_by_username(username)
        
        if user and user.is_active:
            if verify_password(password, user.hashed_password):
                await user_repo.update_last_login(user.id)
                logger.info(f"User '{username}' authenticated successfully via database")
                return True
            else:
                logger.warning(f"Failed login attempt for user '{username}' - invalid password")
                return False
        
        if not user:
            logger.debug(f"User '{username}' not found in database, checking environment config")
    
    if username == settings.admin_username:
        if verify_password(password, settings.admin_password):
            logger.info(f"User '{username}' authenticated successfully via environment config")
            return True
        else:
            logger.warning(f"Failed login attempt for admin user - invalid password")
            return False
    
    logger.warning(f"Failed login attempt for unknown user '{username}'")
    return False


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return access token.
    """
    logger.info(f"Login attempt for user: {credentials.username}")
    
    is_authenticated = await _authenticate_user(
        credentials.username,
        credentials.password,
        db
    )
    
    if not is_authenticated:
        logger.warning(f"Authentication failed for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(
        data={"sub": credentials.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    logger.info(f"User '{credentials.username}' logged in successfully")
    return LoginResponse(access_token=access_token)


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(token_data: dict = Depends(verify_token)):
    """
    Refresh an existing access token.
    """
    username = token_data.get("sub")
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    access_token = create_access_token(
        data={"sub": username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    logger.info(f"Token refreshed for user: {username}")
    return LoginResponse(access_token=access_token)


@router.post("/logout")
async def logout(_: dict = Depends(verify_token)):
    """
    Logout endpoint. Since we use stateless JWT, actual logout
    happens on the client side by discarding the token.
    """
    return {"message": "Successfully logged out"}
