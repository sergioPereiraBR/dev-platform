# src/dev_platform/application/ports/logger.py
from abc import ABC, abstractmethod
from typing import Optional


class ILogger(ABC):
    """Interface for a structured logger."""

    @abstractmethod
    def set_correlation_id(self, correlation_id: Optional[str] = None):
        """Set a correlation ID for tracking logs across requests."""
        raise NotImplementedError
   
    @abstractmethod
    def info(self, message: str, **kwargs):
        """Log an informational message."""
        raise NotImplementedError

    @abstractmethod
    def error(self, message: str, **kwargs):
        """Log an error message."""
        raise NotImplementedError

    @abstractmethod
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        raise NotImplementedError

    @abstractmethod
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        raise NotImplementedError

    @abstractmethod
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        raise NotImplementedError
