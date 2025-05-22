# src/dev_platform/domain/user/validators.py
import re
from shared.exceptions import ValidationException


class UserValidator:
    @staticmethod
    def validate_name(name: str) -> None:
        if not name or len(name) < 3:
            raise ValidationException("Name must be at least 3 characters long")
        if len(name) > 100:
            raise ValidationException("Name cannot exceed 100 characters")

    @staticmethod
    def validate_email(email: str) -> None:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email or not re.match(email_pattern, email):
            raise ValidationException("Invalid email format")

class UserValidationService:
    @staticmethod
    def validate_user(name: str, email: str) -> None:
        UserValidator.validate_name(name)
        UserValidator.validate_email(email)
