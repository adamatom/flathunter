"""Define exceptions related to solving captcha puzzles."""


class CaptchaUnsolvableError(Exception):
    """Raised when Captcha was unsolveable"""

    def __init__(self):
        super().__init__()
        self.message = "Failed to solve captcha."


class CaptchaBalanceEmpty(Exception):
    """Raised when Captcha account is out of credit"""

    def __init__(self):
        super().__init__()
        self.message = "Captcha account balance empty."
