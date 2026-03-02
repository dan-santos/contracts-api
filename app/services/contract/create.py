
from abc import abstractmethod, ABC

from app.logging_config import get_logger
from app.models import Contract, ContractStatus
from app.repositories.contract.gateway import IContractGateway

logger = get_logger(__name__)


class ICreateContractService(ABC):
    @abstractmethod
    async def create(self, contract: Contract) -> Contract:
        """
        Creates a new contract
        """
        raise NotImplementedError()
    

class CreateContractService(ICreateContractService):
    def __init__(self, gateway: IContractGateway):
        self.gateway = gateway

    async def create(self, contract: Contract) -> Contract:
        logger.info(
            "creating_contract",
            contract_id=str(contract.id),
            amount=str(contract.amount),
            status=contract.status.value
        )
        
        try:
            await self.gateway.create(contract)
            created_contract = await self.gateway.set_contract_status(contract.id, ContractStatus.CREATED.value)
            
            logger.info(
                "contract_created_successfully",
                contract_id=str(contract.id),
                status=ContractStatus.CREATED.value
            )
            
            return created_contract
        except Exception as exc:
            logger.error(
                "error_creating_contract",
                contract_id=str(contract.id),
                error=str(exc),
                exc_info=True
            )
            await self.gateway.set_contract_status(contract.id, ContractStatus.FAILED.value)
            raise