import json
from typing import Any

from app.modules.ai import AIPort, AIProviderError
from app.modules.extraction.schema import EXTRACTION_PROMPT_TEMPLATE, ExtractionSchema
from app.shared.logging import get_logger

logger = get_logger("extraction.llm")


class LLMExtractionService:
    def __init__(self, ai: AIPort) -> None:
        self.ai = ai

    async def extract_batch(
        self,
        texts: list[str],
        batch_size: int = 3,
    ) -> list[ExtractionSchema | None]:
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_results = await self._extract_batch_internal(batch)
            results.extend(batch_results)
        return results

    async def _extract_batch_internal(
        self,
        texts: list[str],
    ) -> list[ExtractionSchema | None]:
        if len(texts) == 1:
            return [await self.extract_single(texts[0])]

        combined_prompt = "Extract data from multiple opportunities (separate JSON objects):\n\n"
        for i, text in enumerate(texts, 1):
            combined_prompt += f"### Opportunity {i}\n{text}\n\n"
        combined_prompt += "Return a JSON array of objects matching the schema."

        try:
            response = await self.ai.structured_extract(
                combined_prompt,
                schema={"type": "array", "items": {"type": "object"}},
            )
        except AIProviderError as e:
            logger.error("batch_extraction_failed", error=e.code, text_count=len(texts))
            return [None] * len(texts)

        try:
            data = json.loads(response.content)
            if not isinstance(data, list):
                data = [data]
            results = []
            for item in data:
                if isinstance(item, dict):
                    results.append(self._parse_extraction(item))
                else:
                    results.append(None)
            while len(results) < len(texts):
                results.append(None)
            return results[:len(texts)]
        except json.JSONDecodeError as e:
            logger.error("batch_extraction_json_error", error=str(e))
            return [None] * len(texts)

    async def extract_single(self, text: str) -> ExtractionSchema | None:
        prompt = EXTRACTION_PROMPT_TEMPLATE.format(text=text[:3000])
        try:
            response = await self.ai.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1000,
            )
        except AIProviderError as e:
            logger.error("single_extraction_failed", error=e.code)
            return None

        try:
            data = json.loads(response.content)
            return self._parse_extraction(data)
        except json.JSONDecodeError as e:
            logger.error("single_extraction_json_error", error=str(e))
            return None

    def _parse_extraction(self, data: dict[str, Any]) -> ExtractionSchema | None:
        try:
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
            return schema
        except (TypeError, ValueError) as e:
            logger.error("extraction_parse_error", error=str(e))
            return None
