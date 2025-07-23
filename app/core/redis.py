# app/core/redis.py - Redis 연결 관리
import redis.asyncio as aioredis
from typing import Optional, Any, Dict
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis 연결 및 작업을 관리하는 클래스"""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.connection_pool: Optional[aioredis.ConnectionPool] = None

    async def connect(self):
        """Redis 연결 설정"""
        try:
            # 연결 풀 생성
            self.connection_pool = aioredis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                db=settings.REDIS_DB,
                decode_responses=True,
                max_connections=20,
                retry_on_timeout=True
            )

            # Redis 클라이언트 생성
            self.redis = aioredis.Redis(connection_pool=self.connection_pool)

            # 연결 테스트
            await self.ping()
            logger.info("✅ Redis 연결 성공")

        except Exception as e:
            logger.error(f"❌ Redis 연결 실패: {e}")
            raise

    async def disconnect(self):
        """Redis 연결 해제"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis 연결 해제 완료")

    async def ping(self) -> bool:
        """Redis 연결 상태 확인"""
        if not self.redis:
            raise Exception("Redis not connected")

        result = await self.redis.ping()
        return result

    # ==== 기본 Redis 작업 ====

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """키-값 저장"""
        try:
            if isinstance(value, dict):
                value = json.dumps(value)
            result = await self.redis.set(key, value, ex=ex)
            return result
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """키로 값 조회"""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def delete(self, key: str) -> int:
        """키 삭제"""
        try:
            return await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """키 존재 여부 확인"""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """키 만료 시간 설정"""
        try:
            return await self.redis.expire(key, seconds)
        except Exception as e:
            logger.error(f"Redis expire error: {e}")
            return False

    # ==== 해시 작업 ====

    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """해시 필드 설정"""
        try:
            # 딕셔너리 값들을 JSON 문자열로 변환
            for key, value in mapping.items():
                if isinstance(value, dict):
                    mapping[key] = json.dumps(value)
            return await self.redis.hset(name, mapping=mapping)
        except Exception as e:
            logger.error(f"Redis hset error: {e}")
            return 0

    async def hget(self, name: str, key: str) -> Optional[str]:
        """해시 필드 조회"""
        try:
            return await self.redis.hget(name, key)
        except Exception as e:
            logger.error(f"Redis hget error: {e}")
            return None

    async def hgetall(self, name: str) -> Dict[str, str]:
        """해시의 모든 필드 조회"""
        try:
            return await self.redis.hgetall(name)
        except Exception as e:
            logger.error(f"Redis hgetall error: {e}")
            return {}

    async def hdel(self, name: str, *keys) -> int:
        """해시 필드 삭제"""
        try:
            return await self.redis.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis hdel error: {e}")
            return 0

    # ==== 리스트 작업 ====

    async def lpush(self, name: str, *values) -> int:
        """리스트 왼쪽에 값 추가"""
        try:
            return await self.redis.lpush(name, *values)
        except Exception as e:
            logger.error(f"Redis lpush error: {e}")
            return 0

    async def rpop(self, name: str) -> Optional[str]:
        """리스트 오른쪽에서 값 제거 및 반환"""
        try:
            return await self.redis.rpop(name)
        except Exception as e:
            logger.error(f"Redis rpop error: {e}")
            return None

    async def lrange(self, name: str, start: int, end: int) -> list:
        """리스트 범위 조회"""
        try:
            return await self.redis.lrange(name, start, end)
        except Exception as e:
            logger.error(f"Redis lrange error: {e}")
            return []

    # ==== 세션 관리 전용 메서드 ====

    async def create_session(self, session_id: str, user_data: Dict[str, Any], ttl: int = 1800) -> bool:
        """사용자 세션 생성"""
        try:
            session_key = f"session:{session_id}"
            session_data = {
                "user_id": user_data.get("user_id"),
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "created_at": str(datetime.now()),
                "last_accessed": str(datetime.now())
            }

            await self.hset(session_key, session_data)
            await self.expire(session_key, ttl)
            return True

        except Exception as e:
            logger.error(f"Session creation error: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 정보 조회"""
        try:
            session_key = f"session:{session_id}"
            session_data = await self.hgetall(session_key)

            if session_data:
                # 마지막 접근 시간 업데이트
                await self.hset(session_key, {"last_accessed": str(datetime.now())})
                return session_data
            return None

        except Exception as e:
            logger.error(f"Session retrieval error: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """세션 삭제"""
        try:
            session_key = f"session:{session_id}"
            result = await self.delete(session_key)
            return result > 0
        except Exception as e:
            logger.error(f"Session deletion error: {e}")
            return False

    # ==== 작업 관리 전용 메서드 ====

    async def store_task(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """비동기 작업 정보 저장"""
        try:
            task_key = f"task:{task_id}"
            await self.hset(task_key, task_data)
            await self.expire(task_key, settings.TASK_TIMEOUT)
            return True
        except Exception as e:
            logger.error(f"Task storage error: {e}")
            return False

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """작업 정보 조회"""
        try:
            task_key = f"task:{task_id}"
            return await self.hgetall(task_key)
        except Exception as e:
            logger.error(f"Task retrieval error: {e}")
            return None

    async def update_task_status(self, task_id: str, status: str, result: Any = None) -> bool:
        """작업 상태 업데이트"""
        try:
            task_key = f"task:{task_id}"
            update_data = {
                "status": status,
                "updated_at": str(datetime.now())
            }

            if result is not None:
                update_data["result"] = json.dumps(result) if isinstance(result, dict) else str(result)

            await self.hset(task_key, update_data)
            return True
        except Exception as e:
            logger.error(f"Task update error: {e}")
            return False


# 전역 Redis 매니저 인스턴스
redis_manager = RedisManager()