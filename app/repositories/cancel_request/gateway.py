from abc import ABC, abstractmethod

from app.models import CancelRequest


class ICancelRequestGateway(ABC):
    @abstractmethod
    async def create(self, cancel_request: CancelRequest) -> None:
        """
        Creates a new cancelation request
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def get(self, idempotency_key: str, contract_id: str) -> CancelRequest | None:
        """
        Retrieves a cancelation request by its idempotency key
        """
        raise NotImplementedError()
    
    @abstractmethod
    async def set_request_status(self, idempotency_key: str, status: str) -> CancelRequest | None:
        """
        Updates the status of a cancelation request
        """
        raise NotImplementedError()
