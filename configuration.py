import os
BASE_URL = "https://en.antaranews.com"
LIST_URL = f"{BASE_URL}/business-investment"

MAX_LIST_PAGES = 5
REQUEST_TIMEOUT = 10
DELAY_BETWEEN_REQUESTS = 1.0

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

BROWSERS = {
    "SAFARI": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "CHROME": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
}

DEFAULT_HEADERS = {"User-Agent": BROWSERS["SAFARI"]}

ID_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
