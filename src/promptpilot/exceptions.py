"""Domain specific exceptions used to keep CLI error handling readable"""

class PromptPilotError(Exception):
    """Base class for expected application errors."""

class ConfigurationError(PromptPilotError):
    """Raised when configuration is missing or invalid."""

class QuotaExceededError(PromptPilotError):
    """Raised when the demo prompt allowance has been consumed."""

class GroqAPIError(PromptPilotError):
    """Raised when the remote API rejects a request or returns bd JSON."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code

class SchemaError(PromptPilotError):
    """Raised when a remote response does not match the expected schema."""