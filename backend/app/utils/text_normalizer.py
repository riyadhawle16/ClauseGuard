"""
Text normalization utility.

Cleans obvious PDF extraction artifacts without altering the meaning
of the legal text. Does NOT paraphrase, rewrite, or interpret content.
"""
import re


def normalize_text(text: str) -> str:
    """
    Apply minimal, safe normalization to extracted PDF text:
    - Replace runs of whitespace (excluding newlines) with a single space
    - Collapse more than two consecutive newlines into two
    - Strip leading/trailing whitespace from each line
    - Strip leading/trailing whitespace from the overall result

    Does NOT change wording, correct spelling, or alter legal meaning.
    """
    if not text:
        return ""

    # Normalize non-newline whitespace runs to single space
    text = re.sub(r"[^\S\n]+", " ", text)

    # Strip trailing spaces from each line
    lines = [line.rstrip() for line in text.splitlines()]

    # Collapse more than 2 consecutive blank lines into 2
    normalized_lines = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                normalized_lines.append(line)
        else:
            blank_count = 0
            normalized_lines.append(line)

    return "\n".join(normalized_lines).strip()


def is_effectively_empty(text: str, min_chars: int = 20) -> bool:
    """
    Return True if the text contains fewer than min_chars non-whitespace
    characters — i.e., it is not meaningfully extractable.
    """
    return len(text.strip().replace("\n", "").replace(" ", "")) < min_chars
