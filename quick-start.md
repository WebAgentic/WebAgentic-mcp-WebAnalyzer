# 🚀 빠른 시작 가이드 - MCP WebAnalyzer (Windows)

## 📋 개요
Windows 환경에서 Web Analyzer MCP Server를 빠르게 설정하고 실행하는 방법입니다.

## 🖥️ 로컬 환경 설정 (Windows)

### 1. 사전 준비사항
```powershell
# Python 3.10+ 설치 확인
python --version

# pip 업그레이드
python -m pip install --upgrade pip

# uv 설치
pip install uv

# Git 설치 확인
git --version
```

### 2. 프로젝트 설정
```powershell
# 프로젝트 클론
git clone https://github.com/your-username/mcp-webanalyzer.git
cd mcp-webanalyzer

# 의존성 설치
uv sync
```

### 3. 환경 변수 설정
```powershell
# .env 파일 생성
copy .env.example .env

# 메모장으로 편집
notepad .env
```

필수 설정 내용:
```env
# 서버 설정
HOST=0.0.0.0
PORT=8080
DEBUG=false

# 보안 키 (반드시 변경하세요!)
SECRET_KEY=your-very-secure-secret-key-change-this-now
API_KEY=your-secure-api-key-change-this-too

# Redis 설정
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# 기타 설정
LOG_LEVEL=INFO
RATE_LIMIT_PER_MINUTE=100
CACHE_TTL=3600
REQUEST_TIMEOUT=30
MAX_PAGES_PER_REQUEST=200

# 외부 API (선택사항)
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
```

### 4. Redis 서버 실행

#### Option A: Docker 사용 (권장)
```powershell
# Docker Desktop 설치 후
docker run -d --name redis-server -p 6379:6379 redis:7-alpine
```

#### Option B: Windows용 Redis 설치
1. [Redis for Windows](https://github.com/microsoftarchive/redis/releases) 다운로드
2. MSI 파일 설치
3. 서비스 시작

### 5. 서버 실행
```powershell
# 터미널 1: API 서버 실행
uv run mcp-webanalyzer-api

# 터미널 2: 워커 실행 (선택사항)
uv run mcp-webanalyzer-worker

# 또는 백그라운드 실행 (PowerShell)
Start-Process -WindowStyle Hidden -FilePath "uv" -ArgumentList "run", "web-analyzer-api"
Start-Process -WindowStyle Hidden -FilePath "uv" -ArgumentList "run", "web-analyzer-worker"
```

### 6. 서버 테스트
```powershell
# 헬스 체크
curl http://localhost:8080/health

# API 테스트
curl -X POST http://localhost:8080/mcp/tools/extract_page_summary ^
  -H "X-API-Key: your-secure-api-key-change-this-too" ^
  -H "Content-Type: application/json" ^
  -d "{\"url\": \"https://example.com\"}"
```

## 🔧 Claude Desktop 설정 (Windows)

### 1. 설정 파일 위치
```
%APPDATA%\Claude\claude_desktop_config.json
```

### 2. 로컬 MCP 서버 설정
```json
{
  "mcpServers": {
    "web-analyzer-local": {
      "command": "uv",
      "args": ["run", "mcp-webanalyzer"],
      "cwd": "C:\\Users\\{username}\\mcp-webanalyzer",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 3. 원격 API 서버 설정
```json
{
  "mcpServers": {
    "web-analyzer-remote": {
      "command": "python",
      "args": ["-m", "mcp_webanalyzer.mcp_client"],
      "cwd": "C:\\Users\\{username}\\mcp-webanalyzer",
      "env": {
        "API_BASE_URL": "http://localhost:8080",
        "API_KEY": "your-secure-api-key-change-this-too",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## 🎯 Cursor 설정 (Windows)

### 1. 설정 파일 위치
```
%APPDATA%\Code\User\settings.json
또는 프로젝트 폴더의 .vscode\settings.json
```

### 2. 설정 내용
```json
{
  "mcp.servers": [
    {
      "name": "web-analyzer-local",
      "command": ["uv", "run", "mcp-webanalyzer"],
      "cwd": "C:\\Users\\{username}\\mcp-webanalyzer",
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  ],
  "mcp.enabled": true,
  "mcp.autoStart": true
}
```

## 🧪 테스트 및 확인

### 1. 서버 테스트
```powershell
# 헬스 체크
curl http://localhost:8080/health

# API 키 테스트
curl -X POST http://localhost:8080/mcp/tools/extract_page_summary ^
  -H "X-API-Key: your-secure-api-key-change-this-too" ^
  -H "Content-Type: application/json" ^
  -d "{\"url\": \"https://example.com\"}"
```

### 2. 클라이언트 테스트
```powershell
# 환경 변수 설정 후 실행
$env:API_BASE_URL = "http://localhost:8080"
$env:API_KEY = "your-secure-api-key-change-this-too"
python -m web_analyzer_mcp.mcp_client
```

### 3. Claude Desktop 테스트
1. Claude Desktop 재시작
2. 새 대화 시작
3. 테스트 메시지: "https://example.com 페이지를 분석해줘"

## 🔥 Windows 방화벽 설정

### 1. 포트 열기
```powershell
# 관리자 권한으로 실행
New-NetFirewallRule -DisplayName "Web Analyzer API" -Direction Inbound -Port 8080 -Protocol TCP -Action Allow
```

### 2. 방화벽 상태 확인
```powershell
Get-NetFirewallRule -DisplayName "Web Analyzer API"
```

## 📊 모니터링 (Windows)

### 1. 로그 확인
```powershell
# 서비스 로그
Get-Content logs\api.log -Wait

# 실시간 로그 보기
Get-Content logs\worker.log -Wait
```

### 2. 프로세스 확인
```powershell
# Python 프로세스 확인
Get-Process -Name "python" | Select-Object Id, ProcessName, CPU

# 포트 사용 확인
netstat -an | findstr :8080
```

### 3. 리소스 모니터링
```powershell
# 메모리 사용량
Get-Counter "\Memory\Available MBytes"

# CPU 사용량
Get-Counter "\Processor(_Total)\% Processor Time"
```

## 🔄 서비스 관리 (Windows)

### 1. Windows 서비스 생성 (선택사항)
```powershell
# NSSM 다운로드 및 설치
# https://nssm.cc/download

# 서비스 생성
nssm install WebAnalyzerAPI
```

### 2. 서비스 관리 명령
```powershell
# 서비스 시작
net start WebAnalyzerAPI

# 서비스 중지
net stop WebAnalyzerAPI

# 서비스 상태 확인
Get-Service WebAnalyzerAPI
```

## 🚨 문제 해결 (Windows)

### 1. 포트 충돌
```powershell
# 포트 사용 프로세스 확인
netstat -ano | findstr :8080

# 프로세스 종료
taskkill /PID <PID> /F
```

### 2. Redis 연결 실패
```powershell
# Redis 상태 확인 (Docker)
docker ps | findstr redis

# Redis 재시작
docker restart redis-server
```

### 3. 권한 문제
```powershell
# 관리자 권한으로 PowerShell 실행
# 디렉토리 권한 확인
icacls "C:\Users\{username}\web-analyzer-mcp"
```

### 4. 의존성 문제
```powershell
# 가상 환경 재생성
Remove-Item -Recurse -Force .venv
uv sync
```

## 🎯 중요한 점들

1. **사용자명**을 실제 Windows 사용자명으로 변경하세요
2. **API_KEY**를 강력한 키로 변경하세요
3. **SECRET_KEY**를 안전한 키로 변경하세요
4. **방화벽**에서 포트 8080을 열어주세요
5. **Redis** 서버가 실행 중인지 확인하세요

## 🚀 Docker 실행 (Windows)

### 1. Docker Desktop 설치
[Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) 다운로드

### 2. 컨테이너 실행
```powershell
# 모든 서비스 시작
docker-compose up -d

# 서비스 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f web-analyzer-api
```

### 3. 접속 URL
- **API 서버**: http://localhost:8080
- **API 문서**: http://localhost:8080/docs
- **Flower 모니터링**: http://localhost:5555

이제 Windows 환경에서 Web Analyzer MCP Server를 성공적으로 실행할 수 있습니다! 🚀