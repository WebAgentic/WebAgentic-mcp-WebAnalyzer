# app/core/security.py - JWT 인증 시스템
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.redis import redis_manager
import uuid
import logging

logger = logging.getLogger(__name__)

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 토큰 추출
security = HTTPBearer(auto_error=False)


class SecurityManager:
    """보안 관련 기능을 관리하는 클래스"""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.expire_minutes = settings.JWT_EXPIRE_MINUTES

    def hash_password(self, password: str) -> str:
        """비밀번호 해싱"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        return pwd_context.verify(plain_password, hashed_password)

    async def create_access_token(
            self,
            data: Dict[str, Any],
            expires_delta: Optional[timedelta] = None
    ) -> str:
        """JWT 액세스 토큰 생성"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.expire_minutes)

        # JWT 표준 클레임 추가
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID
        })

        # JWT 토큰 생성
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

        # Redis에 토큰 저장 (블랙리스트 관리용)
        await self._store_token_info(to_encode["jti"], data["sub"], expire)

        return encoded_jwt

    async def verify_token(self, token: str) -> Dict[str, Any]:
        """JWT 토큰 검증"""
        try:
            # JWT 디코딩
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 토큰 ID 확인
            jti = payload.get("jti")
            if not jti:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing jti"
                )

            # Redis에서 토큰 유효성 확인
            if await self._is_token_blacklisted(jti):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )

            return payload

        except JWTError as e:
            logger.warning(f"JWT validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def revoke_token(self, jti: str) -> bool:
        """토큰 무효화 (로그아웃)"""
        try:
            await redis_manager.set(f"blacklist:{jti}", "revoked", ex=86400)  # 24시간
            return True
        except Exception as e:
            logger.error(f"Token revocation failed: {e}")
            return False

    async def _store_token_info(self, jti: str, user_id: str, expire: datetime):
        """토큰 정보를 Redis에 저장"""
        token_info = {
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expire.isoformat()
        }

        # 만료 시간까지 Redis에 저장
        ttl = int((expire - datetime.utcnow()).total_seconds())
        await redis_manager.hset(f"token:{jti}", mapping=token_info)
        await redis_manager.expire(f"token:{jti}", ttl)

    async def _is_token_blacklisted(self, jti: str) -> bool:
        """토큰이 블랙리스트에 있는지 확인"""
        result = await redis_manager.get(f"blacklist:{jti}")
        return result is not None


# 전역 보안 매니저 인스턴스
security_manager = SecurityManager()


async def get_current_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """현재 사용자 정보 가져오기 (의존성 주입용)"""

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Bearer 토큰에서 실제 토큰 추출
    token = credentials.credentials

    # 토큰 검증
    payload = await security_manager.verify_token(token)

    # 사용자 정보 반환
    user_info = {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "email": payload.get("email"),
        "jti": payload.get("jti")
    }

    return user_info


async def get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """선택적 사용자 정보 (토큰이 없어도 됨)"""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None