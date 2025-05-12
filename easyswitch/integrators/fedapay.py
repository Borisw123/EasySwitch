"""
EasySwitch - Fedapay Integrator
"""
import hashlib
import hmac
import json
from typing import Any, ClassVar, Dict, List, Optional

from easyswitch.adapters.base import AdaptersRegistry, BaseAdapter
from easyswitch.exceptions import (
    AuthenticationError,
    PaymentError,
    UnsupportedOperationError,
)
from easyswitch.types import (
    Currency,
    CustomerInfo,
    PaymentResponse,
    Provider,
    TransactionDetail,
    TransactionStatus,
    TransactionStatusResponse,
    TransactionType,
    WebhookEvent,
)
from easyswitch.utils import parse_phone


####
##      FEDAPAY INTEGRATOR
#####
@AdaptersRegistry.register()
class FedapayAdapter(BaseAdapter):
    """FedaPay Integrator for EasySwitch SDK."""

    SANDBOX_URL: str = "https://sandbox-api.fedapay.com"

    PRODUCTION_URL: str = "https://api-checkout.cinetpay.com"

    ENDPOINTS: Dict[str, str] = {
        "payment": "/v1/transactions",
        "payment_status": "/v1/payment/check",
    }

    SUPPORTED_CURRENCIES: ClassVar[List[Currency]] = [
        Currency.XOF,
        Currency.GNF,
        Currency.USD,
        Currency.EUR,
    ]

    MIN_AMOUNT: ClassVar[Dict[Currency, float]] = {
        Currency.XOF: 100.0,
        Currency.GNF: 1000.0,
        Currency.USD: 1.0,
        Currency.EUR: 1.0,
    }

    MAX_AMOUNT: ClassVar[Dict[Currency, float]] = {  # Currently unknown
        Currency.XOF: 1000000.0,
        Currency.GNF: 1000000.0,
        Currency.EUR: 10000.0,
        Currency.USD: 10000.0,
    }

    def _validate_credentials(self) -> bool:
        """Validate the credentials for FedaPay."""

        return all(
            [
                self.config.api_key,
                self.config.extra,  # Extra configs must be set
                self.config.extra.get("public_key"),  # FedaPay uses Public key
                self.config.extra.get("secret_key"),  # and secret key (token)
                self.config.extra.get("account_id"),  # For those requests
            ]
        )

    def get_credentials(self):
        """Get the credentials for FedaPay."""
        # NOTE that credentials are checked in the constructor

        return {
            "api_key": self.config.api_key,
            "public_key": self.config.extra.get("public_key", ""),
            "secret_key": self.config.extra.get("secret_key", ""),
        }

    def get_headers(self, authorization=False):
        """Get the headers for CinetPay."""

        headers = {"Content-Type": "application/json"}
        # Add Authorizations if needed
        if authorization:
            headers["Authorization"] = f'Bearer {self.config.extra.get("public_key")}'

        return headers

    def format_transaction(self, transaction: TransactionDetail) -> Dict[str, Any]:
        """Format the transaction data into a standardized format."""

        # Check if the transaction is valid
        self.validate_transaction(transaction)  # Will raise ValidationError if needed.

        return {
            "amount": int(transaction.amount),
            "currency": {"iso": transaction.currency},
            "description": transaction.reason,
            "callback_url": transaction.callback_url or self.config.callback_url,
            "metadata": transaction.metadata,
            "customer": {
                "id": transaction.customer.id,
                "email": transaction.customer.email,
                "firstname": transaction.customer.first_name,
                "lastname": transaction.customer.last_name,
                "phone_number": {
                    "number": parse_phone(
                        transaction.customer.phone_number, raise_exception=True
                    ).get(
                        "national_number"
                    ),  # Will return the phone number without country code
                },
                "fees": 0,  # Transaction fees
            },
        }
