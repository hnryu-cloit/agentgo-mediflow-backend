from __future__ import annotations

from sqlmodel import Session, select

from app.schemas.contracts import Campaign, PublishedContent


class ArchiveRepository:
    def filter_published(
        self,
        db: Session,
        channel: str | None = None,
        event: str | None = None,
        status: str | None = None,
    ) -> list[PublishedContent]:
        statement = select(PublishedContent)
        if channel:
            statement = statement.where(PublishedContent.channel == channel)
        if status:
            statement = statement.where(PublishedContent.status == status)
        items = list(db.exec(statement).all())
        if event:
            campaign_ids = {
                c.id
                for c in db.exec(select(Campaign).where(Campaign.event_name.contains(event))).all()
                if c.id is not None
            }
            items = [item for item in items if item.campaign_id in campaign_ids]
        return items