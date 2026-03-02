from datetime import datetime
from uuid import UUID

from app.exceptions import ContractNotFoundError
from app.infra.db.engine import get_engine
from app.models import Contract, ContractStatus
from app.infra.db.entities import Contract as DBContract, ContractStatusEnum
from app.repositories.contract.gateway import IContractGateway

from sqlmodel import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession


class ContractGateway(IContractGateway):
    def __init__(self):
        self.engine = get_engine()

    def _to_domain(self, db_contract: DBContract) -> Contract:
        return Contract(
            id=db_contract.id,
            amount=db_contract.amount,
            refundable_amount=db_contract.refundable_amount,
            status=ContractStatus[db_contract.status.value],
            created_at=db_contract.created_at,
            updated_at=db_contract.updated_at
        )

    def _to_db(self, contract: Contract) -> DBContract:
        return DBContract(
            id=contract.id,
            amount=contract.amount,
            refundable_amount=contract.refundable_amount,
            status=ContractStatusEnum[contract.status.value],
            created_at=contract.created_at,
            updated_at=contract.updated_at
        )

    async def create(self, contract: Contract) -> Contract:
        async with AsyncSession(self.engine) as dbsession:
            db_contract = self._to_db(contract)
            dbsession.add(db_contract)
            await dbsession.commit()
            await dbsession.refresh(db_contract)

        return self._to_domain(db_contract)

    async def get(self, contract_id: UUID) -> Contract:
        statement = select(DBContract).filter_by(id=contract_id).with_for_update()

        try:
            async with AsyncSession(self.engine) as dbsession:
                result = await dbsession.execute(statement)
                db_contract = result.scalar_one()
                return self._to_domain(db_contract)
        except NoResultFound:
            raise ContractNotFoundError(f"Contract with id {contract_id} not found")

    async def cancel(self, contract_id: UUID) -> None:
        try:
            async with AsyncSession(self.engine) as dbsession:
                result = await dbsession.execute(select(DBContract).filter_by(id=contract_id).with_for_update())
                contract = result.scalar_one()
                contract.status = ContractStatusEnum.CANCELLED
                contract.updated_at = datetime.now()
                dbsession.add(contract)
                await dbsession.commit()
                await dbsession.refresh(contract)
        except NoResultFound:
            raise ContractNotFoundError(f"Contract with id {contract_id} not found")

    async def reprocess(self, contract_id: UUID) -> Contract:
        """
        Since the technical test didn't specify the reprocessing workflow, 
        this method will simply update the contract status to CREATED.
        
        The entire application was designed to created a contract with a PROCESSING status and
        then update it to CREATED or FAILED (like an async operation). Thats why I decided
        to implement the reprocessing this way.
        """

        try:
            async with AsyncSession(self.engine) as dbsession:
                result = await dbsession.execute(select(DBContract).filter_by(id=contract_id).with_for_update())
                contract = result.scalar_one()
                contract.status = ContractStatusEnum.CREATED
                contract.updated_at = datetime.now()
                dbsession.add(contract)
                await dbsession.commit()
                await dbsession.refresh(contract)

                return self._to_domain(contract)
        except NoResultFound:
            raise ContractNotFoundError(f"Contract with id {contract_id} not found")

    async def set_contract_status(self, contract_id: UUID, status: str) -> Contract:
        try:
            async with AsyncSession(self.engine) as dbsession:
                result = await dbsession.execute(select(DBContract).filter_by(id=contract_id).with_for_update())
                contract = result.scalar_one()
                contract.status = ContractStatusEnum[status]
                contract.updated_at = datetime.now()
                dbsession.add(contract)
                await dbsession.commit()
                await dbsession.refresh(contract)
                return self._to_domain(contract)
        except NoResultFound:
            raise ContractNotFoundError(f"Contract with id {contract_id} not found")
