from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict
from uuid import uuid4

import httpx
from sqlmodel import Session

from app.core.config import settings
from app.schemas.contracts import (
    Campaign,
    Clinic,
    ConsistencyCheck,
    ContentRequest,
    DraftContent,
    ExplainabilityPayload,
    GenerationResponse,
    ShortsRequest,
    ShortsResponse,
    ShortsScene,
)
from app.services.medlaw_service import MedlawService

logger = logging.getLogger(__name__)

AI_TEMPLATE_CHANNELS = {"blog", "sns", "web", "app"}
PUBLIC_CONTENT_CHANNELS = {
    "ig_feed",
    "ig_story",
    "seo_blog",
    "blog",
    "web",
    "place",
    "kakao",
    "email",
    "app",
}
REAL_TO_TEMPLATE_CHANNEL = {
    "ig_feed": "sns",
    "ig_story": "sns",
    "seo_blog": "blog",
    "blog": "blog",
    "web": "web",
    "place": "web",
    "kakao": "app",
    "email": "web",
    "app": "app",
}

CHANNEL_LABELS = {
    "ig_feed": "인스타그램 피드",
    "ig_story": "인스타그램 스토리",
    "seo_blog": "SEO 블로그",
    "blog": "블로그",
    "web": "홈페이지",
    "place": "네이버 플레이스",
    "kakao": "카카오 알림톡",
    "email": "이메일",
    "app": "앱 푸시",
}

FUNNEL_STAGE_TO_AI = {
    "awareness": "awareness",
    "trust": "trust",
    "convert": "convert",
    "conversion": "convert",
}


class ContentService:
    def __init__(self) -> None:
        self.medlaw_service = MedlawService()

    async def generate(
        self, db: Session, clinic: Clinic, request: ContentRequest
    ) -> GenerationResponse:
        trace_id = f"content-{uuid4()}"
        ai_payload = {
            "payload": {
                "product": request.event_name,
                "summary": request.core_message,
                "goals": request.highlights,
                "features": request.highlights,
                "funnel_stage": FUNNEL_STAGE_TO_AI.get(request.funnel_stage, "convert"),
                "promo_period_weeks": request.promo_period_weeks,
            },
            "brand": {
                "hospital_name": clinic.name,
                "clinic_type": clinic.clinic_type,
                "target_audience": clinic.target_audience,
                "doctor_philosophy": clinic.doctor_philosophy,
                "signature_procedures": clinic.signature_procedures,
                "brand_tone": clinic.brand_tone,
                "banned_terms": clinic.banned_terms,
                "differentiators": [clinic.head_office_message, clinic.branch_context],
            },
        }

        ai_data = await self._post_generate_with_retry(ai_payload, trace_id)
        if ai_data is None:
            ai_data = self._fallback_ai_data(clinic, request)

        channels: Dict[str, DraftContent] = {}
        for ch_id in request.channels:
            template_channel = REAL_TO_TEMPLATE_CHANNEL.get(ch_id, ch_id)
            content = ai_data.get("channels", {}).get(ch_id) or ai_data.get("channels", {}).get(template_channel)
            if content:
                channels[ch_id] = DraftContent(
                    channel_id=ch_id,
                    funnel=FUNNEL_STAGE_TO_AI.get(content.get("funnel", request.funnel_stage), "convert"),
                    label=CHANNEL_LABELS.get(ch_id, ch_id),
                    headline=self._adapt_headline(ch_id, content["headline"]),
                    body=self._adapt_body(ch_id, content["body"]),
                    cta=content["cta"],
                    note=content.get("note", ""),
                    image_prompt=content.get("image_prompt"),
                )

        review_notes = list(ai_data.get("review_notes") or [])
        # review_notes 누락은 허용하지 않음 — 의료광고 검토 플로우에 반드시 노출
        if not review_notes:
            review_notes = ["AI 응답에 검토 노트가 없습니다. 의료광고법 제56조 기준으로 직접 검토하세요."]

        consistency_checks = self._build_consistency_checks(clinic, request, channels)
        for violation in self.medlaw_service.check(
            " ".join([d.headline + " " + d.body + " " + d.cta for d in channels.values()])
        ):
            review_notes.append(f"[의료광고] {violation.keyword}: {violation.message}")

        result = GenerationResponse(
            event_name=request.event_name,
            channels=channels,
            review_notes=review_notes,
            consistency_checks=consistency_checks,
            trace_id=trace_id,
        )

        db.add(
            Campaign(
                event_name=request.event_name,
                core_message=request.core_message,
                channels_content={key: value.model_dump() for key, value in channels.items()},
                review_notes=review_notes,
            )
        )
        db.add(
            ExplainabilityPayload(
                trace_id=trace_id,
                evidence=[
                    {"source": "Clinic", "clinic_id": clinic.id, "sample_count": 1},
                    {"source": "ContentRequest", "channels": request.channels, "sample_count": len(request.channels)},
                ],
                actions=[
                    "채널별 초안의 가격 표현을 시뮬레이션 값과 대조하세요.",
                    "의료광고 검토 노트를 확인한 뒤 승인 큐로 넘기세요.",
                ],
                follow_up_questions=[
                    "원장 승인 전에 수정해야 할 금칙어가 있나요?",
                    "채널별 CTA가 같은 이벤트 기간을 가리키나요?",
                ],
            )
        )
        db.commit()
        return result

    def write_brand_draft(self, db: Session, clinic: Clinic, field: str) -> tuple[str, str]:
        trace_id = f"brand-{uuid4()}"
        ai_draft = self._post_brand_write(field, clinic, trace_id)
        if ai_draft:
            draft = ai_draft
        elif field == "target_audience":
            draft = (
                f"{clinic.name}의 주요 고객은 {', '.join(clinic.signature_procedures[:2])}에 관심이 높고 "
                "가격, 회복기간, 안전성을 함께 확인하려는 신규 상담 고객입니다."
            )
        else:
            draft = (
                "정품과 정량, 개인별 적합성 설명, 시술 후 주의사항 안내를 기준으로 "
                "과장 없이 신뢰할 수 있는 상담 경험을 제공합니다."
            )
        result = self._remove_banned_terms(draft, clinic.banned_terms)
        db.add(
            ExplainabilityPayload(
                trace_id=trace_id,
                evidence=[
                    {"source": "Clinic", "clinic_id": clinic.id, "field": field},
                    {"source": "BrandProfile", "signature_count": len(clinic.signature_procedures)},
                ],
                actions=[
                    "초안 표현이 병원 실제 운영 톤과 맞는지 확인하세요.",
                    "금칙어 치환으로 의미가 어색해진 부분을 다듬으세요.",
                ],
                follow_up_questions=[
                    "주요 고객군의 연령/니즈가 더 구체적인가요?",
                    "원장 철학에서 반드시 피해야 할 표현이 있나요?",
                ],
            )
        )
        db.commit()
        return result, trace_id

    def _post_brand_write(self, field: str, clinic: Clinic, trace_id: str) -> str | None:
        payload = {
            "field": field,
            "brand": {
                "hospital_name": clinic.name,
                "clinic_type": clinic.clinic_type,
                "target_audience": clinic.target_audience,
                "doctor_philosophy": clinic.doctor_philosophy,
                "signature_procedures": clinic.signature_procedures,
                "brand_tone": clinic.brand_tone,
                "banned_terms": clinic.banned_terms,
                "differentiators": [clinic.head_office_message, clinic.branch_context],
            },
        }
        try:
            response = httpx.post(
                f"{settings.ai_service_url.rstrip('/')}/brand/ai-write",
                json=payload,
                timeout=5.0,
                headers={"X-Request-ID": trace_id},
            )
            response.raise_for_status()
            return response.json().get("draft")
        except Exception as exc:
            logger.warning("AI 브랜드 작성 실패 (trace_id=%s): %s", trace_id, exc)
            return None

    def generate_shorts(self, payload: ShortsRequest) -> ShortsResponse:
        trace_id = f"shorts-{datetime.utcnow().timestamp()}"
        body = payload.longform_draft.body
        return ShortsResponse(
            template_id=payload.template_id,
            trace_id=trace_id,
            scenes=[
                ShortsScene(order=1, duration_sec=3, script=payload.longform_draft.headline, visual_guide="시술명과 이벤트 핵심 문구를 9:16 첫 화면에 배치"),
                ShortsScene(order=2, duration_sec=5, script=body[:80], visual_guide="상담 장면 또는 시술 준비 과정을 짧게 구성"),
                ShortsScene(order=3, duration_sec=4, script=payload.longform_draft.cta, visual_guide="예약 CTA와 주의사항을 함께 노출"),
            ],
        )

    async def _post_generate_with_retry(self, payload: dict, trace_id: str) -> dict | None:
        retryable_statuses = {408, 429, 500, 502, 503, 504}
        async with httpx.AsyncClient() as client:
            for attempt in range(3):
                try:
                    response = await client.post(
                        f"{settings.ai_service_url.rstrip('/')}/generate",
                        json=payload,
                        timeout=10.0,
                        headers={"X-Request-ID": trace_id, "X-Retry-Attempt": str(attempt)},
                    )
                    if response.status_code in retryable_statuses:
                        logger.warning("AI API 재시도 가능 상태 (attempt=%d, status=%d, trace_id=%s)", attempt, response.status_code, trace_id)
                        continue
                    response.raise_for_status()
                    return response.json()
                except (httpx.ConnectError, httpx.TimeoutException) as exc:
                    logger.warning("AI API 연결/타임아웃 실패 (attempt=%d, trace_id=%s): %s", attempt, trace_id, exc)
                    continue
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code in retryable_statuses:
                        logger.warning("AI API HTTP 오류 재시도 (attempt=%d, status=%d, trace_id=%s)", attempt, exc.response.status_code, trace_id)
                        continue
                    logger.error("AI API 비재시도 HTTP 오류 (status=%d, trace_id=%s)", exc.response.status_code, trace_id)
                    return None
                except Exception as exc:
                    logger.error("AI API 예상치 못한 오류 (attempt=%d, trace_id=%s): %s", attempt, trace_id, exc)
                    return None
        logger.error("AI API 3회 재시도 모두 실패 (trace_id=%s) — fallback 적용", trace_id)
        return None

    def _fallback_ai_data(self, clinic: Clinic, request: ContentRequest) -> dict:
        highlight_text = ", ".join(request.highlights) if request.highlights else request.core_message
        return {
            "channels": {
                channel: {
                    "channel_id": channel,
                    "funnel": FUNNEL_STAGE_TO_AI.get(request.funnel_stage, "convert"),
                    "headline": f"{clinic.name} {request.event_name}",
                    "body": (
                        f"{request.core_message}\n\n"
                        f"핵심 포인트: {highlight_text}\n"
                        f"브랜드 톤: {', '.join(clinic.brand_tone)}\n"
                        "개인 상태에 따라 적합성과 회복 과정은 달라질 수 있어 상담 후 결정하세요."
                    ),
                    "cta": "상담 예약하기",
                    "note": "Backend fallback 초안입니다.",
                }
                for channel in PUBLIC_CONTENT_CHANNELS
            },
            "review_notes": [
                "AI 서버 fallback 템플릿으로 생성되었습니다.",
                "의료광고법 제56조 기준으로 과장·보장 표현을 검토하세요.",
            ],
        }

    def _adapt_headline(self, channel: str, headline: str) -> str:
        label = CHANNEL_LABELS.get(channel)
        return f"[{label}] {headline}" if label else headline

    def _adapt_body(self, channel: str, body: str) -> str:
        if channel == "ig_story":
            return body[:180]
        if channel == "kakao":
            return body[:300]
        if channel == "email":
            return f"안녕하세요.\n\n{body}"
        return body

    def _remove_banned_terms(self, text: str, banned_terms: list[str]) -> str:
        for term in banned_terms:
            text = text.replace(term, "주의 표현")
        return text

    def _build_consistency_checks(
        self,
        clinic: Clinic,
        request: ContentRequest,
        channels: dict[str, DraftContent],
    ) -> list[ConsistencyCheck]:
        full_text = " ".join([request.core_message] + [d.headline + " " + d.body for d in channels.values()])
        banned_hits = [term for term in clinic.banned_terms if term and term in full_text]
        price_mentions = [token for token in ("원", "%", "할인") if token in full_text]
        return [
            ConsistencyCheck(
                key="brand_tone",
                label="브랜드 톤",
                status="pass" if clinic.brand_tone else "warn",
                message="브랜드 톤이 생성 컨텍스트에 포함되었습니다." if clinic.brand_tone else "브랜드 톤이 비어 있습니다.",
                detail="브랜드 톤이 생성 컨텍스트에 포함되었습니다." if clinic.brand_tone else "브랜드 톤이 비어 있습니다.",
                channels=list(channels.keys()),
            ),
            ConsistencyCheck(
                key="banned_terms",
                label="금지어",
                status="fail" if banned_hits else "pass",
                message="금지어 후보가 발견되었습니다: " + ", ".join(banned_hits) if banned_hits else "금지어 후보가 발견되지 않았습니다.",
                detail="금지어 후보가 발견되었습니다: " + ", ".join(banned_hits) if banned_hits else "금지어 후보가 발견되지 않았습니다.",
                channels=list(channels.keys()),
            ),
            ConsistencyCheck(
                key="price",
                label="가격 정보",
                status="warn" if price_mentions else "pass",
                message="가격/할인 표현이 있으면 시뮬레이션 가격과 대조하세요." if price_mentions else "가격 표현이 본문에 직접 노출되지 않았습니다.",
                detail="가격/할인 표현이 있으면 시뮬레이션 가격과 대조하세요." if price_mentions else "가격 표현이 본문에 직접 노출되지 않았습니다.",
                channels=list(channels.keys()),
            ),
        ]
