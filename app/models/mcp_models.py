# app/models/mcp.py - MCP 메시지 모델 (JSON-RPC 2.0 기반)
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from enum import Enum

# ==== JSON-RPC 2.0 기본 메시지 형식 ====

BoolOrDict = Union[bool, Dict[str, Any]]


class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 요청 메시지"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC 버전")
    id: Union[str, int] = Field(..., description="요청 식별자")
    method: str = Field(..., description="호출할 메서드명")
    params: Optional[Dict[str, Any]] = Field(None, description="메서드 매개변수")


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 응답 메시지"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC 버전")
    id: Union[str, int] = Field(..., description="요청 식별자")
    result: Optional[Any] = Field(None, description="성공 결과")
    error: Optional[Dict[str, Any]] = Field(None, description="오류 정보")


class JSONRPCNotification(BaseModel):
    """JSON-RPC 2.0 알림 메시지 (응답 없음)"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC 버전")
    method: str = Field(..., description="알림 메서드명")
    params: Optional[Dict[str, Any]] = Field(None, description="알림 매개변수")


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 오류 구조"""
    code: int = Field(..., description="오류 코드")
    message: str = Field(..., description="오류 메시지")
    data: Optional[Any] = Field(None, description="추가 오류 데이터")


# ==== MCP 프로토콜 구조 ====

class MCPCapabilities(BaseModel):
    """MCP 기능 정의"""
    tools: Optional[BoolOrDict] = Field(None, description="도구 관련 기능")
    resources: Optional[BoolOrDict] = Field(None, description="리소스 관련 기능")
    prompts: Optional[BoolOrDict] = Field(None, description="프롬프트 관련 기능")
    roots: Optional[BoolOrDict] = Field(None, description="루트 디렉토리 관련 기능")
    logging: Optional[BoolOrDict] = Field(None, description="로그/샘플링 관련 기능")


class MCPClientInfo(BaseModel):
    """MCP 클라이언트 정보"""
    name: str = Field(..., description="클라이언트 이름")
    version: str = Field(..., description="클라이언트 버전")


class MCPServerInfo(BaseModel):
    """MCP 서버 정보"""
    name: str = Field(..., description="서버 이름")
    version: str = Field(..., description="서버 버전")


# ==== 1. Initialize (필수 엔드포인트) ====

class InitializeParams(BaseModel):
    """초기화 요청 매개변수"""
    protocolVersion: str = Field(..., description="MCP 프로토콜 버전")
    capabilities: MCPCapabilities = Field(..., description="클라이언트 기능")
    clientInfo: MCPClientInfo = Field(..., description="클라이언트 정보")


class InitializeResult(BaseModel):
    """초기화 응답 결과"""
    protocolVersion: str = Field(..., description="서버가 지원하는 프로토콜 버전")
    capabilities: MCPCapabilities = Field(..., description="서버 기능")
    serverInfo: MCPServerInfo = Field(..., description="서버 정보")


# ==== 2. Tools (필수 엔드포인트) ====

class MCPTool(BaseModel):
    """MCP 도구 정의"""
    name: str = Field(..., description="도구 이름")
    description: str = Field(..., description="도구 설명")
    server: Optional[str] = Field(None, description="소속 서버")
    inputSchema: Dict[str, Any] = Field(..., description="입력 스키마 (JSON Schema)")


class ToolsListResult(BaseModel):
    """도구 목록 응답"""
    tools: List[MCPTool] = Field(default_factory=list, description="사용 가능한 도구 목록")


class ToolCallParams(BaseModel):
    """도구 호출 매개변수"""
    name: str = Field(..., description="호출할 도구 이름")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="도구 실행 인자")


class ToolCallResult(BaseModel):
    """도구 호출 결과"""
    content: List[Dict[str, Any]] = Field(default_factory=list, description="실행 결과 콘텐츠")
    isError: Optional[bool] = Field(False, description="오류 여부")


# ==== 3. Resources (필수 엔드포인트) ====

class MCPResource(BaseModel):
    """MCP 리소스 정의"""
    uri: str = Field(..., description="리소스 URI")
    name: str = Field(..., description="리소스 이름")
    description: Optional[str] = Field(None, description="리소스 설명")
    mimeType: Optional[str] = Field(None, description="MIME 타입")


class ResourcesListResult(BaseModel):
    """리소스 목록 응답"""
    resources: List[MCPResource] = Field(default_factory=list, description="사용 가능한 리소스 목록")


class ResourceReadParams(BaseModel):
    """리소스 읽기 매개변수"""
    uri: str = Field(..., description="읽을 리소스 URI")


class ResourceContent(BaseModel):
    """리소스 콘텐츠"""
    uri: str = Field(..., description="리소스 URI")
    mimeType: str = Field(..., description="콘텐츠 MIME 타입")
    text: Optional[str] = Field(None, description="텍스트 콘텐츠")
    blob: Optional[str] = Field(None, description="바이너리 콘텐츠 (base64)")


class ResourceReadResult(BaseModel):
    """리소스 읽기 결과"""
    contents: List[ResourceContent] = Field(..., description="리소스 콘텐츠 목록")


# ==== 비동기 작업 관리 ====

class TaskStatus(str, Enum):
    """작업 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AsyncTask(BaseModel):
    """비동기 작업 정보"""
    task_id: str = Field(..., description="작업 ID")
    status: TaskStatus = Field(TaskStatus.PENDING, description="작업 상태")
    server_name: str = Field(..., description="작업을 처리하는 서버")
    method: str = Field(..., description="호출된 메서드")
    user_id: str = Field(..., description="요청 사용자 ID")
    created_at: str = Field(..., description="생성 시간")
    updated_at: Optional[str] = Field(None, description="업데이트 시간")
    result: Optional[Any] = Field(None, description="작업 결과")
    error: Optional[str] = Field(None, description="오류 메시지")
    progress: Optional[int] = Field(None, description="진행률 (0-100)")


class TaskResponse(BaseModel):
    """비동기 작업 응답"""
    task_id: str = Field(..., description="작업 ID")
    status: TaskStatus = Field(..., description="현재 상태")
    message: str = Field(..., description="상태 메시지")


# ==== 서버 상태 및 메트릭 ====

class ServerStatus(BaseModel):
    """MCP 서버 상태"""
    name: str = Field(..., description="서버 이름")
    url: str = Field(..., description="서버 URL")
    status: str = Field(..., description="연결 상태")
    last_ping: Optional[str] = Field(None, description="마지막 핑 시간")
    tools_count: int = Field(0, description="제공하는 도구 수")
    resources_count: int = Field(0, description="제공하는 리소스 수")


class BridgeStatus(BaseModel):
    """브리지 전체 상태"""
    service: str = Field(..., description="서비스 이름")
    version: str = Field(..., description="버전")
    uptime: str = Field(..., description="실행 시간")
    servers: List[ServerStatus] = Field(..., description="연결된 MCP 서버들")
    active_sessions: int = Field(0, description="활성 세션 수")
    active_tasks: int = Field(0, description="실행 중인 작업 수")


# ==== 에러 코드 정의 ====

class MCPErrorCodes:
    """MCP 표준 에러 코드"""

    # JSON-RPC 표준 에러
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP 특화 에러
    AUTHENTICATION_FAILED = -32000
    AUTHORIZATION_FAILED = -32001
    SERVER_UNAVAILABLE = -32002
    TOOL_NOT_FOUND = -32003
    RESOURCE_NOT_FOUND = -32004
    TASK_TIMEOUT = -32005
    TASK_CANCELLED = -32006


# ==== 유틸리티 함수 ====

def create_error_response(
        request_id: Union[str, int],
        code: int,
        message: str,
        data: Optional[Any] = None
) -> JSONRPCResponse:
    """에러 응답 생성"""
    error = JSONRPCError(code=code, message=message, data=data)
    return JSONRPCResponse(id=request_id, error=error.dict())


def create_success_response(
        request_id: Union[str, int],
        result: Any
) -> JSONRPCResponse:
    """성공 응답 생성"""
    return JSONRPCResponse(id=request_id, result=result)