from sqlmodel import Session, create_engine
from app.core.config import settings

# 실제 운영 시 pool_size 등 추가 설정 가능
engine = create_engine(settings.database_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
