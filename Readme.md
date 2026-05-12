
# AntaraNews Data Ingestion Pipeline

A robust, fault-tolerant web scraping pipeline designed to extract, clean, and structure business and investment news from AntaraNews.

Built with a focus on maintainability and data quality, this repository moves beyond simple scripts to provide a modular architecture suitable for daily, automated data extraction. The pipeline handles network instability, dynamic DOM structures, and complex timestamp variations to output clean JSON payloads ready for downstream processing.

## 🏗 System Architecture & Design Philosophy

As data pipelines scale, the primary bottlenecks are usually network unreliability and changing source formats. This project is structured around **Separation of Concerns** to ensure long-term maintainability:

* **`client.py` (The Network Layer):** Completely isolated HTTP logic. Implements exponential backoff and retry mechanisms to gracefully handle connection drops and rate limits without crashing the pipeline.
* **`parsers.py` (The Extraction Layer):** Pure functions dedicated solely to traversing the DOM. Separates the extraction of metadata from the article body. Includes explicit pre-emptive destruction of boilerplate HTML (e.g., "Related News", Editor credits) *before* text extraction to guarantee clean data.
* **`utils.py` (The Transformation Layer):** Handles the most fragile part of scraping: dates. Translates a mix of relative times ("15 hours ago", "yesterday") and multi-language standard dates into normalized Python `date` objects.
* **`Scraper.py` (The Orchestrator):** Combines the network and extraction layers. Manages pagination limits, date-matching logic, and safely handles `None` returns to ensure the loop continues running even if individual articles fail.

## ⚙️ Configuration

Before running the pipeline, you can adjust the scraping parameters in `configuration.py`. Key settings include:

* `MAX_LIST_PAGES`: Controls how deep the scraper paginates (default is `3` to capture recent news without overloading the server).
* `DELAY_BETWEEN_REQUESTS`: Time (in seconds) to pause between fetching individual articles to prevent IP bans.
* `OUTPUT_DIR`: The directory where raw JSON files and execution logs are saved.
* `DEFAULT_HEADERS`: Swap out User-Agents if needed (Safari and Chrome strings are provided).

## 🚀 Quick Start

**Prerequisites:** Python 3.10+

### Option A: Using `uv` (Recommended)

If you use Astral's `uv` for fast dependency management:

```bash
uv pip install requests beautifulsoup4 lxml
uv run main.py

```

### Option B: Using Standard `pip`

If you prefer standard virtual environments, create a `requirements.txt` file containing `requests`, `beautifulsoup4`, and `lxml`, then run:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

```

**Output:**
The scraper targets yesterday's news by default and generates:

* **Raw Data:** `data/raw/scrapeResult.json`
* **Execution Log:** `data/log_scrape_news.json` (Tracks the success state and for further run to check date that arent ingest and volume of the run).

---
