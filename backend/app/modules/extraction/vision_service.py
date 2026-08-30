import base64

from app.modules.ai import AIPort, AIProviderError
from app.modules.extraction.schema import ExtractionSchema
from app.shared.logging import get_logger

logger = get_logger("extraction.vision")


class VisionExtractionService:
    def __init__(self, ai: AIPort) -> None:
        self.ai = ai

    async def extract_from_image(self, image_bytes: bytes) -> ExtractionSchema | None:
        if len(image_bytes) > 10 * 1024 * 1024:
            logger.warning("image_too_large", size=len(image_bytes))
            return None

        prompt = (
            "This is a poster or document image containing opportunity information. "
            "Extract all structured data: title, description, deadline, organizer, location, prize, category, requirements. "
            "Return JSON with schema: {title, description, end_date, start_date, organizer, location, prize, category, "
            "gpa_requirement, field_confidence}. Return ONLY valid JSON."
        )

        try:
            # Vision selalu route ke model VL via purpose key
            vision_model = self.ai.get_model("vision")
            response = await self.ai.chat(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64.b64encode(image_bytes).decode(),
                                },
                            },
                        ],
                    }
                ],
                temperature=0.0,
                max_tokens=1000,
                model_key=vision_model,
            )
        except AIProviderError as e:
            logger.error("vision_extraction_failed", error=e.code)
            return None

        import json

        try:
            data = json.loads(response.content)
            schema = ExtractionSchema(
                title=data.get("title"),
                description=data.get("description"),
                end_date=data.get("end_date"),
                start_date=data.get("start_date"),
                organizer=data.get("organizer"),
                location=data.get("location"),
                prize=data.get("prize"),
                category=data.get("category"),
                gpa_requirement=data.get("gpa_requirement"),
                field_confidence=data.get("field_confidence", {}),
            )
            logger.info("vision_extraction_success", fields_found=len([f for f in [schema.title, schema.end_date, schema.organizer] if f]))
            return schema
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.error("vision_extraction_parse_error", error=str(e))
            return None
