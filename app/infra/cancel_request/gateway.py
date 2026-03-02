from app.exceptions import ContractCancellationConflictError
from app.infra.db.engine import get_engine
from app.infra.db.entities import CancelRequest as DBCancelRequest, CancelRequestStatusEnum
from app.repositories.cancel_request.gateway import ICancelRequestGateway
from app.models import CancelRequest, CancelRequestStatus

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

class CancelRequestGateway(ICancelRequestGateway):
    def __init__(self):
        self.engine = get_engine()
        
    def _to_domain(self, db_cancel_request: DBCancelRequest) -> CancelRequest:
        return CancelRequest(
            id=db_cancel_request.id,
            contract_id=db_cancel_request.contract_id,
            idempotency_key=db_cancel_request.idempotency_key,
            status=CancelRequestStatus[db_cancel_request.status.value],
            created_at=db_cancel_request.created_at
        )

    def _to_db(self, cancel_request: CancelRequest) -> DBCancelRequest:
        return DBCancelRequest(
            id=cancel_request.id,
            contract_id=cancel_request.contract_id,
            idempotency_key=cancel_request.idempotency_key,
            status=CancelRequestStatusEnum[cancel_request.status.value],
            created_at=cancel_request.created_at
        )

    async def create(self, cancel_request: CancelRequest) -> None:
        try:
            async with AsyncSession(self.engine) as db_session:
                db_cancel_request = self._to_db(cancel_request)
                db_session.add(db_cancel_request)
                await db_session.commit()
                await db_session.refresh(db_cancel_request)
        except IntegrityError:
            raise ContractCancellationConflictError(f"Cancel request with idempotency key {cancel_request.idempotency_key} already exists.")

    async def get(self, idempotency_key: str, contract_id: str) -> CancelRequest | None:
        async with AsyncSession(self.engine) as db_session:
            result = await db_session.execute(
                select(DBCancelRequest).filter_by(idempotency_key=idempotency_key, contract_id=contract_id).with_for_update()
            )
            db_cancel_request = result.scalar_one_or_none()
            if db_cancel_request:
                return self._to_domain(db_cancel_request)

            return None

    async def set_request_status(self, idempotency_key: str, status: str) -> CancelRequest | None:
        async with AsyncSession(self.engine) as db_session:
            result = await db_session.execute(
                select(DBCancelRequest).filter_by(idempotency_key=idempotency_key).with_for_update()
            )
            db_cancel_request = result.scalar_one_or_none()
            if db_cancel_request:
                db_cancel_request.status = CancelRequestStatusEnum[status]
                db_session.add(db_cancel_request)
                await db_session.commit()
                await db_session.refresh(db_cancel_request)

                return self._to_domain(db_cancel_request)
