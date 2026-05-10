# Backend 바이브코딩 가이드

## 목적

이 문서는 `agentgo-mediflow-backend`의 FastAPI, SQLModel, 서비스 로직을 일관되게 확장하기 위한 기준이다.

MediFlow 백엔드는 병원 프로필, 시술 마스터, 수익성 시뮬레이션, 리드/CRM, 콘텐츠 생성 연동, 검토/승인 상태를 담당한다. 의료광고와 개인정보가 포함될 수 있으므로 스키마 계약과 계층 책임을 좁게 유지한다.

---

## br-korea-poc 호환 컨벤션

mediflow 백엔드도 `br-korea-poc-backend`와 같은 계층 컨벤션을 따른다. 현재 PoC는 `app/api/routes.py` 단일 라우터 구조지만, 신규 기능과 리팩토링은 아래 기준으로 수렴한다.

* 기본 흐름은 `endpoint(route) -> service -> repository -> schema`이다.
* route/endpoint는 request 파싱, DI 연결, HTTP 예외 변환만 담당한다.
* service는 비즈니스 로직 조합을 담당하고 DB 쿼리를 직접 흩뿌리지 않는다.
* repository는 DB 접근만 담당하고 비즈니스 판단을 하지 않는다.
* schema는 SQLModel/Pydantic 요청·응답 계약만 정의하고 로직을 포함하지 않는다.
* 파일명은 `snake_case.py`를 사용한다.
* 응답 모델은 `XxxResponse`, 요청 모델은 `XxxRequest` 또는 기존 mediflow 계약의 `XxxInput`을 사용한다.
* 서비스 클래스는 `XxxService`, repository 클래스는 `XxxRepository`를 사용한다.
* 로깅은 `logging.getLogger(__name__)`를 기본으로 한다.
* 주석과 docstring은 한국어로 작성하고, WHY가 필요한 곳에만 둔다.

---

## 현재 구조

```text
app
├── api
│   ├── deps.py
│   └── routes.py
├── core
│   ├── auth.py
│   ├── config.py
│   ├── db.py
│   ├── init_db.py
│   └── ttl_cache.py
├── repositories
│   ├── bootstrap_repository.py
│   ├── brand_repository.py
│   └── review_repository.py
├── schemas
│   └── contracts.py
├── services
│   ├── audit_service.py
│   ├── analytics_service.py
│   ├── content_service.py
│   ├── medlaw_service.py
│   ├── planning_service.py
│   └── signal_service.py
└── main.py
```

---

## 계층 구조

기본 흐름은 아래와 같다.

```text
route -> service -> db session / repository -> schema
```

| 계층 | 책임 | 금지 사항 |
|---|---|---|
| `api/routes.py` | 요청 파싱, 응답 모델 지정, HTTP 예외 변환 | 수익 계산, 콘텐츠 변환 같은 비즈니스 로직 장기 보관 |
| `api/deps.py` | DB Session 등 FastAPI 의존성 제공 | 도메인 판단 |
| `services` | 수익성 계산, AI 연동, 도메인 흐름 조합 | HTTP request 직접 파싱 |
| `repositories` | 저장소 접근 캡슐화 | 의료광고 정책 판단 |
| `schemas/contracts.py` | SQLModel 테이블과 API 요청/응답 계약 | 서비스 로직 포함 |
| `core` | 설정, DB 초기화, 앱 인프라 | feature 전용 유틸 |

현재 `routes.py`에 일부 DB 조회 조합이 남아 있다. 신규 기능부터는 service 또는 repository로 분리한다. 라우터가 커지면 br-korea-poc 구조처럼 도메인별 endpoint 파일로 분리한다.

권장 확장 구조:

```text
app
├── api
│   └── v1
│       └── endpoints
│           ├── brand.py
│           ├── procedures.py
│           ├── simulation.py
│           ├── content.py
│           ├── leads.py
│           └── review.py
├── core
│   ├── config.py
│   ├── db.py
│   └── deps.py
├── repositories
├── schemas
└── services
```

---

## 도메인별 책임

### Brand / Clinic

병원 프로필은 콘텐츠 생성의 기준 데이터다.

주요 필드:

* `name`
* `clinic_type`: `FACTORY` 또는 `PREMIUM`
* `target_audience`
* `doctor_philosophy`
* `head_office_message`
* `branch_context`
* `signature_procedures`
* `brand_tone`
* `banned_terms`

규칙:

* 프로필 저장 API는 기존 프로필이 있으면 업데이트한다.
* 콘텐츠 생성 전 병원 프로필이 없으면 422를 반환한다.
* FACTORY/PREMIUM 분기는 service에서 처리하고 route에 흩뿌리지 않는다.

### Procedure Master

시술 마스터는 수익성 계산과 콘텐츠 소재의 기준 데이터다.

주요 모델:

* `Procedure`
* `ProcedureVariant`
* `ProcedureRecommendation`
* `ProcedureFaq`
* `ProcedureCaution`

규칙:

* 원가, 정가, 마진 하한선은 `Procedure`를 기준으로 계산한다.
* 옵션 가격, 회차, 과세 문구는 `ProcedureVariant`에 둔다.
* 추천 대상, 주의사항, FAQ는 콘텐츠 생성에 쓰일 수 있으므로 catalog 응답에서 함께 제공한다.

### Simulation

수익성 시뮬레이션은 `PlanningService.simulate()`에서 계산한다.

계산 기준:

```text
예상 환자 수 = expected_leads * conversion_rate / 100
총 매출 = 환자 수 * (promo_price + upsell_estimate)
총 비용 = 환자 수 * (consumable_cost + labor_cost) + ad_spend
예상 순이익 = 총 매출 - 총 비용
손익분기 환자 수 = ad_spend / 1인당 공헌이익
```

규칙:

* route는 `ValueError`를 HTTP 404 등으로 변환만 한다.
* 계산식 변경 시 테스트와 README의 설명을 같이 업데이트한다.
* `float("inf")` 같은 특수값이 응답으로 나갈 수 있는지 항상 확인한다.
* `SimulationResponse.trace_id`가 생기면 `ExplainabilityPayload` 조회 가능성을 유지한다.

### Content Generation

`ContentService`는 Backend 계약을 AI 서비스 계약으로 변환한다.

규칙:

* AI API URL은 `settings.ai_service_url`을 사용한다.
* Backend `ContentRequest.channels`는 AI 템플릿 채널과 다를 수 있으므로 변환 책임을 명확히 둔다.
* AI 호출 실패 시 사용자 흐름이 끊기지 않도록 동일 `GenerationResponse` 스키마의 fallback을 반환한다.
* retryable status(408/429/5xx)는 제한된 횟수만 재시도하고, 실패 시 graceful degradation으로 전환한다.
* AI 응답의 `review_notes`는 의료광고 검토 플로우에 노출되므로 누락을 허용하지 않는다.
* 9채널 실제 ID와 4종 AI 템플릿 채널 매핑은 Backend 서비스에서도 유지한다.

### MedLaw / Audit / Auth

규칙:

* 의료광고 검출은 `MedlawService`에서 관리하고, route에 금칙어 사전을 흩뿌리지 않는다.
* 주요 변경 이벤트는 `AuditService.record()`로 남긴다.
* 역할은 `X-User-Role` 헤더에서 읽고, 비로컬 환경에서는 `X-Role-Token` 검증을 유지한다.
* 감사 로그 조회 같은 민감 API는 owner 역할만 허용한다.
* analytics처럼 반복 조회되는 집계는 `TTLCache`를 사용하고, 원천 데이터 변경 시 cache clear를 호출한다.
* signal 생성은 `SignalService.refresh()`에 모으고 route에서는 refresh 여부만 결정한다.

### Review / Approval

검토 큐는 AI 단독 발행을 막는 안전 장치다.

규칙:

* 상태값은 `pending`, `in_review`, `approved`, `rejected` 중 하나로 제한한다.
* 상태 변경 API는 존재하지 않는 항목에 404를 반환한다.
* 의료광고법, 금칙어, 가격 정확성, 최종 원장 승인 단계는 삭제하지 않는다.

### Lead / CRM

리드 데이터는 개인정보를 포함할 수 있다.

규칙:

* 이름은 마스킹된 값만 저장한다.
* 연락처는 `phone_enc`에 암호화 또는 암호화 예정 값으로 저장한다.
* 새 분석 API는 원본 개인정보를 응답하지 않는다.

---

## 네이밍 규칙

* Python 파일명은 `snake_case.py`
* 요청 모델은 `XxxInput` 또는 `XxxRequest`
* 응답 모델은 `XxxResponse`
* 테이블 모델은 도메인 명사형
* 서비스 클래스는 `XxxService`
* Repository 클래스는 `XxxRepository`

현재 `contracts.py`는 SQLModel 테이블과 API 스키마를 함께 둔다. 파일이 커지면 아래처럼 도메인별로 분리한다.

```text
schemas
├── brand.py
├── procedure.py
├── simulation.py
├── content.py
├── review.py
└── contracts.py
```

분리 시 기존 import 경로를 한 번에 갱신하고 테스트를 통과시킨다.

---

## API 작성 규칙

* route 함수는 `response_model`을 항상 지정한다.
* DB Session은 `Depends(get_session)`으로 주입한다.
* 비즈니스 예외는 route에서 `HTTPException`으로 변환한다.
* 같은 예외 변환이 반복되면 private helper로 묶는다.
* route에서 `select()` 조합이 길어지면 service 또는 repository로 이동한다.
* DI 팩토리 함수가 늘어나면 `app/core/deps.py`로 이동해 br-korea-poc과 동일하게 관리한다.
* repository에서 SQL을 직접 작성해야 하면 SQLAlchemy `text()` + `mappings()` 패턴을 우선 검토한다.

예시:

```python
@router.post("/api/simulation/preview", response_model=SimulationResponse)
def simulate(
    payload: SimulationInput,
    db: Session = Depends(get_session),
) -> SimulationResponse:
    try:
        return planning_service.simulate(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
```

---

## 주석과 로깅

* 주석은 한국어로 작성한다.
* WHY가 비자명한 계산식, 정책 근거, 의료광고 제한에만 주석을 둔다.
* 단순 대입 설명 주석은 쓰지 않는다.
* 로깅은 `logging.getLogger(__name__)`를 기본으로 한다.
* 외부 AI API 실패, DB 초기화, 개인정보 처리 관련 이벤트는 로그 레벨을 명확히 한다.

---

## 검증 규칙

Backend 변경 후 기본 검증:

```bash
pytest
```

API 계약이나 DB 초기화 변경 시 추가 확인:

```bash
uvicorn app.main:app --reload
```

확인 대상:

* `GET /health`
* `GET /api/procedures`
* `GET /api/procedures/catalog`
* `POST /api/simulation/preview`
* `POST /api/brand`
* `POST /api/content/generate`
* `PATCH /api/review/{item_id}`

---

## 기능 추가 체크리스트

1. `feature list/agentgo-mediflow-backend.csv`에서 기능 상태와 우선순위를 확인한다.
2. 스키마 계약을 먼저 정의하고 route/service에서 재사용한다.
3. route에 비즈니스 로직이 길게 들어가지 않는지 확인한다.
4. 의료광고 표현, 가격 정확성, 개인정보 마스킹 요구사항을 확인한다.
5. 테스트를 추가하거나 기존 테스트를 갱신한다.
6. README와 이 guide에 반복 적용될 규칙을 반영한다.
