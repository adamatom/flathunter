"""Expose crawler for ImmobilienScout"""
import backoff
import datetime
import re

from bs4 import BeautifulSoup
from jsonpath_ng.ext import parse
from selenium.common.exceptions import JavascriptException
from selenium.webdriver import Chrome
from selenium.common.exceptions import TimeoutException
from time import sleep

from flathunter.crawlers.crawler import Crawler
from flathunter.logging import logger
from flathunter.chrome_wrapper import get_chrome_driver


class Immobilienscout(Crawler):
    """Implementation of Crawler interface for ImmobilienScout"""

    URL_PATTERN = re.compile(r'https://www\.immobilienscout24\.de')
    JSON_PATH_PARSER_ENTRIES = parse("$..['resultlist.realEstate']")
    JSON_PATH_PARSER_IMAGES = parse("$..galleryAttachments"
                                    "..attachment[?'@xsi.type'=='common:Picture']"
                                    "..['@href'].`sub(/(.*\\\\.jpe?g).*/, \\\\1)`")
    FALLBACK_IMAGE_URL = "https://www.static-immobilienscout24.de/statpic/placeholder_house/" + \
        "496c95154de31a357afa978cdb7f15f0_placeholder_medium.png"

    RESULT_LIMIT = 50

    def __init__(self, config):
        self.config = config
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

        self.driver = None
        if "immoscout_cookie" in self.config:
            self.HEADERS['Cookie'] = f'reese84:${self.config["immoscout_cookie"]}'

    def get_results(self, search_url, max_pages=None):
        """Load the list of listings from the site, starting at the provided URL."""
        if self.disabled:
            return []

        # convert to paged URL
        if '&pagenumber' in search_url:
            search_url = re.sub(r"&pagenumber=[0-9]", "&pagenumber={0}", search_url)
        else:
            search_url = search_url + '&pagenumber={0}'
        logger.debug("Got search URL %s", search_url)

        try:
            # load first page to get number of entries
            page_no = 1
            paginated_url = search_url.format(page_no)
            json = self._load_page(paginated_url).execute_script('return window.IS24.resultList;')
            entries = self._extract_entries_from_json(json)
            logger.debug('Number of found entries: %d', len(entries))
            return entries

        except JavascriptException:
            logger.warning("Unable to find IS24 variable in window")
            return []

    def get_expose_details(self, expose):
        """Load additional details for a single listing."""
        if self.disabled:
            return expose
        soup = BeautifulSoup(self._load_page(expose['url']).page_source, 'lxml')
        date = soup.find('dd', {"class": "is24qa-bezugsfrei-ab"})
        expose['from'] = datetime.datetime.now().strftime("%2d.%2m.%Y")
        if date is not None:
            if not re.match(r'.*sofort.*', date.text):
                expose['from'] = date.text.strip()
        return expose

    @property
    def url_pattern(self) -> re.Pattern:
        """A regex that matches urls that this crawler targets."""
        return self.URL_PATTERN

    @backoff.on_exception(wait_gen=backoff.constant, exception=TimeoutException, max_tries=3)
    def _load_page(self, url: str) -> Chrome:
        # TODO: use get_proxies, use those with driver to get the page
        # if self.config.use_proxy():
        #     return get_soup_with_proxy(url, self.HEADERS)

        if self.driver is None:
            self.driver = get_chrome_driver(self.config.captcha_driver_arguments())

        self.driver.get(url)

        while "Wir überprüfen schnell, dass du kein Roboter" in self.driver.page_source:
            # Let the initial bot check page load/bounce to the page that contains the captcha
            logger.info("Found captcha loading page, waiting 5s for it to load captcha")
            sleep(5)
            self.driver.get(url)

        while "Warum haben wir deine Anfrage blockiert?" in self.driver.page_source:
            self.captcha_strategy.resolve_geetest(self.driver)
            sleep(5)
            self.driver.get(url)

        # return the driver as a sort of builder pattern.
        return self.driver

    def _extract_entries_from_json(self, json):
        def _extract_entry(entry):
            # the url that is being returned to the frontend has a placeholder for screen size.
            # i.e. (%WIDTH% and %HEIGHT%)
            # The website's frontend fills these variables based on the user's screen size.
            # If we remove this part, the API will return the original size of the image.
            #
            # Before:
            # https://pictures.immobilienscout24.de/listings/$$IMAGE_ID$$.jpg/ORIG/legacy_thumbnail/%WIDTH%x%HEIGHT%3E/format/webp/quality/50
            #
            # After: https://pictures.immobilienscout24.de/listings/$$IMAGE_ID$$.jpg

            images = [image.value for image in self.JSON_PATH_PARSER_IMAGES.find(entry)]

            object_id = int(entry.get("@id", 0))
            return {
                'id': object_id,
                'url': f"https://www.immobilienscout24.de/expose/{str(object_id)}",
                'image': images[0] if len(images) else self.FALLBACK_IMAGE_URL,
                'images': images,
                'title': entry.get("title", '').replace('\n', ''),
                'address': entry.get("address", {}).get("description", {}).get("text", ''),
                'crawler': self.get_name(),
                'price': str(entry.get("price", {}).get("value", '')),
                'total_price':
                    str(entry.get('calculatedTotalRent', {}).get("totalRent", {}).get('value', '')),
                'size': str(entry.get("livingSpace", '')),
                'rooms': str(entry.get("numberOfRooms", ''))
            }

        return [_extract_entry(entry.value) for entry in self.JSON_PATH_PARSER_ENTRIES.find(json)]
