from __future__ import annotations

from functools import lru_cache

from app.repositories.bootstrap_repository import BootstrapRepository
from app.repositories.brand_repository import BrandRepository
from app.repositories.review_repository import ReviewRepository
from app.services.content_service import ContentService
from app.services.planning_service import PlanningService


@lru_cache(maxsize=1)
def get_bootstrap_repository() -> BootstrapRepository:
    return BootstrapRepository()


@lru_cache(maxsize=1)
def get_brand_repository() -> BrandRepository:
    return BrandRepository()


@lru_cache(maxsize=1)
def get_review_repository() -> ReviewRepository:
    return ReviewRepository()


def get_planning_service(
    repo: BootstrapRepository = ...,  # injected via Depends in routes
) -> PlanningService:
    return PlanningService(repository=repo)


def get_content_service() -> ContentService:
    return ContentService()