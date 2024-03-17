"""Solve catch puzzles presented by listing websites."""

from .solving_strategy import SolvingStrategy
from .manual_strategy import ManualSolvingStrategy
from .commercial_strategy import CommercialSolvingStrategy

from .commercial_solver import CommercialSolver, GeetestResponse, RecaptchaResponse
from .commercial_solvers.imagetyperz_solver import ImageTyperzSolver
from .commercial_solvers.twocaptcha_solver import TwoCaptchaSolver

from .exceptions import CaptchaBalanceEmpty, CaptchaUnsolvableError

__all__ = (
    "SolvingStrategy",
    "ManualSolvingStrategy",
    "CommercialSolvingStrategy",

    "CommercialSolver",
    "GeetestResponse",
    "RecaptchaResponse",

    "ImageTyperzSolver",
    "TwoCaptchaSolver",

    "CaptchaBalanceEmpty",
    "CaptchaUnsolvableError",
)
