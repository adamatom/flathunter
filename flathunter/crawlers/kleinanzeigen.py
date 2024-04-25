"""Expose crawler for Ebay Kleinanzeigen"""
import re
import datetime
import backoff

from bs4 import BeautifulSoup, Tag
from selenium.webdriver import Chrome
from selenium.common.exceptions import TimeoutException

from flathunter.crawlers.crawler import Crawler
from flathunter.chrome_wrapper import get_chrome_driver
from flathunter.logging import logger

MONTHS = {
    "Januar": "01",
    "Februar": "02",
    "März": "03",
    "April": "04",
    "Mai": "05",
    "Juni": "06",
    "Juli": "07",
    "August": "08",
    "September": "09",
    "Oktober": "10",
    "November": "11",
    "Dezember": "12"
}


class Kleinanzeigen(Crawler):
    """Implementation of Crawler interface for Ebay Kleinanzeigen"""

    URL_PATTERN = re.compile(r'https://www\.kleinanzeigen\.de')

    def __init__(self, config):
        self.config = config
        self.driver = None
        self.disabled = False

        if not self.config.captcha_enabled():
            logger.info("disabling %s because captcha solving is not enabled", self.get_name())
            self.disabled = True
            return

        self.captcha_strategy = self.config.get_captcha_strategy()
        if self.captcha_strategy is None:
            logger.info("disabling %s because captcha strategy is not declared", self.get_name())
            self.disabled = True
            return

    # pylint: disable=unused-argument
    def get_results(self, search_url, max_pages=None):
        """Load the list of listings from the site, starting at the provided URL."""
        if self.disabled:
            return []

        logger.debug("Got search URL %s", search_url)

        # load first page
        soup = self._load_page(search_url)

        # get data from first page
        entries = self._extract_data(soup)
        logger.debug('Number of found entries: %d', len(entries))

        return entries

    def get_expose_details(self, expose):
        """Load additional details for a single listing."""
        if self.disabled:
            return expose

        soup = self._load_page(expose['url'])
        for detail in soup.find_all('li', {"class": "addetailslist--detail"}):
            if re.match(r'Verfügbar ab', detail.text):
                date_string = re.match(r'(\w+) (\d{4})', detail.text)
                if date_string is not None:
                    expose['from'] = "01." + MONTHS[date_string[1]] + "." + date_string[2]
        if 'from' not in expose:
            expose['from'] = datetime.datetime.now().strftime('%02d.%02m.%Y')
        return expose

    @property
    def url_pattern(self) -> re.Pattern:
        """A regex that matches urls that this crawler targets."""
        return self.URL_PATTERN

    @backoff.on_exception(wait_gen=backoff.constant, exception=TimeoutException, max_tries=3)
    def _load_page(self, url) -> BeautifulSoup:
        """Applies a page number to a formatted search URL and fetches the exposes at that page"""

        # TODO: use get_proxies, use those with driver to get the page
        # if self.config.use_proxy():
        #     return get_soup_with_proxy(url, self.HEADERS)
        if self.driver is None:
            driver_arguments = self.config.captcha_driver_arguments()
            self.driver = get_chrome_driver(driver_arguments)

        self.driver.get(url)
        if "initGeetest" in self.driver.page_source:
            self.captcha_strategy.resolve_geetest(self.driver)
        elif "g-recaptcha" in self.driver.page_source:
            self.captcha_strategy.resolve_recaptcha(self.driver, False, "")

        return BeautifulSoup(self.driver.page_source, 'lxml')

    # pylint: disable=too-many-locals
    def _extract_data(self, soup):
        """Extracts all exposes from a provided Soup object"""
        entries = []
        soup = soup.find(id="srchrslt-adtable")

        try:
            title_elements = soup.find_all(lambda e: e.has_attr('class')
                                           and 'ellipsis' in e['class'])
        except AttributeError:
            return entries

        expose_ids = soup.find_all("article", class_="aditem")

        for idx, title_el in enumerate(title_elements):
            try:
                price = expose_ids[idx].find(
                    class_="aditem-main--middle--price-shipping--price").text.strip()
                tags = expose_ids[idx].find_all(class_="simpletag")
                address = expose_ids[idx].find("div", {"class": "aditem-main--top--left"})
                image_element = expose_ids[idx].find("div", {"class": "galleryimage-element"})
            except AttributeError as error:
                logger.warning("Unable to process eBay expose: %s", str(error))
                continue

            if image_element is not None:
                image = image_element["data-imgsrc"]
            else:
                image = None

            address = address.text.strip()
            address = address.replace('\n', ' ').replace('\r', '')
            address = " ".join(address.split())

            rooms = ""
            if len(tags) > 1:
                rooms_match = re.match(r'(\d+)', tags[1].text)
                if rooms_match is not None:
                    rooms = rooms_match[1]

            try:
                size = tags[0].text
            except (IndexError, TypeError):
                size = ""
            details = {
                'id': int(expose_ids[idx].get("data-adid")),
                'image': image,
                'url': ("https://www.kleinanzeigen.de" + title_el.get("href")),
                'title': title_el.text.strip(),
                'price': price,
                'size': size,
                'rooms': rooms,
                'address': address,
                'crawler': self.get_name()
            }
            entries.append(details)

        logger.debug('Number of entries found: %d', len(entries))

        return entries

    def load_address(self, url):
        """Extract address from expose itself"""
        expose_soup = self._load_page(url)
        street_raw = ""
        street_el = expose_soup.find(id="street-address")
        if isinstance(street_el, Tag):
            street_raw = street_el.text
        address_raw = ""
        address_el = expose_soup.find(id="viewad-locality")
        if isinstance(address_el, Tag):
            address_raw = address_el.text

        return address_raw.strip().replace("\n", "") + " " + street_raw.strip()
