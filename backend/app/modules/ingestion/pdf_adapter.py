import io
from dataclasses import dataclass

from pypdf import PdfReader

from app.shared.logging import get_logger

logger = get_logger("ingestion.pdf")


@dataclass
class PDFResult:
    text: str
    page_count: int
    has_text_layer: bool


class PDFAdapter:
    def extract_text(self, content: bytes) -> PDFResult:
        try:
            reader = PdfReader(io.BytesIO(content))
        except Exception as e:
            logger.error("pdf_parse_failed", error=str(e))
            return PDFResult(text="", page_count=0, has_text_layer=False)

        pages_text = []
        for page in reader.pages:
            try:
                pages_text.append(page.extract_text() or "")
            except Exception:
                pages_text.append("")

        full_text = "\n".join(pages_text).strip()
        has_text = len(full_text) > 50

        if not has_text:
            logger.info("pdf_no_text_layer", pages=len(reader.pages))

        return PDFResult(
            text=full_text,
            page_count=len(reader.pages),
            has_text_layer=has_text,
        )
