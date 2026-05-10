from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.api.deps import get_session
from app.core.auth import require_min_role, require_roles
from app.repositories.archive_repository import ArchiveRepository
from app.schemas.contracts import (
    ArchiveMetricsUpdate,
    AssetConnectorResponse,
    AuditLogEntry,
    BrandAiWriteRequest,
    BrandAiWriteResponse,
    BrandProfile,
    CampaignRoiResponse,
    ChannelPerformanceResponse,
    Clinic,
    ContentRequest,
    ExplainabilityPayload,
    GenerationResponse,
    HealthResponse,
    Lead,
    MedlawCheckRequest,
    MedlawCheckResponse,
    Procedure,
    ProcedureCatalogResponse,
    Promotion,
    PublishedContent,
    ReviewItem,
    ReviewSnapshotResponse,
    ReviewStatusUpdate,
    SalesSignal,
    ShortsRequest,
    ShortsResponse,
    SimulationInput,
    SimulationResponse,
)
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.brand_service import BrandService
from app.services.content_service import ContentService
from app.services.medlaw_service import MedlawService
from app.services.planning_service import PlanningService
from app.services.signal_service import SignalService

router = APIRouter()
analytics_service = AnalyticsService()
audit_service = AuditService()
brand_service = BrandService()
content_service = ContentService()
medlaw_service = MedlawService()
planning_service = PlanningService()
signal_service = SignalService()
archive_repository = ArchiveRepository()

ASSET_CONNECTORS = [
    AssetConnectorResponse(id="naver_place", name="네이버 플레이스", status="connected", last_synced_at="2026-05-10T09:00:00"),
    AssetConnectorResponse(id="kakao_channel", name="카카오톡 채널", status="pending", last_synced_at=None),
    AssetConnectorResponse(id="instagram", name="인스타그램", status="connected", last_synced_at="2026-05-09T18:30:00"),
    AssetConnectorResponse(id="emr", name="EMR", status="pending", last_synced_at=None),
]

REVIEW_SNAPSHOTS = [
    ReviewSnapshotResponse(platform="naver", rating=4.7, count=128, delta=6),
    ReviewSnapshotResponse(platform="kakao", rating=4.5, count=84, delta=2),
    ReviewSnapshotResponse(platform="google", rating=4.6, count=42, delta=-1),
]


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


@router.get("/api/procedures/catalog", response_model=list[ProcedureCatalogResponse])
def list_procedure_catalog(
    db: Session = Depends(get_session)
) -> list[ProcedureCatalogResponse]:
    return planning_service.get_procedure_catalog(db)


# ── Simulation ────────────────────────────────────────────────────────────────

@router.post("/api/simulation/preview", response_model=SimulationResponse)
def simulate(
    payload: SimulationInput,
    db: Session = Depends(get_session),
    actor_role: str = Depends(require_min_role("staff")),
    request: Request = None,
) -> SimulationResponse:
    try:
        result = planning_service.simulate(db, payload)
        audit_service.record(
            db,
            domain="simulation",
            event_type="sim_run",
            actor_role=actor_role,
            route=str(request.url.path) if request else "/api/simulation/preview",
            message=f"시뮬레이션 실행: {payload.procedure_id or payload.procedure}",
            metadata={"trace_id": result.trace_id},
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Content Generation ────────────────────────────────────────────────────────

@router.post("/api/content/generate", response_model=GenerationResponse)
async def generate_content(
    payload: ContentRequest,
    db: Session = Depends(get_session),
    actor_role: str = Depends(require_min_role("staff")),
    request: Request = None,
) -> GenerationResponse:
    clinic = brand_service.get(db)
    if not clinic:
        raise HTTPException(status_code=422, detail="콘텐츠 생성 전 병원 프로필을 먼저 저장하세요.")
    result = await content_service.generate(db, clinic, payload)
    audit_service.record(
        db,
        domain="content",
        event_type="draft_generated",
        actor_role=actor_role,
        route=str(request.url.path) if request else "/api/content/generate",
        message=f"{payload.event_name} 초안 생성",
        metadata={"trace_id": result.trace_id, "channels": list(result.channels.keys())},
    )
    return result


@router.post("/api/content/shorts", response_model=ShortsResponse)
def generate_shorts(payload: ShortsRequest) -> ShortsResponse:
    return content_service.generate_shorts(payload)


# ── CRM / Lead ────────────────────────────────────────────────────────────────

@router.post("/api/leads", response_model=Lead, status_code=201)
def create_lead(
    payload: Lead,
    db: Session = Depends(get_session),
    actor_role: str = Depends(require_min_role("staff")),
) -> Lead:
    payload.customer_name = _mask_name(payload.customer_name)
    payload.phone_enc = _mask_phone(payload.phone_enc)
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
    payload: ReviewStatusUpdate,
    db: Session = Depends(get_session),
    actor_role: str = Depends(require_min_role("staff")),
    request: Request = None,
) -> ReviewItem:
    item = db.get(ReviewItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="검토 항목을 찾을 수 없습니다.")
    item.status = payload.status
    db.add(item)
    db.commit()
    db.refresh(item)
    audit_service.record(
        db,
        domain="review",
        event_type="review_approved" if payload.status == "approved" else "review_updated",
        actor_role=actor_role,
        route=str(request.url.path) if request else f"/api/review/{item_id}",
        message=f"{item.step} 상태 변경: {payload.status}",
        metadata={"notes": payload.notes},
    )
    return item


# ── Brand / Clinic ────────────────────────────────────────────────────────────

@router.post("/api/brand", response_model=Clinic, status_code=201)
def save_clinic_profile(
    payload: BrandProfile,
    db: Session = Depends(get_session),
    actor_role: str = Depends(require_min_role("marketing_manager")),
    request: Request = None,
) -> Clinic:
    clinic, created = brand_service.upsert(db, payload)
    audit_service.record(
        db,
        domain="brand",
        event_type="brand_saved",
        actor_role=actor_role,
        route=str(request.url.path) if request else "/api/brand",
        message="브랜드 프로필 생성" if created else "브랜드 프로필 수정",
    )
    return clinic


@router.get("/api/brand", response_model=Clinic)
def get_clinic_profile(
    db: Session = Depends(get_session)
) -> Clinic:
    clinic = brand_service.get(db)
    if not clinic:
        raise HTTPException(status_code=404, detail="병원 프로필이 없습니다.")
    return clinic


@router.post("/api/brand/ai-write", response_model=BrandAiWriteResponse)
def write_brand_field(
    payload: BrandAiWriteRequest,
    db: Session = Depends(get_session),
    actor_role: str = Depends(require_min_role("staff")),
) -> BrandAiWriteResponse:
    clinic = brand_service.get(db)
    if not clinic:
        raise HTTPException(status_code=422, detail="AI 초안 생성 전 병원 프로필을 먼저 저장하세요.")
    draft, trace_id = content_service.write_brand_draft(db, clinic, payload.field)
    return BrandAiWriteResponse(field=payload.field, draft=draft, trace_id=trace_id)


# ── Asset Collection ─────────────────────────────────────────────────────────

@router.get("/api/assets/connectors", response_model=list[AssetConnectorResponse])
def list_asset_connectors() -> list[AssetConnectorResponse]:
    return ASSET_CONNECTORS


@router.get("/api/assets/reviews", response_model=list[ReviewSnapshotResponse])
def list_review_snapshots() -> list[ReviewSnapshotResponse]:
    return REVIEW_SNAPSHOTS


@router.get("/api/assets/promotions", response_model=list[Promotion])
def list_asset_promotions(db: Session = Depends(get_session)) -> list[Promotion]:
    return db.exec(select(Promotion)).all()


# ── Medical Advertising ──────────────────────────────────────────────────────

@router.post("/api/medlaw/check", response_model=MedlawCheckResponse)
def check_medlaw(payload: MedlawCheckRequest) -> MedlawCheckResponse:
    return MedlawCheckResponse(violations=medlaw_service.check(payload.text))


# ── Published Archive ────────────────────────────────────────────────────────

@router.get("/api/archive", response_model=list[PublishedContent])
def list_archive(
    channel: str | None = None,
    event: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_session),
) -> list[PublishedContent]:
    return archive_repository.filter_published(db, channel=channel, event=event, status=status)


@router.get("/api/archive/{archive_id}", response_model=PublishedContent)
def get_archive_item(archive_id: int, db: Session = Depends(get_session)) -> PublishedContent:
    item = db.get(PublishedContent, archive_id)
    if not item:
        raise HTTPException(status_code=404, detail="발행 콘텐츠를 찾을 수 없습니다.")
    return item


@router.patch("/api/archive/{archive_id}/metrics", response_model=PublishedContent)
def update_archive_metrics(
    archive_id: int,
    payload: ArchiveMetricsUpdate,
    db: Session = Depends(get_session),
) -> PublishedContent:
    try:
        return analytics_service.update_metrics(db, archive_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Audit / Signals / Explainability / Analytics ─────────────────────────────

@router.get("/api/audit", response_model=list[AuditLogEntry])
def list_audit_logs(
    domain: str | None = None,
    event_type: str | None = None,
    actor_role: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    role: str = Depends(require_roles("owner")),
    db: Session = Depends(get_session),
) -> list[AuditLogEntry]:
    statement = select(AuditLogEntry)
    if domain:
        statement = statement.where(AuditLogEntry.domain == domain)
    if event_type:
        statement = statement.where(AuditLogEntry.event_type == event_type)
    if actor_role:
        statement = statement.where(AuditLogEntry.actor_role == actor_role)
    if date_from:
        statement = statement.where(AuditLogEntry.timestamp >= date_from)
    if date_to:
        statement = statement.where(AuditLogEntry.timestamp <= date_to)
    return db.exec(statement.order_by(AuditLogEntry.timestamp.desc())).all()


@router.get("/api/signals", response_model=list[SalesSignal])
def list_signals(
    priority: str | None = None,
    domain: str | None = None,
    refresh: bool = False,
    db: Session = Depends(get_session),
) -> list[SalesSignal]:
    if refresh:
        signal_service.refresh(db)
    statement = select(SalesSignal)
    if priority:
        statement = statement.where(SalesSignal.priority == priority)
    if domain:
        statement = statement.where(SalesSignal.domain == domain)
    return db.exec(statement.order_by(SalesSignal.priority)).all()


@router.get("/api/explain/{trace_id}", response_model=ExplainabilityPayload)
def get_explainability(trace_id: str, db: Session = Depends(get_session)) -> ExplainabilityPayload:
    payload = db.get(ExplainabilityPayload, trace_id)
    if not payload:
        raise HTTPException(status_code=404, detail="설명성 페이로드를 찾을 수 없습니다.")
    return payload


@router.get("/api/analytics/campaign", response_model=list[CampaignRoiResponse])
def campaign_roi(db: Session = Depends(get_session)) -> list[CampaignRoiResponse]:
    return analytics_service.campaign_roi(db)


@router.get("/api/analytics/channels", response_model=list[ChannelPerformanceResponse])
def channel_performance(db: Session = Depends(get_session)) -> list[ChannelPerformanceResponse]:
    return analytics_service.channel_performance(db)


def _mask_name(name: str) -> str:
    if len(name) <= 1:
        return "*"
    if len(name) == 2:
        return f"{name[0]}*"
    return f"{name[0]}*{name[-1]}"


def _mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 4:
        return "****"
    return f"{digits[:3]}-****-{digits[-4:]}"