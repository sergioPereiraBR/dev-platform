# Mock mais simples
async def test_create_user():
    mock_uow = Mock(spec=AbstractUnitOfWork)
    mock_uow.users.save.return_value = User(id=1, name="Test", email="test@test.com")
    
    use_case = AsyncCreateUserUseCase()
    # Test com mock...