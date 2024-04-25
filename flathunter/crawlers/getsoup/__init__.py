"""Provides functions for retrieving website content as BeautifulSoup objects."""
from .requests import get_page_as_soup, get_soup_with_proxy

__all__ = (
    "get_page_as_soup"
    "get_soup_with_proxy"
)
