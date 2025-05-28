from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Email:
    value: str
    
    def __post_init__(self):
        if not self._is_valid():
            raise ValueError("Invalid email format")
    
    def _is_valid(self) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, self.value))

@dataclass(frozen=True)
class UserName:
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value) < 3:
            raise ValueError("Name must be at least 3 characters long")
        if len(self.value) > 100:
            raise ValueError("Name cannot exceed 100 characters")