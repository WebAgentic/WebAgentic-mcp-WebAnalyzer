# 🏗️ MCP WebAnalyzer - 아키텍처 가이드

## 📋 개요

MCP WebAnalyzer는 웹 페이지 분석을 위한 엔터프라이즈급 MCP (Model Context Protocol) 서버입니다. 이 프로젝트는 **FastMCP**와 **FastAPI**를 기반으로 하며, 비동기 작업 처리, 분산 캐싱, 인증 시스템, 모니터링 등의 프로덕션 환경에 적합한 기능들을 제공합니다.

## 🎯 프로젝트 목표

### 핵심 목표
- **웹 분석 자동화**: 웹사이트의 서브페이지 발견, 내용 요약, RAG용 콘텐츠 추출
- **확장성**: 대용량 웹 분석 작업을 처리할 수 있는 분산 시스템 구조  
- **안정성**: 프로덕션 환경에서 안정적으로 동작하는 엔터프라이즈급 서비스
- **호환성**: Claude Desktop, Cursor 등 다양한 MCP 클라이언트와 호환

### 주요 기능
1. **웹 분석 도구**
   - 서브페이지 발견 및 탐색
   - AI 기반 페이지 내용 요약
   - RAG(Retrieval-Augmented Generation)용 구조화된 콘텐츠 추출

2. **엔터프라이즈 기능**
   - 비동기 작업 처리 (Celery + Redis)
   - 분산 캐싱 시스템
   - JWT 및 API 키 기반 인증
   - 실시간 모니터링 및 메트릭
   - 구조화된 로깅

## 🏛️ 시스템 아키텍처

### 전체 시스템 구조
```
┌─────────────────────────────────────────────────────────────────┐
│                        클라이언트 레이어                           │
├─────────────────────────────────────────────────────────────────┤
│  Claude Desktop    │    Cursor IDE     │   직접 HTTP 호출         │
│  (MCP 클라이언트)    │   (MCP 클라이언트)  │   (API 클라이언트)        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API 게이트웨이                               │
├─────────────────────────────────────────────────────────────────┤
│           MCP Client (mcp_client.py)                           │
│           - HTTP API 호출 및 MCP 프로토콜 변환                    │
│           - 인증 및 요청 라우팅                                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      웹 서버 레이어                               │
├─────────────────────────────────────────────────────────────────┤
│           FastAPI Server (api_server.py)                      │
│           - REST API 엔드포인트 제공                             │
│           - 인증 및 권한 관리                                     │
│           - 요청 검증 및 응답 처리                                │
│           - 비동기 작업 스케줄링                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      작업 처리 레이어                             │
├─────────────────────────────────────────────────────────────────┤
│    Celery Workers (worker.py)                                 │
│    - 웹 스크래핑 및 분석 작업                                     │
│    - 비동기 작업 처리                                           │
│    - 분산 작업 큐 관리                                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      코어 서비스 레이어                           │
├─────────────────────────────────────────────────────────────────┤
│    MCP Server (server.py)                                     │
│    - 웹 분석 핵심 로직                                           │
│    - 페이지 파싱 및 내용 추출                                     │
│    - AI 기반 내용 요약                                           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      데이터 및 캐시 레이어                         │
├─────────────────────────────────────────────────────────────────┤
│    Redis Cluster                                              │
│    - 세션 및 캐시 저장                                           │
│    - Celery 메시지 브로커                                        │
│    - 작업 결과 저장소                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 컴포넌트 상세 설명

#### 1. **MCP Server (server.py)**
- **역할**: 웹 분석 핵심 로직 구현
- **주요 기능**:
  - `discover_subpages()`: 웹사이트의 서브페이지 발견 및 탐색
  - `extract_page_summary()`: AI 기반 페이지 내용 요약
  - `extract_content_for_rag()`: RAG용 구조화된 콘텐츠 추출
- **기술 스택**: FastMCP, BeautifulSoup, Selenium, OpenAI API

#### 2. **API Server (api_server.py)**
- **역할**: HTTP REST API 제공 및 요청 처리
- **주요 기능**:
  - RESTful API 엔드포인트 제공
  - JWT 및 API 키 기반 인증
  - 요청 검증 및 응답 처리
  - Celery 작업 스케줄링
  - 메트릭 및 모니터링
- **기술 스택**: FastAPI, Uvicorn, Pydantic, PyJWT

#### 3. **Celery Workers (worker.py)**
- **역할**: 비동기 작업 처리 및 분산 실행
- **주요 기능**:
  - 웹 스크래핑 작업 비동기 처리
  - 대용량 웹사이트 분석 작업 분산
  - 작업 결과 캐싱 및 저장
  - 실패한 작업 재시도 처리
- **기술 스택**: Celery, Redis, Windows 호환 설정

#### 4. **MCP Client (mcp_client.py)**
- **역할**: MCP 프로토콜과 HTTP API 간 브릿지
- **주요 기능**:
  - MCP 프로토콜을 HTTP API 호출로 변환
  - Claude Desktop/Cursor와 원격 서버 연결
  - 인증 정보 관리
  - 요청/응답 변환
- **기술 스택**: FastMCP, httpx, asyncio

#### 5. **Redis Cluster**
- **역할**: 캐시 및 메시지 브로커
- **주요 기능**:
  - 세션 및 캐시 데이터 저장
  - Celery 메시지 브로커 및 결과 저장소
  - 분산 락 및 상태 관리
- **설정**: 
  - DB 0: 일반 캐시
  - DB 1: Celery 브로커
  - DB 2: Celery 결과 저장소

## 🔧 주요 컴포넌트 구조

### 파일 구조
```
mcp-webanalyzer/
├── src/
│   └── mcp_webanalyzer/
│       ├── __init__.py
│       ├── server.py          # MCP 서버 (핵심 로직)
│       ├── api_server.py      # FastAPI HTTP 서버
│       ├── worker.py          # Celery 워커
│       ├── mcp_client.py      # MCP 클라이언트
│       ├── config.py          # 설정 관리
│       └── utils/
│           ├── __init__.py
│           ├── auth.py        # 인증 및 권한
│           ├── cache.py       # 캐시 관리
│           ├── monitoring.py  # 모니터링 및 메트릭
│           ├── web_scraper.py # 웹 스크래핑 도구
│           └── text_processor.py  # 텍스트 처리
├── tests/                     # 테스트 코드
├── logs/                      # 로그 파일
├── data/                      # 데이터 저장소
├── docs/                      # 문서
├── docker-compose.yml         # Docker 컴포즈 설정
├── Dockerfile                 # Docker 이미지
├── pyproject.toml            # Python 프로젝트 설정
├── .env.example              # 환경 변수 예시
└── README.md                 # 프로젝트 문서
```

## 🚀 배포 아키텍처

### 로컬 개발 환경
```
Developer Machine (Windows)
├── Python 3.10+ + uv
├── Redis (Docker 또는 Windows 네이티브)
├── Web Analyzer MCP Server
│   ├── API Server (포트 8080)
│   ├── Celery Worker
│   └── Flower 모니터링 (포트 5555)
└── Claude Desktop/Cursor
    └── MCP Client 연결
```

### 프로덕션 환경 (Docker)
```
Production Server (Windows Server)
├── Docker Desktop
├── Docker Compose Services:
│   ├── Redis Cluster
│   ├── Web Analyzer API (포트 8080)
│   ├── Celery Workers (스케일링 가능)
│   ├── Flower 모니터링 (포트 5555)
│   └── Nginx 리버스 프록시 (선택사항)
└── External Clients
    ├── Claude Desktop (HTTP API)
    └── Cursor IDE (HTTP API)
```

### 클라우드 배포 (확장성)
```
Cloud Infrastructure (AWS/Azure)
├── Load Balancer
├── Auto Scaling Group
│   ├── Web Analyzer API Instances
│   └── Celery Worker Instances
├── Redis Cluster (ElastiCache/Azure Cache)
├── Monitoring (CloudWatch/Azure Monitor)
└── Storage (S3/Azure Storage)
```

## 🔐 보안 아키텍처

### 인증 및 권한 관리
1. **API 키 인증**: 헤더 기반 API 키 검증
2. **JWT 토큰**: 세션 기반 인증 지원
3. **역할 기반 접근 제어**: 사용자별 권한 관리
4. **Rate Limiting**: 요청 빈도 제한
5. **CORS 설정**: 교차 출처 요청 제어

### 데이터 보안
- **전송 암호화**: HTTPS/TLS 지원
- **저장 암호화**: 민감 정보 암호화 저장
- **로그 필터링**: 민감 정보 로그 제외
- **환경 변수**: 중요 설정 정보 분리

## 📊 모니터링 및 관찰성

### 메트릭 수집
- **Prometheus 메트릭**: 시스템 성능 지표
- **사용자 정의 메트릭**: 웹 분석 작업 통계
- **리소스 모니터링**: CPU, 메모리, 디스크 사용량
- **API 응답 시간**: 성능 추적

### 로깅 시스템
- **구조화된 로깅**: JSON 형식의 로그
- **로그 레벨**: DEBUG, INFO, WARNING, ERROR
- **로그 회전**: 자동 로그 파일 관리
- **중앙 집중식 로깅**: ELK 스택 연동 가능

### 모니터링 도구
- **Flower**: Celery 작업 모니터링
- **Prometheus**: 메트릭 수집 및 저장
- **Grafana**: 대시보드 및 시각화 (선택사항)
- **Health Check**: 서비스 상태 확인

## 🔄 데이터 흐름

### 웹 분석 요청 처리 흐름
```
1. 클라이언트 요청
   │
   ▼
2. MCP Client (인증 및 변환)
   │
   ▼
3. API Server (검증 및 스케줄링)
   │
   ▼
4. Celery Worker (비동기 처리)
   │
   ▼
5. MCP Server (웹 분석 실행)
   │
   ▼
6. Redis (결과 캐싱)
   │
   ▼
7. 클라이언트 응답 반환
```

### 페이지 분석 처리 세부 흐름
```
URL 입력 → 페이지 다운로드 → HTML 파싱 → 콘텐츠 추출 → AI 요약 → 결과 반환
    │            │              │            │            │
    ▼            ▼              ▼            ▼            ▼
브라우저 렌더링  BeautifulSoup   텍스트 정리   OpenAI API   JSON 응답
(Selenium)      (HTML 파싱)    (html2text)  (요약 생성)  (클라이언트)
```

## 🌐 네트워킹 및 통신

### 포트 구성
- **8080**: API Server (HTTP)
- **6379**: Redis Server
- **5555**: Flower 모니터링
- **9090**: Prometheus 메트릭

### 통신 프로토콜
- **HTTP/HTTPS**: 클라이언트-서버 통신
- **Redis Protocol**: 캐시 및 메시지 큐
- **WebSocket**: 실시간 알림 (선택사항)

### 네트워크 보안
- **방화벽 규칙**: 포트별 접근 제어
- **VPN 연결**: 원격 접근 보안
- **SSL/TLS**: 암호화된 통신

## 📈 성능 최적화

### 캐싱 전략
- **Redis 캐싱**: 자주 요청되는 데이터 캐싱
- **브라우저 캐싱**: 클라이언트 사이드 캐싱
- **응답 압축**: gzip 압축 지원

### 비동기 처리
- **Celery 워커**: CPU 집약적 작업 분산
- **비동기 I/O**: aiohttp 기반 비동기 웹 요청
- **연결 풀링**: 데이터베이스 연결 재사용

### 확장성 고려사항
- **수평 확장**: 워커 노드 증설
- **로드 밸런싱**: 요청 분산
- **데이터베이스 샤딩**: 대용량 데이터 처리

## 🛠️ 개발 및 운영

### 개발 환경
- **Python 3.10+**: 메인 런타임
- **uv**: 빠른 패키지 관리
- **Docker**: 컨테이너화
- **VS Code**: 개발 환경 (권장)

### 테스트 전략
- **단위 테스트**: pytest 기반
- **통합 테스트**: API 엔드포인트 테스트
- **부하 테스트**: 성능 벤치마크
- **보안 테스트**: 취약점 스캔

### CI/CD 파이프라인
- **GitHub Actions**: 자동 빌드 및 테스트
- **Docker Hub**: 이미지 레지스트리
- **자동 배포**: 스테이징 및 프로덕션 환경

## 🔧 설정 관리

### 환경 변수
```env
# 서버 설정
HOST=0.0.0.0
PORT=8080
DEBUG=false

# 보안 설정
SECRET_KEY=your-secret-key
API_KEY=your-api-key
JWT_SECRET=your-jwt-secret

# Redis 설정
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# 외부 API
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# 모니터링
LOG_LEVEL=INFO
METRICS_ENABLED=true
FLOWER_PORT=5555
```

### 설정 관리 패턴
- **환경별 설정**: 개발/스테이징/프로덕션
- **시크릿 관리**: 민감 정보 분리
- **설정 검증**: Pydantic 기반 검증
- **동적 설정**: 런타임 설정 변경

## 📚 외부 의존성

### 핵심 라이브러리
- **FastMCP**: MCP 프로토콜 지원
- **FastAPI**: 웹 API 프레임워크
- **Celery**: 분산 작업 처리
- **Redis**: 캐시 및 메시지 브로커
- **BeautifulSoup**: HTML 파싱

### AI 및 텍스트 처리
- **OpenAI API**: 텍스트 요약
- **Anthropic API**: 대안 AI 서비스
- **html2text**: HTML to 마크다운 변환
- **readability-lxml**: 가독성 향상

### 웹 스크래핑
- **Selenium**: 동적 웹 페이지 렌더링
- **httpx**: 비동기 HTTP 클라이언트
- **newspaper3k**: 뉴스 기사 추출
- **urllib3**: URL 처리

## 🔮 향후 계획

### 단기 목표 (1-3개월)
- **성능 최적화**: 캐싱 개선 및 응답 속도 향상
- **모니터링 강화**: 더 상세한 메트릭 수집
- **테스트 커버리지**: 90% 이상 테스트 커버리지 달성

### 중기 목표 (3-6개월)
- **다중 언어 지원**: 다국어 웹 페이지 분석
- **고급 AI 기능**: 더 정교한 내용 분석
- **클라우드 네이티브**: Kubernetes 지원

### 장기 목표 (6개월+)
- **머신러닝 파이프라인**: 학습 기반 웹 분석
- **실시간 분석**: 웹 페이지 변화 추적
- **API 생태계**: 써드파티 통합 지원

## 🎯 핵심 가치

1. **안정성**: 24/7 운영 가능한 안정적인 서비스
2. **확장성**: 대용량 트래픽 처리 가능한 확장성
3. **보안성**: 엔터프라이즈급 보안 기능
4. **사용성**: 직관적이고 사용하기 쉬운 API
5. **호환성**: 다양한 MCP 클라이언트 지원

---

**MCP WebAnalyzer는 현대적인 웹 분석 요구사항을 충족하는 확장 가능하고 안정적인 엔터프라이즈급 솔루션입니다.**