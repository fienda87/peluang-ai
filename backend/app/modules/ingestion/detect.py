PDF_MAGIC = b"%PDF"
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG"
GIF_MAGIC = b"GIF8"
WEBP_MAGIC = b"RIFF"


def detect_doc_type(content: bytes, content_type: str = "") -> str:
    ct = content_type.lower()
    if "pdf" in ct or content[:4] == PDF_MAGIC:
        return "PDF"
    if any(m in ct for m in ("jpeg", "jpg", "png", "gif", "webp", "image")):
        return "IMAGE"
    if content[:3] == JPEG_MAGIC or content[:4] == PNG_MAGIC:
        return "IMAGE"
    if content[:4] == GIF_MAGIC:
        return "IMAGE"
    if content[:4] == WEBP_MAGIC and content[8:12] == b"WEBP":
        return "IMAGE"
    if "html" in ct or "xml" in ct:
        return "HTML"
    try:
        head = content[:512].decode("utf-8", errors="ignore").lower()
        if "<html" in head or "<!doctype" in head or "<div" in head:
            return "HTML"
    except Exception:
        pass
    return "OTHER"
