from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict
from sqlmodel import SQLModel, Field, Relationship, JSON, Column


# ── Base / Mixins ─────────────────────────────────────────────────────────────

class TimestampMixin(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Clinic (Brand Profile) ────────────────────────────────────────────────────

class Clinic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    clinic_type: str = Field(default="PREMIUM") # FACTORY | PREMIUM
    target_audience: str
    doctor_philosophy: str
    signature_procedures: List[str] = Field(sa_column=Column(JSON))
    brand_tone: List[str] = Field(sa_column=Column(JSON))
    banned_terms: List[str] = Field(default=[], sa_column=Column(JSON))


# ── Procedure Master ──────────────────────────────────────────────────────────

class Procedure(SQLModel, table=True):
    id: str = Field(primary_key=True) # e.g. "proc_ult_600"
    name: str
    category: str
    brand: Optional[str] = None
    consumable_cost: float # 팁값, 약제 원가
    labor_cost: float # 인건비 추정
    list_price: float # 정가
    min_price_limit: float # 마진 하한선


# ── Promotion / Simulation ────────────────────────────────────────────────────

class Promotion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    procedure_id: str = Field(foreign_key="procedure.id")
    promo_price: float
    expected_leads: int
    conversion_rate: float
    staff_incentive: float
    ad_spend: float
    upsell_estimate: float


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
    promotion_id: int = Field(foreign_key="promotion.id")
    event_name: str
    core_message: str
    channels_content: Dict[str, Dict] = Field(default={}, sa_column=Column(JSON))
    review_notes: List[str] = Field(default=[], sa_column=Column(JSON))


# ── Review / Approval ─────────────────────────────────────────────────────────

class ReviewItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    step: str
    assignee: str
    description: str
    status: str = Field(default="pending") # pending | in_review | approved | rejected


# ── API Response Schemas (Non-Table) ──────────────────────────────────────────

class HealthResponse(SQLModel):
    status: str

class SimulationResponse(SQLModel):
    expected_patients: float
    expected_revenue: float
    expected_cost: float
    projected_profit: float
    break_even_patients: float
    breakeven_reached: bool


# ── AI Content Request/Response (Non-Table) ───────────────────────────────────

class ContentRequest(SQLModel):
    event_name: str
    event_start: str
    event_end: str
    core_message: str
    highlights: List[str] = []
    channels: List[str] = []


class DraftContent(SQLModel):
    headline: str
    body: str
    cta: str


class GenerationResponse(SQLModel):
    event_name: str
    channels: Dict[str, DraftContent]
    review_notes: List[str]
