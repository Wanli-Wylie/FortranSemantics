from abc import ABC, abstractmethod
from sqlalchemy.orm.session import Session
from .handles import CommandHandle, QueryHandle

class BaseOfflineTask(ABC):
    def __init__(
        self,
        session: Session,
    ) -> None:
        self.query_handle = QueryHandle(session)
        self.command_handle = CommandHandle(session)
    
    @abstractmethod
    def execute(self) -> None:
        """Run the task."""
        pass
