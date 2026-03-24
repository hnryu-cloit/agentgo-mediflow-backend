from pydantic import BaseModel, Field


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str


# ── Bootstrap ─────────────────────────────────────────────────────────────────

class BootstrapResponse(BaseModel):
    product: str
    summary: str
    users: list[str]
    goals: list[str]
    policies: list[str]
    features: dict[str, list[dict[str, str]]]


# ── Brand Profile ─────────────────────────────────────────────────────────────

class BrandProfile(BaseModel):
    hospital_name: str = Field(min_length=1, max_length=50)
    target_audience: str = Field(min_length=1, max_length=100)
    doctor_philosophy: str = Field(min_length=1, max_length=300)
    signature_procedures: list[str] = Field(min_length=1)
    brand_tone: list[str] = Field(min_length=1)
    banned_terms: list[str] = []


# ── Simulation ────────────────────────────────────────────────────────────────

class SimulationInput(BaseModel):
    promotion_name: str
    promo_price: float = Field(gt=0)
    list_price: float = Field(gt=0)
    procedure_cost: float = Field(ge=0)
    expected_leads: int = Field(ge=0)
    close_rate: float = Field(ge=0, le=1)
    upsell_rate: float = Field(ge=0, le=1)
    average_upsell_revenue: float = Field(ge=0)
    repeat_visit_rate: float = Field(ge=0, le=1)
    repeat_visit_revenue: float = Field(ge=0)
    ad_budget: float = Field(ge=0)


class SimulationResponse(BaseModel):
    promotion_name: str
    expected_patients: float
    expected_revenue: float
    expected_cost: float
    projected_profit: float
    break_even_patients: float
    allowed_ad_budget: float
    breakeven_reached: bool


# ── Content Generation ────────────────────────────────────────────────────────

class ContentRequest(BaseModel):
    event_name: str = Field(min_length=1)
    event_start: str
    event_end: str
    core_message: str = Field(min_length=1)
    highlights: list[str] = []
    channels: list[str] = Field(min_length=1)
    additional_notes: str = ""


class DraftContent(BaseModel):
    headline: str
    body: str
    cta: str


class GenerationResponse(BaseModel):
    event_name: str
    channels: dict[str, DraftContent]
    review_notes: list[str]


# ── Review / Approval ─────────────────────────────────────────────────────────

class ReviewChecklistItem(BaseModel):
    stage: str
    owner: str
    status: str
    notes: str


class ReviewStatusUpdate(BaseModel):
    status: str = Field(pattern="^(pending|in_review|approved|rejected)$")
    notes: str = ""


# ── Channel Draft (bootstrap) ─────────────────────────────────────────────────

class ChannelDraft(BaseModel):
    format: str
    headline: str
    body: str
    cta: str