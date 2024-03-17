"""Define an interface for objects that define a process for solving captcha puzzles."""
from abc import ABC, abstractmethod


class SolvingStrategy(ABC):
    """Implement a strategy for solving Captcha puzzles."""

    @abstractmethod
    def resolve_geetest(self, driver):
        """Resolve a geetest puzzle."""
        pass

    @abstractmethod
    def resolve_recaptcha(self, driver, checkbox: bool, afterlogin_string: str = ""):
        """Resolve a recaptcha puzzle."""
        pass
