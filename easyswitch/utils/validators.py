"""
EasySwitch - Fonctions de validation
"""
import hashlib
import hmac
import re
from typing import Any, Dict, Optional, Union

from easyswitch.exceptions import ValidationError


def validate_phone_number(phone_number: str, country_code: Optional[str] = None) -> str:
    """
    Validate and format a phone number.

    Args:
        phone_number: the phone number to validate
        country_code: Country code (ISO 3166-1 alpha-2)

    Returns:
        str: A validated and formatted phone number

    Raises:
        ValidationError: if the phone number is invalid
    """
    # Remove all non-digit characters
    cleaned = re.sub(r"\D", "", phone_number)

    # Check the min len  (at least 8 digits without country code)
    # and max len (at most 15 digits)
    if len(cleaned) < 8:
        raise ValidationError(
            message="The phone number must contain at least 8 digits.",
            field="phone_number",
        )

    # Gérer les préfixes selon le pays
    if country_code:
        country_code = country_code.upper()
        prefixes = {
            "CI": "225",  # Côte d'Ivoire
            "SN": "221",  # Sénégal
            "BJ": "229",  # Bénin
            "TG": "228",  # Togo
            "BF": "226",  # Burkina Faso
            "ML": "223",  # Mali
            "NE": "227",  # Niger
            "GH": "233",  # Ghana
            "NG": "234",  # Nigeria
        }

        # Ajouter le préfixe du pays si nécessaire
        if country_code in prefixes:
            prefix = prefixes[country_code]
            if not cleaned.startswith(prefix):
                # Si le numéro commence par un 0, le remplacer par le préfixe
                if cleaned.startswith("0"):
                    cleaned = prefix + cleaned[1:]
                else:
                    cleaned = prefix + cleaned

    return cleaned


def validate_amount(amount: Union[float, int, str], min_value: float = 0.01) -> float:
    """
    Valide un montant.

    Args:
        amount: Montant à valider
        min_value: Valeur minimale autorisée

    Returns:
        float: Montant validé

    Raises:
        ValidationError: Si le montant est invalide
    """
    try:
        amount_float = float(amount)
    except (ValueError, TypeError):
        raise ValidationError(message="Le montant doit être un nombre", field="amount")

    if amount_float < min_value:
        raise ValidationError(
            message=f"Le montant doit être supérieur ou égal à {min_value}",
            field="amount",
        )

    return amount_float


def validate_currency(
    currency: str, supported_currencies: Optional[list] = None
) -> str:
    """
    Valide un code de devise.

    Args:
        currency: Code de devise à valider
        supported_currencies: Liste de devises prises en charge

    Returns:
        str: Code de devise validé

    Raises:
        ValidationError: Si la devise est invalide
    """
    currency_upper = currency.upper()

    # Liste par défaut des devises prises en charge si aucune n'est fournie
    if supported_currencies is None:
        supported_currencies = ["XOF", "XAF", "NGN", "GHS", "EUR", "USD"]

    if currency_upper not in supported_currencies:
        raise ValidationError(
            message=f"Devise non prise en charge: {currency}. Devises valides: {', '.join(supported_currencies)}",
            field="currency",
        )

    return currency_upper


def validate_reference(reference: str, max_length: int = 50) -> str:
    """
    Valide une référence de transaction.

    Args:
        reference: Référence à valider
        max_length: Longueur maximale autorisée

    Returns:
        str: Référence validée

    Raises:
        ValidationError: Si la référence est invalide
    """
    if not reference or not isinstance(reference, str):
        raise ValidationError(
            message="La référence ne peut pas être vide", field="reference"
        )

    # Supprimer les espaces en début et fin
    reference = reference.strip()

    if len(reference) > max_length:
        raise ValidationError(
            message=f"La référence est trop longue (maximum {max_length} caractères)",
            field="reference",
        )

    # Vérifier que la référence ne contient que des caractères autorisés
    if not re.match(r"^[a-zA-Z0-9_\-\.]+$", reference):
        raise ValidationError(
            message="La référence ne doit contenir que des lettres, chiffres, tirets, points et underscores",
            field="reference",
        )

    return reference


def validate_webhook_signature(
    payload: Union[str, bytes, Dict[str, Any]],
    signature: str,
    secret: str,
    algorithm: str = "sha256",
) -> bool:
    """
    Valide la signature d'un webhook.

    Args:
        payload: Charge utile du webhook
        signature: Signature à valider
        secret: Clé secrète pour la vérification
        algorithm: Algorithme de hachage à utiliser

    Returns:
        bool: True si la signature est valide, False sinon
    """
    if isinstance(payload, dict):
        payload = bytes(repr(payload).encode("utf-8"))
    elif isinstance(payload, str):
        payload = bytes(payload.encode("utf-8"))

    # Calculer le HMAC
    if algorithm.lower() == "sha256":
        computed_signature = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
    elif algorithm.lower() == "sha512":
        computed_signature = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha512
        ).hexdigest()
    else:
        raise ValueError(f"Algorithme non pris en charge: {algorithm}")

    # Comparer les signatures
    return hmac.compare_digest(computed_signature, signature.lower())


def validate_email(email: str) -> str:
    """
    Valide une adresse e-mail.

    Args:
        email: Adresse e-mail à valider

    Returns:
        str: Adresse e-mail validée

    Raises:
        ValidationError: Si l'adresse e-mail est invalide
    """
    # Regex simple pour la validation d'e-mail
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError(message="Adresse e-mail invalide", field="email")

    return email.lower()
