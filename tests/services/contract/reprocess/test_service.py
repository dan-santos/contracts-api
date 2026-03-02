from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from freezegun import freeze_time

from app.exceptions import ContractReprocessingError
from app.models import Contract, ContractStatus
from app.services.contract.reprocess import ReprocessContractService


class TestReprocessContractService:
    @pytest.fixture
    def mock_gateway(self):
        gateway = Mock()
        gateway.get = AsyncMock()
        gateway.reprocess = AsyncMock()
        return gateway

    @pytest.fixture
    def service(self, mock_gateway):
        return ReprocessContractService(gateway=mock_gateway)

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

    @freeze_time("2024-01-01 12:10:00")
    @pytest.mark.asyncio
    async def test_reprocess_contract_success(self, service, mock_gateway, sample_contract):
        reprocessed_contract = Contract(
            id=sample_contract.id,
            amount=sample_contract.amount,
            refundable_amount=sample_contract.refundable_amount,
            status=ContractStatus.CREATED,
            created_at=sample_contract.created_at,
            updated_at=datetime(2024, 1, 1, 12, 10, 0)
        )
        mock_gateway.get.return_value = sample_contract
        mock_gateway.reprocess.return_value = reprocessed_contract

        result = await service.reprocess(sample_contract.id)

        mock_gateway.get.assert_awaited_once_with(sample_contract.id)
        mock_gateway.reprocess.assert_awaited_once_with(sample_contract.id)
        assert result == reprocessed_contract

    @freeze_time("2024-01-01 12:10:00")
    @pytest.mark.asyncio
    async def test_reprocess_contract_passes_correct_id(self, service, mock_gateway, sample_contract):
        contract_id = sample_contract.id
        reprocessed_contract = Contract(
            id=contract_id,
            amount=sample_contract.amount,
            refundable_amount=sample_contract.refundable_amount,
            status=ContractStatus.CREATED,
            created_at=sample_contract.created_at,
            updated_at=datetime(2024, 1, 1, 12, 10, 0)
        )
        mock_gateway.get.return_value = sample_contract
        mock_gateway.reprocess.return_value = reprocessed_contract

        await service.reprocess(contract_id)

        get_call_args = mock_gateway.get.await_args
        assert get_call_args[0][0] == contract_id
        
        reprocess_call_args = mock_gateway.reprocess.await_args
        assert reprocess_call_args[0][0] == contract_id

    @freeze_time("2024-01-01 12:03:00")  # 3 minutos depois (não excede 5 min)
    @pytest.mark.asyncio
    async def test_reprocess_contract_updated_recently(self, service, mock_gateway, sample_contract):
        mock_gateway.get.return_value = sample_contract

        with pytest.raises(
            ContractReprocessingError,
            match="Contract was last updated less than 5 minutes ago"
        ):
            await service.reprocess(sample_contract.id)

        mock_gateway.get.assert_awaited_once_with(sample_contract.id)
        mock_gateway.reprocess.assert_not_awaited()

    @freeze_time("2024-01-01 12:10:00")
    @pytest.mark.asyncio
    async def test_reprocess_contract_wrong_status(self, service, mock_gateway):
        wrong_status_contract = Contract(
            id=uuid4(),
            amount=Decimal("100.00"),
            refundable_amount=Decimal("90.00"),
            status=ContractStatus.CREATED,  # Status errado (não é PROCESSING)
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_gateway.get.return_value = wrong_status_contract

        with pytest.raises(
            ContractReprocessingError,
            match=f"Contract is not in {ContractStatus.PROCESSING.value} status"
        ):
            await service.reprocess(wrong_status_contract.id)

        mock_gateway.get.assert_awaited_once()
        mock_gateway.reprocess.assert_not_awaited()

    @freeze_time("2024-01-01 12:10:00")
    @pytest.mark.asyncio
    async def test_reprocess_contract_cancelled_status(self, service, mock_gateway):
        cancelled_contract = Contract(
            id=uuid4(),
            amount=Decimal("100.00"),
            refundable_amount=Decimal("90.00"),
            status=ContractStatus.CANCELLED,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        mock_gateway.get.return_value = cancelled_contract

        with pytest.raises(ContractReprocessingError):
            await service.reprocess(cancelled_contract.id)

        mock_gateway.reprocess.assert_not_awaited()

    @freeze_time("2024-01-01 12:05:00")
    @pytest.mark.asyncio
    async def test_reprocess_contract_exact_tolerance_limit(self, service, mock_gateway, sample_contract):
        reprocessed_contract = Contract(
            id=sample_contract.id,
            amount=sample_contract.amount,
            refundable_amount=sample_contract.refundable_amount,
            status=ContractStatus.CREATED,
            created_at=sample_contract.created_at,
            updated_at=datetime(2024, 1, 1, 12, 5, 0)
        )
        mock_gateway.get.return_value = sample_contract
        mock_gateway.reprocess.return_value = reprocessed_contract

        result = await service.reprocess(sample_contract.id)

        mock_gateway.get.assert_awaited_once_with(sample_contract.id)
        mock_gateway.reprocess.assert_awaited_once_with(sample_contract.id)
        assert result == reprocessed_contract

    @freeze_time("2024-01-01 12:10:00")
    @pytest.mark.asyncio
    async def test_reprocess_contract_multiple_validations(self, service, mock_gateway):
        invalid_contract = Contract(
            id=uuid4(),
            amount=Decimal("100.00"),
            refundable_amount=Decimal("90.00"),
            status=ContractStatus.FAILED,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 9, 0)
        )
        mock_gateway.get.return_value = invalid_contract

        with pytest.raises(
            ContractReprocessingError,
            match="Contract was last updated less than 5 minutes ago"
        ):
            await service.reprocess(invalid_contract.id)

        mock_gateway.reprocess.assert_not_awaited()
