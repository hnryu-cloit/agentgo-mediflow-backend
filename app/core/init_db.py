from sqlalchemy import text
from sqlmodel import Session, SQLModel, select

from app.core.db import engine
from app.schemas.contracts import (
    Clinic,
    Procedure,
    ProcedureCaution,
    ProcedureFaq,
    ProcedureRecommendation,
    ProcedureVariant,
    ReviewItem,
)

INITIAL_CLINIC = Clinic(
    name="톡스앤필 강남점",
    clinic_type="FACTORY",
    target_audience="20~30대 미용시술 관심층, 윤곽·보톡스·필러 니즈가 높은 신규 상담 고객",
    doctor_philosophy="정품과 정량을 기반으로 상담 단계에서 시술 적합성과 주의사항을 명확히 설명합니다.",
    head_office_message="전 지점 공통으로 정품/정량, 합리적 가격, 빠른 예약 동선을 강조합니다.",
    branch_context="강남 상권 특성상 턱보톡스, 필러, 윤곽 계열의 이벤트 반응이 높고 플랫폼 예약 전환이 중요합니다.",
    signature_procedures=["사각턱 보톡스", "주름보톡스", "입술 필러 패키지", "벨라콜린"],
    brand_tone=["명확한 설명", "빠른 예약 유도", "정품 정량 강조"],
    banned_terms=["최고", "영구", "부작용 없음", "완치", "100% 효과"],
)

INITIAL_PROCEDURES = [
    Procedure(
        id="proc_masseter_botox",
        name="사각턱 보톡스",
        category="보톡스",
        brand="휴젤 / 멀츠 / 앨러간",
        summary="발달된 턱 근육을 줄여 갸름한 얼굴 라인을 만드는 대표 보톡스 시술",
        hero_title="발달된 턱 근육을 줄여 갸름한 V라인으로!",
        hero_description="클로스트리디움 보튤리늄 톡신이 주성분으로, 부피가 큰 근육의 사이즈를 감소시켜 갸름한 얼굴 라인을 만들어주는 시술입니다.",
        hashtags=["턱보톡스", "V라인", "윤곽개선", "일상생활가능"],
        target_areas=["턱", "턱라인", "하관"],
        procedure_time_text="10분 이내",
        anesthesia_text="마취 없이 또는 필요 시 연고 마취",
        recovery_text="즉시 생활 가능",
        duration_text="보통 4~6개월",
        recommended_cycle_text="4~5개월 주기 재시술 권장",
        operation_role="저가 유입형 대표 시술",
        marketing_point="정품 정량 확인, 첫 상담 진입용 시술",
        margin_strategy="국산 저가 유입 후 내성 적은 제품과 수입 제품으로 업셀링",
        essential_info=["개인차에 따라 효과 시기와 유지 기간이 다를 수 있음", "질기고 딱딱한 음식은 유지 기간에 영향을 줄 수 있음"],
        consumable_cost=15000,
        labor_cost=5000,
        list_price=50000,
        min_price_limit=29000,
        is_active=True,
        is_featured=True,
    ),
    Procedure(
        id="proc_wrinkle_botox",
        name="주름보톡스",
        category="보톡스",
        brand="국산 / 독일산 / 미국산",
        summary="표정주름과 피부 탄력을 동시에 개선하는 더모톡신 계열 시술",
        hero_title="표정주름과 탄력을 개선하는 주름보톡스",
        hero_description="톡신을 피부층에 주입해 표정주름은 자연스럽게 개선하고 탄력 개선 효과도 더불어 기대할 수 있는 시술입니다.",
        hashtags=["이마", "미간", "눈가", "눈밑", "자갈턱"],
        target_areas=["이마", "미간", "눈가", "눈밑", "콧등", "콧볼", "인중주름", "자갈턱"],
        procedure_time_text="10분 이내",
        anesthesia_text="마취 없이 또는 필요 시 연고 마취",
        recovery_text="즉시 생활 가능",
        duration_text="평균 2~3개월",
        recommended_cycle_text="3개월 이내 재시술 권장",
        operation_role="플랫폼 전환형 반복 시술",
        marketing_point="부드러운 인상 개선과 빠른 효과를 함께 강조",
        margin_strategy="부위 수 증가와 내성 적은 제품 옵션으로 객단가 확장",
        essential_info=["이마 시술 후 일시적으로 눈썹이 무겁게 느껴질 수 있음", "시술 후 3~7일간 과음/사우나/격한 운동 주의"],
        consumable_cost=10000,
        labor_cost=5000,
        list_price=30000,
        min_price_limit=19000,
        is_active=True,
        is_featured=True,
    ),
    Procedure(
        id="proc_lip_filler_package",
        name="입술 필러 패키지",
        category="필러",
        brand="리쥬비엘 / 쥬비덤 / 벨로테로 / 레스틸렌",
        summary="입술 볼륨, 입꼬리 개선, 보톡스를 한 번에 묶은 패키지형 필러 시술",
        hero_title="차밍포인트 이쁜 입술 만들기",
        hero_description="입술에 필러를 주입하여 입술 모양을 교정하고 입꼬리 개선까지 함께 설계하는 패키지 시술입니다.",
        hashtags=["일상생활바로가능", "맞춤필러", "즉각적인효과"],
        target_areas=["입술", "입꼬리"],
        procedure_time_text="10~20분",
        anesthesia_text="연고 마취 및 국소마취",
        recovery_text="즉시 생활 가능",
        duration_text="국산 6~12개월, 수입 12~18개월",
        recommended_cycle_text="멍/부기 가라앉은 후 재시술 상담",
        operation_role="객단가 확장형 패키지",
        marketing_point="맞춤 디자인과 즉각적인 볼륨 변화 강조",
        margin_strategy="국산 보급형과 수입 프리미엄 옵션으로 객단가 차등 운영",
        essential_info=["멍, 부기, 통증, 이물감이 발생할 수 있음", "시술 부위 압박 및 마사지는 2~3주간 주의"],
        consumable_cost=80000,
        labor_cost=25000,
        list_price=380000,
        min_price_limit=199000,
        is_active=True,
        is_featured=True,
    ),
    Procedure(
        id="proc_face_filler",
        name="페이스 필러",
        category="필러",
        brand="뉴라미스 / 리쥬비엘 / 쥬비덤 / 벨로테로 / 레스틸렌",
        summary="얼굴 볼륨과 윤곽, 주름 개선이 필요한 부위에 볼륨을 채우는 맞춤형 필러 시술",
        hero_title="예쁨을 채우는 맞춤형 필러",
        hero_description="얼굴의 볼륨과 주름 개선이 필요한 부위에 히알루론산 성분의 필러를 주입하여 보다 어려보이는 효과를 기대할 수 있습니다.",
        hashtags=["일상생활바로가능", "맞춤필러", "즉각적인효과"],
        target_areas=["이마", "코", "볼", "팔자", "눈밑", "턱끝", "입술"],
        procedure_time_text="10~20분",
        anesthesia_text="연고 마취 및 국소마취",
        recovery_text="즉시 생활 가능",
        duration_text="국산 6~12개월, 수입 12~18개월",
        recommended_cycle_text="멍/부기 완화 후 재시술 상담",
        operation_role="부위 확장형 필러 시술",
        marketing_point="부위별 맞춤 디자인과 즉각적인 볼륨 형성",
        margin_strategy="국산/수입과 부위별 옵션으로 업셀 구조 설계",
        essential_info=["필러는 개인 상태와 부위에 따라 유지기간이 다름", "피부색 변화, 물집, 열감 지속 시 즉시 내원 필요"],
        consumable_cost=35000,
        labor_cost=15000,
        list_price=150000,
        min_price_limit=99000,
        is_active=True,
        is_featured=False,
    ),
    Procedure(
        id="proc_bellacolin",
        name="벨라콜린",
        category="지방분해주사",
        brand="벨라콜린",
        summary="스테로이드 없는 DCA 지방분해 주사로 이중턱과 턱 라인 개선에 초점을 둔 시술",
        hero_title="스테로이드 없는 지방분해 DCA주사",
        hero_description="이중턱과 턱 라인의 지방 개선을 위해 수술 부담 없이 접근하는 DCA 기반 지방분해 시술입니다.",
        hashtags=["지방분해주사", "윤곽주사", "지방세포파괴", "이중턱개선"],
        target_areas=["턱", "이중턱", "턱밑", "목라인"],
        procedure_time_text="10분 이내",
        anesthesia_text="필요 시 연고 마취",
        recovery_text="일상생활 가능",
        duration_text="시리즈 진행 후 점진적 개선",
        recommended_cycle_text="4주 간격 3회 권장",
        operation_role="시리즈형 윤곽 개선 시술",
        marketing_point="수술 부담이 적고 이중턱 개선 니즈가 큰 고객에게 적합",
        margin_strategy="1회 체험형과 3회 패키지형을 함께 운영",
        essential_info=["지방 개선 효과는 점진적으로 나타남", "처음 시술 시 4주 간격 3회 권장"],
        consumable_cost=65000,
        labor_cost=10000,
        list_price=300000,
        min_price_limit=190000,
        is_active=True,
        is_featured=True,
    ),
]

INITIAL_VARIANTS = [
    ProcedureVariant(id="var_masseter_botox_kor_50u", procedure_id="proc_masseter_botox", name="[EVENT] [국산] 턱보톡스 50U", option_label="국산 / 50U", list_price=50000, event_price=29000, unit_type="U", unit_value="50", session_count=1, is_featured=True),
    ProcedureVariant(id="var_masseter_botox_low_resistance", procedure_id="proc_masseter_botox", name="[EVENT] [국산/내성 적은] 턱보톡스 50U", option_label="국산 / 내성 적은 / 50U", list_price=90000, event_price=49000, unit_type="U", unit_value="50", session_count=1),
    ProcedureVariant(id="var_masseter_botox_de", procedure_id="proc_masseter_botox", name="[EVENT] [독일산] 턱보톡스 50U", option_label="독일산 / 50U", list_price=140000, event_price=99000, unit_type="U", unit_value="50", session_count=1),
    ProcedureVariant(id="var_wrinkle_botox_1", procedure_id="proc_wrinkle_botox", name="[EVENT] [국산] 주름보톡스 1부위", option_label="국산 / 1부위", list_price=30000, event_price=19000, unit_type="부위", unit_value="1", session_count=1, is_featured=True),
    ProcedureVariant(id="var_wrinkle_botox_2", procedure_id="proc_wrinkle_botox", name="[EVENT] [국산] 주름보톡스 2부위", option_label="국산 / 2부위", list_price=55000, event_price=34000, unit_type="부위", unit_value="2", session_count=1),
    ProcedureVariant(id="var_lip_filler_kor", procedure_id="proc_lip_filler_package", name="[EVENT] [국산] 입술필러 패키지", option_label="국산 / 1cc + 입꼬리필러 + 입꼬리보톡스", list_price=380000, event_price=199000, unit_type="패키지", unit_value="1", session_count=1, is_featured=True),
    ProcedureVariant(id="var_lip_filler_imported", procedure_id="proc_lip_filler_package", name="[EVENT] [쥬비덤/벨로테로/레스틸렌] 입술필러 패키지", option_label="수입 / 입술필러 패키지", list_price=500000, event_price=350000, unit_type="패키지", unit_value="1", session_count=1),
    ProcedureVariant(id="var_face_filler_domestic_1cc", procedure_id="proc_face_filler", name="[EVENT] [국산] 필러 1cc", option_label="국산 / 1cc", list_price=150000, event_price=99000, unit_type="cc", unit_value="1", session_count=1, is_featured=True),
    ProcedureVariant(id="var_face_filler_imported_1cc", procedure_id="proc_face_filler", name="[EVENT] [수입] 필러 1cc", option_label="수입 / 1cc", list_price=350000, event_price=260000, unit_type="cc", unit_value="1", session_count=1),
    ProcedureVariant(id="var_bellacolin_1vial_1", procedure_id="proc_bellacolin", name="[EVENT] 벨라콜린 1vial (2cc) 1회", option_label="1vial / 2cc / 1회", list_price=300000, event_price=190000, unit_type="vial", unit_value="2cc", session_count=1, is_featured=True),
    ProcedureVariant(id="var_bellacolin_2vial_1", procedure_id="proc_bellacolin", name="[EVENT] 벨라콜린 2vial (4cc) 1회", option_label="2vial / 4cc / 1회", list_price=560000, event_price=340000, unit_type="vial", unit_value="4cc", session_count=1),
    ProcedureVariant(id="var_bellacolin_1vial_3", procedure_id="proc_bellacolin", name="[EVENT] 벨라콜린 1vial (2cc) 3회", option_label="1vial / 2cc / 3회", list_price=780000, event_price=450000, unit_type="vial", unit_value="2cc", session_count=3),
]

INITIAL_RECOMMENDATIONS = [
    ProcedureRecommendation(procedure_id="proc_masseter_botox", sort_order=1, content="사각턱으로 얼굴이 크고 각져보이는 분"),
    ProcedureRecommendation(procedure_id="proc_masseter_botox", sort_order=2, content="작고 부드러운 얼굴선을 원하는 분"),
    ProcedureRecommendation(procedure_id="proc_wrinkle_botox", sort_order=1, content="표정을 지을 때 생기는 주름이 신경쓰이는 분"),
    ProcedureRecommendation(procedure_id="proc_wrinkle_botox", sort_order=2, content="탄력있는 피부와 잔주름 개선을 원하는 분"),
    ProcedureRecommendation(procedure_id="proc_lip_filler_package", sort_order=1, content="얇은 입술이 고민이신 분"),
    ProcedureRecommendation(procedure_id="proc_lip_filler_package", sort_order=2, content="입꼬리를 올려 미소를 더 아름답게 하고 싶은 분"),
    ProcedureRecommendation(procedure_id="proc_face_filler", sort_order=1, content="얼굴의 볼륨과 입체감 개선을 원하는 분"),
    ProcedureRecommendation(procedure_id="proc_face_filler", sort_order=2, content="수술 없이 간단한 1회 시술로 변화를 원하는 분"),
    ProcedureRecommendation(procedure_id="proc_bellacolin", sort_order=1, content="턱 부분에 지방이 많은 분"),
    ProcedureRecommendation(procedure_id="proc_bellacolin", sort_order=2, content="이중턱으로 인상이 둔해 보이는 분"),
]

INITIAL_FAQS = [
    ProcedureFaq(procedure_id="proc_masseter_botox", sort_order=1, question="내성 걱정될 때 어떤 제품이 좋을까요?", answer="내성이 걱정되시면 결합 단백질이 없는 제품을 우선 권장해 드립니다."),
    ProcedureFaq(procedure_id="proc_masseter_botox", sort_order=2, question="사각턱 보톡스와 윤곽주사의 차이는 무엇인가요?", answer="보톡스는 근육, 윤곽주사는 지방을 대상으로 하므로 얼굴 타입에 따라 병행 시너지가 있을 수 있습니다."),
    ProcedureFaq(procedure_id="proc_wrinkle_botox", sort_order=1, question="이마 보톡스 후 눈썹이 무겁게 느껴질 수 있나요?", answer="약물 확산 과정에서 일시적으로 불편할 수 있으나 보통 2~3주 내 완화됩니다."),
    ProcedureFaq(procedure_id="proc_lip_filler_package", sort_order=1, question="보톡스와 필러의 차이점은 무엇인가요?", answer="보톡스는 근육을 이완시키고 필러는 부족한 볼륨을 채우는 시술입니다."),
    ProcedureFaq(procedure_id="proc_lip_filler_package", sort_order=2, question="국산과 수입 필러의 차이는 무엇인가요?", answer="수입 필러는 점탄성과 제품군이 다양해 부위별 정교한 시술에 유리하고, 국산은 경제성이 강점입니다."),
    ProcedureFaq(procedure_id="proc_face_filler", sort_order=1, question="필러와 스컬트라의 차이는 무엇인가요?", answer="필러는 즉시 볼륨을 형성하고 스컬트라는 콜라겐 생성을 유도해 서서히 볼륨이 차오릅니다."),
    ProcedureFaq(procedure_id="proc_bellacolin", sort_order=1, question="벨라콜린은 몇 회가 권장되나요?", answer="처음 시술하시는 경우 4주 간격으로 3회를 권장합니다."),
]

INITIAL_CAUTIONS = [
    ProcedureCaution(procedure_id="proc_masseter_botox", sort_order=1, content="시술 부위를 심하게 문지르거나 경락, 마사지 등 강한 자극은 1개월간 피해주세요."),
    ProcedureCaution(procedure_id="proc_masseter_botox", sort_order=2, content="시술 후 3~7일간 과음, 사우나, 찜질방, 격한 운동은 피해주세요."),
    ProcedureCaution(procedure_id="proc_wrinkle_botox", sort_order=1, content="세안 및 화장은 2~3시간 뒤부터 가능합니다."),
    ProcedureCaution(procedure_id="proc_wrinkle_botox", sort_order=2, content="이마 보톡스 후 눈 뜨기 무겁거나 눈썹이 불편할 수 있으나 보통 서서히 완화됩니다."),
    ProcedureCaution(procedure_id="proc_lip_filler_package", sort_order=1, content="멍, 부기, 통증, 이물감이 1~2주 내 발생할 수 있습니다."),
    ProcedureCaution(procedure_id="proc_lip_filler_package", sort_order=2, content="피부색 변화, 물집, 열감이 지속되면 병원으로 연락 후 내원해주세요."),
    ProcedureCaution(procedure_id="proc_face_filler", sort_order=1, content="시술 부위 압박이나 얼굴 경락 마사지는 2~3주간 피해주세요."),
    ProcedureCaution(procedure_id="proc_face_filler", sort_order=2, content="항생제 알러지 등이 있는 경우 사전에 반드시 알려주세요."),
    ProcedureCaution(procedure_id="proc_bellacolin", sort_order=1, content="지방 개선 효과는 점진적으로 나타나며 개인차가 있습니다."),
]

INITIAL_REVIEW_ITEMS = [
    ReviewItem(step="브랜드 톤 검토", assignee="마케터", description="설정된 톤 키워드와 금칙어가 초안에 반영되었는지 확인", status="approved"),
    ReviewItem(step="금지어 포함 여부", assignee="마케터", description="자동 스캔 결과와 수동 검수 결과를 함께 점검", status="approved"),
    ReviewItem(step="의료광고법 준수", assignee="원장 / 마케터", description="과장 표현과 확정적 표현이 없는지 최종 확인", status="in_review"),
    ReviewItem(step="가격 정보 정확성", assignee="실장", description="이벤트 가격과 기간, 노출 채널별 문구 일치 여부 확인", status="pending"),
    ReviewItem(step="최종 승인", assignee="원장", description="발행 가능 여부 최종 판단", status="pending"),
]


def init_db():
    SQLModel.metadata.create_all(engine)
    _apply_lightweight_migrations()

    with Session(engine, expire_on_commit=False) as session:
        existing_clinic = session.exec(select(Clinic)).first()
        if not existing_clinic:
            session.add(INITIAL_CLINIC)

        for proc in INITIAL_PROCEDURES:
            existing = session.get(Procedure, proc.id)
            if not existing:
                session.add(proc)

        for variant in INITIAL_VARIANTS:
            existing = session.get(ProcedureVariant, variant.id)
            if not existing:
                session.add(variant)

        if not session.exec(select(ProcedureRecommendation)).first():
            for item in INITIAL_RECOMMENDATIONS:
                session.add(item)

        if not session.exec(select(ProcedureFaq)).first():
            for item in INITIAL_FAQS:
                session.add(item)

        if not session.exec(select(ProcedureCaution)).first():
            for item in INITIAL_CAUTIONS:
                session.add(item)

        if not session.exec(select(ReviewItem)).first():
            for item in INITIAL_REVIEW_ITEMS:
                session.add(item)

        session.commit()


def _apply_lightweight_migrations() -> None:
    """PoC SQLite DB의 기존 테이블에 새 컬럼만 보강한다."""
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        rows = connection.execute(text("PRAGMA table_info(promotion)")).fetchall()
        columns = {row[1] for row in rows}
        if rows and "consumable_cost" not in columns:
            connection.execute(text("ALTER TABLE promotion ADD COLUMN consumable_cost FLOAT DEFAULT 0"))
        if rows and "labor_cost" not in columns:
            connection.execute(text("ALTER TABLE promotion ADD COLUMN labor_cost FLOAT DEFAULT 0"))
        if rows and "promo_period_weeks" not in columns:
            connection.execute(text("ALTER TABLE promotion ADD COLUMN promo_period_weeks INTEGER DEFAULT 4"))

        # campaign.promotion_id: NOT NULL → nullable 로 변경
        # SQLite는 NOT NULL 직접 제거 불가 — 테이블 재생성으로 처리
        campaign_rows = connection.execute(text("PRAGMA table_info(campaign)")).fetchall()
        if campaign_rows:
            notnull_flag = {row[1]: row[3] for row in campaign_rows}
            if notnull_flag.get("promotion_id") == 1:
                connection.execute(text("""
                    CREATE TABLE campaign_new (
                        id INTEGER PRIMARY KEY,
                        promotion_id INTEGER REFERENCES promotion(id),
                        event_name VARCHAR NOT NULL,
                        core_message VARCHAR NOT NULL,
                        channels_content JSON,
                        review_notes JSON
                    )
                """))
                connection.execute(text(
                    "INSERT INTO campaign_new SELECT id, promotion_id, event_name, core_message, channels_content, review_notes FROM campaign"
                ))
                connection.execute(text("DROP TABLE campaign"))
                connection.execute(text("ALTER TABLE campaign_new RENAME TO campaign"))
