from __future__ import annotations

from app.schemas.contracts import BrandProfile, ContentRequest, DraftContent, GenerationResponse

_CHANNEL_TEMPLATES: dict[str, dict[str, str]] = {
    "blog": {
        "headline": "{event_name} - {hospital_name}에서 준비한 특별 이벤트",
        "body": (
            "{core_message}\n\n"
            "▶ 이벤트 기간: {event_start} ~ {event_end}\n\n"
            "{highlights_section}"
            "【자주 묻는 질문】\n"
            "Q. 시술 후 일상생활이 가능한가요?\n"
            "A. {doctor_philosophy}\n\n"
            "【주의사항】\n"
            "- 시술 전 충분한 상담을 진행합니다.\n"
            "- 개인차에 따라 결과가 다를 수 있습니다."
        ),
        "cta": "지금 예약하기",
    },
    "sns": {
        "headline": "{core_message}",
        "body": (
            "✔ {event_name}\n"
            "📅 {event_start} ~ {event_end}\n\n"
            "{highlights_section}"
            "#{hospital_name} #{tag_procedures}"
        ),
        "cta": "프로필 링크에서 예약",
    },
    "web": {
        "headline": "{event_name}",
        "body": "{core_message} {event_start}부터 {event_end}까지 진행됩니다.",
        "cta": "이벤트 신청",
    },
    "app": {
        "headline": "[{hospital_name}] {event_name}",
        "body": "{core_message}",
        "cta": "앱에서 예약",
    },
}

_REVIEW_NOTES: list[str] = [
    "의료광고법 제56조 기준으로 과장·허위 표현 여부를 검토하세요.",
    "금지어({banned_terms}) 포함 여부를 수동으로 확인하세요.",
    "시술 결과에 대한 단정적 표현이 없는지 확인하세요.",
]


class ContentService:
    def generate(self, brand: BrandProfile, request: ContentRequest) -> GenerationResponse:
        highlights_section = (
            "【주요 혜택】\n" + "\n".join(f"• {h}" for h in request.highlights) + "\n\n"
            if request.highlights
            else ""
        )
        tag_procedures = " #".join(brand.signature_procedures[:3])
        banned_terms_str = ", ".join(brand.banned_terms) if brand.banned_terms else "없음"

        context = {
            "event_name": request.event_name,
            "hospital_name": brand.hospital_name,
            "core_message": request.core_message,
            "event_start": request.event_start,
            "event_end": request.event_end,
            "doctor_philosophy": brand.doctor_philosophy,
            "highlights_section": highlights_section,
            "tag_procedures": tag_procedures,
            "banned_terms": banned_terms_str,
        }

        channels: dict[str, DraftContent] = {}
        for channel in request.channels:
            tmpl = _CHANNEL_TEMPLATES.get(channel)
            if tmpl:
                channels[channel] = DraftContent(
                    headline=tmpl["headline"].format(**context),
                    body=tmpl["body"].format(**context),
                    cta=tmpl["cta"],
                )

        review_notes = [note.format(**context) for note in _REVIEW_NOTES]

        return GenerationResponse(
            event_name=request.event_name,
            channels=channels,
            review_notes=review_notes,
        )