import io
from dataclasses import dataclass

import pytesseract
from PIL import Image

from app.shared.config import get_app_config
from app.shared.logging import get_logger

logger = get_logger("ingestion.ocr")


@dataclass
class OCRResult:
    text: str
    confidence: float
    needs_vision: bool


class OCRAdapter:
    def __init__(self) -> None:
        cfg = get_app_config().get("ocr", {})
        self.languages = cfg.get("languages", "ind+eng")
        self.min_confidence = cfg.get("min_confidence", 0.6)

    def extract(self, content: bytes) -> OCRResult:
        try:
            image = Image.open(io.BytesIO(content))
        except Exception as e:
            logger.error("ocr_image_open_failed", error=str(e))
            return OCRResult(text="", confidence=0.0, needs_vision=True)

        try:
            data = pytesseract.image_to_data(
                image, lang=self.languages, output_type=pytesseract.Output.DICT
            )
        except pytesseract.TesseractError as e:
            logger.error("ocr_tesseract_failed", error=str(e))
            return OCRResult(text="", confidence=0.0, needs_vision=True)

        words = []
        confidences = []
        for i, conf in enumerate(data["conf"]):
            text = data["text"][i].strip()
            if not text:
                continue
            try:
                c = float(conf)
            except (ValueError, TypeError):
                c = 0.0
            if c > 0:
                words.append(text)
                confidences.append(c)

        full_text = " ".join(words).strip()
        avg_confidence = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.0

        needs_vision = avg_confidence < self.min_confidence or len(full_text) < 20

        logger.info(
            "ocr_completed",
            confidence=round(avg_confidence, 3),
            word_count=len(words),
            needs_vision=needs_vision,
        )
        return OCRResult(text=full_text, confidence=avg_confidence, needs_vision=needs_vision)
