"""Define a captcha strategy that uses a 3rd party service."""
import backoff
import re

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from time import sleep

from flathunter.logging import logger

from flathunter.captcha.solving_strategy import SolvingStrategy
from flathunter.captcha.exceptions import CaptchaUnsolvableError


class CommercialSolvingStrategy(SolvingStrategy):
    """Use a 3rd party, commercial Captcha solving strategy."""

    def __init__(self, captcha_solver):
        """Initialize the strategy with the needed Captcha solver."""
        self.captcha_solver = captcha_solver

    @backoff.on_exception(wait_gen=backoff.constant, exception=CaptchaUnsolvableError, max_tries=3)
    def resolve_geetest(self, driver):
        """Resolve GeeTest Captcha"""
        data = re.findall(
            "geetest_validate: obj.geetest_validate,\n.*?data: \"(.*)\"",
            driver.page_source
        )[0]
        result = re.findall(
            r"initGeetest\({(.*?)}", driver.page_source, re.DOTALL)

        geetest = re.findall("gt: \"(.*?)\"", result[0])[0]
        challenge = re.findall("challenge: \"(.*?)\"", result[0])[0]
        try:
            captcha_response = self.captcha_solver.get_geetest_solution(
                geetest,
                challenge,
                driver.current_url
            )
            script = (f'solvedCaptcha({{geetest_challenge: "{captcha_response.challenge}",'
                      f'geetest_seccode: "{captcha_response.sec_code}",'
                      f'geetest_validate: "{captcha_response.validate}",'
                      f'data: "{data}"}});')
            driver.execute_script(script)
            sleep(2)
        except CaptchaUnsolvableError:
            driver.refresh()
            raise

    @backoff.on_exception(wait_gen=backoff.constant, exception=CaptchaUnsolvableError, max_tries=3)
    def resolve_recaptcha(self, driver, checkbox: bool, afterlogin_string: str = ""):
        """Resolve Captcha"""
        iframe_present = self._wait_for_iframe(driver)
        if checkbox is False and afterlogin_string == "" and iframe_present:
            google_site_key = driver \
                .find_element_by_class_name("g-recaptcha") \
                .get_attribute("data-sitekey")

            try:
                captcha_result = self.captcha_solver.get_recaptcha_solution(
                    google_site_key,
                    driver.current_url
                ).result

                driver.execute_script(
                    f'document.getElementById("g-recaptcha-response").innerHTML="{captcha_result}";'
                )

                #  Below function call can be different depending on the websites
                #  implementation. It is responsible for sending the promise that we
                #  get from recaptcha_answer. For now, if it breaks, it is required to
                #  reverse engineer it by hand. Not sure if there is a way to automate it.
                driver.execute_script(f'solvedCaptcha("{captcha_result}")')
                self._wait_until_iframe_disappears(driver)
            except CaptchaUnsolvableError:
                driver.refresh()
                raise
        else:
            if checkbox:
                self._clickcaptcha(driver, checkbox)
            else:
                self._wait_for_captcha_resolution(driver, checkbox, afterlogin_string)

    def _clickcaptcha(self, driver, checkbox: bool):
        """Find the captcha checkbox and click it."""
        driver.switch_to.frame(driver.find_element_by_tag_name("iframe"))
        recaptcha_checkbox = driver.find_element_by_class_name("recaptcha-checkbox-checkmark")
        recaptcha_checkbox.click()
        self._wait_for_captcha_resolution(driver, checkbox)
        driver.switch_to.default_content()

    def _wait_for_captcha_resolution(self, driver, checkbox: bool, afterlogin_string=""):
        """ Wait for elements that indicate the captcha was solved to appear."""
        if checkbox:
            try:
                WebDriverWait(driver, 120).until(
                    EC.visibility_of_element_located(
                        (By.CLASS_NAME, "recaptcha-checkbox-checked"))
                )
            except TimeoutException:
                logger.warning(
                    "Selenium.Timeoutexception when waiting for captcha to appear")
        else:
            xpath_string = f"//*[contains(text(), '{afterlogin_string}')]"
            try:
                WebDriverWait(driver, 120) \
                    .until(EC.visibility_of_element_located((By.XPATH, xpath_string)))
            except TimeoutException:
                logger.warning(
                    "Selenium.Timeoutexception when waiting for captcha to disappear")

    def _wait_for_iframe(self, driver: Chrome):
        """Wait for iFrame to appear"""
        try:
            iframe = WebDriverWait(driver, 10).until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "iframe[src^='https://www.google.com/recaptcha/api2/anchor?']")))
            return iframe
        except NoSuchElementException:
            logger.info(
                "No iframe found, therefore no chaptcha verification necessary")
            return None
        except TimeoutException:
            logger.info(
                "Timeout waiting for iframe element - no captcha verification necessary?")
            return None

    def _wait_until_iframe_disappears(self, driver: Chrome):
        """Wait for iFrame to disappear."""
        try:
            WebDriverWait(driver, 10).until(EC.invisibility_of_element(
                (By.CSS_SELECTOR, "iframe[src^='https://www.google.com/recaptcha/api2/anchor?']")))
        except NoSuchElementException:
            logger.warning("Element not found")
