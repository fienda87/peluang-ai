from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractionSchema:
    title: str | None = None
    description: str | None = None
    end_date: str | None = None
    start_date: str | None = None
    organizer: str | None = None
    location: str | None = None
    prize: str | None = None
    category: str | None = None
    gpa_requirement: float | None = None
    field_confidence: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "end_date": self.end_date,
            "start_date": self.start_date,
            "organizer": self.organizer,
            "location": self.location,
            "prize": self.prize,
            "category": self.category,
            "gpa_requirement": self.gpa_requirement,
            "field_confidence": self.field_confidence,
        }


EXTRACTION_PROMPT_TEMPLATE = """Extract structured opportunity data from text.
Return valid JSON matching this schema:
{{
  "title": "string or null",
  "description": "string or null",
  "end_date": "YYYY-MM-DD or null",
  "start_date": "YYYY-MM-DD or null",
  "organizer": "string or null",
  "location": "string or null",
  "prize": "string or null",
  "category": "beasiswa|lomba|magang|fellowship|konferensi|volunteer|pelatihan|riset|kompetisi|lainnya or null",
  "gpa_requirement": "float (e.g., 3.0) or null",
  "field_confidence": {{"field_name": 0.0-1.0, ...}}
}}

Text:
{text}

Return ONLY the JSON object, no explanation."""
