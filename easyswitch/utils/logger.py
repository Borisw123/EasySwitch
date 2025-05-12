"""
EasySwitch - Utilitaire de journalisation
"""
import logging
import os
import sys
from typing import Any, Dict, Optional, Union


def setup_logger(
    name: str = "easyswitch",
    level: Union[int, str] = logging.INFO,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure et retourne un logger.

    Args:
        name: Nom du logger
        level: Niveau de journalisation
        log_format: Format des messages de log
        log_file: Chemin vers le fichier de log
        console: Activer la sortie console

    Returns:
        logging.Logger: Logger configuré
    """
    logger = logging.getLogger(name)

    # Définir le niveau de journalisation
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    logger.setLevel(level)

    # Éviter les handlers en double
    if logger.handlers:
        return logger

    # Format par défaut
    if log_format is None:
        log_format = (
            "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
        )

    formatter = logging.Formatter(log_format)

    # Ajouter le handler fichier si spécifié
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Ajouter le handler console si demandé
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


def sanitize_logs(
    data: Dict[str, Any], sensitive_fields: Optional[list] = None
) -> Dict[str, Any]:
    """
    Assainit les données de log en masquant les informations sensibles.

    Args:
        data: Données à assainir
        sensitive_fields: Liste des champs sensibles à masquer

    Returns:
        Dict[str, Any]: Données assainies
    """
    if sensitive_fields is None:
        sensitive_fields = [
            "password",
            "api_key",
            "secret",
            "token",
            "private_key",
            "api_secret",
            "client_secret",
            "card_number",
            "cvv",
            "signature",
        ]

    sanitized = {}

    for key, value in data.items():
        if key.lower() in [f.lower() for f in sensitive_fields]:
            if isinstance(value, str) and value:
                visible_chars = min(4, len(value) // 4)
                sanitized[key] = value[:visible_chars] + "*" * (
                    len(value) - visible_chars
                )
            else:
                sanitized[key] = "***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_logs(value, sensitive_fields)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            sanitized[key] = [
                sanitize_logs(item, sensitive_fields)
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


class PaymentLogger:
    """
    Logger spécialisé pour les opérations de paiement.
    Enregistre les événements de paiement avec les informations appropriées.
    """

    def __init__(self, logger_name: str = "easyswitch.payment"):
        """
        Initialise le logger de paiement.

        Args:
            logger_name: Nom du logger
        """
        self.logger = logging.getLogger(logger_name)

    def payment_initiated(
        self, provider: str, amount: float, currency: str, reference: str, **kwargs
    ):
        """Enregistre l'initiation d'un paiement."""
        self.logger.info(
            f"Paiement initié | Fournisseur: {provider} | Montant: {amount} {currency} | Réf: {reference}",
            extra=sanitize_logs(kwargs),
        )

    def payment_success(
        self,
        provider: str,
        amount: float,
        currency: str,
        reference: str,
        transaction_id: str,
        **kwargs,
    ):
        """Enregistre un paiement réussi."""
        self.logger.info(
            f"Paiement réussi | Fournisseur: {provider} | ID: {transaction_id} | Montant: {amount} {currency} | Réf: {reference}",
            extra=sanitize_logs(kwargs),
        )

    def payment_failed(self, provider: str, reference: str, reason: str, **kwargs):
        """Enregistre un paiement échoué."""
        self.logger.error(
            f"Paiement échoué | Fournisseur: {provider} | Réf: {reference} | Raison: {reason}",
            extra=sanitize_logs(kwargs),
        )

    def refund_initiated(
        self,
        provider: str,
        transaction_id: str,
        amount: Optional[float] = None,
        **kwargs,
    ):
        """Enregistre l'initiation d'un remboursement."""
        amount_str = f"Montant: {amount}" if amount else "Montant total"
        self.logger.info(
            f"Remboursement initié | Fournisseur: {provider} | ID: {transaction_id} | {amount_str}",
            extra=sanitize_logs(kwargs),
        )

    def refund_success(
        self,
        provider: str,
        transaction_id: str,
        amount: Optional[float] = None,
        **kwargs,
    ):
        """Enregistre un remboursement réussi."""
        amount_str = f"Montant: {amount}" if amount else "Montant total"
        self.logger.info(
            f"Remboursement réussi | Fournisseur: {provider} | ID: {transaction_id} | {amount_str}",
            extra=sanitize_logs(kwargs),
        )

    def refund_failed(self, provider: str, transaction_id: str, reason: str, **kwargs):
        """Enregistre un remboursement échoué."""
        self.logger.error(
            f"Remboursement échoué | Fournisseur: {provider} | ID: {transaction_id} | Raison: {reason}",
            extra=sanitize_logs(kwargs),
        )

    def webhook_received(
        self,
        provider: str,
        event_type: str,
        transaction_id: Optional[str] = None,
        **kwargs,
    ):
        """Enregistre la réception d'un webhook."""
        tx_info = f"| ID: {transaction_id}" if transaction_id else ""
        self.logger.info(
            f"Webhook reçu | Fournisseur: {provider} | Événement: {event_type} {tx_info}",
            extra=sanitize_logs(kwargs),
        )

    def api_request(self, provider: str, method: str, endpoint: str, **kwargs):
        """Enregistre une requête API."""
        self.logger.debug(
            f"Requête API | Fournisseur: {provider} | {method} {endpoint}",
            extra=sanitize_logs(kwargs),
        )

    def api_response(self, provider: str, status_code: int, endpoint: str, **kwargs):
        """Enregistre une réponse API."""
        log_level = logging.DEBUG if 200 <= status_code < 300 else logging.ERROR
        self.logger.log(
            log_level,
            f"Réponse API | Fournisseur: {provider} | Status: {status_code} | Endpoint: {endpoint}",
            extra=sanitize_logs(kwargs),
        )


# Créer une instance par défaut du logger
payment_logger = PaymentLogger()

# Configuration par défaut du logger
logger = setup_logger(
    level=os.getenv("EASYSWITCH_LOG_LEVEL", "INFO"),
    log_file=os.getenv("EASYSWITCH_LOG_FILE"),
    console=os.getenv("EASYSWITCH_LOG_CONSOLE", "1") != "0",
)
