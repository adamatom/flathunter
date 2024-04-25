"""Expose crawler for VrmImmo"""
import re
import hashlib

from bs4 import BeautifulSoup

from flathunter.logging import logger
from flathunter.crawlers.crawler import Crawler
from flathunter.crawlers.getsoup import get_page_as_soup, get_soup_with_proxy


class VrmImmo(Crawler):
    """Implementation of Crawler interface for VrmImmo"""

    BASE_URL = "https://vrm-immo.de"
    URL_PATTERN = re.compile(r'https://vrm-immo\.de')

    def __init__(self, config):
        self.config = config

    # pylint: disable=unused-argument
    def get_results(self, search_url, max_pages=None):
        """Load the list of listings from the site, starting at the provided URL."""
        logger.debug("Got search URL %s", search_url)

        # load first page
        if self.config.use_proxy():
            soup = get_soup_with_proxy(search_url, self.HEADERS)
        else:
            soup = get_page_as_soup(search_url, self.HEADERS)

        # get data from first page
        entries = self._extract_data(soup)
        logger.debug('Number of found entries: %d', len(entries))

        return entries

    def get_expose_details(self, expose):
        """Load additional details for a single listing."""
        return expose

    @property
    def url_pattern(self) -> re.Pattern:
        """A regex that matches urls that this crawler targets."""
        return self.URL_PATTERN

    # pylint: disable=too-many-locals
    def _extract_data(self, soup: BeautifulSoup):
        """Extracts all exposes from a provided Soup object"""
        entries = []

        items = soup.find_all("div", {"class": "item-wrap js-serp-item"})

        for item in items:
            link = item.find("a", {"class": "js-item-title-link ci-search-result__link"})
            url = link.get("href")
            title = link.get("title")
            logger.debug("Analyze " + url)

            try:
                price = item.find("div", {"class": "item__spec item-spec-price"}).text
            except (IndexError, AttributeError):
                price = ""

            try:
                size = item.find("div", {"class": "item__spec item-spec-area"}).text
            except (IndexError, AttributeError):
                size = ""

            try:
                rooms = item.find("div", {"class": "item__spec item-spec-rooms"}).text
            except (IndexError, AttributeError):
                rooms = ""

            try:
                image = item.find('img')['src']
            except (IndexError, AttributeError):
                image = ""

            try:
                address = item.find("div", {"class": "item__locality"}).text
            except (IndexError, AttributeError):
                address = ""

            processed_id = int(
                hashlib.sha256(item.get("id").encode('utf-8')).hexdigest(), 16
            ) % 10 ** 16

            details = {
                'id': processed_id,
                'image': image,
                'url': self.BASE_URL + url,
                'title': title,
                'rooms': rooms,
                'price': price.strip(),
                'size': size.strip(),
                'address': address.strip(),
                'crawler': self.get_name()
            }
            entries.append(details)
        logger.debug('Number of entries found: %d', len(entries))
        return entries
