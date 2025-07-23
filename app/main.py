# main.py - MCP Client Bridge 메인 애플리케이션
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.redis import redis_manager
from app.api.mcp import mcp_router
from app.api.auth import auth_router
import uvicorn
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import anyio, uuid, json


# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("🚀 MCP Client Bridge 시작 중...")
    await redis_manager.connect()
    logger.info("✅ Redis 연결 완료")

    yield
    # 종료 시
    logger.info("🔄 MCP Client Bridge 종료 중...")
    await redis_manager.disconnect()
    logger.info("✅ Redis 연결 해제 완료")


# FastAPI 애플리케이션 생성

app = FastAPI(
    title="MCP Client Bridge",
    description="다중 MCP 서버를 통합하는 Enterprise급 클라이언트 브리지",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(auth_router, prefix="/auth", tags=["인증"])
app.include_router(mcp_router, prefix="/mcp", tags=["MCP"])


@app.get("/")
async def root():
    """헬스체크 엔드포인트"""
    return {
        "service": "MCP Client Bridge",
        "version": "1.0.0",
        "status": "healthy",
        "message": "MCP Client Bridge가 정상 동작 중입니다"
    }


@app.get("/health")
async def health_check():
    """상세한 헬스체크"""
    try:
        # Redis 연결 확인
        await redis_manager.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "redis": redis_status,
        "version": "1.0.0"
    }


@app.get("/initialize")
async def initial():
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {
                "tools": True,
                "resources": False,
                "prompts": False,
                "roots": {"listChanged": False},
                "logging": False
            },
            "clientInfo": {"name": "cursor-vscode", "version": "1.0.0"}
        }
    }


@app.get("/notifications/initialized")
async def initial_noti():
    return {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }


@app.get("/tools/list")
async def tool_list():
    return {
        "jsonrpc": "2.0",
        "id": 2,
        "result": {
            "tools": [
                {
                    "name": "extract_sublinks",
                    "description": "웹 URL을 입력받아 하위 URL들을 추출합니다",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "분석할 웹페이지 URL"},
                            "session_id": {"type": "string", "description": "세션 식별자"}
                        },
                        "required": ["url", "session_id"]
                    }
                }
            ]
        }
    }


# ────────── 1. 메시지 모델 ──────────
class RPC(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str
    params: dict | None = None


# ────────── 2. 도구 레지스트리 ──────────
TOOLS: dict[str, callable] = {}


def mcp_tool(fn):
    TOOLS[fn.__name__] = fn
    return fn


@mcp_tool
async def echo(text: str) -> str:
    return text


# ────────── 3. 메인 핸들러 ──────────
# @app.post("/mcp", include_in_schema=False)
# async def mcp_endpoint(request: Request):
#     payload = await request.json()
#     rpc = RPC.model_validate(payload)
#     match rpc.method:
#         case "initialize":
#             return JSONResponse({"jsonrpc":"2.0","id":rpc.id,
#                                  "result":{"protocolVersion":"2025-03-26",
#                                            "capabilities":{"tools":{}},
#                                            "serverInfo":{"name":"FastAPI MCP","version":"0.1.0"}}})
#         case "tools/list":
#             meta = [{"name":k,
#                      "description":fn.__doc__ or "",
#                      "inputSchema":fn.__annotations__}
#                     for k,fn in TOOLS.items()]
#             return JSONResponse({"jsonrpc":"2.0","id":rpc.id,"result":{"tools":meta}})
#         case "tools/call":
#             args = rpc.params.get("arguments",{})
#             name = rpc.params["name"]
#             if name not in TOOLS:
#                 raise HTTPException(404,"tool not found")
#             result = await anyio.to_thread.run_sync(TOOLS[name], **args)
#             return JSONResponse({"jsonrpc":"2.0","id":rpc.id,
#                                  "result":{"content":[{"type":"text","text":result}]}})
#         case "ping":
#             return JSONResponse({"jsonrpc":"2.0","id":rpc.id,"result":{}})
#         case _:
#             return JSONResponse({"jsonrpc":"2.0","id":rpc.id,
#                                  "error":{"code":-32601,"message":"method not found"}})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )