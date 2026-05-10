from __future__ import annotations

from sqlmodel import Session, select

from app.core.ttl_cache import TTLCache
from app.schemas.contracts import ArchiveMetricsUpdate, Campaign, Promotion, PublishedContent


class AnalyticsService:
    def __init__(self) -> None:
        self.campaign_cache: TTLCache[list[dict]] = TTLCache(max_size=64, ttl_seconds=60)
        self.channel_cache: TTLCache[list[dict]] = TTLCache(max_size=64, ttl_seconds=60)

    def campaign_roi(self, db: Session) -> list[dict]:
        cached = self.campaign_cache.get("campaign_roi")
        if cached is not None:
            return cached

        campaigns = db.exec(select(Campaign)).all()
        items = db.exec(select(PublishedContent)).all()
        promotions = {promotion.id: promotion for promotion in db.exec(select(Promotion)).all()}
        result = []
        for campaign in campaigns:
            related = [item for item in items if item.campaign_id == campaign.id]
            views = sum(item.views for item in related)
            clicks = sum(item.clicks for item in related)
            promotion = promotions.get(campaign.promotion_id)
            estimated_revenue = 0
            ad_spend = 0
            if promotion:
                expected_patients = promotion.expected_leads * (promotion.conversion_rate / 100)
                estimated_revenue = expected_patients * (promotion.promo_price + promotion.upsell_estimate)
                ad_spend = promotion.ad_spend
            roi = ((estimated_revenue - ad_spend) / ad_spend * 100) if ad_spend else 0
            result.append(
                {
                    "campaign_id": campaign.id,
                    "event_name": campaign.event_name,
                    "views": views,
                    "clicks": clicks,
                    "ctr": round(clicks / views * 100, 2) if views else 0,
                    "estimated_revenue": round(estimated_revenue),
                    "ad_spend": round(ad_spend),
                    "roi": round(roi, 2),
                }
            )
        self.campaign_cache.set("campaign_roi", result)
        return result

    def channel_performance(self, db: Session) -> list[dict]:
        cached = self.channel_cache.get("channel_performance")
        if cached is not None:
            return cached

        items = db.exec(select(PublishedContent)).all()
        grouped: dict[str, dict] = {}
        for item in items:
            bucket = grouped.setdefault(
                item.channel,
                {"channel": item.channel, "views": 0, "clicks": 0, "published_count": 0},
            )
            bucket["views"] += item.views
            bucket["clicks"] += item.clicks
            bucket["published_count"] += 1
        result = [
            {**value, "ctr": round(value["clicks"] / value["views"] * 100, 2) if value["views"] else 0}
            for value in grouped.values()
        ]
        self.channel_cache.set("channel_performance", result)
        return result

    def update_metrics(self, db: Session, item_id: int, payload: ArchiveMetricsUpdate) -> PublishedContent:
        item = db.get(PublishedContent, item_id)
        if not item:
            raise ValueError(f"발행 콘텐츠를 찾을 수 없습니다: {item_id}")
        item.views = payload.views
        item.clicks = payload.clicks
        item.ctr = payload.ctr if payload.ctr is not None else (payload.clicks / payload.views * 100 if payload.views else 0)
        db.add(item)
        db.commit()
        db.refresh(item)
        self.clear()
        return item

    def clear(self) -> None:
        self.campaign_cache.clear()
        self.channel_cache.clear()
