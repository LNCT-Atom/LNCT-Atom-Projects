"""Shared text-cleaning helpers for the resume parsing pipeline.

Used by both the deterministic parser and the AI extractor to normalise
free-text values (summaries, descriptions) and institution names.
"""
import re
from typing import Optional, Tuple


def clean_text(val: Optional[str]) -> Optional[str]:
    """Normalise a free-text value extracted from a PDF.

    Steps (applied in this exact order):
    1. Convert literal two-char sequence ``\\n`` (backslash + n that survived
       JSON round-tripping) into a real newline.
    2. Rejoin line-wrap hyphenation: a hyphen sitting at the end of a line
       followed by a lowercase letter on the next line is a word that was
       broken by the PDF renderer.
       Example: ``"Tech-\\nnocrats"`` → ``"Technocrats"``.
       NOTE: a genuinely hyphenated word broken at a line end
       (``"full-\\nstack"``) becomes ``"fullstack"``.  This cannot be told
       apart reliably, so it is an accepted trade-off.
    3. Replace all remaining newlines (``\\n``, ``\\r\\n``) with a single space.
       Example: ``"React.js,\\nNode.js"`` → ``"React.js, Node.js"``.
    4. Collapse repeated whitespace and trim.

    Real mid-word hyphens that are NOT followed by a newline
    (``full-stack``, ``IoT-based``) stay unchanged.
    """
    if val is None:
        return None

    text = val

    # 1. Literal backslash-n → real newline
    text = text.replace("\\n", "\n")

    # 2. Rejoin line-wrap hyphenation
    text = re.sub(r"-\s*\n\s*([a-z])", r"\1", text)

    # 3. Remaining newlines → single space
    text = text.replace("\r\n", " ").replace("\n", " ")

    # 4. Collapse whitespace and trim
    text = re.sub(r"[ \t]+", " ", text).strip()

    return text if text else None


def clean_institution(
    text: Optional[str],
    start_year: Optional[str] = None,
    end_year: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Strip trailing percentage/CGPA and trailing year range from an institution name.

    Returns ``(cleaned_institution, start_year, end_year)``.

    * Trailing percentages e.g. "87.4%", "(87.4%)", "8.5 CGPA" are stripped.
    * ``start_year`` / ``end_year`` are filled **only** when the caller's
      current values are empty (``None`` or ``""``).
    * Institution names without trailing scores or year ranges are returned untouched.
    """
    if not text:
        return text, start_year, end_year

    cleaned = text.strip()

    # 1. Strip trailing percentage or CGPA e.g. "PCM Senior Secondary School 87.4%" -> "PCM Senior Secondary School"
    pct_pattern = r"\s*,?\s*\(?(?:(?:[0-9]{1,2}(?:\.[0-9]{1,2})?\s*%)|(?:[0-9](?:\.[0-9]{1,2})?\s*(?:/\s*10|cgpa|gpa)))\)?\s*$"
    cleaned = re.sub(pct_pattern, "", cleaned, flags=re.IGNORECASE).strip()

    # 2. Match trailing year ranges like "2023-2027", "2023–2027", "2023—2027",
    # "2023 to 2027", optionally preceded by a comma and/or wrapped in parens.
    year_pattern = r"\s*,?\s*\(?((?:19|20)\d{2})\s*(?:[-\u2013\u2014]|to)\s*((?:19|20)\d{2})\)?\s*$"
    m = re.search(year_pattern, cleaned)
    if m:
        yr_cleaned = cleaned[: m.start()].strip()
        # Fill years only when currently empty
        if not start_year:
            start_year = m.group(1)
        if not end_year:
            end_year = m.group(2)
        cleaned = yr_cleaned if yr_cleaned else cleaned

    # 3. Strip a standalone trailing year e.g. "ABES College, Noida 2024" → "ABES College, Noida"
    standalone_year_pattern = r"\s*,?\s*\(?((?:19|20)\d{2})\)?\s*$"
    m2 = re.search(standalone_year_pattern, cleaned)
    if m2:
        yr_cleaned = cleaned[: m2.start()].strip()
        if yr_cleaned:  # Only strip if something remains
            if not start_year:
                start_year = m2.group(1)
            cleaned = yr_cleaned

    # Clean trailing punctuation
    cleaned = re.sub(r"^[,\-–—:\s]+|[,\-–—:\s]+$", "", cleaned).strip()

    return cleaned if cleaned else text, start_year, end_year

