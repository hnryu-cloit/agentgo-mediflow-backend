from __future__ import annotations

from sqlmodel import Session, select

from app.schemas.contracts import BrandProfile, Clinic


class BrandService:
    def upsert(self, db: Session, payload: BrandProfile) -> tuple[Clinic, bool]:
        # 기존 프로필이 있으면 업데이트, 없으면 신규 생성. bool은 신규 생성 여부
        existing = db.exec(select(Clinic)).first()
        data = {
            "name": payload.hospital_name,
            "clinic_type": payload.clinic_type,
            "target_audience": payload.target_audience,
            "doctor_philosophy": payload.doctor_philosophy,
            "head_office_message": payload.head_office_message,
            "branch_context": payload.branch_context,
            "signature_procedures": payload.signature_procedures,
            "brand_tone": payload.brand_tone,
            "banned_terms": payload.banned_terms,
        }
        if existing:
            for key, value in data.items():
                setattr(existing, key, value)
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing, False
        clinic = Clinic(**data)
        db.add(clinic)
        db.commit()
        db.refresh(clinic)
        return clinic, True

    def get(self, db: Session) -> Clinic | None:
        return db.exec(select(Clinic)).first()
