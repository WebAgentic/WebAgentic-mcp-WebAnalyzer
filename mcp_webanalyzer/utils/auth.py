"""Authentication and authorization utilities."""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from passlib.context import CryptContext

from ..config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security schemes
bearer_scheme = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthError(HTTPException):
    """Custom authentication error."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.JWTError:
        raise AuthError("Invalid token")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


async def get_current_user_jwt(credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)) -> Optional[Dict[str, Any]]:
    """Get current user from JWT token."""
    if not credentials:
        return None
    
    token = credentials.credentials
    return verify_token(token)


async def get_current_user_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[Dict[str, str]]:
    """Get current user from API key."""
    if not api_key:
        return None
    
    if settings.api_key and api_key != settings.api_key:
        raise AuthError("Invalid API key")
    
    return {"user_id": "api_user", "auth_type": "api_key"}


async def get_current_user(
    jwt_user: Optional[Dict[str, Any]] = Depends(get_current_user_jwt),
    api_user: Optional[Dict[str, str]] = Depends(get_current_user_api_key)
) -> Dict[str, Any]:
    """Get current user from either JWT or API key."""
    if jwt_user:
        return jwt_user
    elif api_user:
        return api_user
    else:
        raise AuthError("No valid authentication provided")


def require_auth(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency that requires authentication."""
    return user


def require_admin(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency that requires admin privileges."""
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user