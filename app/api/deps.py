from __future__ import annotations

from typing import Generator
from sqlmodel import Session
from app.core.db import engine


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
