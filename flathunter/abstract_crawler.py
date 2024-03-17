"""Interface for webcrawlers. Crawler implementations should subclass this"""
from abc import ABC, abstractmethod, abstractproperty
import re


class Crawler(ABC):
    """A Crawler retrieves the list of listings as well as further details of a single listing."""

    HEADERS = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'Accept': 'text/html,application/xhtml+xml,application/xml;'
                  'q=0.9,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3;q=0.9',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-User': '?1',
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    @abstractmethod
    def get_results(self, search_url, max_pages=None):
        """Load the list of listings from the site, starting at the provided URL."""
        pass

    @abstractmethod
    def get_expose_details(self, expose):
        """Load additional details for a single listing."""
        pass

    @property
    @abstractmethod
    def url_pattern(self) -> re.Pattern:
        """A regex that matches urls that this crawler targets."""
        pass

    def get_name(self):
        """Return the name of this crawler"""
        return type(self).__name__
