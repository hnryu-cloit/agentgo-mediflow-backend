# agentgo-mediflow-backend

AI 기반 병원 마케팅 운영 플랫폼의 FastAPI 백엔드입니다.
브랜드 프로필 관리, 수익성 시뮬레이션, 멀티채널 콘텐츠 생성, 검토/승인 워크플로를 API로 제공합니다.

## 아키텍처

```
Router → Service → Repository
```

- **Router** (`app/api/routes.py`): 요청 수신, 스키마 검증, 응답 반환
- **Service** (`app/services/`): 비즈니스 로직 (수익성 계산, 콘텐츠 생성)
- **Repository** (`app/repositories/`): 데이터 접근 (in-memory, 추후 DB 교체 가능)
- **Schema** (`app/schemas/contracts.py`): 입출력 계약 (Pydantic)
- **Deps** (`app/api/deps.py`): 의존성 주입 (lru_cache 싱글턴)

## 디렉토리 구조

```
app/
├── api/
│   ├── deps.py          # 의존성 주입 함수 (lru_cache 싱글턴)
│   └── routes.py        # 전체 엔드포인트 정의
├── core/
│   └── config.py        # pydantic-settings 기반 환경 변수 로딩
├── repositories/
│   ├── bootstrap_repository.py   # 정적 부트스트랩 데이터
│   ├── brand_repository.py       # 브랜드 프로필 in-memory 저장소
│   └── review_repository.py      # 검토 항목 in-memory 저장소
├── schemas/
│   └── contracts.py     # 전체 입출력 스키마
├── services/
│   ├── planning_service.py   # 수익성 시뮬레이션 계산
│   └── content_service.py   # 채널별 콘텐츠 초안 생성
└── main.py              # FastAPI 앱 초기화 + CORS
tests/
├── test_health.py       # 헬스체크 + 시뮬레이션
├── test_brand.py        # 브랜드 프로필 CRUD
├── test_content.py      # 콘텐츠 생성
└── test_review.py       # 검토 상태 업데이트
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/health` | 헬스체크 |
| `GET` | `/api/bootstrap` | 앱 초기 설정 데이터 |
| `POST` | `/api/brand` | 브랜드 프로필 저장 |
| `GET` | `/api/brand` | 브랜드 프로필 조회 |
| `POST` | `/api/simulation/preview` | 수익성 시뮬레이션 계산 |
| `POST` | `/api/content/generate` | 채널별 콘텐츠 초안 생성 |
| `GET` | `/api/review/checklist` | 검토 체크리스트 조회 |
| `PATCH` | `/api/review/{stage}` | 검토 항목 상태 변경 |
| `GET` | `/api/channels/drafts` | 부트스트랩 정적 채널 초안 |

### 주요 스키마

**`POST /api/brand`** 요청
```json
{
  "hospital_name": "테스트 피부과",
  "target_audience": "30-40대 직장 여성",
  "doctor_philosophy": "과장 없는 솔직한 설명",
  "signature_procedures": ["피코토닝", "잡티케어"],
  "brand_tone": ["신뢰감", "친근함"],
  "banned_terms": ["완치", "100% 효과"]
}
```

**`POST /api/simulation/preview`** 요청
```json
{
  "promotion_name": "봄 이벤트",
  "promo_price": 149000,
  "list_price": 220000,
  "procedure_cost": 42000,
  "expected_leads": 30,
  "close_rate": 0.4,
  "upsell_rate": 0.2,
  "average_upsell_revenue": 80000,
  "repeat_visit_rate": 0.1,
  "repeat_visit_revenue": 100000,
  "ad_budget": 1000000
}
```

**`POST /api/content/generate`** 요청 (브랜드 프로필 저장 후 사용 가능)
```json
{
  "event_name": "봄 피부 이벤트",
  "event_start": "2026-04-01",
  "event_end": "2026-04-30",
  "core_message": "봄맞이 피부 관리를 전문의와 함께",
  "highlights": ["30% 할인", "무료 상담"],
  "channels": ["blog", "sns", "web", "app"]
}
```

**`PATCH /api/review/{stage}`** 요청
```json
{
  "status": "approved",
  "notes": "확인 완료"
}
```
- `status` 허용값: `pending` | `in_review` | `approved` | `rejected`

## 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# http://localhost:8000
# API 문서: http://localhost:8000/docs
```

## 테스트

```bash
python3 -m pytest tests/ -v
# 25 passed
```

## 환경 변수

`.env.example`을 복사해 `.env`로 사용합니다.

```env
APP_NAME=agentgo-mediflow
APP_ENV=local
DATABASE_URL=sqlite:///./app.db
EXTERNAL_API_KEY=stub-key
ALLOWED_ORIGINS=["http://localhost:5173"]
```

## 스택

- Python 3.9+
- FastAPI 0.115
- Pydantic 2.9 + pydantic-settings 2.5
- Uvicorn 0.30
- pytest 8.3 + httpx 0.27

## 정책

- 의료광고 심의와 표현 제한 검토가 반드시 포함되어야 한다.
- AI가 만든 초안은 항상 사람 검수와 최종 승인 단계를 거쳐야 한다.
- 플랫폼별 정책 차이에 따라 문안 룰셋을 분리 관리해야 한다.