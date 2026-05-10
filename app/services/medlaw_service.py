from __future__ import annotations

from app.schemas.contracts import MedlawViolation


MEDLAW_RULES = [
    ("최고", "의료법 제56조", "최상급 표현은 객관적 근거 없이 사용할 수 없습니다.", "medium"),
    ("유일", "의료법 제56조", "배타적 표현은 객관적 근거 확인이 필요합니다.", "medium"),
    ("100% 효과", "의료법 제56조", "효과를 보장하는 표현은 금지 표현 후보입니다.", "high"),
    ("완치", "의료법 제56조", "치료 결과를 확정하는 표현은 사용할 수 없습니다.", "high"),
    ("부작용 없음", "의료법 제56조", "부작용이 없다고 단정하는 표현은 위험합니다.", "high"),
    ("영구", "의료법 제56조", "유지 기간을 영구적으로 단정할 수 없습니다.", "medium"),
    ("무통", "의료법 제56조", "통증이 없다고 단정하는 표현은 개인차 안내가 필요합니다.", "medium"),
    ("즉각 효과", "의료법 제56조", "효과 발생 시점을 단정하는 표현은 주의가 필요합니다.", "medium"),
]


class MedlawService:
    def check(self, text: str) -> list[MedlawViolation]:
        normalized = text.lower()
        violations: list[MedlawViolation] = []
        for keyword, article, message, severity in MEDLAW_RULES:
            if keyword.lower() in normalized:
                violations.append(
                    MedlawViolation(
                        type="medical_ad",
                        keyword=keyword,
                        article=article,
                        message=message,
                        severity=severity,
                    )
                )
        return violations
