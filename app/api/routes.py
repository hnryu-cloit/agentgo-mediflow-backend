from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.api.deps import get_session
from app.schemas.contracts import (
    Procedure,
    SimulationInput,
    SimulationResponse,
    HealthResponse,
    Clinic,
    ContentRequest,
    GenerationResponse,
    Lead,
    ReviewItem
)
from app.services.planning_service import PlanningService
from app.services.content_service import ContentService

router = APIRouter()
planning_service = PlanningService()
content_service = ContentService()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


# ── Procedures (Master Data) ──────────────────────────────────────────────────

@router.get("/api/procedures", response_model=list[Procedure])
def list_procedures(
    db: Session = Depends(get_session)
) -> list[Procedure]:
    return planning_service.get_procedures(db)


# ── Simulation ────────────────────────────────────────────────────────────────

@router.post("/api/simulation/preview", response_model=SimulationResponse)
def simulate(
    payload: SimulationInput,
    db: Session = Depends(get_session)
) -> SimulationResponse:
    try:
        return planning_service.simulate(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Content Generation ────────────────────────────────────────────────────────

@router.post("/api/content/generate", response_model=GenerationResponse)
async def generate_content(
    payload: ContentRequest,
    db: Session = Depends(get_session)
) -> GenerationResponse:
    """병원 프로필과 유형을 기반으로 AI 모듈 API를 호출하여 콘텐츠를 생성합니다."""
    clinic = db.exec(select(Clinic)).first()
    if not clinic:
        raise HTTPException(status_code=422, detail="콘텐츠 생성 전 병원 프로필을 먼저 저장하세요.")
    
    return await content_service.generate(clinic, payload)


# ── CRM / Lead ────────────────────────────────────────────────────────────────

@router.post("/api/leads", response_model=Lead, status_code=201)
def create_lead(
    payload: Lead,
    db: Session = Depends(get_session)
) -> Lead:
    db.add(payload)
    db.commit()
    db.refresh(payload)
    return payload


# ── Review / Approval ─────────────────────────────────────────────────────────

@router.get("/api/review/checklist", response_model=list[ReviewItem])
def list_review_checklist(
    db: Session = Depends(get_session)
) -> list[ReviewItem]:
    return db.exec(select(ReviewItem)).all()


@router.patch("/api/review/{item_id}", response_model=ReviewItem)
def update_review_status(
    item_id: int,
    status: str,
    db: Session = Depends(get_session)
) -> ReviewItem:
    item = db.get(ReviewItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="검토 항목을 찾을 수 없습니다.")
    item.status = status
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ── Brand / Clinic ────────────────────────────────────────────────────────────

@router.post("/api/brand", response_model=Clinic, status_code=201)
def save_clinic_profile(
    payload: Clinic,
    db: Session = Depends(get_session)
) -> Clinic:
    # 기존 프로필이 있으면 업데이트, 없으면 신규 생성
    existing = db.exec(select(Clinic)).first()
    if existing:
        for key, value in payload.model_dump(exclude={"id"}).items():
            setattr(existing, key, value)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing
    
    db.add(payload)
    db.commit()
    db.refresh(payload)
    return payload


@router.get("/api/brand", response_model=Clinic)
def get_clinic_profile(
    db: Session = Depends(get_session)
) -> Clinic:
    clinic = db.exec(select(Clinic)).first()
    if not clinic:
        raise HTTPException(status_code=404, detail="병원 프로필이 없습니다.")
    return clinic
