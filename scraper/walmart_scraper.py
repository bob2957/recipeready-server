#!/usr/bin/python

from typing import List, Optional
import undetected_chromedriver.v2 as uc
import logging

log = logging.getLogger("walmart_scraper")
log.setLevel(logging.INFO)
log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
log.addHandler(log_handler)


class GroceryItem():
    __slots__ = ["name", "price", "price_per_unit", "description", "image_url"]

    def __init__(self, name: str, price: float, price_per_unit: str, description: str, image_url: Optional[str] = None):
        self.name = name
        self.price = price
        self.price_per_unit = price_per_unit
        self.description = description
        self.image_url = image_url

    def __repr__(self) -> str:
        return f"{self.name} - ${self.price} ({self.price_per_unit} - {self.description})"


class WalmartScraper():
    def __init__(self, headless: bool = False, debug_log: bool = False):
        if debug_log:
            log.setLevel(logging.DEBUG)
        log.debug("Initialising web engine")
        options = uc.ChromeOptions()
        options.add_argument(
            "--disable-infobars --disable-dev-shm-usage --disable-browser-side-navigation --disable-gpu --no-first-run --no-service-autorun --password-store=basic")
        if headless:
            options.add_argument("--headless")
            options.add_argument(
                "--user-agent=\"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36\"")
        self.driver = uc.Chrome(
            options=options)
        self.driver.get("https://walmart.ca/cp/grocery")
        log.info("Ready to serve grocery queries")

    def query(self, query: str) -> GroceryItem:
        log.debug(f"Searching for {query}")
        result: GroceryItem = self.query_ten(query)
        if len(result) > 0:
            return result[0]
        raise IndexError(f"No items found for query {query}")

    def query_ten(self, query: str) -> List[GroceryItem]:
        log.debug(f"Searching top ten results for {query}")
        # c=10019 required to indicate grocery
        self.driver.get(f"https://www.walmart.ca/search?q={query}&c=10019")
        results: list = self.driver.execute_script("""
        const products = Array.from(document.querySelectorAll('[data-automation="main-search-wrapper"] [data-automation="grocery-product"]')).splice(0, 10);
        return products.map((e) => {
            return {
                name: e.querySelector('[data-automation="name"]').innerText,
                price: e.querySelector('[data-automation="current-price"]')?.innerText,
                pricePerUnit: e.querySelectorAll('[data-automation="price-per-unit"]')[1]?.innerText,
                description: e.querySelector('[data-automation="description"]')?.innerText,
                imageUrl: e.querySelector('[data-automation="image"]')?.src
            }
        });
        """)
        groceries = []
        for i in results:
            # cents vs dollars
            if "price" in i:
                processed_price = float(i["price"][1:]) if "$" in i["price"] else (float(i["price"][:-1]) / 100)
            else:
                processed_price = 0.0
            groceries.append(GroceryItem(
                name=i["name"], price=processed_price, price_per_unit=i["pricePerUnit"], description=i["description"], image_url=i["imageUrl"]))
        log.debug(f"Found at least {len(groceries)} results")
        if len(groceries) > 0:
            return groceries
        raise IndexError(f"No items found for query {query}")

    def exit(self):
        self.driver.close()


if __name__ == "__main__":
    # test version
    scraper = WalmartScraper(debug_log=True)
    print(scraper.query("apple").image_url)
    scraper.exit()
