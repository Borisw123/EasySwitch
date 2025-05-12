import asyncio
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from easyswitch.client import EasySwitch
from easyswitch.exceptions import ConfigurationError, InvalidProviderError, PaymentError
from easyswitch.types import (
    Currency,
    CustomerInfo,
    PaymentResponse,
    Provider,
    TransactionStatus,
)


# Fixtures
@pytest.fixture
def sample_config_dict():
    return {
        "environment": "sandbox",
        "timeout": 30,
        "providers": {
            "cinetpay": {
                "api_key": "test_api_key",
                "extra": {"site_id": "test_site_id", "secret": "test_secret"},
            }
        },
        "default_provider": "cinetpay",
    }


@pytest.fixture
def sample_transaction():
    return {
        "amount": 1000,
        "phone_number": "+221771234567",
        "currency": Currency.XOF,
        "reference": "test123",
        "customer_info": CustomerInfo(
            first_name="John", last_name="Doe", phone_number="+221771234567"
        ),
    }


@pytest.fixture
def mock_cinetpay_adapter():
    with patch("easyswitch.adapters.AdaptersRegistry.get") as mock:
        adapter = MagicMock()
        adapter.return_value.send_payment = AsyncMock(
            return_value=PaymentResponse(
                success=True, transaction_id="test123", status=TransactionStatus.PENDING
            )
        )
        adapter.return_value.check_status = AsyncMock(
            return_value=TransactionStatus.PENDING
        )
        mock.return_value = adapter
        yield


# Tests d'initialisation
def test_client_from_dict(sample_config_dict):
    """Test initialization from dictionary"""
    client = EasySwitch.from_dict(sample_config_dict)
    assert client.config.environment == "sandbox"
    assert "cinetpay" in client.config.providers


def test_client_from_json(tmp_path, sample_config_dict):
    """Test initialization from JSON file"""
    json_file = tmp_path / "config.json"
    json_file.write_text(json.dumps(sample_config_dict))

    client = EasySwitch.from_json(json_file)
    assert client.config.default_provider == "cinetpay"


def test_client_from_yaml(tmp_path, sample_config_dict):
    """Test initialization from YAML file"""
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text(yaml.dump(sample_config_dict))

    client = EasySwitch.from_yaml(yaml_file)
    assert client.config.timeout == 30


def test_client_from_env(tmp_path, sample_config_dict):
    """Test initialization from environment variables"""
    env_file = tmp_path / ".env"
    env_content = "\n".join(
        [
            "EASYSWITCH_ENVIRONMENT=sandbox",
            "EASYSWITCH_ENABLED_PROVIDERS=cinetpay",
            "EASYSWITCH_CINETPAY_API_KEY=test_api_key",
            "EASYSWITCH_CINETPAY_SITE_ID=test_site_id",
        ]
    )
    env_file.write_text(env_content)

    client = EasySwitch.from_env(env_file)
    assert "cinetpay" in client.config.providers


def test_client_from_multi_sources(tmp_path, sample_config_dict):
    """Test initialization from multiple sources"""
    json_file = tmp_path / "base_config.json"
    json_file.write_text(json.dumps({"timeout": 30}))

    env_file = tmp_path / ".env"
    env_file.write_text("EASYSWITCH_ENVIRONMENT=production")

    client = EasySwitch.from_multi_sources(json_file=json_file, env_file=env_file)
    assert client.config.timeout == 30
    assert client.config.environment == "production"


# Tests de fonctionnalités
@pytest.mark.asyncio
async def test_send_payment(
    sample_config_dict, sample_transaction, mock_cinetpay_adapter
):
    """Test payment sending"""
    client = EasySwitch.from_dict(sample_config_dict)
    response = await client.send_payment(
        provider=Provider.CINETPAY, **sample_transaction
    )

    assert response.status == TransactionStatus.PENDING
    assert response.transaction_id == "test123"


@pytest.mark.asyncio
async def test_send_payment_default_provider(
    sample_config_dict, sample_transaction, mock_cinetpay_adapter
):
    """Test payment with default provider"""
    client = EasySwitch.from_dict(sample_config_dict)
    response = await client.send_payment(
        amount=sample_transaction["amount"],
        phone_number=sample_transaction["phone_number"],
        currency=sample_transaction["currency"],
        reference=sample_transaction["reference"],
    )

    assert response.success is True


@pytest.mark.asyncio
async def test_check_status(sample_config_dict, mock_cinetpay_adapter):
    """Test transaction status check"""
    client = EasySwitch.from_dict(sample_config_dict)
    status = await client.check_status(
        provider=Provider.CINETPAY, transaction_id="test123"
    )

    assert status == TransactionStatus.PENDING


@pytest.mark.asyncio
async def test_invalid_provider(sample_config_dict):
    """Test with invalid provider"""
    client = EasySwitch.from_dict(sample_config_dict)

    with pytest.raises(InvalidProviderError):
        await client.send_payment(
            provider="invalid_provider",
            amount=1000,
            phone_number="+221771234567",
            currency=Currency.XOF,
            reference="test123",
        )


def test_missing_provider_config():
    """Test with missing provider configuration"""
    with pytest.raises(ConfigurationError):
        EasySwitch.from_dict(
            {"environment": "sandbox", "providers": {}}  # No providers configured
        )


@pytest.mark.asyncio
async def test_payment_error(
    sample_config_dict, sample_transaction, mock_cinetpay_adapter
):
    """Test payment error handling"""
    client = EasySwitch.from_dict(sample_config_dict)

    # Configure mock to raise error
    client._integrators["cinetpay"].send_payment = AsyncMock(
        side_effect=PaymentError("API error")
    )

    with pytest.raises(PaymentError):
        await client.send_payment(provider=Provider.CINETPAY, **sample_transaction)


# Tests de validation
def test_validate_providers(sample_config_dict):
    """Test provider validation"""
    client = EasySwitch.from_dict(sample_config_dict)
    assert "cinetpay" in client._integrators


def test_missing_default_provider():
    """Test when default provider is missing"""
    config = {"environment": "sandbox", "providers": {"cinetpay": {"api_key": "test"}}}
    client = EasySwitch.from_dict(config)
    assert client.config.default_provider == "cinetpay"  # Should be auto-set


# Tests d'intégration (avec des mocks)
@pytest.mark.asyncio
async def test_full_payment_flow(
    sample_config_dict, sample_transaction, mock_cinetpay_adapter
):
    """Test complete payment flow"""
    client = EasySwitch.from_dict(sample_config_dict)

    # Send payment
    payment_response = await client.send_payment(
        provider=Provider.CINETPAY, **sample_transaction
    )

    # Check status
    status = await client.check_status(
        provider=Provider.CINETPAY, transaction_id=payment_response.transaction_id
    )

    assert payment_response.success is True
    assert status == TransactionStatus.PENDING


@pytest.mark.asyncio
async def test_payment_performance(sample_config_dict, sample_transaction):
    """Test payment response time"""
    client = EasySwitch.from_dict(sample_config_dict)

    start_time = datetime.now()
    await client.send_payment(**sample_transaction)
    elapsed = (datetime.now() - start_time).total_seconds()

    assert elapsed < 2.0  # Should respond in under 2 seconds


@pytest.mark.asyncio
async def test_concurrent_payments(sample_config_dict, sample_transaction):
    """Test handling of concurrent requests"""
    client = EasySwitch.from_dict(sample_config_dict)

    tasks = [client.send_payment(**sample_transaction) for _ in range(5)]

    responses = await asyncio.gather(*tasks)
    assert len(responses) == 5
    assert all(r.success for r in responses)
