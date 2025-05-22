#   src/dev_platform/shared/exceptions.py
class DomainException(Exception):
    """Exception for domain-related errors (e.g., validation)."""
    pass

class DatabaseException(Exception):
    """Exception for database-related errors."""
    pass

class DomainError(Exception):
    """Exception for domain-related errors."""
    pass

class ConfigurationException(Exception):
    """Exception for configuration-related errors."""
    pass

class ValidationException(Exception):
    """Exception for validation-related errors."""
    pass