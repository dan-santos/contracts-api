from abc import ABC, abstractmethod
from uuid import UUID

from app.models import Contract


class IContractGateway(ABC):
    @abstractmethod
    async def create(self, contract: Contract) -> Contract:
        """
        Creates a new contract
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def get(self, contract_id: UUID) -> Contract:
        """
        Retrieves a contract by its ID
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def cancel(self, contract_id: UUID) -> None:
        """
        Cancels a contract by its ID
        """
        raise NotImplementedError()

    @abstractmethod
    async def reprocess(self, contract_id: UUID) -> Contract:
        """
        Reprocesses a contract by its ID
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def set_contract_status(self, contract_id: UUID, status: str) -> Contract:
        """
        Updates the status of a contract
        """
        raise NotImplementedError()
