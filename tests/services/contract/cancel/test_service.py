from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from freezegun import freeze_time

from app.exceptions import ContractCancellationError
from app.models import CancelRequest, CancelRequestStatus, Contract, ContractStatus
from app.services.contract.cancel import CancelContractService


class TestCancelContractService:
    @pytest.fixture
    def mock_contract_gateway(self):
        gateway = Mock()
        gateway.get = AsyncMock()
        gateway.cancel = AsyncMock()
        return gateway

    @pytest.fixture
    def mock_cancel_request_gateway(self):
        gateway = Mock()
        gateway.get = AsyncMock()
        gateway.create = AsyncMock()
        gateway.set_request_status = AsyncMock()
        return gateway

    @pytest.fixture
    def service(self, mock_contract_gateway, mock_cancel_request_gateway):
        return CancelContractService(
            contract_gateway=mock_contract_gateway,
            cancel_request_gateway=mock_cancel_request_gateway
        )

    @pytest.fixture
    def sample_contract(self):
        return Contract(
            id=uuid4(),
            amount=Decimal("100.00"),
            refundable_amount=Decimal("90.00"),
            status=ContractStatus.CREATED,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )

    @freeze_time("2024-01-03 12:00:00")
    @pytest.mark.asyncio
    async def test_cancel_contract_success(
        self, service, mock_contract_gateway, mock_cancel_request_gateway, sample_contract
    ):
        idempotency_key = "test-key-123"
        mock_cancel_request_gateway.get.return_value = None
        mock_contract_gateway.get.return_value = sample_contract

        successful_cancel_request = CancelRequest(
            id=uuid4(),
            contract_id=sample_contract.id,
            idempotency_key=idempotency_key,
            status=CancelRequestStatus.SUCCESS,
            created_at=datetime(2024, 1, 3, 12, 0, 0)
        )
        mock_cancel_request_gateway.set_request_status.return_value = successful_cancel_request

        result = await service.cancel(sample_contract.id, idempotency_key)

        mock_cancel_request_gateway.get.assert_awaited_once_with(idempotency_key, sample_contract.id)
        mock_contract_gateway.get.assert_awaited_once_with(sample_contract.id)
        
        assert mock_cancel_request_gateway.create.await_count == 1
        created_request = mock_cancel_request_gateway.create.await_args[0][0]
        assert created_request.contract_id == sample_contract.id
        assert created_request.idempotency_key == idempotency_key
        assert created_request.status == CancelRequestStatus.PROCESSING
        
        mock_contract_gateway.cancel.assert_awaited_once_with(sample_contract.id)

        mock_cancel_request_gateway.set_request_status.assert_awaited_once_with(
            idempotency_key,
            CancelRequestStatus.SUCCESS.value
        )
        
        assert result == successful_cancel_request
        assert result.status == CancelRequestStatus.SUCCESS

    @freeze_time("2024-01-03 12:00:00")
    @pytest.mark.asyncio
    async def test_cancel_contract_returns_existing_cancel_request(
        self, service, mock_contract_gateway, mock_cancel_request_gateway, sample_contract
    ):
        idempotency_key = "test-key-123"
        existing_cancel_request = CancelRequest(
            id=uuid4(),
            contract_id=sample_contract.id,
            idempotency_key=idempotency_key,
            status=CancelRequestStatus.SUCCESS,
            created_at=datetime(2024, 1, 2, 12, 0, 0)
        )
        mock_cancel_request_gateway.get.return_value = existing_cancel_request

        result = await service.cancel(sample_contract.id, idempotency_key)

        mock_cancel_request_gateway.get.assert_awaited_once_with(idempotency_key, sample_contract.id)
        
        mock_contract_gateway.get.assert_not_awaited()
        mock_cancel_request_gateway.create.assert_not_awaited()
        mock_contract_gateway.cancel.assert_not_awaited()
        mock_cancel_request_gateway.set_request_status.assert_not_awaited()
        
        assert result == existing_cancel_request

    @freeze_time("2024-01-03 12:00:00")
    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_contract(
        self, service, mock_contract_gateway, mock_cancel_request_gateway, sample_contract
    ):
        idempotency_key = "test-key-456"
        already_cancelled_contract = Contract(
            id=sample_contract.id,
            amount=sample_contract.amount,
            refundable_amount=sample_contract.refundable_amount,
            status=ContractStatus.CANCELLED,
            created_at=sample_contract.created_at,
            updated_at=datetime(2024, 1, 2, 12, 0, 0)
        )
        
        mock_cancel_request_gateway.get.return_value = None
        mock_contract_gateway.get.return_value = already_cancelled_contract

        result = await service.cancel(sample_contract.id, idempotency_key)

        mock_cancel_request_gateway.get.assert_awaited_once_with(idempotency_key, sample_contract.id)
        mock_contract_gateway.get.assert_awaited_once_with(sample_contract.id)
        
        mock_cancel_request_gateway.create.assert_not_awaited()
        mock_contract_gateway.cancel.assert_not_awaited()
        mock_cancel_request_gateway.set_request_status.assert_not_awaited()

        assert result.contract_id == sample_contract.id
        assert result.idempotency_key == idempotency_key
        assert result.status == CancelRequestStatus.SUCCESS

    @freeze_time("2024-01-10 12:00:00")
    @pytest.mark.asyncio
    async def test_cancel_contract_exceeds_tolerance_period(
        self, service, mock_contract_gateway, mock_cancel_request_gateway, sample_contract
    ):
        idempotency_key = "test-key-789"
        mock_cancel_request_gateway.get.return_value = None
        mock_contract_gateway.get.return_value = sample_contract

        with pytest.raises(ContractCancellationError, match="Cancellation period of 7 days has been exceeded"):
            await service.cancel(sample_contract.id, idempotency_key)

        mock_cancel_request_gateway.get.assert_awaited_once()
        mock_contract_gateway.get.assert_awaited_once()

        mock_cancel_request_gateway.create.assert_not_awaited()
        mock_contract_gateway.cancel.assert_not_awaited()
        mock_cancel_request_gateway.set_request_status.assert_not_awaited()

    @freeze_time("2024-01-03 12:00:00")
    @pytest.mark.asyncio
    async def test_cancel_contract_no_refundable_amount(
        self, service, mock_contract_gateway, mock_cancel_request_gateway
    ):
        contract_no_refund = Contract(
            id=uuid4(),
            amount=Decimal("100.00"),
            refundable_amount=Decimal("0.00"),
            status=ContractStatus.CREATED,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        idempotency_key = "test-key-999"
        
        mock_cancel_request_gateway.get.return_value = None
        mock_contract_gateway.get.return_value = contract_no_refund

        with pytest.raises(ContractCancellationError, match="Contract does not have refundable amount"):
            await service.cancel(contract_no_refund.id, idempotency_key)

        mock_cancel_request_gateway.get.assert_awaited_once()
        mock_contract_gateway.get.assert_awaited_once()

        mock_cancel_request_gateway.create.assert_not_awaited()
        mock_contract_gateway.cancel.assert_not_awaited()

    @freeze_time("2024-01-03 12:00:00")
    @pytest.mark.asyncio
    async def test_cancel_contract_failure_sets_failed_status(
        self, service, mock_contract_gateway, mock_cancel_request_gateway, sample_contract
    ):
        idempotency_key = "test-key-error"
        mock_cancel_request_gateway.get.return_value = None
        mock_contract_gateway.get.return_value = sample_contract
        mock_contract_gateway.cancel.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await service.cancel(sample_contract.id, idempotency_key)

        mock_cancel_request_gateway.create.assert_awaited_once()
        mock_contract_gateway.cancel.assert_awaited_once_with(sample_contract.id)

        mock_cancel_request_gateway.set_request_status.assert_awaited_once_with(
            idempotency_key,
            CancelRequestStatus.FAILED.value
        )
