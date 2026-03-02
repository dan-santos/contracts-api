from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from decimal import Decimal

from app.models import CancelRequest, CancelRequestStatus, Contract

from pydantic import BaseModel

class ContractStatus(Enum):
    CREATED = "CREATED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    REPROCESSING = "REPROCESSING"


class CreateContractRequest(BaseModel):
    amount: Decimal
    refundable_amount: Decimal
    
    @staticmethod
    def to_domain(request: "CreateContractRequest") -> Contract:
        return Contract(
            id=uuid4(),
            amount=request.amount,
            refundable_amount=request.refundable_amount,
        )


class ContractResponse(BaseModel):
    id: UUID
    amount: Decimal
    refundable_amount: Decimal
    status: ContractStatus
    created_at: datetime
    updated_at: datetime
    
    @staticmethod
    def from_contract(contract: Contract) -> "ContractResponse":
        return ContractResponse(
            id=contract.id,
            amount=contract.amount,
            refundable_amount=contract.refundable_amount,
            status=ContractStatus(contract.status.value),
            created_at=contract.created_at,
            updated_at=contract.updated_at
        )
        
class CancelRequestResponse(BaseModel):
    id: UUID
    contract_id: UUID
    idempotency_key: str
    status: str
    created_at: datetime
    
    @staticmethod
    def from_cancel_request(cancel_request: CancelRequest) -> "CancelRequestResponse":
        return CancelRequestResponse(
            id=cancel_request.id,
            contract_id=cancel_request.contract_id,
            idempotency_key=cancel_request.idempotency_key,
            status=CancelRequestStatus(cancel_request.status.value),
            created_at=cancel_request.created_at
        )