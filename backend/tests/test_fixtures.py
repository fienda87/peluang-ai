"""Fixture corpus test: validate extraction against expected outputs."""
import json
from pathlib import Path

from app.modules.extraction.deterministic import DeterministicExtractor
from app.modules.ingestion.detect import detect_doc_type

FIXTURES = Path(__file__).parent / "fixtures"
EXPECTED = json.loads((FIXTURES / "expected" / "expected.json").read_text(encoding="utf-8"))


class TestDocTypeDetection:
    def test_html_detection(self):
        for f in (FIXTURES / "html").glob("*.html"):
            content = f.read_bytes()
            assert detect_doc_type(content, "text/html") == "HTML", f.name

    def test_pdf_detection(self):
        for f in (FIXTURES / "pdf").glob("*.pdf"):
            content = f.read_bytes()
            assert detect_doc_type(content, "application/pdf") == "PDF", f.name

    def test_image_detection(self):
        for f in (FIXTURES / "image").glob("*.png"):
            content = f.read_bytes()
            assert detect_doc_type(content, "image/png") == "IMAGE", f.name


class TestHTMLExtraction:
    def setup_method(self):
        self.extractor = DeterministicExtractor()

    def test_all_html_fixtures_extract_title(self):
        for f in (FIXTURES / "html").glob("*.html"):
            html = f.read_text(encoding="utf-8")
            result = self.extractor.extract_html(html)
            expected = EXPECTED.get(f.name, {})
            assert result.title is not None, f"{f.name}: title not extracted"
            if "title" in expected:
                assert expected["title"].lower() in result.title.lower(), (
                    f"{f.name}: expected '{expected['title']}', got '{result.title}'"
                )

    def test_all_html_fixtures_extract_category(self):
        for f in (FIXTURES / "html").glob("*.html"):
            html = f.read_text(encoding="utf-8")
            result = self.extractor.extract_html(html)
            expected = EXPECTED.get(f.name, {})
            if "category" in expected:
                assert result.category == expected["category"], (
                    f"{f.name}: expected category '{expected['category']}', got '{result.category}'"
                )

    def test_all_html_fixtures_extract_deadline(self):
        for f in (FIXTURES / "html").glob("*.html"):
            html = f.read_text(encoding="utf-8")
            result = self.extractor.extract_html(html)
            expected = EXPECTED.get(f.name, {})
            if "end_date" in expected:
                assert result.end_date is not None, f"{f.name}: end_date not extracted"
                assert result.end_date.isoformat() == expected["end_date"], (
                    f"{f.name}: expected {expected['end_date']}, got {result.end_date}"
                )

    def test_extraction_confidence_above_threshold(self):
        for f in (FIXTURES / "html").glob("*.html"):
            html = f.read_text(encoding="utf-8")
            result = self.extractor.extract_html(html)
            assert result.confidence >= 0.3, f"{f.name}: confidence too low ({result.confidence})"


class TestPDFExtraction:
    def test_pdf_files_exist_and_valid(self):
        from pypdf import PdfReader

        for f in (FIXTURES / "pdf").glob("*.pdf"):
            reader = PdfReader(str(f))
            assert len(reader.pages) >= 1, f"{f.name}: no pages"

    def test_pdf_metadata_contains_title(self):
        from pypdf import PdfReader

        for f in (FIXTURES / "pdf").glob("*.pdf"):
            reader = PdfReader(str(f))
            meta = reader.metadata
            expected = EXPECTED.get(f.name, {})
            if "title" in expected:
                assert meta and meta.title == expected["title"], (
                    f"{f.name}: expected title '{expected['title']}'"
                )


class TestImageFixtures:
    def test_image_files_exist_and_valid(self):
        from PIL import Image

        for f in (FIXTURES / "image").glob("*.png"):
            img = Image.open(f)
            assert img.size[0] > 0 and img.size[1] > 0, f"{f.name}: invalid image"

    def test_image_count(self):
        images = list((FIXTURES / "image").glob("*.png"))
        assert len(images) == 10


class TestCorpusCompleteness:
    def test_total_fixture_count(self):
        html_count = len(list((FIXTURES / "html").glob("*.html")))
        pdf_count = len(list((FIXTURES / "pdf").glob("*.pdf")))
        image_count = len(list((FIXTURES / "image").glob("*.png")))
        assert html_count == 10
        assert pdf_count == 10
        assert image_count == 10
        assert html_count + pdf_count + image_count == 30

    def test_expected_json_covers_all_fixtures(self):
        assert len(EXPECTED) == 30
