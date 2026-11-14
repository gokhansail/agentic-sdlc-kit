"""Exception types raised by the package.

Everything the command line shows as ``error: ...`` derives from BudgetbookError.
"""


class BudgetbookError(Exception):
    """Base class for errors that are the user's to fix."""


class AmountError(BudgetbookError, ValueError):
    """An amount could not be parsed or is not allowed."""


class DateError(BudgetbookError, ValueError):
    """A date or month could not be parsed."""


class CategoryError(BudgetbookError, ValueError):
    """A category name is empty or malformed."""


class NotFoundError(BudgetbookError, LookupError):
    """A transaction or other record does not exist."""


class LedgerFileError(BudgetbookError):
    """The ledger file cannot be read or has an unknown format."""


class CsvImportError(BudgetbookError):
    """A CSV file could not be imported. ``line`` is the 1-based line of the problem."""

    def __init__(self, line: int, message: str) -> None:
        super().__init__(f"line {line}: {message}")
        self.line = line
        self.message = message
