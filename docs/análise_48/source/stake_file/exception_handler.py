# src/dev_platform/infrastructure/database/exception_handler.py
from abc import ABC, abstractmethod
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dev_platform.domain.user.user_exceptions import UserAlreadyExistsException
from dev_platform.domain.exceptions import DatabaseException, DataIntegrityException
from dev_platform.application.ports.logger import ILogger


class IExceptionMapper(ABC):
    @abstractmethod
    def map_and_raise(self, error: Exception, operation: str, **context) -> None:
        """
        Mapeia uma exceção de infraestrutura para uma exceção de domínio e a lança.

        Args:
            error (Exception): A exceção original capturada.
            operation (str): O nome da operação que estava em andamento.
            **context (Any): Dados de contexto adicionais sobre a operação.
        """
        pass

class SQLAlchemyExceptionMapper(IExceptionMapper):
    def __init__(self, logger: ILogger):
        self._logger = logger

    def map_and_raise(self, error: Exception, operation: str, **context):
        self._logger.error(
            "SQLAlchemy error captured by decorator",
            operation=operation,
            error=str(error),
            context=context
        )
        if isinstance(error, IntegrityError):
            dbapi_exception = error.orig
            if hasattr(dbapi_exception, 'errno') and dbapi_exception.errno == 1062:
                if "'uq_users_email'" in str(dbapi_exception):
                    raise UserAlreadyExistsException(context.get("email", "unknown")) from error
            raise DataIntegrityException(
                constraint_name="unknown",
                details=str(error),
                original_exception=error
            ) from error
        
        raise DatabaseException(
            operation=operation,
            reason=str(error),
            original_exception=error
        )

def handle_repository_errors(func):
    """
    Decorator que captura SQLAlchemyError, loga, e usa um IExceptionMapper
    anexado à instância do repositório para traduzir a exceção.
    """
    @wraps(func)
    async def wrapper(repo_instance, *args, **kwargs):
        # Acessa o mapper diretamente da instância do repositório ('self')
        mapper = getattr(repo_instance, '_exception_mapper', None)
        if not isinstance(mapper, IExceptionMapper):
            # Fallback de segurança se o mapper não for injetado corretamente
            raise TypeError("O repositório decorado deve ter um atributo '_exception_mapper' do tipo IExceptionMapper.")

        try:
            return await func(repo_instance, *args, **kwargs)
        except SQLAlchemyError as e:
            # Extrai contexto dos argumentos para um log mais rico
            context = {**kwargs}
            try:
                arg_names = func.__code__.co_varnames[1:len(args)+1] # Pula 'self'/'repo_instance'
                context.update(dict(zip(arg_names, args)))
            except (IndexError, AttributeError):
                pass # Ignora falhas na introspecção dos argumentos

            mapper.map_and_raise(e, operation=func.__name__, **context)
    return wrapper
