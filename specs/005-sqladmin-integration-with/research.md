# 연구 보고서: SQLAdmin + Llama AI 채팅 통합

**작성일**: 2025-10-17
**Feature Branch**: `005-sqladmin-integration-with`
**목적**: SQLAdmin 관리자 패널에 Llama AI 채팅 인터페이스 통합을 위한 기술 설계 연구

---

## 1. SQLAdmin 모범 사례

### 결정 (Decision)

**SQLAdmin 0.16.0+** 라이브러리를 사용하여 FastAPI와 SQLAlchemy 2.0 async 엔진 기반의 관리자 패널을 구축하고, 커스텀 페이지를 추가하여 Llama AI 채팅 인터페이스를 통합한다.

**핵심 구조**:
```python
# backend/src/admin/config.py
from sqladmin import Admin, ModelView
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

async def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    """SQLAdmin 인스턴스 생성 및 설정"""
    admin = Admin(
        app=app,
        engine=engine,
        title="보담 관리자 패널",
        base_url="/admin",
        # 인증 미들웨어는 auth.py에서 별도 처리
    )

    # ModelView 등록
    from .views import UserAdmin, DonationAdmin, RefundAdmin, FireStationAdmin
    admin.add_view(UserAdmin)
    admin.add_view(DonationAdmin)
    admin.add_view(RefundAdmin)
    admin.add_view(FireStationAdmin)

    # 커스텀 페이지 등록 (Llama Chat)
    from .llama_chat import LlamaChatPage
    admin.add_view(LlamaChatPage)

    return admin
```

**ModelView 커스터마이징 패턴**:
```python
# backend/src/admin/views/refund.py
from sqladmin import ModelView
from src.models.refund import Refund, RefundStatus

class RefundAdmin(ModelView, model=Refund):
    name = "환불 요청"
    name_plural = "환불 요청 목록"
    icon = "fa-solid fa-money-bill-transfer"

    # 리스트 페이지 설정
    column_list = [
        Refund.id,
        Refund.donation_id,
        Refund.amount,
        Refund.status,
        Refund.created_at
    ]
    column_searchable_list = [Refund.donation_id]
    column_sortable_list = [Refund.created_at, Refund.amount, Refund.status]
    column_filters = [Refund.status, Refund.created_at]
    column_default_sort = [(Refund.created_at, True)]  # 최신순

    # 상세 페이지 설정
    form_columns = [
        Refund.donation_id,
        Refund.reason,
        Refund.amount,
        Refund.status,
        Refund.reviewer_id,
    ]

    # 접근 권한 (모든 ModelView에 적용)
    can_create = False  # 환불은 사용자가 요청하므로 관리자가 생성하지 않음
    can_edit = True     # 상태 변경 가능
    can_delete = False  # 환불 기록은 삭제 불가
    can_view_details = True

    # 커스텀 액션 정의 (bulk approve/reject)
    # SQLAdmin 0.16.0+는 action 데코레이터 지원
    @action(
        name="bulk_approve",
        label="선택 항목 승인",
        confirmation="선택한 환불 요청을 모두 승인하시겠습니까?",
        add_in_detail=False,
        add_in_list=True,
    )
    async def bulk_approve_action(self, ids: List[str]):
        # RefundService를 통해 bulk 처리
        from src.services.refund_service import RefundService
        service = RefundService()
        results = await service.bulk_approve(
            refund_ids=[uuid.UUID(id) for id in ids],
            reviewer_id=current_admin_user.id  # 인증된 관리자 ID
        )
        return f"{results['approved']}건 승인 완료"
```

### 근거 (Rationale)

1. **Async SQLAlchemy 2.0 호환성**: SQLAdmin 0.16.0+는 `AsyncEngine`을 네이티브로 지원하므로 기존 보담 프로젝트의 비동기 데이터베이스 연결 풀과 완벽히 통합됨

2. **라이브러리 우선 원칙 준수**: 커스텀 관리자 UI를 직접 구현하는 대신 SQLAdmin 라이브러리를 활용하여 개발 시간 단축 및 유지보수성 향상

3. **ModelView 자동 생성**: SQLAlchemy 모델을 기반으로 CRUD UI가 자동 생성되므로 12개 엔티티(User, Donation, FireStation, Refund, NewsContent, SeleniumCrawlJob 등)에 대한 관리 페이지를 최소한의 코드로 구현 가능

4. **커스텀 페이지 확장성**: SQLAdmin의 `BaseView`를 상속하여 Llama 채팅 같은 완전한 커스텀 페이지를 추가할 수 있으며, 동일한 인증 및 레이아웃 컨텍스트를 공유함

5. **한글 UI 지원**: `name`, `name_plural`, `column_labels` 등을 한글로 설정 가능하여 한국어 관리자 패널 구축 용이

### 검토한 대안 (Alternatives Considered)

**대안 1: Django Admin 스타일 커스텀 구현**
- **장점**: 완전한 UI/UX 제어
- **단점**: 개발 시간 과다 소요, SQLAlchemy 2.0 async 통합 복잡도 높음, 보안 취약점 위험 증가
- **평가**: 라이브러리 우선 원칙 위반

**대안 2: FastAPI-Admin**
- **장점**: FastAPI 전용 관리자 패널
- **단점**: SQLAdmin보다 커뮤니티 지원 부족, async SQLAlchemy 2.0 지원 불완전, 커스텀 페이지 추가 방법 불명확
- **평가**: 성숙도가 SQLAdmin보다 낮음

**대안 3: Flask-Admin 포크 + FastAPI 통합**
- **장점**: Flask-Admin의 풍부한 기능
- **단점**: Flask 종속성 추가, FastAPI와의 통합 복잡, async 지원 제한적
- **평가**: 아키텍처 복잡도 증가

**선택 이유**: SQLAdmin이 FastAPI + SQLAlchemy 2.0 async 환경에서 가장 성숙하고 커스텀 페이지 추가가 명확하게 지원됨

---

## 2. Llama 채팅 UI 통합

### 결정 (Decision)

**REST API 기반 채팅 인터페이스 + 서버 세션 기반 대화 상태 관리**를 채택하며, SQLAdmin의 커스텀 페이지(`BaseView`)와 Jinja2 템플릿을 활용하여 채팅 UI를 구현한다.

**아키텍처**:
```
[관리자 브라우저]
       ↓ GET /admin/llama-chat
[SQLAdmin - LlamaChatPage]
       ↓ render_template("llama_chat.html")
[Jinja2 템플릿 - 채팅 UI]
       ↓ POST /admin/api/chat/query (fetch API)
[FastAPI 엔드포인트]
       ↓ async def chat_query(...)
[LlamaChatService]
       ↓ 1. Semantic Cache 조회 (Redis)
       ↓ 2. Cache miss → TogetherAIHttpClient 호출
       ↓ 3. GraphClient 쿼리 실행 (Knowledge Graph)
       ↓ 4. 결과를 Redis에 캐싱
       ↓ 5. 응답 반환
```

**커스텀 페이지 구현**:
```python
# backend/src/admin/llama_chat/page.py
from sqladmin import BaseView, expose
from starlette.requests import Request
from starlette.responses import Response

class LlamaChatPage(BaseView):
    name = "AI 채팅"
    icon = "fa-solid fa-message"

    @expose("/llama-chat", methods=["GET"])
    async def chat_page(self, request: Request) -> Response:
        """Llama AI 채팅 인터페이스 페이지"""
        # 세션에서 대화 기록 조회
        session_id = request.session.get("chat_session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session["chat_session_id"] = session_id

        # 세션 기록 조회 (Redis에서)
        history = await self._get_chat_history(session_id)

        return await self.templates.TemplateResponse(
            "llama_chat.html",
            {
                "request": request,
                "session_id": session_id,
                "history": history,
            }
        )

    async def _get_chat_history(self, session_id: str) -> list[dict]:
        """Redis에서 세션 대화 기록 조회"""
        from src.cache.clients import get_standard_client
        client = await get_standard_client()
        key = f"admin:chat_session:{session_id}"
        history_json = await client.get(key)
        if history_json:
            return json.loads(history_json)
        return []
```

**Jinja2 템플릿 (채팅 UI)**:
```html
<!-- backend/src/admin/llama_chat/templates/llama_chat.html -->
{% extends "sqladmin/layout.html" %}

{% block content %}
<div class="llama-chat-container">
    <div class="chat-header">
        <h2>🤖 Llama AI 어시스턴트</h2>
        <button id="clear-chat" class="btn btn-sm btn-danger">대화 초기화</button>
    </div>

    <div id="chat-messages" class="chat-messages">
        {% for msg in history %}
        <div class="message {{ msg.role }}">
            <strong>{{ msg.role|upper }}:</strong> {{ msg.content }}
        </div>
        {% endfor %}
    </div>

    <div class="chat-input-container">
        <textarea id="chat-input" placeholder="질문을 입력하세요 (예: 이번 달 기부금 총액은?)"></textarea>
        <button id="send-btn" class="btn btn-primary">전송</button>
        <div id="loading-indicator" style="display: none;">⏳ AI가 생각 중...</div>
    </div>
</div>

<script>
    const sessionId = "{{ session_id }}";
    const sendBtn = document.getElementById("send-btn");
    const chatInput = document.getElementById("chat-input");
    const chatMessages = document.getElementById("chat-messages");
    const loadingIndicator = document.getElementById("loading-indicator");

    sendBtn.addEventListener("click", async () => {
        const query = chatInput.value.trim();
        if (!query) return;

        // 사용자 메시지 표시
        appendMessage("USER", query);
        chatInput.value = "";

        // 로딩 표시
        loadingIndicator.style.display = "block";
        sendBtn.disabled = true;

        try {
            const response = await fetch("/admin/api/chat/query", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({query, session_id: sessionId})
            });

            const data = await response.json();

            // AI 응답 표시
            appendMessage("ASSISTANT", data.response);

        } catch (error) {
            appendMessage("SYSTEM", "오류: " + error.message);
        } finally {
            loadingIndicator.style.display = "none";
            sendBtn.disabled = false;
        }
    });

    function appendMessage(role, content) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${role.toLowerCase()}`;
        msgDiv.innerHTML = `<strong>${role}:</strong> ${content}`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // 엔터 키로 전송
    chatInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendBtn.click();
        }
    });
</script>

<style>
    .llama-chat-container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .chat-header { display: flex; justify-content: space-between; margin-bottom: 20px; }
    .chat-messages {
        height: 500px;
        overflow-y: auto;
        border: 1px solid #ddd;
        padding: 15px;
        background: #f9f9f9;
        margin-bottom: 20px;
        border-radius: 5px;
    }
    .message { margin-bottom: 15px; padding: 10px; border-radius: 5px; }
    .message.user { background: #e3f2fd; text-align: right; }
    .message.assistant { background: #fff3e0; text-align: left; }
    .message.system { background: #ffebee; text-align: center; }
    .chat-input-container { display: flex; gap: 10px; align-items: center; }
    #chat-input { flex: 1; min-height: 60px; padding: 10px; border: 1px solid #ccc; border-radius: 5px; }
    #loading-indicator { color: #666; font-style: italic; }
</style>
{% endblock %}
```

**REST API 엔드포인트**:
```python
# backend/src/api/admin/chat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.admin.llama_chat.service import LlamaChatService
from src.middleware.auth import require_admin

router = APIRouter(prefix="/admin/api/chat", tags=["admin-chat"])

class ChatQueryRequest(BaseModel):
    query: str
    session_id: str

class ChatQueryResponse(BaseModel):
    response: str
    sources: list[dict] = []
    cached: bool = False

@router.post("/query", dependencies=[Depends(require_admin)])
async def chat_query(request: ChatQueryRequest) -> ChatQueryResponse:
    """Llama AI 채팅 쿼리 처리"""
    service = LlamaChatService()
    result = await service.process_query(
        query=request.query,
        session_id=request.session_id
    )
    return result
```

### 근거 (Rationale)

1. **WebSocket 대신 REST API 선택 이유**:
   - 관리자 패널은 동시 사용자 수가 적음 (5-10명)
   - WebSocket 연결 관리 복잡도 불필요
   - SQLAdmin의 기본 Starlette 라우팅과 REST API가 더 자연스럽게 통합됨
   - Llama AI 응답이 스트리밍이 아닌 일괄 반환이므로 WebSocket의 이점이 제한적

2. **서버 세션 기반 상태 관리**:
   - Starlette의 `SessionMiddleware`를 활용하여 세션 ID 자동 관리
   - Redis에 대화 기록 저장 (TTL: 1시간, 키: `admin:chat_session:{session_id}`)
   - 데이터베이스에 대화 기록을 저장하지 않아 스토리지 부담 감소 (audit log는 별도 테이블에 저장)

3. **Jinja2 템플릿 사용**:
   - SQLAdmin이 Jinja2를 기본 템플릿 엔진으로 사용하므로 일관성 유지
   - 서버 사이드 렌더링으로 초기 로딩 속도 향상
   - JavaScript fetch API로 동적 상호작용 구현

4. **로딩 인디케이터**:
   - Llama AI 응답 시간이 3-10초 소요될 수 있으므로 명확한 로딩 상태 표시 필수

### 검토한 대안 (Alternatives Considered)

**대안 1: WebSocket 기반 실시간 채팅**
- **장점**: 스트리밍 응답 지원 (토큰 단위 출력 가능), 실시간성 우수
- **단점**:
  - Llama 3.3 70B 모델이 스트리밍을 지원하지 않는 경우 이점 없음
  - WebSocket 연결 관리 복잡도 증가 (재연결, heartbeat 등)
  - SQLAdmin 내에서 WebSocket 통합이 REST API보다 복잡
- **평가**: 관리자 패널의 사용 패턴(적은 사용자, 비실시간 쿼리)에 과도한 기술

**대안 2: 데이터베이스 기반 대화 기록 저장**
- **장점**: 영구 보관, 감사 추적 용이
- **단점**:
  - 대화 기록이 업무 기록이 아닌 임시 컨텍스트이므로 영구 보관 불필요
  - 데이터베이스 쓰기 부하 증가
  - Audit log는 별도로 이미 기록됨 (FR-043)
- **평가**: Redis 세션 기반이 더 적합

**대안 3: React SPA로 채팅 UI 구현**
- **장점**: 풍부한 UI/UX, 컴포넌트 재사용성
- **단점**:
  - SQLAdmin 외부에 별도 프론트엔드 구축 필요
  - 관리자 인증 통합 복잡도 증가
  - 빌드 프로세스 추가 필요
- **평가**: 단일 페이지 기능을 위해 과도한 복잡도

**선택 이유**: REST API + Jinja2 템플릿이 SQLAdmin 통합과 관리자 패널의 사용 패턴에 가장 적합

---

## 3. Knowledge Graph 쿼리 패턴

### 결정 (Decision)

**Llama AI가 자연어 질문을 SQL 쿼리로 변환**하는 패턴을 채택하며, Knowledge Graph는 기존 PostgreSQL의 `graph_search` 함수를 활용한다. Llama는 질문을 분석하여 적절한 SQL WHERE 조건과 JOIN을 생성하고, GraphClient를 통해 실행한다.

**쿼리 생성 패턴**:
```python
# backend/src/admin/llama_chat/service.py
from src.integrations.together_ai import TogetherAIHttpClient
from src.integrations.graph import GraphClient

class LlamaChatService:
    def __init__(self):
        self._llama_client = TogetherAIHttpClient()
        self._graph_client = GraphClient()

    async def process_query(self, query: str, session_id: str) -> dict:
        """자연어 쿼리를 처리하여 응답 생성"""

        # 1. 쿼리 분류 (Knowledge Graph 쿼리인지 판단)
        query_type = await self._classify_query(query)

        if query_type == "knowledge_graph":
            return await self._handle_graph_query(query, session_id)
        elif query_type == "database":
            return await self._handle_database_query(query, session_id)
        else:
            return await self._handle_general_query(query, session_id)

    async def _classify_query(self, query: str) -> str:
        """쿼리 유형 분류"""
        classification_prompt = f"""
다음 질문이 어떤 유형인지 분류하세요:

질문: {query}

유형:
1. knowledge_graph: 엔티티 간 관계를 묻는 질문 (예: "사고 XXX와 연결된 소방서는?", "뉴스 YYY와 관련된 사건은?")
2. database: 집계, 통계, 필터링 질문 (예: "이번 달 기부금 총액은?", "환불 대기 건수는?")
3. general: 일반적인 질문 (예: "시스템 상태는?", "사용법 알려줘")

JSON 형식으로만 답변: {{"type": "knowledge_graph|database|general"}}
"""

        response = await self._llama_client._client.post(
            "/v1/chat/completions",
            json={
                "model": "meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo",
                "messages": [
                    {"role": "system", "content": "당신은 쿼리 분류 전문가입니다. JSON만 출력하세요."},
                    {"role": "user", "content": classification_prompt}
                ],
                "temperature": 0.0,
                "max_tokens": 50
            }
        )
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        classification = json.loads(content.strip())
        return classification["type"]

    async def _handle_graph_query(self, query: str, session_id: str) -> dict:
        """Knowledge Graph 쿼리 처리"""

        # 2. Llama에게 SQL 쿼리 생성 요청
        sql_prompt = f"""
다음 자연어 질문을 PostgreSQL 쿼리로 변환하세요.

**데이터베이스 스키마**:
- fire_incidents (id, occurrence_date, address, fire_name, status)
- fire_stations (id, name, location, total_donations)
- news_content (id, title, content, source, relevance_score, published_at)
- news_match (id, incident_id, news_id, similarity_score)
- donations (id, user_id, fire_station_id, amount, created_at)

**질문**: {query}

**규칙**:
1. SELECT 문만 생성 (INSERT/UPDATE/DELETE 금지)
2. JOIN을 활용하여 관계 탐색
3. WHERE 조건으로 필터링
4. LIMIT 10으로 결과 제한

JSON 형식으로만 답변:
{{
  "sql": "SELECT ... FROM ... WHERE ...",
  "explanation": "쿼리 설명"
}}
"""

        response = await self._llama_client._client.post(
            "/v1/chat/completions",
            json={
                "model": "meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo",
                "messages": [
                    {"role": "system", "content": "당신은 SQL 쿼리 생성 전문가입니다. 보안을 위해 SELECT만 허용합니다."},
                    {"role": "user", "content": sql_prompt}
                ],
                "temperature": 0.0,
                "max_tokens": 500
            }
        )

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        query_result = json.loads(content)

        sql = query_result["sql"]
        explanation = query_result["explanation"]

        # 3. SQL Injection 방지 검증
        if not self._is_safe_query(sql):
            raise ValueError("안전하지 않은 쿼리가 감지되었습니다.")

        # 4. GraphClient를 통해 쿼리 실행
        await self._graph_client.connect()
        try:
            records = await self._graph_client.query(sql)
            results = [dict(record) for record in records]
        finally:
            await self._graph_client.close()

        # 5. 결과를 자연어로 변환
        summary_prompt = f"""
다음 쿼리 결과를 자연어로 요약하세요:

**질문**: {query}
**쿼리**: {sql}
**결과**: {json.dumps(results, ensure_ascii=False, indent=2)}

요약을 한국어로 작성하세요. 마크다운 형식 사용 가능.
"""

        summary_response = await self._llama_client._client.post(
            "/v1/chat/completions",
            json={
                "model": "meta-llama/Meta-Llama-3.3-70B-Instruct-Turbo",
                "messages": [
                    {"role": "system", "content": "당신은 데이터 분석 결과를 명확하게 설명하는 어시스턴트입니다."},
                    {"role": "user", "content": summary_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1000
            }
        )

        summary_result = summary_response.json()
        summary = summary_result["choices"][0]["message"]["content"]

        # 6. 세션 기록 저장
        await self._save_to_session(session_id, query, summary)

        return {
            "response": summary,
            "sources": [{"type": "knowledge_graph", "query": sql, "results": results}],
            "cached": False
        }

    def _is_safe_query(self, sql: str) -> bool:
        """SQL Injection 방지 검증"""
        sql_lower = sql.lower()
        # SELECT만 허용
        if not sql_lower.strip().startswith("select"):
            return False
        # 위험한 키워드 차단
        dangerous_keywords = [
            "insert", "update", "delete", "drop", "create", "alter",
            "truncate", "exec", "execute", "grant", "revoke"
        ]
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return False
        return True
```

**엔티티 관계 탐색 예시**:
```python
# 질문: "사고 ID abc-123과 관련된 뉴스 기사를 보여줘"
# Llama 생성 SQL:
SELECT
    nc.id, nc.title, nc.source, nc.relevance_score, nm.similarity_score
FROM news_content nc
JOIN news_match nm ON nc.id = nm.news_id
WHERE nm.incident_id = 'abc-123'
ORDER BY nm.similarity_score DESC
LIMIT 10;

# 질문: "강남구에서 발생한 화재와 연결된 소방서는?"
# Llama 생성 SQL:
SELECT DISTINCT
    fs.id, fs.name, fs.location, fi.address
FROM fire_stations fs
JOIN fire_incidents fi ON fi.fire_name = fs.name
WHERE fi.address LIKE '%강남구%'
LIMIT 10;
```

### 근거 (Rationale)

1. **SQL 기반 접근 선택 이유**:
   - 보담 프로젝트의 Knowledge Graph가 Neo4j가 아닌 PostgreSQL 기반이므로 Cypher 대신 SQL 사용이 자연스러움
   - 기존 SQLAlchemy 모델과 완벽히 호환
   - Llama 3.3 70B는 SQL 생성에 매우 뛰어난 성능을 보임

2. **3단계 프로세스**:
   - **분류 (Classification)**: 쿼리 유형을 먼저 판단하여 적절한 처리 경로 선택 (Knowledge Graph vs 일반 데이터베이스)
   - **생성 (Generation)**: Llama가 스키마 정보를 바탕으로 SQL 쿼리 생성
   - **요약 (Summarization)**: 쿼리 결과를 자연어로 변환하여 사용자 친화적인 응답 제공

3. **보안 고려**:
   - SELECT 문만 허용하여 데이터 수정 방지
   - SQL Injection 키워드 필터링
   - 관리자 전용 기능이므로 추가적인 권한 검증

4. **결과 제한**:
   - `LIMIT 10`으로 대량 데이터 조회 방지
   - 응답 시간 최적화 (10초 이내 목표)

### 검토한 대안 (Alternatives Considered)

**대안 1: Neo4j Cypher 쿼리 생성**
- **장점**: 그래프 쿼리에 최적화된 언어
- **단점**:
  - 보담 프로젝트가 Neo4j를 사용하지 않음 (PostgreSQL 기반)
  - 추가 데이터베이스 도입 필요
  - Llama가 SQL보다 Cypher 생성 능력이 떨어짐
- **평가**: 현재 아키텍처와 불일치

**대안 2: 하드코딩된 쿼리 템플릿**
- **장점**: 보안성 높음, 쿼리 성능 보장
- **단점**:
  - 유연성 부족 (새로운 질문에 대응 불가)
  - 유지보수 부담 (질문 유형마다 템플릿 추가 필요)
- **평가**: AI 활용의 이점을 살리지 못함

**대안 3: ORM 기반 쿼리 생성**
- **장점**: SQLAlchemy ORM 활용으로 타입 안전성 향상
- **단점**:
  - Llama가 Python ORM 코드를 생성하는 것보다 SQL 생성이 더 신뢰성 높음
  - ORM 코드 실행의 보안 위험 (eval 사용 불가)
- **평가**: SQL 생성이 더 안전하고 효과적

**선택 이유**: PostgreSQL 기반 Knowledge Graph에 SQL 쿼리 생성이 가장 적합하며, Llama 3.3의 SQL 생성 능력이 검증됨

---

## 4. Semantic Cache 통합

### 결정 (Decision)

**기존 Redis Semantic Cache를 Llama 채팅에 통합**하여 유사한 질문에 대한 응답을 캐싱하고, 임베딩 기반 유사도 계산으로 캐시 히트를 판단한다. Together AI의 `text-embedding-3-small` 모델 (1536차원)을 사용하여 쿼리 임베딩을 생성한다.

**통합 패턴**:
```python
# backend/src/admin/llama_chat/service.py (계속)

class LlamaChatService:
    async def process_query(self, query: str, session_id: str) -> dict:
        """Semantic Cache를 활용한 쿼리 처리"""

        # 1. 쿼리 임베딩 생성
        query_embedding = await self._generate_embedding(query)

        # 2. Semantic Cache 조회
        cached_response = await self._check_semantic_cache(query, query_embedding)
        if cached_response:
            logger.info(f"[LlamaChat] Semantic cache hit for query: {query[:50]}")
            await self._save_to_session(session_id, query, cached_response["response"])
            return {
                "response": cached_response["response"],
                "sources": cached_response.get("sources", []),
                "cached": True
            }

        # 3. Cache miss → 실제 쿼리 처리
        response = await self._process_query_with_llama(query, session_id)

        # 4. 결과를 Semantic Cache에 저장
        await self._save_to_semantic_cache(query, query_embedding, response)

        return response

    async def _generate_embedding(self, text: str) -> list[float]:
        """Together AI 임베딩 생성"""
        response = await self._llama_client._client.post(
            "/v1/embeddings",
            json={
                "model": "togethercomputer/text-embedding-3-small",
                "input": text
            }
        )
        result = response.json()
        embedding = result["data"][0]["embedding"]
        return embedding  # 1536 dimensions

    async def _check_semantic_cache(
        self,
        query: str,
        query_embedding: list[float]
    ) -> dict | None:
        """Semantic Cache에서 유사한 쿼리 조회"""
        from src.cache.clients import get_semantic_client

        client = await get_semantic_client()

        # Redis에서 admin:llama:* 패턴의 모든 캐시 키 조회
        cache_keys = []
        async for key in client.scan_iter(match="admin:llama:*"):
            cache_keys.append(key)

        # 각 캐시 항목과 코사인 유사도 계산
        best_match = None
        best_similarity = 0.0
        SIMILARITY_THRESHOLD = 0.85  # 85% 이상 유사도면 캐시 히트

        for key in cache_keys:
            cached_data = await client.get(key)
            if not cached_data:
                continue

            cached = json.loads(cached_data)
            cached_embedding = cached.get("embedding")
            if not cached_embedding:
                continue

            # 코사인 유사도 계산
            similarity = self._cosine_similarity(query_embedding, cached_embedding)

            if similarity > best_similarity and similarity >= SIMILARITY_THRESHOLD:
                best_similarity = similarity
                best_match = cached

        if best_match:
            logger.info(
                f"[SemanticCache] Cache hit with similarity {best_similarity:.2f} "
                f"for query: {query[:50]}"
            )
            return best_match

        return None

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """코사인 유사도 계산"""
        import numpy as np
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        return dot_product / (norm1 * norm2)

    async def _save_to_semantic_cache(
        self,
        query: str,
        embedding: list[float],
        response: dict
    ) -> None:
        """Semantic Cache에 저장"""
        from src.cache.clients import get_semantic_client
        from src.cache.settings import get_cache_settings

        client = await get_semantic_client()
        settings = get_cache_settings()

        # 캐시 키 생성 (쿼리 해시 기반)
        query_hash = hashlib.sha256(query.encode()).hexdigest()[:16]
        cache_key = f"admin:llama:{query_hash}"

        # 캐시 데이터 구조
        cache_data = {
            "query": query,
            "embedding": embedding,
            "response": response["response"],
            "sources": response.get("sources", []),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Redis에 저장 (TTL: 1시간)
        ttl = settings.default_semantic_ttl_seconds  # 3600초 (1시간)
        await client.setex(
            cache_key,
            ttl,
            json.dumps(cache_data, ensure_ascii=False)
        )

        logger.info(f"[SemanticCache] Cached response for query: {query[:50]} (TTL: {ttl}s)")
```

**TTL 전략**:
```python
# backend/src/cache/settings.py (기존 파일에 추가)

class CacheSettings:
    # 기존 설정...

    # Llama 채팅 캐시 TTL 전략
    ADMIN_LLAMA_CACHE_TTL = 3600  # 1시간 (관리자 쿼리는 자주 변하지 않음)

    # 캐시 무효화 규칙
    # - 새로운 기부금이 들어오면 "이번 달 기부금 총액" 같은 캐시 무효화
    # - 환불 승인/거부 시 "환불 대기 건수" 캐시 무효화

    @staticmethod
    def get_llama_cache_ttl(query_type: str) -> int:
        """쿼리 유형별 TTL 결정"""
        if query_type == "real_time":  # 실시간 데이터 (기부금, 환불)
            return 300  # 5분
        elif query_type == "statistical":  # 통계 데이터 (월별 집계)
            return 3600  # 1시간
        elif query_type == "knowledge_graph":  # 그래프 관계 (거의 변하지 않음)
            return 7200  # 2시간
        else:
            return 3600  # 기본 1시간
```

**캐시 무효화 트리거**:
```python
# backend/src/services/refund_service.py (기존 파일 수정)

class RefundService:
    async def bulk_approve(self, refund_ids: list[uuid.UUID], reviewer_id: uuid.UUID):
        # ... 환불 승인 로직 ...

        # Semantic Cache 무효화 (환불 관련 쿼리)
        from src.cache.semantic import soft_invalidate_queries
        await soft_invalidate_queries(ttl_seconds=10)  # 10초로 TTL 단축

        return results
```

### 근거 (Rationale)

1. **임베딩 기반 유사도 매칭**:
   - "이번 달 기부금 총액은?" 과 "이달 기부금 합계는?" 같은 의미적으로 유사한 질문을 동일하게 처리
   - 코사인 유사도 0.85 이상이면 캐시 히트 (실험적으로 조정 가능)

2. **Together AI 임베딩 모델 사용 이유**:
   - 기존 NewsContent 모델이 이미 Together AI 임베딩 사용 (1536차원)
   - 추가 임베딩 서비스 도입 불필요
   - 한국어 텍스트 처리 성능 우수

3. **TTL 전략**:
   - 관리자 쿼리는 일반적으로 실시간성이 덜 중요하므로 1시간 TTL 적용
   - 실시간 데이터 (기부금, 환불)는 5분으로 단축
   - 데이터 변경 시 soft invalidation으로 TTL을 10초로 단축 (hard delete 대신)

4. **성능 목표**:
   - 캐시 히트 시 응답 시간: < 500ms (임베딩 생성 + 유사도 계산 + Redis 조회)
   - 캐시 미스 시 응답 시간: < 10초 (Llama API 호출 + DB 쿼리)
   - 캐시 히트율 목표: > 60% (관리자가 유사한 질문을 반복적으로 물을 가능성 높음)

5. **Redis 스캔 최적화**:
   - `admin:llama:*` 패턴으로 관리자 채팅 캐시만 스캔
   - 캐시 키 수가 적을 것으로 예상 (< 100개)
   - 성능 이슈 발생 시 RediSearch 모듈로 벡터 유사도 검색 업그레이드 가능

### 검토한 대안 (Alternatives Considered)

**대안 1: 문자열 기반 캐시 키 (정확한 매칭)**
- **장점**: 구현 간단, Redis 조회 빠름
- **단점**:
  - 의미적으로 동일한 질문도 표현이 다르면 캐시 미스
  - 캐시 히트율 낮음 (예상 < 30%)
- **평가**: 임베딩 기반이 훨씬 효과적

**대안 2: PostgreSQL pgvector로 유사도 검색**
- **장점**: 벡터 인덱스로 빠른 검색, 대량 데이터 처리 가능
- **단점**:
  - 캐시 데이터를 DB에 저장하면 오버헤드 증가
  - Redis 캐시의 빠른 조회 성능 포기
  - 캐시 키가 적은 상황에서 과도한 복잡도
- **평가**: 현재 규모에서는 Redis scan이 충분

**대안 3: 캐시 무효화 없이 고정 TTL**
- **장점**: 구현 간단
- **단점**:
  - 데이터 변경 후 최대 1시간 동안 오래된 응답 반환
  - 관리자가 실시간 데이터 불일치 경험
- **평가**: Soft invalidation이 더 나은 UX 제공

**선택 이유**: 임베딩 기반 Semantic Cache가 캐시 히트율과 응답 정확도 모두 우수

---

## 5. SQLAdmin 커스텀 액션

### 결정 (Decision)

SQLAdmin의 `@action` 데코레이터를 활용하여 **bulk 환불 승인/거부 액션**을 구현하며, 확인 대화상자와 함께 RefundService를 통해 트랜잭션 기반 bulk 처리를 수행한다.

**구현 패턴**:
```python
# backend/src/admin/views/refund.py (계속)

from sqladmin import ModelView, action
from sqladmin.exceptions import ActionFailed
from starlette.requests import Request
from src.models.refund import Refund, RefundStatus
from src.services.refund_service import RefundService

class RefundAdmin(ModelView, model=Refund):
    name = "환불 요청"
    name_plural = "환불 요청 목록"

    # ... 기존 설정 ...

    @action(
        name="bulk_approve",
        label="선택 항목 승인",
        confirmation="선택한 환불 요청을 모두 승인하시겠습니까?",
        add_in_detail=False,  # 리스트 페이지에만 표시
        add_in_list=True,
    )
    async def bulk_approve_action(self, request: Request):
        """Bulk 환불 승인 액션"""

        # 선택된 ID 추출 (SQLAdmin이 자동으로 pks 파라미터 전달)
        pks = request.query_params.getlist("pks")
        if not pks:
            raise ActionFailed("선택된 항목이 없습니다.")

        refund_ids = [uuid.UUID(pk) for pk in pks]

        # 현재 관리자 ID (세션에서 추출)
        admin_user_id = request.session.get("user_id")
        if not admin_user_id:
            raise ActionFailed("관리자 인증 정보를 찾을 수 없습니다.")

        # RefundService를 통해 bulk 승인 처리
        service = RefundService()
        try:
            results = await service.bulk_approve(
                refund_ids=refund_ids,
                reviewer_id=uuid.UUID(admin_user_id)
            )

            # 성공/실패 메시지 생성
            success_count = results["approved"]
            failed_items = results.get("failed", [])

            if failed_items:
                failed_msgs = [f"ID {item['id']}: {item['reason']}" for item in failed_items]
                message = f"{success_count}건 승인 완료. 실패: {', '.join(failed_msgs)}"
            else:
                message = f"{success_count}건 환불 요청을 승인했습니다."

            return message

        except Exception as e:
            logger.error(f"[RefundAdmin] Bulk approve failed: {e}", exc_info=True)
            raise ActionFailed(f"환불 승인 중 오류 발생: {str(e)}")

    @action(
        name="bulk_reject",
        label="선택 항목 거부",
        confirmation="선택한 환불 요청을 모두 거부하시겠습니까? 거부 사유를 입력해주세요.",
        add_in_detail=False,
        add_in_list=True,
        # 폼 필드 정의 (거부 사유 입력)
        form={
            "rejection_reason": {
                "label": "거부 사유",
                "type": "textarea",
                "required": True
            }
        }
    )
    async def bulk_reject_action(self, request: Request):
        """Bulk 환불 거부 액션"""

        pks = request.query_params.getlist("pks")
        if not pks:
            raise ActionFailed("선택된 항목이 없습니다.")

        # 폼 데이터에서 거부 사유 추출
        form_data = await request.form()
        rejection_reason = form_data.get("rejection_reason")
        if not rejection_reason:
            raise ActionFailed("거부 사유를 입력해주세요.")

        refund_ids = [uuid.UUID(pk) for pk in pks]
        admin_user_id = uuid.UUID(request.session.get("user_id"))

        service = RefundService()
        try:
            results = await service.bulk_reject(
                refund_ids=refund_ids,
                reviewer_id=admin_user_id,
                rejection_reason=rejection_reason
            )

            success_count = results["rejected"]
            return f"{success_count}건 환불 요청을 거부했습니다."

        except Exception as e:
            logger.error(f"[RefundAdmin] Bulk reject failed: {e}", exc_info=True)
            raise ActionFailed(f"환불 거부 중 오류 발생: {str(e)}")
```

**RefundService (bulk 처리 로직)**:
```python
# backend/src/services/refund_service.py

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.refund import Refund, RefundStatus
from src.database.connection import get_db_session

class RefundService:
    async def bulk_approve(
        self,
        refund_ids: list[uuid.UUID],
        reviewer_id: uuid.UUID
    ) -> dict:
        """Bulk 환불 승인 처리 (트랜잭션)"""

        async with get_db_session() as session:
            approved = 0
            failed = []

            for refund_id in refund_ids:
                try:
                    # 환불 조회
                    stmt = select(Refund).where(Refund.id == refund_id)
                    result = await session.execute(stmt)
                    refund = result.scalar_one_or_none()

                    if not refund:
                        failed.append({"id": refund_id, "reason": "환불 요청을 찾을 수 없음"})
                        continue

                    # 이미 처리된 환불은 스킵
                    if refund.status != RefundStatus.PENDING:
                        failed.append({"id": refund_id, "reason": f"이미 {refund.status.value} 상태"})
                        continue

                    # 환불 승인 처리
                    refund.status = RefundStatus.APPROVED
                    refund.reviewer_id = reviewer_id
                    refund.reviewed_at = datetime.utcnow()

                    session.add(refund)
                    approved += 1

                    # 도너에게 알림 발송 (비동기 태스크)
                    from src.workers.notification_sender import send_refund_approved_notification
                    send_refund_approved_notification.delay(str(refund.id))

                except Exception as e:
                    logger.error(f"[RefundService] Failed to approve {refund_id}: {e}")
                    failed.append({"id": refund_id, "reason": str(e)})

            # 트랜잭션 커밋
            await session.commit()

            # Semantic Cache 무효화
            from src.cache.semantic import soft_invalidate_queries
            await soft_invalidate_queries(ttl_seconds=10)

            return {"approved": approved, "failed": failed}

    async def bulk_reject(
        self,
        refund_ids: list[uuid.UUID],
        reviewer_id: uuid.UUID,
        rejection_reason: str
    ) -> dict:
        """Bulk 환불 거부 처리 (트랜잭션)"""

        async with get_db_session() as session:
            rejected = 0
            failed = []

            for refund_id in refund_ids:
                try:
                    stmt = select(Refund).where(Refund.id == refund_id)
                    result = await session.execute(stmt)
                    refund = result.scalar_one_or_none()

                    if not refund:
                        failed.append({"id": refund_id, "reason": "환불 요청을 찾을 수 없음"})
                        continue

                    if refund.status != RefundStatus.PENDING:
                        failed.append({"id": refund_id, "reason": f"이미 {refund.status.value} 상태"})
                        continue

                    refund.status = RefundStatus.REJECTED
                    refund.reviewer_id = reviewer_id
                    refund.reviewed_at = datetime.utcnow()
                    # 거부 사유 저장 (별도 필드 추가 필요 또는 reason 필드 업데이트)
                    # refund.admin_note = rejection_reason  # 마이그레이션 필요 시

                    session.add(refund)
                    rejected += 1

                    # 도너에게 거부 알림 발송
                    from src.workers.notification_sender import send_refund_rejected_notification
                    send_refund_rejected_notification.delay(str(refund.id), rejection_reason)

                except Exception as e:
                    logger.error(f"[RefundService] Failed to reject {refund_id}: {e}")
                    failed.append({"id": refund_id, "reason": str(e)})

            await session.commit()

            # Semantic Cache 무효화
            from src.cache.semantic import soft_invalidate_queries
            await soft_invalidate_queries(ttl_seconds=10)

            return {"rejected": rejected, "failed": failed}
```

**확인 대화상자 UI (SQLAdmin 자동 생성)**:
```
SQLAdmin은 confirmation 파라미터에 지정된 메시지로 자동으로 JavaScript 확인 대화상자를 생성합니다.

예시:
- 리스트 페이지에서 여러 행 선택 (체크박스)
- "선택 항목 승인" 버튼 클릭
- 확인 대화상자 표시: "선택한 환불 요청을 모두 승인하시겠습니까?"
- "확인" 클릭 시 bulk_approve_action 실행
- 성공 메시지 표시: "5건 환불 요청을 승인했습니다."
```

### 근거 (Rationale)

1. **SQLAdmin 네이티브 액션 사용**:
   - `@action` 데코레이터로 선언적 액션 정의
   - SQLAdmin이 자동으로 UI (버튼, 체크박스, 대화상자) 생성
   - 커스텀 JavaScript 작성 불필요

2. **트랜잭션 기반 처리**:
   - 각 환불을 개별 try-except로 감싸서 일부 실패 시에도 나머지 처리 계속
   - 트랜잭션 커밋으로 원자성 보장 (모두 성공 또는 모두 롤백)

3. **확인 대화상자 필수**:
   - 환불 승인/거부는 되돌리기 어려운 작업이므로 확인 절차 필수
   - SQLAdmin의 `confirmation` 파라미터로 간단히 구현

4. **알림 발송**:
   - Celery 비동기 태스크로 도너에게 이메일/푸시 알림 발송
   - 관리자 UI 응답 시간에 영향 없음 (백그라운드 처리)

5. **Semantic Cache 무효화**:
   - 환불 승인/거부 후 "환불 대기 건수" 같은 쿼리의 캐시를 무효화하여 데이터 일관성 유지

### 검토한 대안 (Alternatives Considered)

**대안 1: 커스텀 API 엔드포인트 + JavaScript**
- **장점**: UI 완전 제어
- **단점**:
  - SQLAdmin 외부에 별도 API 구축 필요
  - JavaScript로 체크박스 처리, AJAX 호출, 에러 핸들링 직접 구현
  - 개발 시간 증가
- **평가**: SQLAdmin 네이티브 액션이 더 간단하고 유지보수 용이

**대안 2: 단일 환불만 처리 (bulk 액션 없음)**
- **장점**: 구현 간단
- **단점**:
  - 관리자가 여러 환불을 처리할 때 반복 작업 필요 (UX 저하)
  - spec.md의 FR-022, FR-023 요구사항 미충족
- **평가**: Bulk 액션이 필수

**대안 3: 환불 승인/거부를 별도 상태 변경 UI로 제공**
- **장점**: 세밀한 제어
- **단점**:
  - 사용자가 리스트 페이지 → 상세 페이지 → 편집 → 저장 단계를 거쳐야 함
  - 워크플로우 복잡
- **평가**: 액션 버튼이 더 직관적

**선택 이유**: SQLAdmin의 `@action` 데코레이터가 bulk 환불 처리에 최적화되어 있으며, 확인 대화상자와 트랜잭션 처리로 안전성 보장

---

## 종합 결론 (Summary)

### 전체 아키텍처 요약

보담 프로젝트에 SQLAdmin 0.16.0+ 기반 관리자 패널을 통합하고, Llama AI 채팅 인터페이스를 커스텀 페이지로 추가하여 자연어 기반 데이터 조회 및 Knowledge Graph 탐색 기능을 제공한다.

**핵심 결정 사항**:

1. **SQLAdmin 통합**: FastAPI + SQLAlchemy 2.0 async 엔진과 완벽히 호환되는 SQLAdmin 라이브러리를 사용하여 12개 엔티티에 대한 CRUD UI를 자동 생성

2. **Llama 채팅 UI**: REST API + Jinja2 템플릿 기반 채팅 인터페이스를 SQLAdmin의 `BaseView`로 구현하며, 서버 세션 기반 대화 상태 관리 (Redis 저장, TTL 1시간)

3. **Knowledge Graph 쿼리**: Llama 3.3 70B가 자연어 질문을 PostgreSQL 쿼리로 변환하고, GraphClient를 통해 실행하여 엔티티 관계 탐색 (SQL Injection 방지 검증 포함)

4. **Semantic Cache**: Together AI 임베딩 (1536차원)으로 쿼리 유사도 계산하여 Redis Semantic Cache에서 중복 질문 응답 재사용 (히트율 목표 60%+, 응답 시간 < 500ms)

5. **Bulk 환불 액션**: SQLAdmin의 `@action` 데코레이터로 bulk 승인/거부 구현, 트랜잭션 기반 처리 및 Celery 비동기 알림 발송

### 기술 스택

- **Frontend (Admin UI)**: SQLAdmin 0.16.0 + Jinja2 템플릿 + Vanilla JavaScript (fetch API)
- **Backend**: FastAPI + SQLAlchemy 2.0 async + httpx (HTTP 연결 풀)
- **AI/LLM**: Together AI Llama 3.3 70B Instruct Turbo + text-embedding-3-small (1536d)
- **Cache**: Redis Semantic Cache (임베딩 기반 유사도 매칭)
- **Knowledge Graph**: PostgreSQL 기반 (GraphClient를 통한 SQL 쿼리)
- **Background Tasks**: Celery (알림 발송, 캐시 무효화)

### 성능 목표

- 관리자 패널 페이지 로드: < 2초
- Llama AI 채팅 응답 (캐시 히트): < 500ms
- Llama AI 채팅 응답 (캐시 미스): < 10초
- Semantic Cache 히트율: > 60%
- Bulk 환불 처리: 10건 기준 < 3초

### 보안 및 권한

- 관리자 역할(UserRole.ADMIN) 전용 접근 제어 (미들웨어 검증)
- Llama 생성 SQL 쿼리는 SELECT만 허용 (INSERT/UPDATE/DELETE 차단)
- 모든 관리자 액션과 AI 쿼리는 audit log에 기록 (user_id, timestamp, query, action)
- 세션 기반 인증 (Starlette SessionMiddleware) + 비활성 타임아웃 (30분)

### 개발 우선순위

1. **Phase 1**: SQLAdmin 설정 + ModelView 구현 (User, Donation, Refund, FireStation 등)
2. **Phase 2**: 관리자 인증 미들웨어 + 세션 관리
3. **Phase 3**: Llama 채팅 서비스 + Semantic Cache 통합
4. **Phase 4**: Knowledge Graph 쿼리 패턴 구현 (SQL 생성 + 검증)
5. **Phase 5**: Bulk 환불 액션 + 알림 통합
6. **Phase 6**: Contract/Integration/Unit 테스트 (TDD)

### 위험 요소 및 완화 방안

**위험 1**: Llama가 잘못된 SQL 쿼리 생성
- **완화**: SQL Injection 필터 + SELECT 전용 검증 + 쿼리 결과 검토 단계 추가

**위험 2**: Semantic Cache 히트율이 목표(60%)에 미달
- **완화**: 유사도 임계값 조정 (0.85 → 0.80), 캐시 키 수 증가 시 RediSearch 벡터 인덱스로 업그레이드

**위험 3**: Llama API 응답 시간 10초 초과
- **완화**: 타임아웃 설정 (15초), 응답 시간 모니터링, 쿼리 복잡도 제한 (LIMIT 10)

**위험 4**: 동시 환불 승인 충돌
- **완화**: 데이터베이스 트랜잭션 격리 수준 (Read Committed), Optimistic Locking 또는 Pessimistic Locking 추가

### 다음 단계

1. **Phase 0 완료**: 이 research.md 문서 작성 완료 ✅
2. **Phase 1 시작**: `data-model.md`, `contracts/*.yaml`, `quickstart.md` 작성
3. **Contract Tests 작성**: TDD 원칙에 따라 실패하는 테스트 먼저 작성
4. **CLAUDE.md 업데이트**: 새로운 기술 스택 및 명령어 추가
5. **Phase 2 준비**: `/tasks` 명령으로 tasks.md 생성 준비

---

**문서 작성 완료일**: 2025-10-17
**다음 Phase**: Phase 1 - Design & Contracts (`/plan` 명령 계속 진행)
