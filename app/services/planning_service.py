from uuid import uuid4

from sqlmodel import Session, select
from app.schemas.contracts import (
    ExplainabilityPayload,
    Procedure,
    ProcedureCatalogResponse,
    ProcedureCaution,
    ProcedureFaq,
    ProcedureFaqResponse,
    ProcedureRecommendation,
    ProcedureVariant,
    ProcedureVariantResponse,
    SimulationInput,
    SimulationResponse,
)


class PlanningService:
    def get_procedures(self, db: Session) -> list[Procedure]:
        return db.exec(select(Procedure)).all()

    def get_procedure_catalog(self, db: Session) -> list[ProcedureCatalogResponse]:
        """활성 시술의 추천 대상·주의사항·FAQ·옵션까지 한 번에 조합해 반환."""
        procedures = db.exec(select(Procedure).where(Procedure.is_active == True)).all()
        recommendations = db.exec(select(ProcedureRecommendation)).all()
        cautions = db.exec(select(ProcedureCaution)).all()
        faqs = db.exec(select(ProcedureFaq)).all()
        variants = db.exec(select(ProcedureVariant).where(ProcedureVariant.is_active == True)).all()

        rec_map: dict[str, list[str]] = {}
        for item in recommendations:
            rec_map.setdefault(item.procedure_id, []).append(item.content)

        cau_map: dict[str, list[str]] = {}
        for item in cautions:
            cau_map.setdefault(item.procedure_id, []).append(item.content)

        faq_map: dict[str, list[ProcedureFaqResponse]] = {}
        for item in faqs:
            faq_map.setdefault(item.procedure_id, []).append(
                ProcedureFaqResponse(question=item.question, answer=item.answer)
            )

        var_map: dict[str, list[ProcedureVariantResponse]] = {}
        for item in variants:
            var_map.setdefault(item.procedure_id, []).append(
                ProcedureVariantResponse(
                    id=item.id,
                    name=item.name,
                    option_label=item.option_label,
                    list_price=item.list_price,
                    event_price=item.event_price,
                    tax_note=item.tax_note,
                    unit_type=item.unit_type,
                    unit_value=item.unit_value,
                    session_count=item.session_count,
                    is_active=item.is_active,
                    is_featured=item.is_featured,
                )
            )

        return [
            ProcedureCatalogResponse(
                id=p.id,
                name=p.name,
                category=p.category,
                brand=p.brand,
                summary=p.summary,
                hero_title=p.hero_title,
                hero_description=p.hero_description,
                hashtags=p.hashtags,
                target_areas=p.target_areas,
                procedure_time_text=p.procedure_time_text,
                anesthesia_text=p.anesthesia_text,
                recovery_text=p.recovery_text,
                duration_text=p.duration_text,
                recommended_cycle_text=p.recommended_cycle_text,
                operation_role=p.operation_role,
                marketing_point=p.marketing_point,
                margin_strategy=p.margin_strategy,
                essential_info=p.essential_info,
                consumable_cost=p.consumable_cost,
                labor_cost=p.labor_cost,
                list_price=p.list_price,
                min_price_limit=p.min_price_limit,
                is_active=p.is_active,
                is_featured=p.is_featured,
                recommendations=rec_map.get(p.id, []),
                cautions=cau_map.get(p.id, []),
                faqs=faq_map.get(p.id, []),
                variants=var_map.get(p.id, []),
            )
            for p in procedures
        ]

    def simulate(self, db: Session, payload: SimulationInput) -> SimulationResponse:
        """
        로직: 순이익 = (예상매출 + 업셀링) - (소모품원가 + 인건비 + 광고비)
        BEP = 광고비 / (1인당 매출 - 1인당 변동비)
        """
        procedure_id = payload.procedure_id
        procedure = db.get(Procedure, procedure_id) if procedure_id else None
        if not procedure and payload.procedure:
            procedure = db.exec(select(Procedure).where(Procedure.name == payload.procedure)).first()
        if not procedure:
            target = payload.procedure_id or payload.procedure or ""
            raise ValueError(f"시술 정보를 찾을 수 없습니다: {target}")

        expected_patients = payload.expected_leads * (payload.conversion_rate / 100)
        total_revenue = expected_patients * (payload.promo_price + payload.upsell_estimate)

        consumable_cost = payload.consumable_cost or procedure.consumable_cost
        labor_cost = payload.labor_cost or procedure.labor_cost
        variable_cost_per_patient = consumable_cost + labor_cost
        total_cost = expected_patients * variable_cost_per_patient + payload.ad_spend
        projected_profit = total_revenue - total_cost

        margin_per_patient = (payload.promo_price + payload.upsell_estimate) - variable_cost_per_patient
        if margin_per_patient > 0:
            break_even_patients: float | None = round(payload.ad_spend / margin_per_patient, 1)
        else:
            # 1인당 공헌이익 0 이하 → 광고비 회수 불가, JSON 직렬화 불가한 inf 대신 None
            break_even_patients = None

        trace_id = f"sim-{uuid4()}"
        db.add(
            ExplainabilityPayload(
                trace_id=trace_id,
                evidence=[
                    {"source": "Procedure", "procedure_id": procedure.id, "sample_count": 1},
                    {"source": "SimulationInput", "promo_period_weeks": payload.promo_period_weeks},
                ],
                actions=[
                    "손익분기 환자 수와 예상 모집객을 비교하세요.",
                    "콘텐츠 생성 전 이벤트 가격과 기간을 검토하세요.",
                ],
                follow_up_questions=[
                    "동일 시술의 과거 전환율 평균이 있나요?",
                    "업셀링 매출 가정은 보수적으로 잡았나요?",
                ],
            )
        )
        db.commit()

        return SimulationResponse(
            expected_patients=round(expected_patients, 1),
            expected_revenue=round(total_revenue),
            expected_cost=round(total_cost),
            projected_profit=round(projected_profit),
            break_even_patients=break_even_patients,
            breakeven_reached=break_even_patients is not None and expected_patients >= break_even_patients,
            promo_period_weeks=payload.promo_period_weeks,
            trace_id=trace_id,
        )