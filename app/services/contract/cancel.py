from abc import abstractmethod, ABC
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.exceptions import ContractCancellationError
from app.logging_config import get_logger
from app.models import CancelRequest, CancelRequestStatus, Contract, ContractStatus
from app.repositories.cancel_request.gateway import ICancelRequestGateway
from app.repositories.contract.gateway import IContractGateway

CANCELLATION_DAYS_TOLERANCE = 7

logger = get_logger(__name__)


class ICancelContractService(ABC):
    @abstractmethod
    async def cancel(self, contract_id: UUID, idempotency_key: str) -> Contract:
        """
        Cancels an existing contract
        """
        raise NotImplementedError()


class CancelContractService(ICancelContractService):
    def __init__(self, contract_gateway: IContractGateway, cancel_request_gateway: ICancelRequestGateway):
        self.contract_gateway = contract_gateway
        self.cancel_request_gateway = cancel_request_gateway

    async def cancel(self, contract_id: UUID, idempotency_key: str) -> CancelRequest:
        logger.info(
            "cancelling_contract",
            contract_id=str(contract_id),
            idempotency_key=idempotency_key
        )
        
        operation_at = datetime.now()

        existing_cancel_request = await self.cancel_request_gateway.get(idempotency_key, contract_id)
        if existing_cancel_request:
            logger.info(
                "cancel_request_already_exists",
                contract_id=str(contract_id),
                idempotency_key=idempotency_key,
                status=existing_cancel_request.status.value
            )
            return existing_cancel_request

        contract = await self.contract_gateway.get(contract_id)

        """
        If the workflow reaches this point, it means that the contract has already been cancelled
        by another cancellation request (the idempotency key isnt the same).
        In this case, we simply return a successful cancel request instance without persisting it.
        """
        if contract.status == ContractStatus.CANCELLED:
            logger.info(
                "contract_already_cancelled",
                contract_id=str(contract_id),
                idempotency_key=idempotency_key
            )
            return self._create_cancel_request(contract_id, idempotency_key, already_cancelled=True)

        self._run_cancellation_rules(contract, operation_at)

        cancel_request = self._create_cancel_request(contract_id, idempotency_key)

        try:
            await self.cancel_request_gateway.create(cancel_request)
            await self.contract_gateway.cancel(contract_id)

            cancel_request = await self.cancel_request_gateway.set_request_status(idempotency_key, CancelRequestStatus.SUCCESS.value)
            
            logger.info(
                "contract_cancelled_successfully",
                contract_id=str(contract_id),
                idempotency_key=idempotency_key,
                cancel_request_id=str(cancel_request.id)
            )
            
            return cancel_request
        except Exception as exc:
            logger.error(
                "error_cancelling_contract",
                contract_id=str(contract_id),
                idempotency_key=idempotency_key,
                error=str(exc),
                exc_info=True
            )
            await self.cancel_request_gateway.set_request_status(idempotency_key, CancelRequestStatus.FAILED.value)
            raise

    def _run_cancellation_rules(self, contract: Contract, operation_at: datetime) -> None:
        timedelta = operation_at - contract.created_at
        days_difference = timedelta.days

        if days_difference > CANCELLATION_DAYS_TOLERANCE:
            logger.warning(
                "cancellation_period_exceeded",
                contract_id=str(contract.id),
                days_difference=days_difference,
                tolerance=CANCELLATION_DAYS_TOLERANCE
            )
            raise ContractCancellationError(f"Cancellation period of {CANCELLATION_DAYS_TOLERANCE} days has been exceeded")

        if contract.refundable_amount <= Decimal():
            logger.warning(
                "no_refundable_amount",
                contract_id=str(contract.id),
                refundable_amount=str(contract.refundable_amount)
            )
            raise ContractCancellationError("Contract does not have refundable amount")

    def _create_cancel_request(self, contract_id: UUID, idempotency_key: str, already_cancelled: bool = False) -> CancelRequest:
        cancel_request = CancelRequest(
            id=uuid4(),
            contract_id=contract_id,
            idempotency_key=idempotency_key,
            status=CancelRequestStatus.SUCCESS if already_cancelled else CancelRequestStatus.PROCESSING,
        )
        
        return cancel_request
