"""Expose crawler for MeineStadt"""
import re
import hashlib

from flathunter.logging import logger
from flathunter.crawler.abstract_crawler import Crawler
from flathunter.crawler.getsoup import get_page_as_soup, get_soup_with_proxy


class MeineStadt(Crawler):
    """Implementation of Crawler interface for MeineStadt"""

    URL_PATTERN = re.compile(r'https://www\.meinestadt\.de')

    def __init__(self, config):
        self.config = config

    def get_results(self, search_url, max_pages=None):
        """Load the list of listings from the site, starting at the provided URL."""
        logger.debug("Got search URL %s", search_url)

        if self.config.use_proxy():
            soup = get_soup_with_proxy(search_url, self.HEADERS)
        else:
            soup = get_page_as_soup(search_url, self.HEADERS)

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
    def _extract_data(self, soup):
        """Extracts all exposes from a provided Soup object"""
        entries = []

        items = soup.find_all("div", {"class": "m-resultListEntries__content"})
        for item in items:
            # find image
            image_tag = item.find(
                "div", {"class": "m-resultListEntries__img"}).find("img")
            image = image_tag.get("data-objectimage")

            [title_address_info, price_size_rooms] = item.find_all(
                "div", {"class": "m-resultListEntries__metainfosEntries"})

            title = title_address_info.find("a").text.strip()
            url = title_address_info.find("a").get("href")
            address = title_address_info.find(
                "div", {"class": "m-resultListEntries__metainfo"}).text.strip()
            infos = price_size_rooms.find_all(
                "div", {"class": "a-resultListMetainfoItem__text"})
            [price, size, rooms] = [""] * 3
            for info in infos:
                if "€" in info.text:
                    price = info.text.strip()
                if "m²" in info.text:
                    size = info.text.strip()
                if "Zimmer" in info.text:
                    rooms = info.text.strip()

            details = {
                'image': image,
                'url': url,
                'title': title,
                'price': price,
                'size': size,
                'rooms': rooms,
                'address': address
            }
            details['id'] = int(
                hashlib.sha256(str(details).encode(
                    'utf-8')).hexdigest(), 16
            ) % 10**16
            details['crawler'] = self.get_name()

            entries.append(details)
        logger.debug('Number of entries found: %d', len(entries))
        return entries
