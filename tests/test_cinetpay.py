import hashlib
import hmac
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from easyswitch.exceptions import PaymentError, UnsupportedOperationError
from easyswitch.integrators.cinetpay import CinetpayAdapter
from easyswitch.types import (
    Currency,
    CustomerInfo,
    TransactionDetail,
    TransactionStatus,
)


# Fixtures pour les données de test
@pytest.fixture
def cinetpay_config():
    return {
        "api_key": "test_api_key",
        "environment": "sandbox",
        "extra": {
            "site_id": "test_site_id",
            "secret": "test_secret_key",
            "channels": "MOBILE_MONEY",
        },
        "callback_url": "https://example.com/callback",
    }


@pytest.fixture
def sample_transaction():
    return TransactionDetail(
        amount=1000,
        currency=Currency.XOF,
        transaction_id="test123",
        reference="order_123",
        customer=CustomerInfo(
            id="cust_123",
            first_name="John",
            last_name="Doe",
            phone_number="+221771234567",
            email="john.doe@example.com",
        ),
        reason="Test payment",
    )


@pytest.fixture
def cinetpay_adapter(cinetpay_config):
    return CinetpayAdapter(cinetpay_config)


@pytest.mark.asyncio
async def test_send_payment_success(cinetpay_adapter, sample_transaction):
    """Test successful payment request"""
    mock_response = {
        "code": "201",
        "message": "SUCCESS",
        "data": {"payment_url": "https://payment.link", "payment_token": "test_token"},
    }

    with patch.object(
        cinetpay_adapter.client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.data = mock_response

        response = await cinetpay_adapter.send_payment(sample_transaction)

        # Vérifications
        assert response.status == TransactionStatus.PENDING
        assert response.payment_link == "https://payment.link"
        assert response.transaction_token == "test_token"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_send_payment_failure(cinetpay_adapter, sample_transaction):
    """Test failed payment request"""

    with patch.object(
        cinetpay_adapter.client, "post", new_callable=AsyncMock
    ) as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.data = {"message": "Invalid request"}

        with pytest.raises(PaymentError):
            await cinetpay_adapter.send_payment(sample_transaction)


def test_format_transaction(cinetpay_adapter, sample_transaction):
    """Test transaction formatting"""
    formatted = cinetpay_adapter.format_transaction(sample_transaction)

    assert formatted["amount"] == 1000
    assert formatted["currency"] == "XOF"
    assert formatted["customer_phone"] == "221771234567"
    assert formatted["channels"] == "MOBILE_MONEY"


def test_validate_credentials(cinetpay_adapter):
    """Test credentials validation"""

    assert cinetpay_adapter._validate_credentials() is True

    # Test with missing credentials
    invalid_config = cinetpay_adapter.config.copy()
    invalid_config["extra"] = {}
    adapter = CinetpayAdapter(invalid_config)
    assert adapter._validate_credentials() is False


def test_get_normalize_status(cinetpay_adapter):
    """Test status normalization"""

    assert (
        cinetpay_adapter.get_normalize_status("SUCCESS") == TransactionStatus.SUCCESSFUL
    )
    assert cinetpay_adapter.get_normalize_status("PENDING") == TransactionStatus.PENDING
    assert (
        cinetpay_adapter.get_normalize_status("PAYMENT_FAILED")
        == TransactionStatus.FAILED
    )
    assert cinetpay_adapter.get_normalize_status("UNKNOWN") == TransactionStatus.UNKNOWN


@pytest.mark.asyncio
async def test_check_status_success(cinetpay_adapter):
    """Test successful status check"""

    mock_response = {
        "code": "200",
        "message": "SUCCESS",
        "data": {"amount": 1000, "currency": "XOF"},
    }

    with patch.object(
        cinetpay_adapter.client, "get", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value.data = mock_response

        response = await cinetpay_adapter.check_status("test123")
        assert response.status == TransactionStatus.SUCCESSFUL
        assert response.amount == 1000


@pytest.mark.asyncio
async def test_cancel_transaction_not_supported(cinetpay_adapter):
    """Test that cancel operation raises proper exception"""

    with pytest.raises(UnsupportedOperationError):
        await cinetpay_adapter.cancel_transaction("test123")


@pytest.mark.asyncio
async def test_refund_not_supported(cinetpay_adapter):
    """Test that refund operation raises proper exception"""

    with pytest.raises(UnsupportedOperationError):
        await cinetpay_adapter.refund("test123")


def test_webhook_validation(cinetpay_adapter):
    """Test webhook validation"""

    payload = {
        "cpm_site_id": "test_site_id",
        "cpm_trans_id": "test123",
        "cpm_trans_date": "20230101",
        "cpm_amount": "1000",
        "cpm_currency": "XOF",
        "signature": "test",
        "payment_method": "MOBILE_MONEY",
        "cel_phone_num": "221771234567",
    }

    # Generate valid token
    payload_str = (
        f"{payload['cpm_site_id']}{payload['cpm_trans_id']}"
        f"{payload['cpm_trans_date']}{payload['cpm_amount']}"
        f"{payload['cpm_currency']}{payload['signature']}"
        f"{payload['payment_method']}{payload['cel_phone_num']}"
    )
    valid_token = hmac.new(
        key=cinetpay_adapter.config["extra"]["secret"].encode(),
        msg=payload_str.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Test with valid token
    headers = {"x-token": valid_token}
    assert cinetpay_adapter.validate_webhook(payload, headers) is True

    # Test with invalid token
    headers = {"x-token": "invalid_token"}
    assert cinetpay_adapter.validate_webhook(payload, headers) is False


def test_parse_webhook(cinetpay_adapter):
    """Test webhook parsing"""

    payload = {
        "cpm_site_id": "test_site_id",
        "cpm_trans_id": "test123",
        "cpm_trans_date": "20230101",
        "cpm_amount": "1000",
        "cpm_currency": "XOF",
        "cpm_page_action": "PAYMENT_SUCCESS",
        "signature": "test",
        "payment_method": "MOBILE_MONEY",
        "cel_phone_num": "221771234567",
    }

    # Generate valid token
    payload_str = (
        f"{payload['cpm_site_id']}{payload['cpm_trans_id']}"
        f"{payload['cpm_trans_date']}{payload['cpm_amount']}"
        f"{payload['cpm_currency']}{payload['signature']}"
        f"{payload['payment_method']}{payload['cel_phone_num']}"
    )
    valid_token = hmac.new(
        key=cinetpay_adapter.config["extra"]["secret"].encode(),
        msg=payload_str.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    headers = {"x-token": valid_token}
    event = cinetpay_adapter.parse_webhook(payload, headers)

    assert event.transaction_id == "test123"
    assert event.amount == "1000"
    assert event.provider == "cinetpay"


def test_validate_transaction(cinetpay_adapter, sample_transaction):
    """Test transaction validation"""

    assert cinetpay_adapter.validate_transaction(sample_transaction) is True

    # Test with invalid amount
    invalid_transaction = sample_transaction.copy()
    invalid_transaction.amount = 50  # Below minimum for XOF
    with pytest.raises(ValueError):
        cinetpay_adapter.validate_transaction(invalid_transaction)

    # Test with invalid currency
    invalid_transaction = sample_transaction.copy()
    invalid_transaction.currency = "EUR"  # Not supported
    with pytest.raises(ValueError):
        cinetpay_adapter.validate_transaction(invalid_transaction)


def test_get_headers(cinetpay_adapter):
    """Test headers generation"""
    headers = cinetpay_adapter.get_headers()
    assert headers["Content-Type"] == "application/json"
