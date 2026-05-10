# agentgo-mediflow-backend

AI 기반 병원 마케팅 운영 플랫폼의 FastAPI 백엔드입니다.
Procedure Master 기반 수익성 분석 → 9채널 AI 콘텐츠 생성 → HITL 검수/승인 → 발행 아카이브까지 프론트엔드 8개 페이지 워크플로를 지원하는 REST API를 제공합니다.

## 핵심 도메인 모델

### 1. Clinic (브랜드 프로필)
- 병원명·타겟 고객·의사 철학·시그니처 시술·브랜드 톤·금지어 저장
- `clinic_type`: FACTORY(공장형) | PREMIUM — AI 콘텐츠 생성 페르소나 분기에 사용

### 2. Procedure Master (시술 마스터)
- 시술별 소모품 원가(consumable_cost)·인건비(labor_cost)·정가·최저가 기준 관리
- 시술 Variant(옵션)·FAQ·추천 포인트·주의사항 관계형 구조
- 수익성 시뮬레이션의 원가 데이터 소스

### 3. Promotion (프로모션/시뮬레이션)
- 시술 + 프로모션 가격·리드·전환율·업셀·광고비·프로모션 기간(주) 저장
- 프론트 `SimulationInput`과 1:1 대응 — staff_incentive 제거, promo_period_weeks 추가

### 4. Campaign (콘텐츠 이력)
- Promotion 기반으로 생성된 9채널 초안과 컴플라이언스 검토 노트 JSON 저장

### 5. ReviewItem (검수 체크리스트)
- 브랜드 톤·금지어·의료광고법·가격 정확성·최종 원장 승인 5단계 상태 관리

### 6. PublishedContent (발행 아카이브)
- Campaign 초안 발행 후 채널별 성과 지표(조회수·클릭수·CTR) 저장

### 7. AuditLog / Explainability / Signal
- 주요 이벤트(브랜드 저장, 시뮬레이션, 초안 생성, 검토 상태 변경) 감사 로그 저장
- 시뮬레이션 결과에 `trace_id`를 부여하고 설명성 페이로드 조회 지원
- 마케팅 신호 조회용 `SalesSignal` 테이블과 API 제공

## 아키텍처

```
Router → Service → Repository → SQLite (SQLModel)
             ↕
        AI Server API (localhost:8001)
```

- **Router** (`app/api/routes.py`): 요청 수신 + 스키마 검증
- **Service** (`app/services/`): 비즈니스 로직 (수익 계산, AI 호출, 컴플라이언스, 감사 로그)
- **Repository** (`app/repositories/`): 데이터 접근
- **Schema** (`app/schemas/contracts.py`): SQLModel 테이블 + API 응답 스키마

## API 엔드포인트

### 구현 완료 / PoC 구현

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/health` | 헬스체크 |
| `POST` | `/api/brand` | 브랜드 프로필 저장 (upsert) |
| `GET` | `/api/brand` | 브랜드 프로필 조회 |
| `POST` | `/api/brand/ai-write` | 타겟 고객·의사 철학 초안 생성 |
| `GET` | `/api/assets/connectors` | 데이터 커넥터 상태 목록 |
| `GET` | `/api/assets/reviews` | 리뷰 플랫폼 스냅샷 |
| `GET` | `/api/assets/promotions` | 프로모션 이력 목록 |
| `GET` | `/api/procedures` | 시술 마스터 리스트 |
| `GET` | `/api/procedures/catalog` | 시술 상세 카탈로그 (variant·faq·caution 포함) |
| `POST` | `/api/simulation/preview` | 수익 시뮬레이션 |
| `POST` | `/api/content/generate` | 9채널 콘텐츠 초안 생성 + 일관성 검사 |
| `POST` | `/api/content/shorts` | 숏폼 스토리보드 생성 |
| `POST` | `/api/medlaw/check` | 의료광고법 위반 후보 검출 |
| `POST` | `/api/leads` | 리드 등록 |
| `GET` | `/api/review/checklist` | 검수 체크리스트 조회 |
| `PATCH` | `/api/review/{item_id}` | 검수 상태 변경 |
| `GET` | `/api/archive` | 발행 아카이브 목록 |
| `GET` | `/api/archive/{id}` | 발행 콘텐츠 상세 |
| `PATCH` | `/api/archive/{id}/metrics` | 성과 지표 갱신 |
| `GET` | `/api/audit` | 감사 로그 목록(owner 전용) |
| `GET` | `/api/signals` | 마케팅 신호 목록 |
| `GET` | `/api/explain/{trace_id}` | 설명성 페이로드 조회 |
| `GET` | `/api/analytics/campaign` | 캠페인 성과 분석 |
| `GET` | `/api/analytics/channels` | 채널별 성과 분석 |

### 남은 보완

| 영역 | 상태 |
|---|---|
| RBAC | `X-User-Role` 기반 역할 검증, 최소 역할 보호, owner 전용 감사 로그, 비로컬 role token 검증 구현 |
| AI Client | `httpx.AsyncClient`, Request-ID, retryable status 재시도, graceful fallback 구현 |
| TTL Cache | 프로세스 내 LRU + TTL 캐시 구현, analytics 집계에 적용 |
| Signal Detection | CTR 저하, 의료광고 리스크 반복, 승인 지연 신호 자동 생성 구현 |
| Analytics | 캠페인 ROI와 채널 성과 집계 구현, 60초 TTL 캐시 적용 |
| 운영 전환 | 실제 사용자/권한 저장소, Alembic migration, 운영 모니터링은 별도 작업 필요 |

## 스키마 동기화 필요 사항

### SimulationInput

`procedure_id` 또는 `procedure`로 시술을 지정하고, `consumable_cost`, `labor_cost`, `promo_period_weeks`를 수신한다. `staff_incentive`는 계약에서 제거했다.

### ContentRequest

`event_name`, `event_start`, `event_end`, `core_message`, `highlights`, `channels`, `funnel_stage`, `promo_period_weeks`를 받는다. 9채널 ID(`ig_feed`, `ig_story`, `seo_blog`, `blog`, `web`, `place`, `kakao`, `email`, `app`)를 지원한다.

### GenerationResponse

`event_name`, `channels`, `review_notes`, `consistency_checks`, `trace_id`를 반환한다. AI 서버 장애 시 템플릿 fallback으로 동일 스키마를 유지한다.

## 실행

### Docker Compose

루트 디렉터리에서 전체 스택을 실행합니다.

```bash
docker compose up --build
# Nginx: http://localhost:8080
# Backend health: http://localhost:8080/health
```

Compose 환경에서 Backend는 PostgreSQL(`db:5432`)과 AI 서버(`http://ai:8001`)를 내부 네트워크로 호출합니다.

### 로컬 단독 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
# http://localhost:8000
# Swagger: http://localhost:8000/docs
```

## 테스트

```bash
pytest
```

## 정책

- 연락처·성함은 마스킹 및 암호화 처리를 원칙으로 합니다.
- AI가 생성한 모든 초안은 사람 검수 후에만 발행 가능합니다.
- 의료법 제56조 기반 금칙어 필터는 AI 파이프라인과 백엔드 양쪽에서 적용합니다.

## 스택

- Python 3.9+
- FastAPI
- SQLModel + SQLite
- Pydantic 2
- httpx (AI 파이프라인 호출)
