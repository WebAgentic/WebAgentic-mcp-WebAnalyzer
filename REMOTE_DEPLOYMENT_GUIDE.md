# 🌐 MCP WebAnalyzer 원격 서버 배포 가이드 (Windows)

이 가이드는 MCP WebAnalyzer를 Windows 서버에 배포하고 Windows 클라이언트에서 HTTP API를 통해 접근하는 방법을 설명합니다.

## 📋 배포 개요

### 아키텍처
```
Claude Desktop/Cursor (Windows 클라이언트)
        ↓ HTTP API
Web Analyzer MCP Server (Windows 서버)
    ├── API Server (FastAPI)
    ├── Celery Worker
    ├── Redis Cache
    └── IIS/Nginx Proxy (선택사항)
```

## 🚀 1. Windows 서버 준비

### 1.1 서버 요구사항
- **OS**: Windows Server 2019+ / Windows 10/11 Pro
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Storage**: 50GB+
- **Network**: 공인 IP 또는 도메인

### 1.2 필수 소프트웨어 설치
```powershell
# PowerShell을 관리자 권한으로 실행

# Chocolatey 설치
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 필수 소프트웨어 설치
choco install -y python git docker-desktop redis-64
```

### 1.3 Python 및 uv 설치
```powershell
# Python 3.10+ 설치 확인
python --version

# pip 업그레이드
python -m pip install --upgrade pip

# uv 설치
pip install uv
```

## 🔧 2. 프로젝트 배포

### 2.1 프로젝트 클론
```powershell
# 프로젝트 디렉토리 생성
mkdir C:\WebAnalyzerMCP
cd C:\WebAnalyzerMCP

# 프로젝트 클론
git clone https://github.com/your-username/mcp-webanalyzer.git .

# 의존성 설치
uv sync
```

### 2.2 환경 설정
```powershell
# .env 파일 생성
copy .env.example .env

# 환경 변수 수정
notepad .env
```

#### 필수 변경 사항:
```env
# 서버 설정
HOST=0.0.0.0
PORT=8080
DEBUG=false

# 강력한 비밀 키로 변경
SECRET_KEY=your-very-secure-secret-key-change-this-in-production

# API 접근 키 설정
API_KEY=your-secure-api-key-change-this-too

# Redis 설정 (패스워드 없이)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# 외부 API 키 (선택사항)
OPENAI_API_KEY=sk-your-openai-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key-here
```

### 2.3 Redis 서버 실행
```powershell
# Redis 서비스 시작
redis-server

# 또는 백그라운드에서 실행
Start-Process redis-server -WindowStyle Hidden

# Redis 상태 확인
redis-cli ping
```

### 2.4 서버 실행
```powershell
# API 서버 실행
uv run mcp-webanalyzer-api

# 다른 PowerShell 창에서 워커 실행
uv run mcp-webanalyzer-worker

# 또는 백그라운드 실행
Start-Process -WindowStyle Hidden -FilePath "uv" -ArgumentList "run", "web-analyzer-api"
Start-Process -WindowStyle Hidden -FilePath "uv" -ArgumentList "run", "web-analyzer-worker"
```

### 2.5 서비스 상태 확인
```powershell
# 헬스 체크
curl http://localhost:8080/health

# 프로세스 확인
Get-Process -Name "python" | Where-Object {$_.MainWindowTitle -like "*web-analyzer*"}

# 포트 확인
netstat -an | findstr :8080
```

## 🔐 3. 보안 설정

### 3.1 Windows 방화벽 설정
```powershell
# 관리자 권한으로 PowerShell 실행

# API 서버 포트 열기
New-NetFirewallRule -DisplayName "Web Analyzer API" -Direction Inbound -Port 8080 -Protocol TCP -Action Allow

# Redis 포트 열기 (로컬만)
New-NetFirewallRule -DisplayName "Redis Server" -Direction Inbound -Port 6379 -Protocol TCP -Action Allow -RemoteAddress LocalSubnet

# 방화벽 규칙 확인
Get-NetFirewallRule -DisplayName "Web Analyzer API"
```

### 3.2 SSL/TLS 설정 (선택사항)
```powershell
# Let's Encrypt for Windows 설치
choco install -y letsencrypt

# SSL 인증서 발급
certbot certonly --standalone -d your-domain.com

# 인증서 위치
# C:\Certbot\live\your-domain.com\
```

### 3.3 IIS 리버스 프록시 설정 (선택사항)
```powershell
# IIS 및 URL Rewrite 모듈 설치
Enable-WindowsOptionalFeature -Online -FeatureName IIS-WebServerRole, IIS-WebServer, IIS-CommonHttpFeatures, IIS-HttpErrors, IIS-HttpLogging, IIS-HttpRedirect, IIS-ApplicationDevelopment, IIS-NetFxExtensibility45, IIS-HealthAndDiagnostics, IIS-HttpTracing, IIS-Security, IIS-RequestFiltering, IIS-Performance, IIS-WebServerManagementTools, IIS-ManagementConsole, IIS-IIS6ManagementCompatibility, IIS-Metabase

# URL Rewrite 모듈 다운로드 및 설치
# https://www.iis.net/downloads/microsoft/url-rewrite
```

## 🔗 4. 클라이언트 연결 설정

### 4.1 Windows 클라이언트 설정
```powershell
# 클라이언트 컴퓨터에서 프로젝트 클론
git clone https://github.com/your-username/mcp-webanalyzer.git
cd web-analyzer-mcp

# 클라이언트용 최소 의존성 설치
pip install httpx fastmcp pydantic pydantic-settings
```

### 4.2 Claude Desktop 설정 (Windows 클라이언트)

#### 설정 파일 위치:
```
%APPDATA%\Claude\claude_desktop_config.json
```

#### 설정 내용:
```json
{
  "mcpServers": {
    "web-analyzer-remote": {
      "command": "python",
      "args": ["-m", "mcp_webanalyzer.mcp_client"],
      "cwd": "C:\\Users\\{username}\\mcp-webanalyzer",
      "env": {
        "API_BASE_URL": "http://YOUR_SERVER_IP:8080",
        "API_KEY": "your-secure-api-key-change-this-too",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 4.3 Cursor 설정 (Windows 클라이언트)

#### 설정 파일 위치:
```
%APPDATA%\Code\User\settings.json
또는 프로젝트 폴더의 .vscode\settings.json
```

#### 설정 내용:
```json
{
  "mcp.servers": [
    {
      "name": "web-analyzer-remote",
      "command": ["python", "-m", "web_analyzer_mcp.mcp_client"],
      "cwd": "C:\\Users\\{username}\\mcp-webanalyzer",
      "env": {
        "API_BASE_URL": "http://YOUR_SERVER_IP:8080",
        "API_KEY": "your-secure-api-key-change-this-too",
        "LOG_LEVEL": "INFO"
      }
    }
  ],
  "mcp.enabled": true,
  "mcp.autoStart": true
}
```

## 🧪 5. 연결 테스트

### 5.1 직접 API 테스트
```powershell
# 서버에서 헬스 체크
curl http://YOUR_SERVER_IP:8080/health

# API 키를 사용한 직접 호출
curl -X POST http://YOUR_SERVER_IP:8080/mcp/tools/extract_page_summary ^
  -H "X-API-Key: your-secure-api-key-change-this-too" ^
  -H "Content-Type: application/json" ^
  -d "{\"url\": \"https://example.com\"}"
```

### 5.2 MCP Client 테스트
```powershell
# 클라이언트에서 테스트
$env:API_BASE_URL = "http://YOUR_SERVER_IP:8080"
$env:API_KEY = "your-secure-api-key-change-this-too"
python -m web_analyzer_mcp.mcp_client
```

### 5.3 Claude Desktop 테스트
1. Claude Desktop 재시작
2. 새 대화 시작
3. 웹 분석 도구 사용 테스트: "https://example.com 페이지를 분석해줘"

## 📊 6. 모니터링 및 관리

### 6.1 서비스 모니터링
```powershell
# 서비스 상태 확인
curl http://YOUR_SERVER_IP:8080/health

# 메트릭 확인
curl http://YOUR_SERVER_IP:9090/metrics

# Flower 모니터링 (별도 실행 필요)
# http://YOUR_SERVER_IP:5555
```

### 6.2 로그 관리
```powershell
# 로그 확인
Get-Content logs\api.log -Wait

# 로그 파일 목록
Get-ChildItem logs\

# 로그 크기 확인
Get-ChildItem logs\ | Select-Object Name, Length
```

### 6.3 백업 및 복원
```powershell
# Redis 데이터 백업
redis-cli BGSAVE

# 로그 백업
$date = Get-Date -Format "yyyyMMdd"
Compress-Archive -Path logs\ -DestinationPath "logs-backup-$date.zip"

# 설정 백업
copy .env ".env.backup"
```

## 🚨 7. 문제 해결

### 7.1 일반적인 문제들

#### 서버 연결 실패
```powershell
# 포트 확인
netstat -an | findstr :8080

# 방화벽 확인
Get-NetFirewallRule -DisplayName "Web Analyzer API"

# 서비스 재시작
Get-Process -Name "python" | Where-Object {$_.MainWindowTitle -like "*web-analyzer*"} | Stop-Process
```

#### 인증 실패
```powershell
# API 키 확인
Select-String -Path .env -Pattern "API_KEY"

# 환경 변수 확인
Get-ChildItem env: | Where-Object {$_.Name -like "*API*"}
```

#### 성능 문제
```powershell
# 리소스 사용량 확인
Get-Process -Name "python" | Select-Object Name, CPU, WorkingSet

# Redis 메모리 사용량 확인
redis-cli INFO memory
```

### 7.2 성능 최적화

#### Redis 튜닝
```powershell
# Redis 설정 최적화
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### 멀티 프로세스 실행
```powershell
# 여러 워커 프로세스 실행
for ($i=1; $i -le 3; $i++) {
    Start-Process -WindowStyle Hidden -FilePath "uv" -ArgumentList "run", "web-analyzer-worker"
}
```

## 🔄 8. 서비스 관리

### 8.1 Windows 서비스 생성
```powershell
# NSSM 설치
choco install -y nssm

# API 서버 서비스 생성
nssm install WebAnalyzerAPI "C:\WebAnalyzerMCP\.venv\Scripts\python.exe"
nssm set WebAnalyzerAPI Parameters "-m web_analyzer_mcp.api_server"
nssm set WebAnalyzerAPI AppDirectory "C:\WebAnalyzerMCP"
nssm set WebAnalyzerAPI DisplayName "Web Analyzer MCP API Server"
nssm set WebAnalyzerAPI Description "엔터프라이즈급 웹 분석 MCP 서버"

# 서비스 시작
nssm start WebAnalyzerAPI
```

### 8.2 서비스 관리 명령
```powershell
# 서비스 시작
Start-Service WebAnalyzerAPI

# 서비스 중지
Stop-Service WebAnalyzerAPI

# 서비스 상태 확인
Get-Service WebAnalyzerAPI

# 서비스 로그 확인
Get-EventLog -LogName Application -Source WebAnalyzerAPI -Newest 10
```

## 🎯 9. 업데이트 및 유지보수

### 9.1 서비스 업데이트
```powershell
# 서비스 중지
Stop-Service WebAnalyzerAPI

# 코드 업데이트
git pull origin main

# 의존성 업데이트
uv sync

# 서비스 재시작
Start-Service WebAnalyzerAPI
```

### 9.2 정기 유지보수
```powershell
# 임시 파일 정리
Remove-Item -Path "C:\WebAnalyzerMCP\logs\*.log" -Force -Recurse

# Redis 메모리 정리
redis-cli FLUSHALL

# 시스템 리소스 확인
Get-ComputerInfo | Select-Object TotalPhysicalMemory, AvailablePhysicalMemory
```

## 📞 10. 지원 및 문제 해결

### 10.1 로그 분석
```powershell
# 오류 로그 검색
Select-String -Path logs\api.log -Pattern "ERROR"

# 특정 시간 범위 로그 확인
Get-Content logs\api.log | Where-Object {$_ -match "2024-01-01"}
```

### 10.2 네트워크 진단
```powershell
# 포트 연결 테스트
Test-NetConnection -ComputerName YOUR_SERVER_IP -Port 8080

# DNS 해상도 확인
Resolve-DnsName your-domain.com
```

## 🎯 중요한 점들

1. **YOUR_SERVER_IP**를 실제 서버 IP로 변경하세요
2. **API_KEY**를 강력한 키로 변경하세요
3. **SECRET_KEY**를 안전한 키로 변경하세요
4. **Windows 방화벽**에서 포트 8080을 열어주세요
5. **Redis** 서버가 실행 중인지 확인하세요
6. **Windows 서비스**로 등록하여 자동 시작 설정하세요

이제 Windows 서버에서 Web Analyzer MCP Server를 실행하고 Windows 클라이언트에서 HTTP API를 통해 안전하게 접근할 수 있습니다! 🚀

---

**Windows 환경에서 최적화된 엔터프라이즈급 MCP 서버 배포가 완료되었습니다.**