# src/dev_platform/domain/user/services.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
import re
from datetime import datetime, timedelta
from domain.user.entities import User
from domain.user.exceptions import (
    UserAlreadyExistsException,
    EmailDomainNotAllowedException,
    UserValidationException,
    InvalidUserDataException
)


class ValidationRule(ABC):
    """Base class for validation rules."""
    
    @abstractmethod
    async def validate(self, user: User) -> Optional[str]:
        """
        Validate user according to this rule.
        Returns None if valid, error message if invalid.
        """
        pass
    
    @property
    @abstractmethod
    def rule_name(self) -> str:
        pass


class EmailDomainValidationRule(ValidationRule):
    """Validates that email domain is in allowed list."""
    
    def __init__(self, allowed_domains: List[str]):
        self.allowed_domains = set(allowed_domains)
    
    async def validate(self, user: User) -> Optional[str]:
        email_domain = user.email.value.split('@')[1].lower()
        if email_domain not in self.allowed_domains:
            return f"Email domain '{email_domain}' is not allowed. Allowed domains: {', '.join(self.allowed_domains)}"
        return None
    
    @property
    def rule_name(self) -> str:
        return "email_domain_validation"


class NameProfanityValidationRule(ValidationRule):
    """Validates that name doesn't contain profanity."""
    
    def __init__(self, forbidden_words: List[str]):
        self.forbidden_words = [word.lower() for word in forbidden_words]
    
    async def validate(self, user: User) -> Optional[str]:
        name_lower = user.name.value.lower()
        for word in self.forbidden_words:
            if word in name_lower:
                return f"Name contains forbidden word: {word}"
        return None
    
    @property
    def rule_name(self) -> str:
        return "name_profanity_validation"


class EmailFormatAdvancedValidationRule(ValidationRule):
    """Advanced email format validation beyond basic regex."""
    
    def __init__(self):
        # More restrictive email validation
        self.pattern = re.compile(
            r'^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$'
        )
    
    async def validate(self, user: User) -> Optional[str]:
        email = user.email.value
        
        # Check basic format
        if not self.pattern.match(email):
            return "Email format is invalid"
        
        # Check for consecutive dots
        if '..' in email:
            return "Email cannot contain consecutive dots"
        
        # Check for valid length
        if len(email) > 254:
            return "Email is too long (max 254 characters)"
        
        local_part, domain_part = email.split('@')
        
        # Check local part length
        if len(local_part) > 64:
            return "Email local part is too long (max 64 characters)"
        
        # Check domain part
        if len(domain_part) > 253:
            return "Email domain part is too long (max 253 characters)"
            
        return None
    
    @property
    def rule_name(self) -> str:
        return "email_format_advanced_validation"


class NameContentValidationRule(ValidationRule):
    """Validates name content and format."""
    
    async def validate(self, user: User) -> Optional[str]:
        name = user.name.value
        
        # Check for only whitespace
        if name.strip() != name:
            return "Name cannot start or end with whitespace"
        
        # Check for excessive whitespace
        if '  ' in name:
            return "Name cannot contain consecutive spaces"
        
        # Check for numbers
        if any(char.isdigit() for char in name):
            return "Name cannot contain numbers"
        
        # Check for special characters (allow only letters, spaces, hyphens, apostrophes)
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ -'")
        if not all(char in allowed_chars for char in name):
            return "Name contains invalid characters"
        
        # Check minimum word count
        words = name.split()
        if len(words) < 2:
            return "Name must contain at least first and last name"
        
        # Check each word length
        for word in words:
            if len(word) < 2:
                return "Each name part must be at least 2 characters long"
        
        return None
    
    @property
    def rule_name(self) -> str:
        return "name_content_validation"


class UserDomainService:
    """Service for complex user domain validations and business rules."""
    
    def __init__(self, user_repository, validation_rules: List[ValidationRule] = None):
        self._repository = user_repository
        self._validation_rules = validation_rules or []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default validation rules if none provided."""
        if not self._validation_rules:
            self._validation_rules = [
                EmailFormatAdvancedValidationRule(),
                NameContentValidationRule(),
                # Add more default rules as needed
            ]
    
    def add_validation_rule(self, rule: ValidationRule):
        """Add a custom validation rule."""
        self._validation_rules.append(rule)
    
    def remove_validation_rule(self, rule_name: str):
        """Remove a validation rule by name."""
        self._validation_rules = [
            rule for rule in self._validation_rules 
            if rule.rule_name != rule_name
        ]
    
    async def validate_business_rules(self, user: User) -> None:
        """
        Validate all business rules for a user.
        Raises UserValidationException if any rule fails.
        """
        validation_errors = {}
        
        # Check uniqueness first
        try:
            await self._validate_unique_email(user.email.value)
        except UserAlreadyExistsException as e:
            validation_errors["email"] = e.message
        
        # Run all validation rules
        for rule in self._validation_rules:
            try:
                error_message = await rule.validate(user)
                if error_message:
                    validation_errors[rule.rule_name] = error_message
            except Exception as e:
                validation_errors[rule.rule_name] = f"Validation rule failed: {str(e)}"
        
        # If there are validation errors, raise exception
        if validation_errors:
            raise UserValidationException(validation_errors)
    
    async def _validate_unique_email(self, email: str):
        """Validate that email is unique in the system."""
        existing_user = await self._repository.find_by_email(email)
        if existing_user:
            raise UserAlreadyExistsException(email)
    
    async def validate_user_update(self, user_id: int, updated_user: User) -> None:
        """
        Validate user update, checking uniqueness only if email changed.
        """
        validation_errors = {}
        
        # Get current user
        current_user = await self._repository.find_by_id(user_id)
        if not current_user:
            raise UserNotFoundException(str(user_id))
        
        # Check email uniqueness only if email changed
        if current_user.email.value != updated_user.email.value:
            try:
                await self._validate_unique_email(updated_user.email.value)
            except UserAlreadyExistsException as e:
                validation_errors["email"] = e.message
        
        # Run validation rules
        for rule in self._validation_rules:
            try:
                error_message = await rule.validate(updated_user)
                if error_message:
                    validation_errors[rule.rule_name] = error_message
            except Exception as e:
                validation_errors[rule.rule_name] = f"Validation rule failed: {str(e)}"
        
        if validation_errors:
            raise UserValidationException(validation_errors)
    
    def get_validation_summary(self) -> Dict[str, str]:
        """Get summary of all active validation rules."""
        return {
            rule.rule_name: rule.__class__.__doc__ or "No description available"
            for rule in self._validation_rules
        }
