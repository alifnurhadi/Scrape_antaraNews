import logging
from datetime import date, timedelta
from scraper import AntaraScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

def main():
    scraper = AntaraScraper()

    target_date = date.today() - timedelta(days=1)

    scraper.scrape_target_date(target_date)

if __name__ == "__main__":
    main()
