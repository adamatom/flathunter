"""Interface for captcha solvers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import requests
import backoff


@dataclass
class GeetestResponse:
    """Responde from GeeTest Captcha"""
    challenge: str
    validate: str
    sec_code: str


@dataclass
class RecaptchaResponse:
    """Response from reCAPTCHA"""
    result: str


class CommercialSolver(ABC):
    """Interface for Captcha solvers"""

    backoff_options = {
        "wait_gen": backoff.constant,
        "exception": requests.exceptions.RequestException,
        "max_time": 100
    }

    def __init__(self, api_key):
        self.api_key = api_key

    @abstractmethod
    def get_geetest_solution(self, geetest: str, challenge: str, page_url: str) -> GeetestResponse:
        """Solve a geetest puzzle."""
        pass

    @abstractmethod
    def get_recaptcha_solution(self, google_site_key: str, page_url: str) -> RecaptchaResponse:
        """Solve a recaptcha puzzle."""
        pass
