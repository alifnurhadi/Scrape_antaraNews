import json
import logging
import re
import time
import uuid


import requests
from bs4 import BeautifulSoup





# ---------------------------------------------------------------------------
# Step 1 – Collect candidate article links from the list page(s)
# ---------------------------------------------------------------------------



def collect_candidates(target_date: date) -> list[str]:
    """
    Paginate the list page, collect all article links dated == target_date.
    Returns list of unique URLs.
    """
    links: list[str] = []
    seen: set[str] = set()

    # Antaranews paginates via  ?page=N  or  /page/N  (try both)
    for page_num in range(1, MAX_LIST_PAGES + 1):
        if page_num == 1:
            url = LIST_URL
        else:
            url = f"{LIST_URL}?page={page_num}"

        log.info("Fetching list page %d: %s", page_num, url)
        soup = _get(url)
        if soup is None:
            log.warning("Failed to fetch list page %d — stopping pagination", page_num)
            break

        articles = _extract_articles_from_list(soup)
        if not articles:
            log.info("No articles found on page %d — stopping pagination", page_num)
            break

        found_on_page = 0
        older_than_target = 0

        for art in articles:
            if art["date"] == target_date:
                if art["link"] not in seen:
                    seen.add(art["link"])
                    links.append(art["link"])
                    found_on_page += 1
            elif art["date"] < target_date:
                older_than_target += 1

        log.info(
            "Page %d → %d total articles | %d matched | %d older",
            page_num,
            len(articles),
            found_on_page,
            older_than_target,
        )

        # If most articles are already older than our target, stop paginating
        if older_than_target > len(articles) * 0.6:
            log.info("Majority of articles are older — stopping pagination")
            break

        time.sleep(0.5)

    return links


# ---------------------------------------------------------------------------
# Step 2 – Fetch detail page and extract full article text
# ---------------------------------------------------------------------------


def extract_article_text(url: str) -> str | None:
    """
    Fetch an article page and return the clean full-text string,
    or None if extraction fails.

    Antaranews article body selectors (observed):
      • <div class="post-content"> … <p> … </p> … </div>
      • <div class="detail-text"> … <p> … </p> … </div>
      • <div class="single-post-content"> … </div>
    We try all candidates and pick the richest one.
    """
    soup = _get(url)
    if soup is None:
        return None

    # Remove boilerplate sections
    for tag in soup.find_all(
        ["script", "style", "noscript", "aside", "nav", "footer", "header"]
    ):
        tag.decompose()

    # Remove known ad / promo containers
    for tag in soup.find_all(
        class_=re.compile(
            r"ads|advertisement|promo|related|rekomendasi|"
            r"sidebar|widget|social|share|comment|subscribe|"
            r"newsletter|banner|iklan",
            re.I,
        )
    ):
        tag.decompose()

    # Candidate content selectors (ordered by specificity)
    CONTENT_SELECTORS = [
        {"class": re.compile(r"post.?content", re.I)},
        {"class": re.compile(r"detail.?text", re.I)},
        {"class": re.compile(r"single.?post", re.I)},
        {"class": re.compile(r"article.?body", re.I)},
        {"class": re.compile(r"entry.?content", re.I)},
        {"class": re.compile(r"news.?content", re.I)},
        {"class": re.compile(r"content.?detail", re.I)},
    ]

    best_div = None
    best_len = 0

    for sel in CONTENT_SELECTORS:
        div = soup.find("div", sel)
        if div:
            candidate_len = len(div.get_text(strip=True))
            if candidate_len > best_len:
                best_len = candidate_len
                best_div = div

    # Fallback: find the <div> with the most <p> children
    if best_div is None:
        divs = soup.find_all("div")
        for div in divs:
            p_count = len(div.find_all("p", recursive=False))
            text_len = len(div.get_text(strip=True))
            if p_count >= 3 and text_len > best_len:
                best_len = text_len
                best_div = div

    if best_div is None:
        log.warning("No content container found for %s", url)
        return None

    # ── Extract paragraphs ────────────────────────────────────────────────
    paragraphs: list[str] = []
    seen_para: set[str] = set()

    for p in best_div.find_all("p"):
        # Skip paragraphs that are inside aside/figure/caption/footer
        if p.find_parent(["aside", "figure", "figcaption", "footer"]):
            continue
        text = _clean_text(p.get_text(separator=" "))
        if not text:
            continue

        # Skip very short "paragraphs" (likely labels / buttons)
        if len(text) < 20:
            continue

        # Skip duplicates
        if text in seen_para:
            continue
        seen_para.add(text)

        # Skip common boilerplate snippets
        BOILERPLATE_PATTERNS = [
            r"^Baca juga",
            r"^Pewarta\s*:",
            r"^Editor\s*:",
            r"^COPYRIGHT\s*©",
            r"^Hak Cipta",
            r"^Antara News",
            r"^\*\s*",
        ]
        if any(re.match(pat, text, re.I) for pat in BOILERPLATE_PATTERNS):
            continue

        paragraphs.append(text)

    if not paragraphs:
        log.warning("Zero usable paragraphs extracted from %s", url)
        return None

    return " ".join(paragraphs)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def scrape(output_path: str | None = None) -> list[dict]:
    yesterday = date.today() - timedelta(days=1)
    log.info("Target date: %s", yesterday.isoformat())

    # ── Phase 1: collect links ────────────────────────────────────────────
    candidate_links = collect_candidates(yesterday)
    log.info("Total candidate links from yesterday: %d", len(candidate_links))

    if not candidate_links:
        log.warning("No articles found for %s", yesterday.isoformat())
        return []

    # ── Phase 2: fetch article content ───────────────────────────────────
    results: list[dict] = []

    for idx, link in enumerate(candidate_links, 1):
        log.info("[%d/%d] Fetching article: %s", idx, len(candidate_links), link)
        time.sleep(DELAY_BETWEEN)

        text = extract_article_text(link)
        if not text:
            log.warning("Skipping (no content): %s", link)
            continue

        results.append(
            {
                "id": str(uuid.uuid4()),
                "link": link,
                "news": text,
            }
        )
        log.info("  ✓ extracted %d characters", len(text))

    log.info("Final records: %d", len(results))

    # ── Phase 3: output ───────────────────────────────────────────────────
    json_out = json.dumps(results, ensure_ascii=False, indent=2)

    if output_path is None:
        output_path = f"antaranews_bisnis_{yesterday.isoformat()}.json"

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(json_out)
    log.info("Saved → %s", output_path)

    # Also print to stdout (strict JSON only)
    print(json_out)
    return results


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    scrape()
