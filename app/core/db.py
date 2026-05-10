from sqlmodel import create_engine
from app.core.config import settings

# 실제 운영 시 pool_size 등 추가 설정 가능
engine = create_engine(settings.database_url, echo=False)
