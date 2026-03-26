from sqlmodel import Session, SQLModel, select
from app.core.db import engine
from app.schemas.contracts import Procedure, ReviewItem

# 현업 조사 기반 초기 시술 데이터 (Seed Data)
INITIAL_PROCEDURES = [
    Procedure(
        id="proc_botox_kor_50",
        name="사각턱 보톡스 (국산/보툴렉스)",
        category="보톡스",
        brand="휴젤",
        consumable_cost=15000,
        labor_cost=5000,
        list_price=49000,
        min_price_limit=29000
    ),
    Procedure(
        id="proc_botox_imp_50",
        name="사각턱 보톡스 (수입/제오민)",
        category="보톡스",
        brand="멀츠",
        consumable_cost=85000,
        labor_cost=5000,
        list_price=180000,
        min_price_limit=150000
    ),
    Procedure(
        id="proc_filler_kor_1cc",
        name="국산 볼륨 필러 (뉴라미스) 1cc",
        category="필러",
        brand="메디톡스",
        consumable_cost=35000,
        labor_cost=15000,
        list_price=120000,
        min_price_limit=80000
    ),
    Procedure(
        id="proc_ulthera_600",
        name="울쎄라 커스텀 리프팅 600샷",
        category="리프팅",
        brand="멀츠",
        consumable_cost=450000,
        labor_cost=100000,
        list_price=2200000,
        min_price_limit=1800000
    ),
    Procedure(
        id="proc_shurink_300",
        name="슈링크 유니버스 300샷",
        category="리프팅",
        brand="클래시스",
        consumable_cost=35000,
        labor_cost=20000,
        list_price=150000,
        min_price_limit=99000
    )
]

INITIAL_REVIEW_ITEMS = [
    ReviewItem(step="브랜드 톤 검토", assignee="마케터", description="설정된 톤 키워드와 금칙어가 초안에 반영되었는지 확인", status="approved"),
    ReviewItem(step="금지어 포함 여부", assignee="마케터", description="자동 스캔 결과와 수동 검수 결과를 함께 점검", status="approved"),
    ReviewItem(step="의료광고법 준수", assignee="원장 / 마케터", description="과장 표현과 확정적 표현이 없는지 최종 확인", status="in_review"),
    ReviewItem(step="가격 정보 정확성", assignee="실장", description="이벤트 가격과 기간, 노출 채널별 문구 일치 여부 확인", status="pending"),
    ReviewItem(step="최종 승인", assignee="원장", description="발행 가능 여부 최종 판단", status="pending"),
]

def init_db():
    # 1. 테이블 생성
    SQLModel.metadata.create_all(engine)
    
    # 2. 초기 데이터 주입
    with Session(engine) as session:
        # Procedures
        for proc in INITIAL_PROCEDURES:
            existing = session.get(Procedure, proc.id)
            if not existing:
                session.add(proc)
        
        # Review Items
        existing_reviews = session.exec(select(ReviewItem)).all()
        if not existing_reviews:
            for item in INITIAL_REVIEW_ITEMS:
                session.add(item)
                
        session.commit()
