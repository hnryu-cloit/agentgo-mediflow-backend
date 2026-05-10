from __future__ import annotations

from sqlmodel import Session

from app.schemas.contracts import AuditLogEntry


class AuditService:
    def record(
        self,
        db: Session,
        *,
        domain: str,
        event_type: str,
        actor_role: str,
        route: str,
        outcome: str = "success",
        message: str = "",
        metadata: dict | None = None,
    ) -> AuditLogEntry:
        entry = AuditLogEntry(
            domain=domain,
            event_type=event_type,
            actor_role=actor_role,
            route=route,
            outcome=outcome,
            message=message,
            audit_metadata=metadata or {},
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
