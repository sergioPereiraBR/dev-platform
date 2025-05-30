# src/dev_platform/domain/user/services.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Set
import re
from datetime import datetime, timedelta
from domain.user.entities import User
from domain.user.exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException,
    EmailDomainNotAllowedException,
    UserValidationException,
    InvalidUserDataException
)


class UserValidationService:
    """Service focused solely on validation rules."""
    
    def __init__(self, validation_rules: List['ValidationRule'] = None):
        self._validation_rules = validation_rules or []
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        if not self._validation_rules:
            self._validation_rules = [
                EmailFormatAdvancedValidationRule(),
                NameContentValidationRule(),
            ]
    
    async def validate(self, user: User) -> None:
        validation_errors = {}
        
        for rule in self._validation_rules:
            try:
                error_message = await rule.validate(user)
                if error_message:
                    validation_errors[rule.rule_name] = error_message
            except Exception as e:
                validation_errors[rule.rule_name] = f"Validation rule failed: {str(e)}"
        
        if validation_errors:
            raise UserValidationException(validation_errors)


class UserUniquenessService:
    """Service focused on uniqueness validation."""
    
    def __init__(self, user_repository):
        self._repository = user_repository
    
    async def ensure_email_is_unique(self, email: str, exclude_user_id: int = None) -> None:
        existing_user = await self._repository.find_by_email(email)
        if existing_user and (exclude_user_id is None or existing_user.id != exclude_user_id):
            from domain.user.exceptions import UserAlreadyExistsException
            raise UserAlreadyExistsException(email)

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
        self.allowed_domains = set(domain.lower() for domain in allowed_domains)
    
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
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ -'àáâãèéêìíîòóôõùúûçÀÁÂÃÈÉÊÌÍÎÒÓÔÕÙÚÛÇ")
        if not all(char in allowed_chars for char in name):
            invalid_chars = [char for char in name if char not in allowed_chars]
            return f"Name contains invalid characters: {', '.join(set(invalid_chars))}"
        
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


class BusinessHoursValidationRule(ValidationRule):
    """Example rule that validates based on business hours."""
    
    def __init__(self, business_hours_only: bool = False):
        self.business_hours_only = business_hours_only
    
    async def validate(self, user: User) -> Optional[str]:
        if not self.business_hours_only:
            return None
            
        now = datetime.now()
        # Check if it's business hours (9 AM to 5 PM, Monday to Friday)
        if now.weekday() >= 5:  # Saturday or Sunday
            return "User registration only allowed during business days"
        
        if now.hour < 9 or now.hour >= 17:
            return "User registration only allowed during business hours (9 AM - 5 PM)"
        
        return None
    
    @property
    def rule_name(self) -> str:
        return "business_hours_validation"

# ==========================================================================================================================================
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
    
    async def validate_user_creation_constraints(self, user: User) -> None:
        """
        Validate constraints specific to user creation.
        This can include rate limiting, domain restrictions, etc.
        """
        validation_errors = {}
        
        # Example: Check if we've reached user limit for the day
        # This is just an example - you'd implement based on your business rules
        try:
            current_count = await self._repository.count()
            if current_count >= 10000:  # Example limit
                validation_errors["system_limit"] = "Maximum number of users reached"
        except Exception as e:
            validation_errors["system_check"] = f"Unable to verify system constraints: {str(e)}"
        
        if validation_errors:
            raise UserValidationException(validation_errors)
    
    async def validate_business_domain_rules(self, user: User, domain_whitelist: List[str] = None) -> None:
        """
        Validate business-specific domain rules.
        """
        if domain_whitelist:
            email_domain = user.email.value.split('@')[1].lower()
            if email_domain not in [d.lower() for d in domain_whitelist]:
                raise EmailDomainNotAllowedException(
                    user.email.value, 
                    email_domain, 
                    domain_whitelist
                )


class UserAnalyticsService:
    """Service for user analytics and reporting."""
    
    def __init__(self, user_repository):
        self._repository = user_repository
    
    async def get_user_statistics(self) -> Dict[str, int]:
        """Get basic user statistics."""
        try:
            total_users = await self._repository.count()
            
            # You could add more analytics here
            return {
                "total_users": total_users,
                # Add more metrics as needed
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get user statistics: {str(e)}")
    
    async def find_users_by_domain(self, domain: str) -> List[User]:
        """Find all users with emails from a specific domain."""
        try:
            all_users = await self._repository.find_all()
            return [
                user for user in all_users 
                if user.email.value.split('@')[1].lower() == domain.lower()
            ]
        except Exception as e:
            raise RuntimeError(f"Failed to find users by domain: {str(e)}")


# Factory for creating domain services with common configurations
class DomainServiceFactory:
    @staticmethod
    def create_user_domain_service(
        user_repository, 
        enable_profanity_filter: bool = False,
        allowed_domains: List[str] = None,
        business_hours_only: bool = False
    ) -> UserDomainService:
        """Create a UserDomainService with common rule configurations."""
        
        rules = [
            EmailFormatAdvancedValidationRule(),
            NameContentValidationRule(),
        ]
        
        if enable_profanity_filter:
            # Add common profanity words - in production, load from config/database
            forbidden_words = ["badword1", "badword2"]  # Replace with actual list
            rules.append(NameProfanityValidationRule(forbidden_words))
        
        if allowed_domains:
            rules.append(EmailDomainValidationRule(allowed_domains))
        
        if business_hours_only:
            rules.append(BusinessHoursValidationRule(business_hours_only))
        
        return UserDomainService(user_repository, rules)
    
    @staticmethod
    def create_analytics_service(user_repository) -> UserAnalyticsService:
        """Create a UserAnalyticsService."""
        return UserAnalyticsService(user_repository)
