from application.user.use_cases import CreateUserUseCase, ListUsersUseCase
from infrastructure.database.unit_of_work import SQLUnitOfWork
from infrastructure.logging.structured_logger import StructuredLogger

class CompositionRoot:
    def __init__(self):
        self._logger = StructuredLogger()
    
    def create_user_use_case(self) -> CreateUserUseCase:
        return CreateUserUseCase(
            uow=SQLUnitOfWork(),
            logger=self._logger
        )
    
    def list_users_use_case(self) -> ListUsersUseCase:
        return ListUsersUseCase(
            uow=SQLUnitOfWork(),
            logger=self._logger
        )