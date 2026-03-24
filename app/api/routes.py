from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import (
    get_bootstrap_repository,
    get_brand_repository,
    get_content_service,
    get_review_repository,
)
from app.repositories.bootstrap_repository import BootstrapRepository
from app.repositories.brand_repository import BrandRepository
from app.repositories.review_repository import ReviewRepository
from app.schemas.contracts import (
    BrandProfile,
    BootstrapResponse,
    ChannelDraft,
    ContentRequest,
    GenerationResponse,
    HealthResponse,
    ReviewChecklistItem,
    ReviewStatusUpdate,
    SimulationInput,
    SimulationResponse,
)
from app.services.content_service import ContentService
from app.services.planning_service import PlanningService

router = APIRouter()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


# ── Bootstrap ─────────────────────────────────────────────────────────────────

@router.get("/api/bootstrap", response_model=BootstrapResponse)
def bootstrap(
    repo: BootstrapRepository = Depends(get_bootstrap_repository),
) -> BootstrapResponse:
    return BootstrapResponse(**repo.get_bootstrap())


# ── Brand Profile ─────────────────────────────────────────────────────────────

@router.post("/api/brand", response_model=BrandProfile, status_code=201)
def save_brand_profile(
    payload: BrandProfile,
    repo: BrandRepository = Depends(get_brand_repository),
) -> BrandProfile:
    return repo.save(payload)


@router.get("/api/brand", response_model=BrandProfile)
def get_brand_profile(
    repo: BrandRepository = Depends(get_brand_repository),
) -> BrandProfile:
    profile = repo.get()
    if profile is None:
        raise HTTPException(status_code=404, detail="브랜드 프로필이 설정되지 않았습니다.")
    return profile


# ── Simulation ────────────────────────────────────────────────────────────────

@router.post("/api/simulation/preview", response_model=SimulationResponse)
def simulate(
    payload: SimulationInput,
    repo: BootstrapRepository = Depends(get_bootstrap_repository),
) -> SimulationResponse:
    service = PlanningService(repository=repo)
    return service.simulate(payload)


# ── Content Generation ────────────────────────────────────────────────────────

@router.post("/api/content/generate", response_model=GenerationResponse)
def generate_content(
    payload: ContentRequest,
    brand_repo: BrandRepository = Depends(get_brand_repository),
    content_svc: ContentService = Depends(get_content_service),
) -> GenerationResponse:
    brand = brand_repo.get()
    if brand is None:
        raise HTTPException(status_code=422, detail="콘텐츠 생성 전 브랜드 프로필을 먼저 저장하세요.")
    return content_svc.generate(brand, payload)


# ── Review / Approval ─────────────────────────────────────────────────────────

@router.get("/api/review/checklist", response_model=list[ReviewChecklistItem])
def review_checklist(
    repo: ReviewRepository = Depends(get_review_repository),
) -> list[ReviewChecklistItem]:
    return repo.get_all()


@router.patch("/api/review/{stage}", response_model=ReviewChecklistItem)
def update_review_status(
    stage: str,
    payload: ReviewStatusUpdate,
    repo: ReviewRepository = Depends(get_review_repository),
) -> ReviewChecklistItem:
    item = repo.update_status(stage=stage, status=payload.status, notes=payload.notes)
    if item is None:
        raise HTTPException(status_code=404, detail=f"검토 항목을 찾을 수 없습니다: {stage}")
    return item


# ── Channel Drafts (bootstrap static) ────────────────────────────────────────

@router.get("/api/channels/drafts", response_model=dict[str, ChannelDraft])
def channel_drafts(
    repo: BootstrapRepository = Depends(get_bootstrap_repository),
) -> dict[str, ChannelDraft]:
    return {
        key: ChannelDraft(**value)
        for key, value in repo.get_bootstrap().get("channelDrafts", {}).items()
    }