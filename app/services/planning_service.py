from sqlmodel import Session, select
from app.schemas.contracts import Procedure, SimulationInput, SimulationResponse


class PlanningService:
    def get_procedures(self, db: Session) -> list[Procedure]:
        """DB에서 전체 시술 마스터 리스트를 조회합니다."""
        statement = select(Procedure)
        return db.exec(statement).all()

    def simulate(self, db: Session, payload: SimulationInput) -> SimulationResponse:
        """
        DB의 시술 원가 데이터를 기반으로 정교한 수익 시뮬레이션을 수행합니다.
        로직: 순이익 = (예상매출 + 업셀링) - (소모품원가 + 인건비 + 광고비 + 실장인센티브)
        """
        # 1. 시술 마스터 정보 조회
        procedure = db.get(Procedure, payload.procedure_id)
        if not procedure:
            raise ValueError(f"시술 정보를 찾을 수 없습니다: {payload.procedure_id}")

        # 2. 환자 수 및 매출 계산
        expected_patients = payload.expected_leads * (payload.conversion_rate / 100)
        
        # 기본 시술 매출
        base_revenue = expected_patients * payload.promo_price
        # 업셀링 매출
        upsell_revenue = expected_patients * payload.upsell_estimate
        total_revenue = base_revenue + upsell_revenue

        # 3. 비용 계산
        # 변동비: (소모품원가 + 인건비 + 실장인센티브) * 환자 수
        variable_cost_per_patient = (
            procedure.consumable_cost + 
            procedure.labor_cost + 
            payload.staff_incentive
        )
        total_variable_cost = expected_patients * variable_cost_per_patient
        
        # 총 비용 = 변동비 + 광고비
        total_cost = total_variable_cost + payload.ad_spend

        # 4. 수익 및 지표 산출
        projected_profit = total_revenue - total_cost
        
        # 손익분기 환자 수 (BEP) = 고정비(광고비) / (1인당 매출 - 1인당 변동비)
        margin_per_patient = (payload.promo_price + payload.upsell_estimate) - variable_cost_per_patient
        if margin_per_patient > 0:
            break_even_patients = payload.ad_spend / margin_per_patient
        else:
            break_even_patients = float('inf')

        return SimulationResponse(
            expected_patients=round(expected_patients, 1),
            expected_revenue=round(total_revenue),
            expected_cost=round(total_cost),
            projected_profit=round(projected_profit),
            break_even_patients=round(break_even_patients, 1),
            breakeven_reached=expected_patients >= break_even_patients
        )
