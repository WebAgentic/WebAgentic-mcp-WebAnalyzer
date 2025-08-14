# 🔍 웹 분석기 MCP

<a href="https://glama.ai/mcp/servers/@kimdonghwi94/web-analyzer-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@kimdonghwi94/web-analyzer-mcp/badge" alt="WebAnalyzer MCP server" />
</a>

지능적인 웹 콘텐츠 분석 및 요약 기능을 제공하는 강력한 MCP(Model Context Protocol) 서버입니다. FastMCP로 구축되어 스마트 웹 스크래핑, 콘텐츠 추출, AI 기반 질의응답 기능을 제공합니다.

## ✨ 주요 기능

### 🎯 핵심 도구

1. **`url_to_markdown`** - 웹페이지 핵심 내용 추출 및 요약
   - 맞춤 알고리즘으로 콘텐츠 중요도 분석
   - 광고, 네비게이션, 불필요한 콘텐츠 제거
   - 핵심 정보만 유지 (테이블, 이미지, 주요 텍스트)
   - 분석에 최적화된 구조화된 마크다운 출력

2. **`web_content_qna`** - 웹 콘텐츠 기반 AI 질의응답
   - 웹페이지에서 관련 콘텐츠 섹션 추출
   - 지능형 청킹 및 관련성 매칭 사용
   - OpenAI GPT 모델로 질문 답변

### 🚀 주요 특징

- **스마트 콘텐츠 순위**: 알고리즘 기반 콘텐츠 중요도 스코어링
- **핵심 콘텐츠만**: 불필요한 요소 제거, 중요한 내용만 유지
- **다중 IDE 지원**: Claude Desktop, Cursor, VS Code, PyCharm 지원
- **유연한 모델**: GPT-3.5, GPT-4, GPT-4 Turbo, GPT-5 선택 가능

## 📦 설치

### 사전 요구사항
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (Python 패키지 매니저)
- Chrome/Chromium 브라우저 (Selenium용)
- OpenAI API 키 (Q&A 기능용)

### 🚀 uv로 빠른 시작 (권장)

```bash
# 저장소 클론
git clone https://github.com/kimdonghwi94/web-analyzer-mcp.git
cd web-analyzer-mcp

# uv로 직접 실행 (의존성 자동 설치)
uv run mcp-webanalyzer
```

# IDE/에디터 연동


<details>
<summary><b>Install Claude Desktop</b></summary>

Claude Desktop_config.json 파일에 추가하세요. 자세한 내용은 [Claude Desktop MCP 문서](https://modelcontextprotocol.io/quickstart/user)를 참조하세요.

```json
{
  "mcpServers": {
    "web-analyzer": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/web-analyzer-mcp",
        "run", 
        "mcp-webanalyzer"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "OPENAI_MODEL": "gpt-4"
      }
    }
  }
}
```

</details>

<details>
<summary><b>Install Claude Code (VS Code 확장)</b></summary>

Claude Code CLI를 사용하여 서버를 추가하세요:

```bash
claude mcp add web-analyzer -e OPENAI_API_KEY=your_api_key_here -e OPENAI_MODEL=gpt-4 -- uv --directory /path/to/web-analyzer-mcp run mcp-webanalyzer
```
</details>

<details>
<summary><b>Install Cursor IDE</b></summary>

Cursor 설정에 추가하세요 (`File > Preferences > Settings > Extensions > MCP`):

```json
{
  "mcpServers": {
    "web-analyzer": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/web-analyzer-mcp",
        "run", 
        "mcp-webanalyzer"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "OPENAI_MODEL": "gpt-4"
      }
    }
  }
}
```
</details>

<details>
<summary><b>Install JetBrains AI Assistant</b></summary>

자세한 내용은 [JetBrains AI Assistant 문서](https://www.jetbrains.com/help/idea/ai-assistant.html)를 참조하세요.

1. JetBrains IDE에서 **Settings** → **Tools** → **AI Assistant** → **Model Context Protocol (MCP)**로 이동
2. **+ Add** 클릭
3. 대화상자 왼쪽 상단의 **Command**를 클릭하고 목록에서 **As JSON** 옵션 선택
4. 다음 설정을 추가하고 **OK** 클릭:

```json
{
  "mcpServers": {
    "web-analyzer": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/web-analyzer-mcp",
        "run", 
        "mcp-webanalyzer"
      ],
      "env": {
        "OPENAI_API_KEY": "your_openai_api_key_here",
        "OPENAI_MODEL": "gpt-4"
      }
    }
  }
}
```
</details>

## 🎛️ 도구 설명

### `url_to_markdown`
핵심 콘텐츠 추출과 함께 웹페이지를 깔끔한 마크다운 형식으로 변환합니다.

**매개변수:**
- `url` (문자열): 분석할 웹페이지 URL

**반환값:** 구조화된 데이터 보존과 함께 깔끔한 마크다운 콘텐츠

### `web_content_qna` 
지능형 콘텐츠 분석을 사용하여 웹페이지 콘텐츠에 대한 질문에 답변합니다.

**매개변수:**
- `url` (문자열): 분석할 웹페이지 URL
- `question` (문자열): 페이지 콘텐츠에 대한 질문

**반환값:** 페이지 콘텐츠를 기반으로 한 AI 생성 답변


## 🏗️ 아키텍처

### 콘텐츠 추출 파이프라인

1. **URL 검증** - 적절한 URL 형식 확인
2. **HTML 가져오기** - 동적 콘텐츠용 Selenium 사용
3. **콘텐츠 파싱** - HTML 처리를 위한 BeautifulSoup
4. **요소 스코어링** - 맞춤 알고리즘으로 콘텐츠 중요도 순위 매김
5. **콘텐츠 필터링** - 중복 및 저품질 콘텐츠 제거
6. **마크다운 변환** - 구조화된 출력 생성

### 질의응답 처리 파이프라인

1. **콘텐츠 청킹** - 지능형 텍스트 분할
2. **관련성 스코어링** - 콘텐츠와 질문 매칭
3. **컨텍스트 선택** - 가장 관련성 높은 청크 선택
4. **답변 생성** - OpenAI GPT 통합

## 🏗️ 프로젝트 구조

```
web-analyzer-mcp/
├── web_analyzer_mcp/          # 메인 Python 패키지
│   ├── __init__.py           # 패키지 초기화
│   ├── server.py             # 도구가 포함된 FastMCP 서버
│   ├── web_extractor.py      # 웹 콘텐츠 추출 엔진
│   └── rag_processor.py      # RAG 기반 Q&A 프로세서
├── scripts/                   # 빌드 및 유틸리티 스크립트
│   └── build.js              # Node.js 빌드 스크립트
├── README.md                 # 영어 문서
├── README.ko.md              # 한국어 문서
├── package.json              # npm 설정 및 스크립트
├── pyproject.toml            # Python 패키지 설정
├── .env.example              # 환경 변수 템플릿
└── dist-info.json            # 빌드 정보 (생성됨)
```

## 🛠️ 개발 환경

### uv를 사용한 현대적인 개발

```bash
# 저장소 클론
git clone https://github.com/kimdonghwi94/web-analyzer-mcp.git
cd web-analyzer-mcp

# 개발 명령어
uv run mcp-webanalyzer     # 개발 서버 시작
uv run python -m pytest   # 테스트 실행
uv run ruff check .        # 코드 린팅
uv run ruff format .       # 코드 포맷팅
uv sync                    # 의존성 동기화

# 개발 의존성 설치
uv add --dev pytest ruff mypy

# 프로덕션 빌드
npm run build
```

### 대안: 전통적인 Python 개발

```bash
# Python 환경 설정 (uv를 사용하지 않는 경우)
pip install -e .[dev]

# 개발 명령어
python -m web_analyzer_mcp.server  # 서버 시작
python -m pytest tests/            # 테스트 실행
python -m ruff check .             # 코드 린팅
python -m ruff format .            # 코드 포맷팅
python -m mypy web_analyzer_mcp/   # 타입 체크
```

## 🤝 기여하기

1. 저장소 포크
2. 기능 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시 (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 📋 로드맵

- [ ] 더 많은 콘텐츠 타입 지원 (PDF, 동영상)
- [ ] 다국어 콘텐츠 추출
- [ ] 맞춤 추출 규칙
- [ ] 자주 액세스하는 콘텐츠용 캐싱
- [ ] 실시간 업데이트를 위한 웹훅 지원

## ⚠️ 제한사항

- JavaScript 집약적인 사이트를 위해 Chrome/Chromium 필요
- Q&A 기능을 위해 OpenAI API 키 필요
- 남용 방지를 위한 속도 제한
- 일부 사이트에서 자동화된 액세스 차단 가능

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙋‍♂️ 지원

- 버그 리포트나 기능 요청은 이슈 생성
- GitHub 저장소의 토론에 기여
- 자세한 가이드는 [문서](https://github.com/kimdonghwi94/web-analyzer-mcp)를 확인하세요

## 🌟 감사의 말

- [FastMCP](https://github.com/jlowin/fastmcp) 프레임워크로 구축
- 웹 콘텐츠 처리를 위한 [HTMLRAG](https://github.com/plageon/HtmlRAG) 기술에서 영감을 받음
- 피드백과 기여를 해주신 MCP 커뮤니티에 감사드립니다

---

**MCP 커뮤니티를 위해 ❤️로 만들어졌습니다**