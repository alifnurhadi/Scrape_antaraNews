import json
import logging
import time
import uuid
import os
from datetime import date
from client import fetch_html
from parsers import extract_article_links, extract_article_text
from configuration import LIST_URL, MAX_LIST_PAGES, DELAY_BETWEEN_REQUESTS, OUTPUT_DIR

log = logging.getLogger(__name__)

class AntaraScraper:
    def collect_candidates(self, target_date: date) -> list[str]:
        links = []
        seen = set()

        for page in range(1, MAX_LIST_PAGES + 1):
            url = LIST_URL if page == 1 else f"{LIST_URL}?page={page}"
            log.info("Fetching list page %d: %s", page, url)

            soup = fetch_html(url)

            if not soup:
                log.warning("Network drop or empty page. Stopping pagination.")
                break

            articles = extract_article_links(soup)

            if not articles:
                log.info("No articles parsed on page %d. Stopping.", page)
                break

            for art in articles:
                article_date = art.get("date")

                if not article_date:
                    continue

                # Skip news that is newer than the target date (e.g., today's news)
                if article_date > target_date:
                    continue

                # Skip news that is older than the target date
                if article_date < target_date:
                    continue

                # If it exactly matches the target date, save it
                if article_date == target_date and art["link"] not in seen:
                    seen.add(art["link"])
                    links.append(art["link"])

        log.info("Successfully collected %d links for %s", len(links), target_date)
        return links

    def scrape_target_date(self, target_date: date) -> list[dict]:
        log.info("Starting scrape for date: %s", target_date.isoformat())

        links = self.collect_candidates(target_date)
        results = []

        if not links:
            log.warning("No candidate links to scrape. Exiting.")
            return results

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
            log.warning("No data extracted to save.")
            return

        filepath = os.path.join(OUTPUT_DIR, "raw/scrapeResult.json")
        logFile = os.path.join(OUTPUT_DIR, f"log_scrape_news.json")
        print(filepath,'\n',logFile)

        def writeFile (path:str , data_):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data_, f, ensure_ascii=False, indent=2)

        print(target_date.isoformat() , 'type:\n', type(target_date.isoformat()))

        if os.path.exists(logFile):
            with open (logFile , 'r' ) as r:
                try:
                    data_log = json.load(r)
                except json.JSONDecodeError:
                    data_log = {}
                data_log[target_date.isoformat()] = {
                    "status": "success" if len(data) > 0 else "empty",
                    "total_data": len(data),
                    "executed_at": target_date.isoformat(),
                    "source_url": LIST_URL
                }
                writeFile(logFile , data_log)

        else:
            writeFile(logFile,{target_date.isoformat():'done'})

        writeFile(filepath, data)

        log.info("Saved %d records to %s", len(data), filepath)
