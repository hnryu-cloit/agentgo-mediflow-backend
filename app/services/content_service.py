from __future__ import annotations
import httpx
from typing import List, Dict
from app.schemas.contracts import Clinic, ContentRequest, DraftContent, GenerationResponse

AI_API_URL = "http://localhost:8001/generate"

class ContentService:
    async def generate(self, clinic: Clinic, request: ContentRequest) -> GenerationResponse:
        """
        AI 모듈 API를 호출하여 콘텐츠를 생성합니다 (Backend <-> AI 연동).
        """
        # 1. AI 모듈 스키마에 맞게 데이터 변환
        ai_payload = {
            "payload": {
                "product": request.event_name,
                "summary": request.core_message,
                "goals": request.highlights,
                "features": request.highlights
            },
            "brand": {
                "hospital_name": clinic.name,
                "target_audience": clinic.target_audience,
                "doctor_philosophy": clinic.doctor_philosophy,
                "signature_procedures": clinic.signature_procedures,
                "brand_tone": clinic.brand_tone,
                "banned_terms": clinic.banned_terms
            }
        }

        # 2. AI API 호출
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(AI_API_URL, json=ai_payload, timeout=10.0)
                response.raise_for_status()
                ai_data = response.json()
            except Exception as e:
                # AI API 호출 실패 시 Fallback 로직 또는 에러 처리
                raise RuntimeError(f"AI 모듈 연동 실패: {str(e)}")

        # 3. AI 결과를 Backend 스키마로 변환
        channels: Dict[str, DraftContent] = {}
        for ch_id, content in ai_data["channels"].items():
            if ch_id in request.channels:
                channels[ch_id] = DraftContent(
                    headline=content["headline"],
                    body=content["body"],
                    cta=content["cta"]
                )

        return GenerationResponse(
            event_name=request.event_name,
            channels=channels,
            review_notes=ai_data["review_notes"]
        )
