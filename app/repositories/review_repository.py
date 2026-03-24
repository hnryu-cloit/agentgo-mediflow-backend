from __future__ import annotations

from app.schemas.contracts import ReviewChecklistItem

_DEFAULT_CHECKLIST: list[dict[str, str]] = [
    {"stage": "브랜드 톤 검토", "owner": "마케터", "status": "pending", "notes": "설정된 톤·금지어 준수 여부 확인"},
    {"stage": "금지어 포함 여부", "owner": "마케터", "status": "pending", "notes": "자동 스캔 + 수동 확인"},
    {"stage": "의료광고법 준수", "owner": "마케터", "status": "pending", "notes": "과장·허위 광고 표현 없음 확인"},
    {"stage": "가격 정보 정확성", "owner": "실장", "status": "pending", "notes": "이벤트 가격·기간 정확성 확인"},
    {"stage": "최종 원장 승인", "owner": "원장", "status": "pending", "notes": "최종 발행 승인"},
]


class ReviewRepository:
    def __init__(self) -> None:
        self._items: list[ReviewChecklistItem] = [
            ReviewChecklistItem(**item) for item in _DEFAULT_CHECKLIST
        ]

    def get_all(self) -> list[ReviewChecklistItem]:
        return list(self._items)

    def update_status(self, stage: str, status: str, notes: str = "") -> ReviewChecklistItem | None:
        for item in self._items:
            if item.stage == stage:
                item.status = status
                if notes:
                    item.notes = notes
                return item
        return None

    def reset(self) -> None:
        self._items = [ReviewChecklistItem(**item) for item in _DEFAULT_CHECKLIST]