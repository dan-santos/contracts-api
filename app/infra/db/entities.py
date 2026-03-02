from datetime import datetime
from decimal import Decimal
from uuid import UUID
import enum

from sqlmodel import Field, SQLModel, Column
from sqlalchemy import Enum as SQLEnum


class ContractStatusEnum(str, enum.Enum):
    CREATED = "CREATED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    PROCESSING = "PROCESSING"


class CancelRequestStatusEnum(str, enum.Enum):
    SUCCESS = "SUCCESS"
    PROCESSING = "PROCESSING"
    FAILED = "FAILED"


class Contract(SQLModel, table=True):
    __tablename__ = "contracts"
    
    id: UUID = Field(primary_key=True)
    amount: Decimal = Field(max_digits=10, decimal_places=2)
    refundable_amount: Decimal = Field(max_digits=10, decimal_places=2)
    status: ContractStatusEnum = Field(sa_column=Column(SQLEnum(ContractStatusEnum)))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CancelRequest(SQLModel, table=True):
    __tablename__ = "cancel_requests"
    
    id: UUID = Field(primary_key=True)
    contract_id: UUID = Field(foreign_key="contracts.id")
    idempotency_key: str = Field(unique=True, index=True)
    status: CancelRequestStatusEnum = Field(sa_column=Column(SQLEnum(CancelRequestStatusEnum)))
    created_at: datetime = Field(default_factory=datetime.now)
