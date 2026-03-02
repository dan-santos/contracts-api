from abc import abstractmethod, ABC
from datetime import datetime, timedelta
from uuid import UUID

from app.exceptions import ContractReprocessingError
from app.logging_config import get_logger
from app.models import Contract, ContractStatus
from app.repositories.contract.gateway import IContractGateway

REPROCESSING_MINUTES_TOLERANCE = 5

logger = get_logger(__name__)


class IReprocessContractService(ABC):
    @abstractmethod
    async def reprocess(self, contract_id: UUID) -> Contract:
        """
        Reprocesses an existing contract
        """
        raise NotImplementedError()


class ReprocessContractService(IReprocessContractService):
    def __init__(self, gateway: IContractGateway):
        self.gateway = gateway

    async def reprocess(self, contract_id: UUID) -> Contract:
        logger.info(
            "reprocessing_contract",
            contract_id=str(contract_id)
        )
        
        contract = await self.gateway.get(contract_id)
        
        logger.debug(
            "contract_retrieved_for_reprocessing",
            contract_id=str(contract_id),
            current_status=contract.status.value,
            updated_at=contract.updated_at.isoformat()
        )
        
        self._run_reprocessing_rules(contract)
        
        reprocessed_contract = await self.gateway.reprocess(contract_id)
        
        logger.info(
            "contract_reprocessed_successfully",
            contract_id=str(contract_id),
            new_status=reprocessed_contract.status.value
        )
        
        return reprocessed_contract

    def _run_reprocessing_rules(self, contract: Contract) -> None:
        five_minutes_ago = datetime.now() - timedelta(minutes=REPROCESSING_MINUTES_TOLERANCE)
        
        if five_minutes_ago < contract.updated_at:
            minutes_since_update = (datetime.now() - contract.updated_at).total_seconds() / 60
            logger.warning(
                "contract_updated_too_recently",
                contract_id=str(contract.id),
                minutes_since_update=round(minutes_since_update, 2),
                tolerance_minutes=REPROCESSING_MINUTES_TOLERANCE
            )
            raise ContractReprocessingError(f"Contract was last updated less than {REPROCESSING_MINUTES_TOLERANCE} minutes ago")

        if contract.status != ContractStatus.PROCESSING:
            logger.warning(
                "contract_invalid_status_for_reprocessing",
                contract_id=str(contract.id),
                current_status=contract.status.value,
                expected_status=ContractStatus.PROCESSING.value
            )
            raise ContractReprocessingError(f"Contract is not in {ContractStatus.PROCESSING.value} status")

