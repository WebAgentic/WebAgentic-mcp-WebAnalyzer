# Web Analyzer MCP Server v2.0 - Advanced Features

## 🚀 새로운 기능 개요

이번 업그레이드에서는 기본 MCP 서버에서 엔터프라이즈급 웹 분석 플랫폼으로 발전했습니다.

### 주요 업그레이드 사항

#### 1. 아키텍처 변경
- **기존**: 단순 MCP 서버 (STDIO)
- **신규**: HTTP API 서버 + MCP 호환성 유지
- **혜택**: 웹 인터페이스, RESTful API, 확장성

#### 2. 비동기 작업 처리
- **Celery + Redis** 기반 분산 작업 처리
- 대용량 웹사이트 분석을 백그라운드에서 처리
- 작업 상태 추적 및 결과 관리

#### 3. 고급 보안 시스템
- **JWT 토큰** 기반 인증
- **API 키** 인증 지원
- **Rate Limiting** (요청 제한)
- **CORS** 설정

#### 4. 지능형 캐싱
- **Redis** 기반 다단계 캐싱
- 함수 결과 자동 캐싱
- 캐시 무효화 전략

#### 5. 외부 API 연동
- **OpenAI GPT** 통합 (콘텐츠 향상)
- **Anthropic Claude** 통합
- **Slack** 알림 연동
- **Webhook** 지원

#### 6. 동적 리소스 생성
- **HTML 보고서** 자동 생성 (`data://reports/{id}`)
- **대시보드** 실시간 생성
- **Jinja2** 템플릿 엔진

#### 7. 모니터링 & 로깅
- **Prometheus** 메트릭
- **구조화된 로깅** (JSON)
- **Health Check** 엔드포인트
- **성능 모니터링**

## 📋 API 엔드포인트

### 인증
```bash
POST /auth/token
{
  "username": "admin",
  "password": "admin"
}
```

### 분석 (비동기)
```bash
# 페이지 탐색
POST /analyze/discover
{
  "url": "https://example.com",
  "max_depth": 2,
  "max_pages": 100
}

# 페이지 요약
POST /analyze/summary
{
  "url": "https://example.com",
  "enhance": true,
  "provider": "openai"
}

# RAG 콘텐츠 추출
POST /analyze/rag
{
  "url": "https://example.com",
  "question": "설치 방법은?",
  "enhance": true
}
```

### 작업 상태 확인
```bash
GET /tasks/{task_id}
```

### 리포트
```bash
GET /reports/{report_id}
GET /reports
```

### 모니터링
```bash
GET /health
GET /metrics
GET /  # 대시보드
```

## 🔧 배포 방식

### 1. Docker Compose (권장)
```bash
# 전체 스택 실행
docker-compose up -d

# 서비스별 실행
docker-compose up -d redis web-analyzer-api web-analyzer-worker
```

### 2. Kubernetes
```bash
# 배포 스크립트 사용
./deployment/scripts/deploy.sh kubernetes

# 수동 배포
kubectl apply -f deployment/kubernetes/
```

### 3. 개발 모드
```bash
# API 서버
uv run web-analyzer-api

# 워커
uv run web-analyzer-worker

# 기존 MCP 서버 (호환성)
uv run web-analyzer-mcp
```

## 🌐 서비스 포트

| 서비스 | 포트 | 설명 |
|--------|------|------|
| API Server | 8000 | 메인 API 서버 |
| Metrics | 9090 | Prometheus 메트릭 |
| Flower | 5555 | Celery 모니터링 |
| Redis | 6379 | 캐시 & 메시지 브로커 |

## 🔐 보안 설정

### 환경 변수
```bash
SECRET_KEY=your-secret-key-change-in-production
API_KEY=your-api-key-here
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### JWT 토큰 사용
```javascript
// 토큰 획득
const response = await fetch('/auth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'admin', password: 'admin' })
});
const { access_token } = await response.json();

// API 호출
fetch('/analyze/summary', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ url: 'https://example.com' })
});
```

## 📊 모니터링

### Prometheus 메트릭
- `web_analyzer_requests_total`: 총 요청 수
- `web_analyzer_request_duration_seconds`: 요청 처리 시간
- `web_analyzer_cache_hits_total`: 캐시 히트
- `web_analyzer_tasks_total`: 작업 수행 통계
- `web_analyzer_external_api_calls_total`: 외부 API 호출

### 대시보드
- http://localhost:8000 - 메인 대시보드
- http://localhost:5555 - Celery 모니터링
- http://localhost:9090/metrics - Prometheus 메트릭

## 🔄 MCP 연동 방법

### 1. 기존 MCP 서버 사용 (STDIO)
```json
{
  "mcpServers": {
    "web-analyzer-mcp": {
      "command": "uv",
      "args": ["run", "web-analyzer-mcp"],
      "cwd": "/path/to/web-analyzer-mcp"
    }
  }
}
```

### 2. HTTP API를 통한 MCP 호출
```json
{
  "mcpServers": {
    "web-analyzer-api": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Authorization: Bearer YOUR_TOKEN",
        "http://localhost:8000/mcp/tools/{tool_name}",
        "-d", "{parameters}"
      ]
    }
  }
}
```

## 🎯 사용 사례

### 1. 대량 웹사이트 분석
```python
# 100개 URL 일괄 분석
urls = ["https://site1.com", "https://site2.com", ...]
task = batch_analyze_urls_task.delay(urls, "summary")
```

### 2. AI 강화 분석
```python
# OpenAI로 콘텐츠 향상
result = await api_manager.enhance_analysis(
    content, 
    provider="openai", 
    task="summarize"
)
```

### 3. 실시간 보고서 생성
```python
# 동적 보고서 생성
report_id = await resource_manager.create_analysis_report(
    results, "discover_subpages", "https://example.com"
)
# 접근: data://reports/{report_id}
```

## 🚀 성능 최적화

### 캐싱 전략
- **함수 레벨**: `@cache_async` 데코레이터
- **API 레벨**: Redis 기반 응답 캐싱
- **콘텐츠 레벨**: 웹 페이지 콘텐츠 캐싱

### 확장성
- **수평 확장**: 워커 노드 추가
- **수직 확장**: CPU/메모리 증설
- **캐시 최적화**: Redis 클러스터

### 모니터링
- **실시간 메트릭**: Prometheus + Grafana
- **알림**: Slack/이메일 통합
- **로그 분석**: ELK 스택 연동

## 🔧 개발자 가이드

### 새로운 도구 추가
```python
@mcp.tool()
async def new_analysis_tool(url: str, option: str) -> Dict[str, Any]:
    """새로운 분석 도구"""
    # 구현
    pass
```

### 외부 API 추가
```python
class NewAPIClient:
    async def analyze_content(self, content: str) -> Dict[str, Any]:
        # 구현
        pass
```

### 캐싱 적용
```python
@cache_async(ttl=3600, prefix="new_analysis")
async def expensive_analysis(data: str) -> Dict[str, Any]:
    # 비용이 큰 분석 작업
    pass
```

## 📈 업그레이드 이점

1. **확장성**: 단일 서버 → 분산 시스템
2. **신뢰성**: 작업 실패 시 재시도, 상태 추적
3. **성능**: 캐싱, 비동기 처리, 로드 밸런싱
4. **보안**: 인증, 권한 부여, Rate Limiting
5. **모니터링**: 실시간 메트릭, 알림, 로깅
6. **유연성**: HTTP API, 다양한 클라이언트 지원
7. **운영성**: Docker, Kubernetes, 자동 배포

이제 Web Analyzer MCP Server는 개인 프로젝트에서 대규모 엔터프라이즈 환경까지 모든 요구사항을 만족하는 완전한 웹 분석 플랫폼입니다! 🎉