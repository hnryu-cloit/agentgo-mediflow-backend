# agnetgo-mediflow-backend

> **전역 시스템 제약조건 및 코드 컨벤션**
> 본 프로젝트는 엔터프라이즈 B2B SaaS 아키텍처를 지향하며, 공통 코드 컨벤션을 따릅니다.
> 상세 기준은 상위 디자인 시스템 및 저장소 전역 컨벤션 문서를 우선 확인하세요.
> 주요 백엔드 제약: **Layered Architecture, Schema Validation, Typed Services**

agnetgo-mediflow의 bootstrap API와 정책/상태 전달을 담당하는 백엔드 MVP 초안입니다.

## Summary

- 담당 도메인: 병원별 이벤트 템플릿, 금칙어, 브랜드 톤, 시술 카테고리를 입력값으로…, 하나의 프로모션 기획안에서 블로그, SNS, 홈페이지, 앱용 문안과 소…, 단순 문구 생성이 아니라 병원별 입력 자산을 반영해 결과물 차별화를 만…, 입력값: 프로모션 가격, 정상가, 시술 원가, 예상 모집객 수, 업셀…
- 주요 사용자: 개원의: 병원 브랜딩, 시술 포지셔닝, 계정 운영, 이벤트 프로모션 효율을 함께 관리해야 하는 사용자, 병원 마케터/실장: 이벤트 기획, 가격 판단, 채널 운영, 게시 실행을 실무로 담당하는 사용자, 봉직의: 개원 전 퍼스널 브랜딩과 전문 분야 포지셔닝을 시작하려는 사용자
- 핵심 역할:
- 병원별 이벤트 템플릿, 금칙어, 브랜드 톤, 시술 카테고리를 입력값으로 관리한다.
- 하나의 프로모션 기획안에서 블로그, SNS, 홈페이지, 앱용 문안과 소재 초안을 동시에 만든다.
- 단순 문구 생성이 아니라 병원별 입력 자산을 반영해 결과물 차별화를 만든다.
- 입력값: 프로모션 가격, 정상가, 시술 원가, 예상 모집객 수, 업셀 전환율, 평균 객단가, 재방문율

## Policy Notes

- 의료광고 심의와 표현 제한 검토가 반드시 포함되어야 한다.
- 플랫폼별 정책 차이에 따라 문안 룰셋을 분리 관리해야 한다.
- 초기에는 병원 실데이터 부족으로 일반 모델 기반 추정치가 일부 포함될 수 있다.
- AI가 만든 초안은 항상 사람 검수와 최종 승인 단계를 거쳐야 한다.

## Stack

- Python 3.11+
- FastAPI
- Uvicorn
- Pydantic

## Structure

```text
app/
├── api/
├── core/
├── models/
├── repositories/
├── schemas/
├── services/
└── main.py
```

## Conventions

- Router, Service, Repository 책임을 분리합니다.
- 입력과 출력은 스키마로 검증합니다.
- 정책과 상태 전이는 서비스 계층에서 일관되게 처리합니다.
- bootstrap payload도 API 계약으로 노출합니다.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Test

```bash
pytest
```

## Environment

- `.env.example` 제공
- `APP_NAME`, `APP_ENV`, `DATABASE_URL`, `EXTERNAL_API_KEY` 분리

## Review Points

- API 계약과 서비스 책임이 README에 드러나는가
- 스키마, 서비스, 저장소 계층이 구조와 대응되는가
- 실행과 테스트 방법이 누락되지 않았는가
