import os
import re
import time
import logging
import requests
import yaml

from PIL import Image
from io import BytesIO

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def setup_logger(level="INFO"):
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=getattr(logging, level.upper())
    )
    return logging.getLogger(__name__)


class DuckDuckGoImageScraper:
    def __init__(self, config, logger):
        self.query = config["scraper"]["query"]
        self.num_images = config["scraper"]["num_images"]
        self.output_dir = config["scraper"]["output_dir"]
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger = logger
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/115.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://duckduckgo.com/",
            "X-Requested-With": "XMLHttpRequest"
        }

    def fetch_image_urls(self):
        self.logger.info(f"Searching DuckDuckGo Images for '{self.query}'")
        search_url = f"https://duckduckgo.com/?q={requests.utils.quote(self.query)}&t=h_&iax=images&ia=images"
        res = requests.get(search_url, headers=self.headers)
        match = re.search(r'vqd=([\d-]+)&', res.text)
        if not match:
            self.logger.error("Could not find token (vqd) on DuckDuckGo page")
            return []

        vqd = match.group(1)
        self.logger.info(f"Obtained token vqd={vqd}")

        image_urls = []
        batch_size = 100
        offset = 0

        while len(image_urls) < self.num_images:
            ajax_url = (
                f"https://duckduckgo.com/i.js?q={requests.utils.quote(self.query)}"
                f"&vqd={vqd}&o=json&f=,,,&p=1&l=en-US&s={offset}"
            )
            try:
                ajax_res = requests.get(ajax_url, headers=self.headers)
                data = ajax_res.json()
            except Exception as e:
                self.logger.error(f"Failed to fetch or parse JSON: {e}")
                self.logger.debug(f"Response content: {ajax_res.text[:300]}")
                break

            results = data.get("results", [])
            if not results:
                self.logger.info("No more images found.")
                break

            for r in results:
                image_url = r.get("image")
                if image_url:
                    image_urls.append(image_url)
                if len(image_urls) >= self.num_images:
                    break

            offset += batch_size
            time.sleep(0.5)

        self.logger.info(f"Found {len(image_urls)} image URLs")
        return image_urls

    def save_images(self, urls):
        count = 0
        for i, url in enumerate(urls):
            try:
                resp = requests.get(url, headers=self.headers, timeout=10)
                resp.raise_for_status()
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img = img.resize((512, 512))
                path = os.path.join(self.output_dir, f"ghibli_{i:04}.jpg")
                img.save(path)
                count += 1
                self.logger.info(f"[{count}] Saved image: {url}")
            except Exception as e:
                self.logger.warning(f"Failed to save image {url}: {e}")
        self.logger.info(f"Downloaded {count} images to '{self.output_dir}'")

    def scrape(self):
        urls = self.fetch_image_urls()
        if urls:
            self.save_images(urls)

if __name__ == "__main__":
    config = load_config()
    logger = setup_logger(config["logging"].get("level", "INFO"))
    scraper = DuckDuckGoImageScraper(config, logger)
    scraper.scrape()
