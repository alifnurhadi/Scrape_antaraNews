import re
from datetime import date, datetime, timedelta


def Parser_timestamp(raw: str) -> date | None:
    """
    Parse timestamps emitted by antaranews.com.

    Known formats:
      • "3 Mei 2025 08:45 WIB"
      • "Minggu, 4 Mei 2025 10:00 WIB"
      • "2025-05-03T08:45:00+07:00"   (ISO-8601 in <time> tags)
      • "03/05/2025 08:45"
    Returns a date object or None.
    """
    raw = raw.strip()
    if not raw:
        return None

    # ── ISO-8601 ──────────────────────────────────────────────────────────
    try:
        # strip timezone offset if present
        iso = re.sub(r"[+-]\d{2}:\d{2}$", "", raw).strip()
        return datetime.fromisoformat(iso).date()
    except ValueError:
        pass

    # ── numeric DD/MM/YYYY ────────────────────────────────────────────────
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    # ── Indonesian long form: "3 Mei 2025" ───────────────────────────────
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

    log.debug("Could not parse timestamp: %r", raw)
    return None


def CleaningText(text: str) -> str:
    """Strip excessive whitespace, normalise newlines."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def Parser_text_from_list(soup: BeautifulSoup) -> list[dict]:
    """
    Returns list of  {"link": str, "date": date}  dicts.

    Antaranews list-page patterns (observed across redesigns):

    Pattern A  — <div class="simple-list-*">  or  <div class="card-*">
                   └─ <a class="..." href="…">
                        ├─ <span class="...title...">…title…</span>
                        └─ <span class="...date..."><i class="…clock…"></i> 3 Mei 2025</span>

    Pattern B  — <div class="col-md-...">
                   └─ <a href="…">
                        ├─ <p class="...title...">…title…</p>
                        └─ <span class="..."><i>…</i> timestamp</span>

    We use a broad approach: find every <a> that contains a clock/date indicator,
    then extract the sibling/nested timestamp text.
    """
    results = []
    seen_links: set[str] = set()

    # ── Selector A: anchor tags that wrap the whole card ──────────────────
    # antaranews uses hrefs like /berita/XXXXXXX/slug  or  /ekonomi/bisnis/berita/…
    anchors = soup.find_all("a", href=re.compile(r"/berita/\d+/"))

    for a in anchors:
        href = a.get("href", "").strip()
        if not href:
            continue
        full_url = href if href.startswith("http") else BASE_URL + href
        if full_url in seen_links:
            continue

        # ── Find timestamp ── priority order:
        # 1. <i> tag with clock class inside this <a> or its closest container
        # 2. sibling <span> with date text
        # 3. parent container with a <span>/<time> tag

        raw_ts: str | None = None

        # 1) <i> inside the anchor or its parent container
        container = a.parent or a
        i_tags = container.find_all(
            "i", class_=re.compile(r"clock|time|calendar|date", re.I)
        )
        for i_tag in i_tags:
            # text usually follows the <i> tag in the same <span>
            parent_span = i_tag.parent
            if parent_span:
                raw_ts = parent_span.get_text(" ", strip=True)
                raw_ts = re.sub(r"^[^\d]*", "", raw_ts)  # drop icon text junk
                break

        # 2) <time datetime="…"> anywhere in the container
        if not raw_ts:
            time_tag = container.find("time")
            if time_tag:
                raw_ts = time_tag.get("datetime") or time_tag.get_text(strip=True)

        # 3) Any <span> whose text looks like a date
        if not raw_ts:
            for span in container.find_all("span"):
                txt = span.get_text(" ", strip=True)
                if re.search(r"\d{1,2}\s+[A-Za-z]+\s+\d{4}", txt):
                    raw_ts = txt
                    break

        if not raw_ts:
            log.debug("No timestamp for %s — skipping", full_url)
            continue

        parsed = _parse_timestamp(raw_ts)
        if parsed is None:
            log.debug("Unparseable timestamp %r for %s", raw_ts, full_url)
            continue

        seen_links.add(full_url)
        results.append({"link": full_url, "date": parsed})

    return results
