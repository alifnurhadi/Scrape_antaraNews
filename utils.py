import re
from datetime import date, datetime , timedelta
from configuration import ID_MONTHS

def parse_timestamp(raw: str) -> date | None:
    print('parsing data')
    raw = raw.strip()
    if not raw:
        return None

    if "yesterday" in raw.lower() or "kemarin" in raw.lower():
            return date.today() - timedelta(days=1)

    m_ago = re.search(r"(\d+)\s+(hour|minute|min)s?\s+ago", raw, re.I)
    if m_ago:
        val = int(m_ago.group(1))
        unit = m_ago.group(2).lower()
        if unit == 'hour':
            return (datetime.now() - timedelta(hours=val)).date()
        else:
            return date.today()

    try:
        iso = re.sub(r"[+-]\d{2}:\d{2}$", "", raw).strip()
        return datetime.fromisoformat(iso).date()
    except ValueError:
        pass

    m = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s+(\d{4})", raw)
    if m:
        day = int(m.group(1))
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
        month = ID_MONTHS.get(m.group(2).lower()[:3])
        year = int(m.group(3))
        if month:
            try:
                return date(year, month, day)
            except ValueError:
                pass
    return None

def clean_text(text: str) -> str:
    print('cleaning text')
    return re.sub(r"\s+", " ", text).strip()
