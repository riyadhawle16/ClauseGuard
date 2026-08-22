"""
PDF extraction service.

Extracts text page-by-page from a PDF using pypdf.
Page numbers are 1-based.
No AI, no LLM, no OCR — pure text extraction only.
"""
import io
from dataclasses import dataclass
from typing import List

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.utils.text_normalizer import normalize_text, is_effectively_empty


class ExtractionError(Exception):
    """Raised when PDF text extraction fails or yields no usable content."""


@dataclass
class PageText:
    page_number: int   # 1-based
    text: str          # normalized extracted text


def extract_text_by_page(file_bytes: bytes) -> List[PageText]:
    """
    Extract text from each page of a PDF, returning a list of PageText
    objects with 1-based page numbers.

    Raises ExtractionError if:
    - the bytes cannot be parsed as a PDF
    - the PDF has no pages
    - all pages yield empty/effectively-empty text (scanned/image PDF)
    """
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
    except PdfReadError as exc:
        raise ExtractionError(f"Could not read PDF: {exc}") from exc
    except Exception as exc:
        raise ExtractionError(f"Unexpected error opening PDF: {exc}") from exc

    if len(reader.pages) == 0:
        raise ExtractionError("PDF contains no pages.")

    pages: List[PageText] = []
    for i, page in enumerate(reader.pages):
        try:
            raw = page.extract_text() or ""
        except Exception:
            raw = ""
        normalized = normalize_text(raw)
        pages.append(PageText(page_number=i + 1, text=normalized))

    # Fail fast if every page is empty — likely a scanned/image-only PDF
    if all(is_effectively_empty(p.text) for p in pages):
        raise ExtractionError(
            "No extractable text found in this document. "
            "The file may be a scanned image — OCR is not supported."
        )

    return pages
