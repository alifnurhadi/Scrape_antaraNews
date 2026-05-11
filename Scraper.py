import json
import logging
import time
import uuid
import os
from datetime import date, timedelta
from client import fetch_html
from parsers import extract_article_links, extract_article_text
from configuration import LIST_URL, MAX_LIST_PAGES, DELAY_BETWEEN_REQUESTS, OUTPUT_DIR

log = logging.getLogger(__name__)

class AntaraScraper:
    print('using scraper')
    def collect_candidates(self, target_date: date) -> list[str]:
        links, seen = [], set()

        for page in range(1, MAX_LIST_PAGES + 1):
            url = LIST_URL if page == 1 else f"{LIST_URL}?page={page}"
            log.info("Fetching page %d: %s", page, url)
            print(url)
            soup = fetch_html(url)
            print(soup)
            if not soup:
                return

            articles = extract_article_links(soup)

            print('article ',articles)
            if not articles:
                break

            for art in articles:
                if art["date"] == target_date and art["link"] not in seen:
                    seen.add(art["link"])
                    links.append(art["link"])
        print('collecting')
        print(links)
        print(seen)
        return links

    def scrape_target_date(self, target_date: date) -> list[dict]:
        log.info("Starting scrape for date: %s", target_date.isoformat())
        links = self.collect_candidates(target_date)
        results = []
        print(results)
        for idx, link in enumerate(links, 1):
            log.info("[%d/%d] Fetching: %s", idx, len(links), link)
            time.sleep(DELAY_BETWEEN_REQUESTS)

            soup = fetch_html(link)
            if not soup:
                continue

            text = extract_article_text(soup)
            if text:
                results.append({
                    "id": str(uuid.uuid4()),
                    "link": link,
                    "content": text,
                    "scraped_at": date.today().isoformat()
                })

        self._save_results(results, target_date)
        return results

    def _save_results(self, data: list[dict], target_date: date):
        if not data:
            return
        print('saving result')
        filepath = os.path.join(OUTPUT_DIR, f"antaranews_{target_date.isoformat()}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info("Saved %d records to %s", len(data), filepath)
