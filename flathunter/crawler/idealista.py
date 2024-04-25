"""Expose crawler for Idealista"""
import re

from flathunter.logging import logger
from flathunter.crawler.abstract_crawler import Crawler
from flathunter.crawler.getsoup import get_page_as_soup, get_soup_with_proxy


class Idealista(Crawler):
    """Implementation of Crawler interface for Idealista"""

    URL_PATTERN = re.compile(r'https://www\.idealista\.it')

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

        findings = soup.find_all('article', {"class": "item"})

        base_url = 'https://www.idealista.it'
        for row in findings:
            title_row = row.find('a', {"class": "item-link"})
            title = title_row.text.strip()
            url = base_url + title_row['href']
            picture_element = row.find('picture', {"class": "item-multimedia"})
            if "no-pictures" not in picture_element.get("class"):
                image = ""
            else:
                print(picture_element)
                image = picture_element.find('img')['src']

            # It's possible that not all three fields are present
            detail_items = row.find_all("span", {"class": "item-detail"})
            rooms = detail_items[0].text.strip() if (len(detail_items) >= 1) else ""
            size = detail_items[1].text.strip() if (len(detail_items) >= 2) else ""
            floor = detail_items[2].text.strip() if (len(detail_items) >= 3) else ""
            price = row.find("span", {"class": "item-price"}).text.strip().split("/")[0]

            details_title = (f"{title} - {floor}") if (len(floor) > 0) else title

            details = {
                'id': int(row.get("data-adid")),
                'image': image,
                'url': url,
                'title': details_title,
                'price': price,
                'size': size,
                'rooms': rooms,
                'address': re.findall(r'(?:\sin\s|\sa\s)(.*)$', title)[0],
                'crawler': self.get_name()
            }

            entries.append(details)

        logger.debug('Number of entries found: %d', len(entries))

        return entries
