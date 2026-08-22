from datetime import date, datetime, timedelta

from app.modules.extraction.schema import ExtractionSchema
from app.shared.logging import get_logger

logger = get_logger("extraction.validation")


class ValidationService:
    REQUIRED_FIELDS = ["title", "end_date"]
    MIN_CONFIDENCE = 0.5

    def validate(self, schema: ExtractionSchema) -> tuple[bool, str]:
        if not schema.title or len(schema.title.strip()) < 5:
            return False, "title_too_short"

        if not schema.end_date:
            return False, "end_date_missing"

        try:
            if isinstance(schema.end_date, str):
                end = datetime.strptime(schema.end_date, "%Y-%m-%d").date()
            else:
                end = schema.end_date
        except (ValueError, TypeError):
            return False, "end_date_invalid_format"

        today = date.today()
        if end <= today:
            return False, "end_date_in_past"

        if end > today + timedelta(days=365 * 5):
            return False, "end_date_too_far_future"

        if schema.category and schema.category not in (
            "beasiswa",
            "lomba",
            "magang",
            "fellowship",
            "konferensi",
            "volunteer",
            "pelatihan",
            "riset",
            "kompetisi",
            "lainnya",
        ):
            return False, "category_invalid"

        if schema.gpa_requirement is not None:
            try:
                gpa = float(schema.gpa_requirement)
                if not (0.0 <= gpa <= 4.0):
                    return False, "gpa_requirement_out_of_range"
            except (ValueError, TypeError):
                return False, "gpa_requirement_invalid"

        return True, "valid"

    def compute_overall_confidence(self, schema: ExtractionSchema) -> float:
        fields_present = sum(
            [
                schema.title is not None,
                schema.description is not None,
                schema.end_date is not None,
                schema.organizer is not None,
                schema.location is not None,
                schema.prize is not None,
                schema.category is not None,
            ]
        )
        field_confidences = [v for v in schema.field_confidence.values() if isinstance(v, (int, float))]
        avg_confidence = (sum(field_confidences) / len(field_confidences)) if field_confidences else 0.5

        overall = (fields_present / 7.0) * 0.6 + avg_confidence * 0.4
        return round(min(overall, 1.0), 2)

    def determine_status(self, schema: ExtractionSchema, confidence: float) -> str:
        valid, reason = self.validate(schema)
        if not valid:
            logger.warning("validation_failed", reason=reason)
            return "invalid"

        if confidence >= self.MIN_CONFIDENCE:
            return "valid"

        logger.info("validation_low_confidence", confidence=confidence)
        return "needs_recovery"
