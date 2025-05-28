#   src/dev_platform/shared/exceptions.py
from datetime import datetime
from typing import Optional, Dict, Any


class DomainException(Exception):
    """Base exception for all domain-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class UserAlreadyExistsException(DomainException):
    """Raised when trying to create a user with an email that already exists."""
    
    def __init__(self, email: str):
        self.email = email
        super().__init__(
            message=f"User with email '{email}' already exists",
            error_code="USER_ALREADY_EXISTS",
            details={"email": email}
        )


class UserNotFoundException(DomainException):
    """Raised when a user cannot be found."""
    
    def __init__(self, identifier: str, identifier_type: str = "id"):
        self.identifier = identifier
        self.identifier_type = identifier_type
        super().__init__(
            message=f"User not found with {identifier_type}: {identifier}",
            error_code="USER_NOT_FOUND",
            details={"identifier": identifier, "identifier_type": identifier_type}
        )


class InvalidUserDataException(DomainException):
    """Raised when user data fails validation."""
    
    def __init__(self, field: str, value: Any, reason: str):
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(
            message=f"Invalid {field}: {reason}",
            error_code="INVALID_USER_DATA",
            details={"field": field, "value": str(value), "reason": reason}
        )


class UserValidationException(DomainException):
    """Raised when user business rules validation fails."""
    
    def __init__(self, validation_errors: Dict[str, str]):
        self.validation_errors = validation_errors
        errors_summary = ", ".join([f"{field}: {error}" for field, error in validation_errors.items()])
        super().__init__(
            message=f"User validation failed: {errors_summary}",
            error_code="USER_VALIDATION_FAILED",
            details={"validation_errors": validation_errors}
        )


class EmailDomainNotAllowedException(DomainException):
    """Raised when email domain is not in allowed list."""
    
    def __init__(self, email: str, domain: str, allowed_domains: list):
        self.email = email
        self.domain = domain
        self.allowed_domains = allowed_domains
        super().__init__(
            message=f"Email domain '{domain}' is not allowed. Allowed domains: {', '.join(allowed_domains)}",
            error_code="EMAIL_DOMAIN_NOT_ALLOWED",
            details={
                "email": email,
                "domain": domain, 
                "allowed_domains": allowed_domains
            }
        )


class UserOperationException(DomainException):
    """Raised when a user operation fails."""
    
    def __init__(self, operation: str, user_id: int, reason: str):
        self.operation = operation
        self.user_id = user_id
        self.reason = reason
        super().__init__(
            message=f"Failed to {operation} user {user_id}: {reason}",
            error_code="USER_OPERATION_FAILED",
            details={"operation": operation, "user_id": user_id, "reason": reason}
        )

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
