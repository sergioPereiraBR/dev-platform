# ./tests/test_db.py
import pytest
from unittest.mock import Mock
from src.dev_platform.domain.user.entities import User
from src.dev_platform.infrastructure.database.unit_of_work import (
    AbstractUnitOfWork,
    AsyncCreateUserUseCase,
)  # Add this import or adjust the path as needed


# Mock mais simples
async def test_create_user():
    mock_uow = Mock(spec=AbstractUnitOfWork)
    mock_uow.users.save.return_value = User(id=1, name="Test", email="test@test.com")

    use_case = AsyncCreateUserUseCase()
    # Test com mock...
