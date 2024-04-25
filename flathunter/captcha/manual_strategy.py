from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from flathunter.logging import logger

from flathunter.captcha.solving_strategy import SolvingStrategy


class ManualSolvingStrategy(SolvingStrategy):
    """Implement a strategy for solving Captcha puzzles."""

    def resolve_geetest(self, driver):
        """Resolve a geetest puzzle."""
        logger.warning("waiting for manual solution for the geetest puzzle")
        try:
            WebDriverWait(driver, 60*60*10).until(
                EC.invisibility_of_element((By.XPATH, '//*[@id="captcha-box"]')))
        except NoSuchElementException:
            pass
        logger.debug("captcha-box is gone")

    def resolve_recaptcha(self, driver, checkbox: bool, afterlogin_string: str = ""):
        """Resolve a recaptcha puzzle."""
        logger.warning("waiting for manual solution for the recaptcha puzzle")
        try:
            WebDriverWait(driver, 60*60*10).until(EC.invisibility_of_element(
                (By.CSS_SELECTOR, "iframe[src^='https://www.google.com/recaptcha/api2/anchor?']")))
        except NoSuchElementException:
            pass
        logger.debug("recaptcha frame is gone")
