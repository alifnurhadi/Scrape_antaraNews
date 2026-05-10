import time
import logging
import requests
from bs4 import BeautifulSoup
from configuration import DEFAULT_HEADERS, REQUEST_TIMEOUT

log = logging.getLogger(__name__)

def fetch_html(url: str, retries: int = 3) -> BeautifulSoup | None:
    print('fetch html')
    """Fetch URL and return BeautifulSoup object with retry logic."""
    for attempt in range(1, retries + 1):
        try:
            print('succeed')
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            print(resp)
            print(len(resp.text))
            # print(BeautifulSoup(resp.text, "html.parser"))
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as exc:
            print('fail')
            log.warning("Attempt %d/%d failed for %s: %s", attempt, retries, url, exc)
            if attempt < retries:
                time.sleep(2 ** attempt)
    return None
