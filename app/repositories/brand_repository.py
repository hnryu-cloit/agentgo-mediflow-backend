from __future__ import annotations

from app.schemas.contracts import BrandProfile


class BrandRepository:
    def __init__(self) -> None:
        self._store: BrandProfile | None = None

    def save(self, profile: BrandProfile) -> BrandProfile:
        self._store = profile
        return self._store

    def get(self) -> BrandProfile | None:
        return self._store