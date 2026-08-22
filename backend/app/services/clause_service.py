"""
Clause extraction service — deterministic, no AI/LLM.

Strategy (applied in order):
1. Detect numbered headings: "1.", "1.1", "2.3.1", etc. at line start.
2. Detect ALL-CAPS headings (≥ 4 chars, short line ≤ 80 chars).
3. Detect Title-Case headings (short line ≤ 60 chars, not a sentence).
4. Fallback: if no structured headings found on a page, treat the entire
   page as a single clause record.

Primary requirement: NO EXTRACTED TEXT IS LOST.
A page-level fallback is always applied when heuristics yield nothing.
"""
import re
import uuid as uuid_module
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.pdf_service import PageText
from app.models.clause import Clause


# ── Heading detection patterns ────────────────────────────────────────────────

# Numbered heading: "1.", "1.1", "1.1.1", "2.3" at start of line (optional spaces)
_NUMBERED = re.compile(r"^\s*(\d+(?:\.\d+)*\.?)\s+\S")

# ALL-CAPS heading: line of ≥ 4 uppercase letters, ≤ 80 chars total
_ALLCAPS = re.compile(r"^[A-Z][A-Z\s\-&/]{3,79}$")

# Title-case heading: short line (≤ 60 chars), each word capitalized,
# does NOT end with sentence punctuation
_TITLECASE = re.compile(r"^(?:[A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+)$")


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if _NUMBERED.match(stripped):
        return True
    if len(stripped) <= 80 and _ALLCAPS.match(stripped):
        return True
    if len(stripped) <= 60 and _TITLECASE.match(stripped):
        return True
    return False


def _extract_heading_label(line: str) -> Optional[str]:
    """Return the heading text, stripped."""
    return line.strip() or None


# ── Main extraction function ──────────────────────────────────────────────────

@dataclass
class ClauseData:
    document_id: str
    clause_number: int
    heading: Optional[str]
    content: str
    page_number: int


def extract_clauses(pages: List[PageText], document_id: str) -> List[ClauseData]:
    """
    Extract clauses from page-indexed text.

    Returns a list of ClauseData objects with stable, sequential
    clause_number values (1, 2, 3, …).

    Fallback: if no heading is detected on a page, the entire page text
    becomes one clause record — no text is ever discarded.
    """
    result: List[ClauseData] = []
    clause_counter = 0

    for page in pages:
        if not page.text.strip():
            # Completely blank page — skip, nothing to store
            continue

        lines = page.text.splitlines()
        page_clauses = _extract_from_page_lines(lines, page.page_number, document_id)

        if page_clauses:
            for cd in page_clauses:
                clause_counter += 1
                result.append(ClauseData(
                    document_id=document_id,
                    clause_number=clause_counter,
                    heading=cd.heading,
                    content=cd.content,
                    page_number=cd.page_number,
                ))
        else:
            # Fallback: whole page as one clause
            clause_counter += 1
            result.append(ClauseData(
                document_id=document_id,
                clause_number=clause_counter,
                heading=None,
                content=page.text.strip(),
                page_number=page.page_number,
            ))

    return result


def _extract_from_page_lines(
    lines: List[str], page_number: int, document_id: str
) -> List[ClauseData]:
    """
    Try to split a page's lines into headed clauses.
    Returns an empty list if no headings are detected (triggers fallback).
    """
    # First pass: check if any headings exist on this page
    has_headings = any(_is_heading(line) for line in lines)
    if not has_headings:
        return []

    clauses: List[ClauseData] = []
    current_heading: Optional[str] = None
    current_lines: List[str] = []

    def _flush(heading, body_lines, pnum, doc_id):
        content = "\n".join(body_lines).strip()
        if content:
            clauses.append(ClauseData(
                document_id=doc_id,
                clause_number=0,       # renumbered by caller
                heading=heading,
                content=content,
                page_number=pnum,
            ))

    for line in lines:
        if _is_heading(line):
            # Flush previous clause
            _flush(current_heading, current_lines, page_number, document_id)
            current_heading = _extract_heading_label(line)
            current_lines = []
        else:
            current_lines.append(line)

    # Flush last clause
    _flush(current_heading, current_lines, page_number, document_id)

    # If heading detection fired but all body content was empty,
    # fall back to treating the whole page as one block.
    if not clauses:
        return []

    return clauses


def build_clause_records(clause_data: List[ClauseData]) -> List[Clause]:
    """Convert ClauseData list into Clause ORM objects ready for bulk insert."""
    records = []
    for cd in clause_data:
        records.append(Clause(
            id=uuid_module.uuid4(),
            document_id=cd.document_id,
            clause_number=cd.clause_number,
            heading=cd.heading,
            content=cd.content,
            page_number=cd.page_number,
        ))
    return records
