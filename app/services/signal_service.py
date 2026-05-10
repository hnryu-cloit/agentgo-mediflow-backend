from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.schemas.contracts import AuditLogEntry, PublishedContent, ReviewItem, SalesSignal


class SignalService:
    def refresh(self, db: Session) -> list[SalesSignal]:
        self._clear_generated_signals(db)
        signals: list[SalesSignal] = []
        signals.extend(self._detect_low_ctr(db))
        signals.extend(self._detect_medlaw_spike(db))
        signals.extend(self._detect_review_delay(db))
        for signal in signals:
            db.add(signal)
        db.commit()
        return signals

    def _clear_generated_signals(self, db: Session) -> None:
        existing = db.exec(select(SalesSignal)).all()
        for signal in existing:
            db.delete(signal)
        db.commit()

    def _detect_low_ctr(self, db: Session) -> list[SalesSignal]:
        items = db.exec(select(PublishedContent)).all()
        if not items:
            return []
        total_views = sum(item.views for item in items)
        total_clicks = sum(item.clicks for item in items)
        ctr = total_clicks / total_views * 100 if total_views else 0
        if total_views >= 100 and ctr < 1.0:
            return [
                SalesSignal(
                    domain="archive",
                    title="채널 CTR 저하",
                    metric="ctr",
                    value=round(ctr, 2),
                    change=-1,
                    trend="down",
                    priority="high",
                    insight="전체 발행 콘텐츠 CTR이 1% 미만입니다. CTA와 채널별 메시지를 재점검하세요.",
                )
            ]
        return []

    def _detect_medlaw_spike(self, db: Session) -> list[SalesSignal]:
        since = datetime.utcnow() - timedelta(days=7)
        logs = db.exec(
            select(AuditLogEntry).where(
                AuditLogEntry.domain == "content",
                AuditLogEntry.timestamp >= since,
            )
        ).all()
        risk_count = sum(1 for log in logs if "의료광고" in log.message or "medlaw" in str(log.audit_metadata))
        if risk_count >= 3:
            return [
                SalesSignal(
                    domain="content",
                    title="의료광고 리스크 증가",
                    metric="medlaw_risk_count",
                    value=risk_count,
                    change=risk_count,
                    trend="up",
                    priority="high",
                    insight="최근 생성/검토 흐름에서 의료광고 리스크 로그가 반복되었습니다.",
                )
            ]
        return []

    def _detect_review_delay(self, db: Session) -> list[SalesSignal]:
        pending = db.exec(select(ReviewItem).where(ReviewItem.status != "approved")).all()
        if len(pending) >= 3:
            return [
                SalesSignal(
                    domain="review",
                    title="승인 지연 가능성",
                    metric="pending_review_count",
                    value=len(pending),
                    change=0,
                    trend="flat",
                    priority="medium",
                    insight="승인되지 않은 검토 항목이 3개 이상입니다. 원장 승인 큐를 확인하세요.",
                )
            ]
        return []
