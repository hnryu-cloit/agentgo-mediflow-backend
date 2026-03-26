# agentgo-mediflow-backend

AI 기반 병원 마케팅 운영 플랫폼의 FastAPI 백엔드입니다.
단순한 콘텐츠 생성을 넘어, **Procedure Master 기반의 수익성 분석**과 **CRM 데이터 기반의 마케팅 ROI 측정** 기능을 제공합니다.

## 핵심 도메인 모델

### 1. 시술 마스터 (Procedure Master)
- 시술별 소모품 원가(팁값, 약제비), 시술 시간, 권장 마진율을 관리합니다.
- 실제 병원의 '수익 계산기' 역할을 수행하는 기초 데이터입니다.

### 2. 수익성 시뮬레이션 (Simulation)
- 시술 원가 + 인건비 + 상담 실장 인센티브 + 부가세를 반영한 정교한 순수익 계산 로직을 제공합니다.
- 광고비(Ad Spend) 대비 유입된 리드(Lead)의 가치를 산출하여 마케팅 실행 여부를 결정합니다.

### 3. CRM 및 리드 관리 (Lead Management)
- 마케팅 채널(FB, IG, BLOG)별 잠재 고객 리드를 추적합니다.
- 상담 상태(신청/내원/노쇼)에 따른 실질적인 ROI 분석 기능을 지원합니다.

### 4. 의료 컴플라이언스 (Compliance)
- 의료법 제56조 기반의 금칙어 필터링 로직을 내장하고 있습니다.
- 병원 유형(공장형/프리미엄)에 따른 채널별 페르소나 최적화 문안을 생성합니다.

## 아키텍처

```
Router → Service → Repository
```

- **Router** (`app/api/routes.py`): 요청 수신, 스키마 검증
- **Service** (`app/services/`): 비즈니스 로직 (원가 계산, 리드 ROI, 콘텐츠 필터링)
- **Repository** (`app/repositories/`): 데이터 접근 (In-memory, 확장 가능)
- **Schema** (`app/schemas/contracts.py`): 도메인 스키마 정의 (Pydantic)

## 주요 API 엔드포인트 (v1.1)

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/api/procedures` | 시술 마스터 리스트 조회 |
| `POST` | `/api/simulation/preview` | 고도화된 수익 시뮬레이션 |
| `POST` | `/api/leads` | 신규 리드(상담 신청) 등록 |
| `GET` | `/api/analytics/roi` | 캠페인별 ROI 분석 리포트 |
| `POST` | `/api/content/generate` | 의료법 준수 콘텐츠 생성 |

## 실행 및 테스트

```bash
# 환경 설정
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --reload

# 테스트 실행
pytest
```

## 정책 및 규제
- **개인정보:** 연락처 및 성함은 마스킹 및 암호화 처리를 원칙으로 합니다.
- **의료법:** AI가 생성한 모든 초안은 반드시 '사람 검수'를 거쳐야 발행 가능합니다.
