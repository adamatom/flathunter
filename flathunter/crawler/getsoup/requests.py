"""Provides functions for retrieving website content as BeautifulSoup objects."""
import requests
# pylint: disable=unused-import
import requests_random_user_agent
from lxml.html import fromstring
from bs4 import BeautifulSoup
from flathunter.logging import logger
from flathunter.exceptions import ProxyException


def get_page_as_soup(url, headers) -> BeautifulSoup:
    """Get the source at the given url as a BeautifulSoup object."""
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code not in (200, 405):
        user_agent = 'Unknown'
        if 'User-Agent' in headers:
            user_agent = headers['User-Agent']
        logger.error("Got response (%i): %s\n%s", resp.status_code, resp.content, user_agent)
    return BeautifulSoup(resp.content, 'lxml')


def get_soup_with_proxy(url, request_headers) -> BeautifulSoup:
    """Get the source at the given url as a BeautifulSoup object through a proxy."""
    resolved = False
    resp = None

    # We will keep trying to fetch new proxies until one works
    while not resolved:
        proxies_list = get_proxies()
        for proxy in proxies_list:
            try:
                # Very low proxy read timeout, or it will get stuck on slow proxies
                resp = requests.get(
                    url,
                    headers=request_headers,
                    proxies={"http": proxy, "https": proxy},
                    timeout=(20, 0.1)
                )

                if resp.status_code != 200:
                    logger.error("Got response (%i): %s", resp.status_code, resp.content)
                else:
                    resolved = True
                    break

            except requests.exceptions.ConnectionError:
                logger.error(
                    "Connection failed for proxy %s. Trying new proxy...", proxy)
            except requests.exceptions.Timeout:
                logger.error(
                    "Connection timed out for proxy %s. Trying new proxy...", proxy
                )
            except requests.exceptions.RequestException:
                logger.error("Some error occurred. Trying new proxy...")

    if not resp:
        raise ProxyException(
            "An error occurred while fetching proxies or content")

    return BeautifulSoup(resp.content, 'lxml')


def get_proxies():
    """Gets random, free proxies."""
    url = "https://free-proxy-list.net/"
    response = requests.get(url, timeout=30)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:250]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            # Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies
