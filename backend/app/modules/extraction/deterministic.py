import re
from dataclasses import dataclass, field
from datetime import date

from app.shared.logging import get_logger

logger = get_logger("extraction.deterministic")

INDONESIAN_MONTHS = {
    "januari": 1, "februari": 2, "maret": 3, "april": 4,
    "mei": 5, "juni": 6, "juli": 7, "agustus": 8,
    "september": 9, "oktober": 10, "november": 11, "desember": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "jun": 6, "jul": 7, "agu": 8, "ags": 8, "sep": 9,
    "okt": 10, "nov": 11, "des": 12,
}

DEADLINE_KEYWORDS = [
    r"deadline", r"batas\s+akhir", r"penutupan", r"ditutup\s+(?:pada|tanggal)",
    r"pendaftaran\s+(?:ditutup|berakhir)", r"batas\s+waktu", r"closing\s+date",
    r"due\s+date", r"submission\s+deadline",
]

CATEGORY_KEYWORDS = {
    "beasiswa": [r"beasiswa", r"scholarship", r"bantuan\s+dana\s+studi", r"grant\s+studi"],
    "lomba": [r"lomba", r"kompetisi", r"competition", r"contest", r"olimpiade"],
    "magang": [r"magang", r"internship", r"intern", r"kerja\s+praktik", r"praktik\s+kerja"],
    "fellowship": [r"fellowship", r"program\s+fellow"],
    "konferensi": [r"konferensi", r"conference", r"seminar\s+nasional", r"simposium"],
    "volunteer": [r"volunteer", r"sukarelawan", r"relawan", r"pengabdian"],
    "pelatihan": [r"pelatihan", r"training", r"workshop", r"bootcamp", r"kursus"],
    "riset": [r"riset", r"penelitian", r"research", r"hibah\s+penelitian"],
    "kompetisi": [r"kompetisi", r"hackathon", r"challenge"],
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
URL_RE = re.compile(r"https?://[^\s<>\"']+")

DATE_PATTERNS = [
    re.compile(r"(\d{1,2})\s+(" + "|".join(INDONESIAN_MONTHS.keys()) + r")\s+(\d{4})", re.I),
    re.compile(r"(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})"),
    re.compile(r"(\d{4})[/\-](\d{1,2})[/\-](\d{1,2})"),
]

GPA_RE = re.compile(
    r"(?:IPK|IP)\s*(?:minimal|min|≥|>=|:)?\s*(\d[.,]\d{1,2})", re.I
)


@dataclass
class DeterministicResult:
    title: str | None = None
    url: str | None = None
    description: str | None = None
    end_date: date | None = None
    start_date: date | None = None
    organizer: str | None = None
    location: str | None = None
    prize: str | None = None
    category: str | None = None
    emails: list[str] = field(default_factory=list)
    gpa_requirement: float | None = None
    confidence: float = 0.0
    fields_found: int = 0
    fields_total: int = 8


def clean_title(title: str) -> str:
    """Bersihkan judul dari nav junk, HTML entities, dan suffix situs."""
    import html as html_mod
    import re

    t = html_mod.unescape(title or "")
    for junk in ("Skip to content", "Skip to main content", "Menu and widgets"):
        t = re.sub(re.escape(junk), " | ", t, flags=re.I)
    # potong di separator situs umum
    t = re.split(r"\s+[|–—-]\s+", t)[0]
    # buang sisa kata nav umum setelah potongan pertama
    t = t.split(" :: ")[0]
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" |–—-")
    return t[:200]


def strip_html(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_title_from_html(html: str) -> str | None:
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if m:
        title = m.group(1).strip()
        title = re.sub(r"\s*[|\-–—]\s*.*$", "", title)
        if len(title) > 5:
            return title[:255]
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    if m:
        title = strip_html(m.group(1)).strip()
        if len(title) > 5:
            return title[:255]
    return None


def parse_indonesian_date(text: str) -> date | None:
    m = DATE_PATTERNS[0].search(text)
    if m:
        day, month_str, year = int(m.group(1)), m.group(2).lower(), int(m.group(3))
        month = INDONESIAN_MONTHS.get(month_str)
        if month and 1 <= day <= 31 and 2020 <= year <= 2035:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    m = DATE_PATTERNS[1].search(text)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= day <= 31 and 1 <= month <= 12 and 2020 <= year <= 2035:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    m = DATE_PATTERNS[2].search(text)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= day <= 31 and 1 <= month <= 12 and 2020 <= year <= 2035:
            try:
                return date(year, month, day)
            except ValueError:
                pass
    return None


def extract_deadline(text: str) -> date | None:
    for kw in DEADLINE_KEYWORDS:
        m = re.search(kw + r"[:\s]*(.{0,60})", text, re.I)
        if m:
            context = m.group(1)
            d = parse_indonesian_date(context)
            if d:
                return d
    return None


def extract_category(text: str) -> str | None:
    text_lower = text.lower()
    scores: dict[str, int] = {}
    for category, patterns in CATEGORY_KEYWORDS.items():
        count = sum(1 for p in patterns if re.search(p, text_lower))
        if count > 0:
            scores[category] = count
    if not scores:
        return None
    return max(scores, key=scores.get)


def extract_organizer(text: str) -> str | None:
    patterns = [
        r"(?:diselenggarakan|diselenggrakan)\s+oleh[:\s]+([^\n.]{5,80})",
        r"penyelenggara[:\s]+([^\n.]{5,80})",
        r"organizer[:\s]+([^\n.]{5,80})",
        r"oleh[:\s]+([^\n.]{5,80})",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip()[:255]
    return None


def extract_prize(text: str) -> str | None:
    patterns = [
        r"(?:total\s+)?hadiah[:\s]+([^\n.]{5,120})",
        r"prize[:\s]+([^\n.]{5,120})",
        r"(?:berhadiah|hadiah\s+total)\s+([^\n.]{5,120})",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip()[:255]
    return None


def extract_location(text: str) -> str | None:
    patterns = [
        r"(?:lokasi|tempat|lokasi\s+kegiatan)[:\s]+([^\n.]{3,80})",
        r"(?:bertempat|dilaksanakan)\s+di[:\s]+([^\n.]{3,80})",
        r"location[:\s]+([^\n.]{3,80})",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1).strip()[:255]
    return None


class DeterministicExtractor:
    def extract_html(self, html: str, source_url: str | None = None) -> DeterministicResult:
        text = strip_html(html)
        result = DeterministicResult()
        result.title = extract_title_from_html(html)
        result.url = source_url
        result.description = text[:2000] if len(text) > 100 else None
        result.end_date = extract_deadline(text)
        result.category = extract_category(text)
        result.organizer = extract_organizer(text)
        result.prize = extract_prize(text)
        result.location = extract_location(text)
        result.emails = EMAIL_RE.findall(text)[:5]

        gpa_m = GPA_RE.search(text)
        if gpa_m:
            result.gpa_requirement = float(gpa_m.group(1).replace(",", "."))

        self._compute_confidence(result)
        return result

    def extract_text(self, text: str, source_url: str | None = None) -> DeterministicResult:
        result = DeterministicResult()
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        if lines:
            candidate = max(lines[:5], key=len)
            if len(candidate) > 10:
                result.title = candidate[:255]
        result.url = source_url
        result.description = text[:2000] if len(text) > 100 else None
        result.end_date = extract_deadline(text)
        result.category = extract_category(text)
        result.organizer = extract_organizer(text)
        result.prize = extract_prize(text)
        result.location = extract_location(text)
        result.emails = EMAIL_RE.findall(text)[:5]

        gpa_m = GPA_RE.search(text)
        if gpa_m:
            result.gpa_requirement = float(gpa_m.group(1).replace(",", "."))

        self._compute_confidence(result)
        return result

    def _compute_confidence(self, result: DeterministicResult) -> None:
        found = sum([
            result.title is not None,
            result.end_date is not None,
            result.category is not None,
            result.organizer is not None,
            result.description is not None,
            result.location is not None,
            result.prize is not None,
            result.url is not None,
        ])
        result.fields_found = found
        result.confidence = round(found / result.fields_total, 2)
