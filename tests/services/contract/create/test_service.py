from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from freezegun import freeze_time

from app.models import Contract, ContractStatus
from app.services.contract.create import CreateContractService


class TestCreateContractService:
    @pytest.fixture
    def mock_gateway(self):
        gateway = Mock()
        gateway.create = AsyncMock()
        gateway.set_contract_status = AsyncMock()
        return gateway

    @pytest.fixture
    def service(self, mock_gateway):
        return CreateContractService(gateway=mock_gateway)

    @pytest.fixture
    def sample_contract(self):
        return Contract(
            id=uuid4(),
            amount=Decimal("100.00"),
            refundable_amount=Decimal("90.00"),
            status=ContractStatus.PROCESSING,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )

    @freeze_time("2024-01-01 12:00:00")
    @pytest.mark.asyncio
    async def test_create_contract_success(self, service, mock_gateway, sample_contract):
        created_contract = Contract(
            id=sample_contract.id,
            amount=sample_contract.amount,
            refundable_amount=sample_contract.refundable_amount,
            status=ContractStatus.CREATED,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_gateway.set_contract_status.return_value = created_contract

        result = await service.create(sample_contract)

        mock_gateway.create.assert_awaited_once_with(sample_contract)
        mock_gateway.set_contract_status.assert_awaited_once_with(
            sample_contract.id,
            ContractStatus.CREATED.value
        )
        assert result == created_contract
        assert result.status == ContractStatus.CREATED

    @freeze_time("2024-01-01 12:00:00")
    @pytest.mark.asyncio
    async def test_create_contract_failure(self, service, mock_gateway, sample_contract):
        mock_gateway.create.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await service.create(sample_contract)

        mock_gateway.create.assert_awaited_once_with(sample_contract)
        mock_gateway.set_contract_status.assert_awaited_once_with(
            sample_contract.id,
            ContractStatus.FAILED.value
        )

    @freeze_time("2024-01-01 12:00:00")
    @pytest.mark.asyncio
    async def test_create_contract_passes_correct_contract_id(self, service, mock_gateway, sample_contract):
        contract_id = sample_contract.id
        created_contract = Contract(
            id=contract_id,
            amount=sample_contract.amount,
            refundable_amount=sample_contract.refundable_amount,
            status=ContractStatus.CREATED,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_gateway.set_contract_status.return_value = created_contract

        await service.create(sample_contract)

        call_args = mock_gateway.set_contract_status.await_args
        assert call_args[0][0] == contract_id
        assert call_args[0][1] == ContractStatus.CREATED.value
