#   src/shared/exceptions.py
class DomainException(Exception):
    """Exception for domain-related errors (e.g., validation)."""
    pass

class DatabaseException(Exception):
    """Exception for database-related errors."""
    pass