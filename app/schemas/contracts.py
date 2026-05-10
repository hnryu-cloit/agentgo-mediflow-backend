from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional
from pydantic import field_validator
from sqlmodel import SQLModel, Field, JSON, Column


# ── Clinic (Brand Profile) ────────────────────────────────────────────────────

class Clinic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    clinic_type: str = Field(default="PREMIUM") # FACTORY | PREMIUM
    target_audience: str
    doctor_philosophy: str
    head_office_message: str = ""
    branch_context: str = ""
    signature_procedures: List[str] = Field(sa_column=Column(JSON))
    brand_tone: List[str] = Field(sa_column=Column(JSON))
    banned_terms: List[str] = Field(default=[], sa_column=Column(JSON))


# ── Procedure Master ──────────────────────────────────────────────────────────

class Procedure(SQLModel, table=True):
    id: str = Field(primary_key=True) # e.g. "proc_ult_600"
    name: str
    category: str
    brand: Optional[str] = None
    summary: str = ""
    hero_title: str = ""
    hero_description: str = ""
    hashtags: List[str] = Field(default=[], sa_column=Column(JSON))
    target_areas: List[str] = Field(default=[], sa_column=Column(JSON))
    procedure_time_text: str = ""
    anesthesia_text: str = ""
    recovery_text: str = ""
    duration_text: str = ""
    recommended_cycle_text: str = ""
    operation_role: str = ""
    marketing_point: str = ""
    margin_strategy: str = ""
    essential_info: List[str] = Field(default=[], sa_column=Column(JSON))
    is_active: bool = True
    is_featured: bool = False
    consumable_cost: float # 팁값, 약제 원가
    labor_cost: float # 인건비 추정
    list_price: float # 정가
    min_price_limit: float # 마진 하한선


class ProcedureVariant(SQLModel, table=True):
    id: str = Field(primary_key=True)
    procedure_id: str = Field(foreign_key="procedure.id", index=True)
    name: str
    option_label: str = ""
    list_price: float
    event_price: float
    tax_note: str = "부가세 10% 별도"
    unit_type: str = ""
    unit_value: str = ""
    session_count: int = 1
    is_active: bool = True
    is_featured: bool = False


class ProcedureRecommendation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    procedure_id: str = Field(foreign_key="procedure.id", index=True)
    sort_order: int = 0
    content: str


class ProcedureFaq(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    procedure_id: str = Field(foreign_key="procedure.id", index=True)
    sort_order: int = 0
    question: str
    answer: str


class ProcedureCaution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    procedure_id: str = Field(foreign_key="procedure.id", index=True)
    sort_order: int = 0
    content: str


# ── Promotion / Simulation ────────────────────────────────────────────────────

class Promotion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    procedure_id: str = Field(foreign_key="procedure.id")
    promo_price: float
    expected_leads: int
    conversion_rate: float
    ad_spend: float
    upsell_estimate: float
    consumable_cost: float = 0
    labor_cost: float = 0
    promo_period_weeks: int = 4


# ── CRM / Lead ────────────────────────────────────────────────────────────────

class Lead(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_name: str # 김*수 (마스킹)
    phone_enc: str # 암호화된 연락처
    source: str # FB, IG, BLOG, APP
    status: str = Field(default="APPLIED") # APPLIED | VISITED | NO_SHOW
    promotion_id: Optional[int] = Field(default=None, foreign_key="promotion.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── AI Content / Campaign ─────────────────────────────────────────────────────

class Campaign(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    promotion_id: Optional[int] = Field(default=None, foreign_key="promotion.id")
    event_name: str
    core_message: str
    channels_content: Dict[str, Dict] = Field(default={}, sa_column=Column(JSON))
    review_notes: List[str] = Field(default=[], sa_column=Column(JSON))


class PublishedContent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int = Field(foreign_key="campaign.id", index=True)
    channel: str = Field(index=True)
    label: str = ""
    funnel: str = ""
    headline: str
    body: str
    cta: str
    published_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default="published", index=True) # published | archived
    views: int = 0
    clicks: int = 0
    ctr: float = 0
    tag: str = ""


# ── Review / Approval ─────────────────────────────────────────────────────────

class ReviewItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    step: str
    assignee: str
    description: str
    status: str = Field(default="pending") # pending | in_review | approved | rejected


class AuditLogEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    domain: str = Field(index=True)
    event_type: str = Field(index=True)
    actor_role: str = Field(default="viewer", index=True)
    route: str = ""
    outcome: str = "success"
    message: str = ""
    audit_metadata: Dict = Field(default={}, sa_column=Column(JSON))


class SalesSignal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(default="marketing", index=True)
    title: str
    metric: str
    value: float
    change: float
    trend: str
    priority: str = Field(default="medium", index=True) # high | medium | low
    insight: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExplainabilityPayload(SQLModel, table=True):
    trace_id: str = Field(primary_key=True)
    status: str = "ready" # pending | ready | failed
    evidence: List[Dict] = Field(default=[], sa_column=Column(JSON))
    actions: List[str] = Field(default=[], sa_column=Column(JSON))
    follow_up_questions: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── API Response Schemas (Non-Table) ──────────────────────────────────────────

class HealthResponse(SQLModel):
    status: str


class BrandProfile(SQLModel):
    hospital_name: str
    target_audience: str
    doctor_philosophy: str
    signature_procedures: List[str]
    brand_tone: List[str]
    banned_terms: List[str] = []
    clinic_type: str = "PREMIUM"
    head_office_message: str = ""
    branch_context: str = ""

    @field_validator("hospital_name", "target_audience", "doctor_philosophy")
    @classmethod
    def required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("필수 텍스트를 입력하세요.")
        return value

    @field_validator("signature_procedures")
    @classmethod
    def required_list(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("시그니처 시술을 1개 이상 입력하세요.")
        return value


class SimulationInput(SQLModel):
    procedure_id: Optional[str] = None
    procedure: Optional[str] = None
    promo_price: float
    expected_leads: int
    conversion_rate: float
    ad_spend: float
    upsell_estimate: float
    consumable_cost: float = 0
    labor_cost: float = 0
    promo_period_weeks: int = 4

    @field_validator("promo_price", "expected_leads", "conversion_rate", "ad_spend", "upsell_estimate", "consumable_cost", "labor_cost")
    @classmethod
    def non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("0 이상의 값을 입력하세요.")
        return value


class SimulationResponse(SQLModel):
    expected_patients: float
    expected_revenue: float
    expected_cost: float
    projected_profit: float
    # 1인당 공헌이익이 0 이하이면 광고비 회수 불가 → None 반환
    break_even_patients: Optional[float] = None
    breakeven_reached: bool
    promo_period_weeks: int = 4
    trace_id: str = ""


# ── AI Content Request/Response (Non-Table) ───────────────────────────────────

PublicContentChannelId = Literal[
    "ig_feed",
    "ig_story",
    "seo_blog",
    "blog",
    "web",
    "place",
    "kakao",
    "email",
    "app",
]
FunnelStageId = Literal["awareness", "trust", "convert", "conversion"]


class ContentRequest(SQLModel):
    event_name: str
    event_start: str
    event_end: str
    core_message: str
    highlights: List[str] = []
    channels: List[PublicContentChannelId] = []
    funnel_stage: FunnelStageId = "convert"
    promo_period_weeks: int = 4

    @field_validator("event_name", "core_message")
    @classmethod
    def content_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("필수 텍스트를 입력하세요.")
        return value

    @field_validator("channels")
    @classmethod
    def content_required_channels(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("채널을 1개 이상 선택하세요.")
        return value


class DraftContent(SQLModel):
    channel_id: Optional[PublicContentChannelId] = None
    funnel: Optional[Literal["awareness", "trust", "convert"]] = None
    label: str = ""
    headline: str
    body: str
    cta: str
    note: str = ""
    image_prompt: Optional[str] = None


class ConsistencyCheck(SQLModel):
    key: str
    label: str
    status: Literal["pass", "warn", "fail"]
    message: str
    detail: str = ""
    channels: List[PublicContentChannelId] = []


class GenerationResponse(SQLModel):
    event_name: str
    channels: Dict[str, DraftContent]
    review_notes: List[str]
    consistency_checks: List[ConsistencyCheck] = []
    trace_id: str = ""


class BrandAiWriteRequest(SQLModel):
    field: Literal["target_audience", "doctor_philosophy"]


class BrandAiWriteResponse(SQLModel):
    field: str
    draft: str
    trace_id: str


class ReviewStatusUpdate(SQLModel):
    status: Literal["pending", "in_review", "approved", "rejected"]
    notes: str = ""


class ReviewChecklistItem(SQLModel):
    stage: str
    owner: str
    status: Literal["pending", "in_review", "approved", "rejected"] = "pending"
    notes: str = ""


class MedlawCheckRequest(SQLModel):
    text: str


class MedlawViolation(SQLModel):
    type: str
    keyword: str
    article: str
    message: str
    severity: Literal["low", "medium", "high"] = "medium"


class MedlawCheckResponse(SQLModel):
    violations: List[MedlawViolation]


class ArchiveMetricsUpdate(SQLModel):
    views: int
    clicks: int
    ctr: Optional[float] = None


class ShortsRequest(SQLModel):
    template_id: str
    source_channel: str = "blog"
    longform_draft: DraftContent


class ShortsScene(SQLModel):
    order: int
    duration_sec: int
    script: str
    visual_guide: str


class ShortsResponse(SQLModel):
    template_id: str
    scenes: List[ShortsScene]
    trace_id: str


class ProcedureVariantResponse(SQLModel):
    id: str
    name: str
    option_label: str
    list_price: float
    event_price: float
    tax_note: str
    unit_type: str
    unit_value: str
    session_count: int
    is_active: bool
    is_featured: bool


class ProcedureFaqResponse(SQLModel):
    question: str
    answer: str


class ProcedureCatalogResponse(SQLModel):
    id: str
    name: str
    category: str
    brand: Optional[str] = None
    summary: str
    hero_title: str
    hero_description: str
    hashtags: List[str]
    target_areas: List[str]
    procedure_time_text: str
    anesthesia_text: str
    recovery_text: str
    duration_text: str
    recommended_cycle_text: str
    operation_role: str
    marketing_point: str
    margin_strategy: str
    essential_info: List[str]
    consumable_cost: float
    labor_cost: float
    list_price: float
    min_price_limit: float
    is_active: bool
    is_featured: bool
    recommendations: List[str]
    cautions: List[str]
    faqs: List[ProcedureFaqResponse]
    variants: List[ProcedureVariantResponse]


# ── Analytics / Asset response schemas (response_model 지정용) ────────────────

class AssetConnectorResponse(SQLModel):
    id: str
    name: str
    status: str
    last_synced_at: Optional[str] = None


class ReviewSnapshotResponse(SQLModel):
    platform: str
    rating: float
    count: int
    delta: int


class CampaignRoiResponse(SQLModel):
    campaign_id: Optional[int] = None
    event_name: str
    views: int
    clicks: int
    ctr: float
    estimated_revenue: float
    ad_spend: float
    roi: float


class ChannelPerformanceResponse(SQLModel):
    channel: str
    views: int
    clicks: int
    published_count: int
    ctr: float
