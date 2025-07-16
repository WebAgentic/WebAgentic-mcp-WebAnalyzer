# 🚀 Web Analyzer MCP Server v2.0 - 배포 가이드

## 📋 목차
1. [빠른 시작](#-빠른-시작)
2. [로컬 개발 환경](#-로컬-개발-환경)
3. [Docker 배포](#-docker-배포)
4. [프로덕션 배포](#-프로덕션-배포)
5. [MCP 클라이언트 연동](#-mcp-클라이언트-연동)
6. [API 사용법](#-api-사용법)
7. [문제 해결](#-문제-해결)

## 🚀 빠른 시작

### 1. 프로젝트 클론 및 설정
```bash
git clone https://github.com/your-username/web-analyzer-mcp.git
cd web-analyzer-mcp
```

### 2. 환경 설정
```bash
# 환경 변수 파일 생성
cp .env.example .env

# 필요한 값들을 수정
# - SECRET_KEY: 강력한 비밀 키로 변경
# - API_KEY: API 접근을 위한 키
# - OPENAI_API_KEY: OpenAI API 키 (선택사항)
# - ANTHROPIC_API_KEY: Anthropic API 키 (선택사항)
```

### 3. 의존성 설치
```bash
# uv를 사용한 설치 (권장)
uv sync

# 또는 pip 사용
pip install -e .
```

### 4. 서비스 실행

#### 옵션 1: 기본 MCP 서버 (Claude Desktop용)
```bash
uv run web-analyzer-mcp
```

#### 옵션 2: HTTP API 서버
```bash
# Redis 서버 실행 (별도 터미널)
redis-server

# API 서버 실행
uv run web-analyzer-api
```

#### 옵션 3: 전체 스택 (Docker)
```bash
docker-compose up -d
```

## 🔧 로컬 개발 환경

### 개발 서버 실행
```bash
# 1. Redis 시작
redis-server

# 2. API 서버 (개발 모드)
DEBUG=true uv run web-analyzer-api

# 3. 워커 (별도 터미널)
uv run web-analyzer-worker

# 4. 기본 MCP 서버 (별도 터미널)
uv run web-analyzer-mcp
```

### 개발 도구
```bash
# 코드 포맷팅
uv run black src/ tests/
uv run isort src/ tests/

# 린팅
uv run flake8 src/ tests/

# 타입 체크
uv run mypy src/

# 테스트 실행
uv run pytest
```

## 🐳 Docker 배포

### 로컬 Docker 실행
```bash
# 전체 스택 실행
docker-compose up -d

# 특정 서비스만 실행
docker-compose up -d redis web-analyzer-api

# 로그 확인
docker-compose logs -f web-analyzer-api

# 서비스 중지
docker-compose down
```

### 서비스 접근
| 서비스 | URL | 설명 |
|--------|-----|------|
| API 서버 | http://localhost:8000 | 메인 API 및 대시보드 |
| API 문서 | http://localhost:8000/docs | Swagger UI |
| Celery 모니터 | http://localhost:5555 | Flower 대시보드 |
| Redis | localhost:6379 | 캐시 및 메시지 브로커 |

## 🏢 프로덕션 배포

### Kubernetes 배포
```bash
# 배포 스크립트 사용
./deployment/scripts/deploy.sh kubernetes

# 또는 수동 배포
kubectl apply -f deployment/kubernetes/
```

### 환경 변수 설정
```bash
# Kubernetes Secrets 생성
kubectl create secret generic web-analyzer-secrets \
  --from-literal=SECRET_KEY="your-production-secret-key" \
  --from-literal=API_KEY="your-production-api-key" \
  --from-literal=OPENAI_API_KEY="your-openai-key" \
  --from-literal=ANTHROPIC_API_KEY="your-anthropic-key"
```

### 보안 고려사항
1. **SECRET_KEY**: 강력한 랜덤 키 사용
2. **API_KEY**: 복잡한 API 키 설정
3. **HTTPS**: 프로덕션에서는 반드시 HTTPS 사용
4. **방화벽**: 필요한 포트만 개방
5. **로그 모니터링**: 보안 이벤트 모니터링

## 🔗 MCP 클라이언트 연동

### Claude Desktop 설정

#### 1. Windows 설정 파일 위치
```
%APPDATA%\Claude\claude_desktop_config.json
```

#### 2. macOS 설정 파일 위치
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

#### 3. 설정 예시
```json
{
  "mcpServers": {
    "web-analyzer": {
      "command": "uv",
      "args": ["run", "web-analyzer-mcp"],
      "cwd": "C:/Users/your-username/web-analyzer-mcp",
      "env": {
        "LOG_LEVEL": "INFO",
        "REDIS_URL": "redis://localhost:6379/0"
      }
    }
  }
}
```

### Cursor IDE 설정
```json
{
  "mcp.servers": [
    {
      "name": "web-analyzer",
      "command": ["uv", "run", "web-analyzer-mcp"],
      "cwd": "/path/to/web-analyzer-mcp",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  ]
}
```

## 📡 API 사용법

### 1. 인증 토큰 획득
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

### 2. 웹 페이지 분석
```bash
# 페이지 요약
curl -X POST http://localhost:8000/analyze/summary \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "enhance": false}'

# 하위 페이지 탐색
curl -X POST http://localhost:8000/analyze/discover \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "max_depth": 2, "max_pages": 50}'

# RAG 콘텐츠 추출
curl -X POST http://localhost:8000/analyze/rag \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "question": "이 페이지는 무엇에 관한 것인가?"}'
```

### 3. 작업 상태 확인
```bash
# 작업 결과 확인
curl -X GET http://localhost:8000/tasks/{task_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 보고서 조회
```bash
# 생성된 보고서 조회
curl -X GET http://localhost:8000/reports/{report_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔍 문제 해결

### 일반적인 문제들

#### 1. Redis 연결 실패
```bash
# Redis 서비스 상태 확인
redis-cli ping

# Redis 서비스 시작
redis-server

# Docker에서 Redis 실행
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

#### 2. 포트 충돌
```bash
# 사용 중인 포트 확인
netstat -an | findstr :8000

# 다른 포트로 실행
PORT=8001 uv run web-analyzer-api
```

#### 3. Worker 실행 오류 (Windows)
```bash
# Solo 모드로 실행 (Windows용)
uv run python -m web_analyzer_mcp.worker

# 또는 환경 변수 설정
set CELERY_WORKER_POOL=solo
uv run web-analyzer-worker
```

#### 4. 의존성 충돌
```bash
# 가상환경 재생성
uv sync --reinstall

# 또는 캐시 클리어
uv cache clean
```

#### 5. MCP 서버 연결 실패
```bash
# 경로 확인
uv run web-analyzer-mcp

# 로그 확인
LOG_LEVEL=DEBUG uv run web-analyzer-mcp
```

### 로그 파일 위치
- **로컬**: `./logs/`
- **Docker**: `/app/logs/`
- **Kubernetes**: Pod 로그 확인 `kubectl logs -f pod-name`

### 성능 최적화
```bash
# Redis 최적화
redis-cli config set maxmemory 2gb
redis-cli config set maxmemory-policy allkeys-lru

# Worker 수 증가
celery -A web_analyzer_mcp.worker worker --concurrency=4
```

### 모니터링
```bash
# 헬스 체크
curl http://localhost:8000/health

# 메트릭 확인
curl http://localhost:9090/metrics

# Celery 상태
celery -A web_analyzer_mcp.worker inspect stats
```

## 🎯 다음 단계

1. **프로덕션 배포**: Kubernetes 클러스터에 배포
2. **모니터링 설정**: Prometheus + Grafana 대시보드
3. **CI/CD 구성**: 자동 배포 파이프라인
4. **확장**: 추가 분석 기능 개발
5. **보안 강화**: OAuth 2.0, API 게이트웨이 도입

이제 Web Analyzer MCP Server v2.0을 성공적으로 배포하고 사용할 수 있습니다! 🚀