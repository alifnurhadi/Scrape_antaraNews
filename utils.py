import re
from datetime import date, datetime
from configuration import ID_MONTHS

def parse_timestamp(raw: str) -> date | None:
    """Parse AntaraNews timestamps into a Python date object."""
    print('parsing data')
    raw = raw.strip()
    if not raw:
        return None

    try:
        iso = re.sub(r"[+-]\d{2}:\d{2}$", "", raw).strip()
        return datetime.fromisoformat(iso).date()
    except ValueError:
        pass

    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})", raw)
    if m:
        day = int(m.group(1))
        # Ensure robust matching by checking the first 3 letters
        month = ID_MONTHS.get(m.group(2).lower()[:3])
        year = int(m.group(3))
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                pass

    m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", raw)
    if m:
        day = int(m.group(1))
        # Ensure robust matching by checking the first 3 letters
        month = ID_MONTHS.get(m.group(2).lower()[:3])
        year = int(m.group(3))
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                pass
    return None

def clean_text(text: str) -> str:
    """Strip excessive whitespace and normalize newlines."""
    print('cleaning text')
    return re.sub(r"\s+", " ", text).strip()
