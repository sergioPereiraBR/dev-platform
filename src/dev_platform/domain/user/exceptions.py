# ./src/dev_platform/domain/user/exceptions.py
from datetime import datetime
from typing import Optional, Dict, Any


# Application layer exceptions
class ApplicationException(Exception):
    """Base exception for application layer errors."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        self.message = message
        self.original_exception = original_exception
        self.timestamp = datetime.now()
        super().__init__(self.message)


class UseCaseException(ApplicationException):
    """Raised when a use case execution fails."""

    def __init__(
        self,
        use_case_name: str,
        reason: str,
        original_exception: Optional[Exception] = None,
    ):
        self.use_case_name = use_case_name
        self.reason = reason
        super().__init__(
            message=f"Use case '{use_case_name}' failed: {reason}",
            original_exception=original_exception,
        )


# Infrastructure layer exceptions
class InfrastructureException(Exception):
    """Base exception for infrastructure layer errors."""

    def __init__(
        self,
        message: str,
        component: str,
        original_exception: Optional[Exception] = None,
    ):
        self.message = message
        self.component = component
        self.original_exception = original_exception
        self.timestamp = datetime.now()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "message": self.message,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "original_error": str(self.original_exception)
            if self.original_exception
            else None,
        }


class DatabaseException(InfrastructureException):
    """Raised when database operations fail."""

    def __init__(
        self,
        operation: str,
        reason: str,
        original_exception: Optional[Exception] = None,
    ):
        self.operation = operation
        self.reason = reason
        super().__init__(
            message=f"Database operation '{operation}' failed: {reason}",
            component="database",
            original_exception=original_exception,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Extended dictionary representation for database errors."""
        base_dict = super().to_dict()
        base_dict.update({"operation": self.operation, "reason": self.reason})
        return base_dict


class ConfigurationException(InfrastructureException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, config_key: str, reason: str):
        self.config_key = config_key
        self.reason = reason
        super().__init__(
            message=f"Configuration error for '{config_key}': {reason}",
            component="configuration",
        )


class CacheException(InfrastructureException):
    """Raised when cache operations fail."""

    def __init__(
        self,
        operation: str,
        key: str,
        reason: str,
        original_exception: Optional[Exception] = None,
    ):
        self.operation = operation
        self.key = key
        self.reason = reason
        super().__init__(
            message=f"Cache {operation} failed for key '{key}': {reason}",
            component="cache",
            original_exception=original_exception,
        )


# Repository-specific exceptions
class RepositoryException(InfrastructureException):
    """Base exception for repository layer errors."""

    def __init__(
        self,
        repository_name: str,
        operation: str,
        reason: str,
        original_exception: Optional[Exception] = None,
    ):
        self.repository_name = repository_name
        self.operation = operation
        self.reason = reason
        super().__init__(
            message=f"Repository '{repository_name}' {operation} failed: {reason}",
            component="repository",
            original_exception=original_exception,
        )


class DataIntegrityException(RepositoryException):
    """Raised when data integrity constraints are violated."""

    def __init__(
        self,
        constraint_name: str,
        details: str,
        original_exception: Optional[Exception] = None,
    ):
        self.constraint_name = constraint_name
        self.details = details
        super().__init__(
            repository_name="database",
            operation="constraint_validation",
            reason=f"Constraint '{constraint_name}' violated: {details}",
            original_exception=original_exception,
        )


class DataCorruptionException(RepositoryException):
    """Raised when data corruption is detected."""

    def __init__(self, entity_type: str, entity_id: str, corruption_details: str):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.corruption_details = corruption_details
        super().__init__(
            repository_name="database",
            operation="data_validation",
            reason=f"{entity_type} {entity_id} has corrupted data: {corruption_details}",
        )


# Exceções Específicas do Domínio
class DomainException(Exception):
    """Base exception for all domain-related errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
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
            "timestamp": self.timestamp.isoformat(),
        }


class UserAlreadyExistsException(DomainException):
    """Raised when trying to create a user with an email that already exists."""

    def __init__(self, email: str):
        self.email = email
        super().__init__(
            message=f"User with email '{email}' already exists",
            error_code="USER_ALREADY_EXISTS",
            details={"email": email},
        )


class UserNotFoundException(DomainException):
    """Raised when a user cannot be found."""

    def __init__(self, identifier: str, identifier_type: str = "id"):
        self.identifier = identifier
        self.identifier_type = identifier_type
        super().__init__(
            message=f"User not found with {identifier_type}: {identifier}",
            error_code="USER_NOT_FOUND",
            details={"identifier": identifier, "identifier_type": identifier_type},
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
            details={"field": field, "value": str(value), "reason": reason},
        )


class UserValidationException(DomainException):
    """Raised when user business rules validation fails."""

    def __init__(self, validation_errors: Dict[str, str]):
        self.validation_errors = validation_errors
        errors_summary = ", ".join(
            [f"{field}: {error}" for field, error in validation_errors.items()]
        )
        super().__init__(
            message=f"User validation failed: {errors_summary}",
            error_code="USER_VALIDATION_FAILED",
            details={"validation_errors": validation_errors},
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
                "allowed_domains": allowed_domains,
            },
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
            details={"operation": operation, "user_id": user_id, "reason": reason},
        )


# Compatibility aliases (deprecated, use specific exceptions above)
class DomainError(DomainException):
    """Exception for domain-related errors. DEPRECATED: Use DomainException instead."""

    def __init__(self, message: str):
        import warnings

        warnings.warn(
            "DomainError is deprecated. Use DomainException instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message)


class ValidationException(DomainException):
    """Exception for validation-related errors. DEPRECATED: Use UserValidationException instead."""

    def __init__(self, message: str):
        import warnings

        warnings.warn(
            "ValidationException is deprecated. Use UserValidationException instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(message)
