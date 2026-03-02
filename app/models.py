from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID


class ContractStatus(Enum):
    CREATED = "CREATED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    PROCESSING = "PROCESSING"

@dataclass
class Contract:
    id: UUID
    amount: Decimal
    refundable_amount: Decimal
    status: ContractStatus = ContractStatus.PROCESSING
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class CancelRequestStatus(Enum):
    SUCCESS = "SUCCESS"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"


@dataclass
class CancelRequest:
    id: UUID
    contract_id: UUID
    idempotency_key: str
    status: CancelRequestStatus = CancelRequestStatus.PROCESSING
    created_at: datetime = datetime.now()