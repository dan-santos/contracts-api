from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from app.api.v1.contract.schemas import CancelRequestResponse, CreateContractRequest, ContractResponse
from app.exceptions import ContractCancellationConflictError, ContractCancellationError, ContractCancellationUnexpectedError, ContractNotFoundError, ContractReprocessingError
from app.infra.cancel_request.gateway import CancelRequestGateway
from app.infra.contract.gateway import ContractGateway
from app.logging_config import get_logger
from app.services.contract.cancel import CancelContractService
from app.services.contract.create import CreateContractService
from app.services.contract.reprocess import ReprocessContractService

from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/contracts", tags=["contracts"])
logger = get_logger(__name__)


@router.post("/")
async def create_contract(contract: CreateContractRequest) -> ContractResponse:
    service = CreateContractService(gateway=ContractGateway())

    try:
        domain_contract = CreateContractRequest.to_domain(contract)
        created_contract = await service.create(domain_contract)

        return ContractResponse.from_contract(created_contract)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))


@router.post("/{contract_id}/cancel")
async def cancel_contract(contract_id: UUID, idempotency_key: Annotated[str, Header()]) -> CancelRequestResponse:
    service = CancelContractService(contract_gateway=ContractGateway(), cancel_request_gateway=CancelRequestGateway())
    try:
        cancel_request = await service.cancel(contract_id, idempotency_key)
        return CancelRequestResponse.from_cancel_request(cancel_request)
    except ContractCancellationError as exc:
        logger.warning(
            "cancel_contract_validation_failed",
            contract_id=str(contract_id),
            idempotency_key=idempotency_key,
            error=str(exc)
        )
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc))
    except ContractNotFoundError as exc:
        logger.warning(
            "cancel_contract_not_found",
            contract_id=str(contract_id),
            idempotency_key=idempotency_key
        )
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))
    except ContractCancellationUnexpectedError as exc:
        logger.error(
            "cancel_contract_unexpected_error",
            contract_id=str(contract_id),
            idempotency_key=idempotency_key,
            error=str(exc),
            exc_info=True
        )
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(exc))
    except ContractCancellationConflictError as exc:
        logger.warning(
            "cancel_contract_conflict",
            contract_id=str(contract_id),
            idempotency_key=idempotency_key,
            error=str(exc)
        )
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(exc))


@router.post("/{contract_id}/reprocess")
async def reprocess_contract(contract_id: UUID) -> ContractResponse:
    service = ReprocessContractService(gateway=ContractGateway())
    try:
        contract = await service.reprocess(contract_id)
        return ContractResponse.from_contract(contract)
    except ContractReprocessingError as exc:
        logger.warning(
            "reprocess_contract_validation_failed",
            contract_id=str(contract_id),
            error=str(exc)
        )
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc))
    except ContractNotFoundError as exc:
        logger.warning(
            "reprocess_contract_not_found",
            contract_id=str(contract_id)
        )
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))
