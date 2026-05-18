"""Configuración: carga .env y valida credenciales SP-API."""

import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sp_api.base import Marketplaces

logger = logging.getLogger(__name__)

MARKETPLACE_ID_ES = "A1RKKUPIHCS9HS"

MARKETPLACES = {
    "ES": {
        "id": "A1RKKUPIHCS9HS",
        "currency": "EUR",
        "lang": "es_ES",
        "marketplace": Marketplaces.ES,
    },
    "US": {
        "id": "ATVPDKIKX0DER",
        "currency": "USD",
        "lang": "en_US",
        "marketplace": Marketplaces.US,
    },
    "DE": {
        "id": "A1PA6795UKMFR9",
        "currency": "EUR",
        "lang": "de_DE",
        "marketplace": Marketplaces.DE,
    },
    "FR": {
        "id": "A13V1IB3VIYZZH",
        "currency": "EUR",
        "lang": "fr_FR",
        "marketplace": Marketplaces.FR,
    },
    "IT": {
        "id": "APJ6JRA9NG5V4",
        "currency": "EUR",
        "lang": "it_IT",
        "marketplace": Marketplaces.IT,
    },
    "GB": {
        "id": "A1F83G8C2ARO7P",
        "currency": "GBP",
        "lang": "en_GB",
        "marketplace": Marketplaces.UK,
    },
    "NL": {
        "id": "A1805IZSGTT6HS",
        "currency": "EUR",
        "lang": "nl_NL",
        "marketplace": Marketplaces.NL,
    },
    "BE": {
        "id": "AMEN7PMS3EDWL",
        "currency": "EUR",
        "lang": "fr_BE",
        "marketplace": Marketplaces.BE,
    },
    "PL": {
        "id": "A1C3SOZRARQ6R3",
        "currency": "PLN",
        "lang": "pl_PL",
        "marketplace": Marketplaces.PL,
    },
    "SE": {
        "id": "A2NODRKZP88ZB9",
        "currency": "SEK",
        "lang": "sv_SE",
        "marketplace": Marketplaces.SE,
    },
    "AE": {
        "id": "A2VIGQ35RCS4UG",
        "currency": "AED",
        "lang": "ar_AE",
        "marketplace": Marketplaces.AE,
    },
    "SA": {
        "id": "A17E79C6D8DWNP",
        "currency": "SAR",
        "lang": "ar_SA",
        "marketplace": Marketplaces.SA,
    },
    "IE": {
        "id": "A28R8IXHR4HQHZ",
        "currency": "EUR",
        "lang": "en_IE",
        "marketplace": Marketplaces.IE,
    },
}

EU_MARKETPLACE_CODES: set[str] = {"ES", "DE", "FR", "IT", "NL", "BE", "GB", "SE", "PL"}
EU_MARKETPLACES = {
    code: data for code, data in MARKETPLACES.items() if code in EU_MARKETPLACE_CODES
}

# Derived dicts for backward compatibility
MARKETPLACE_IDS = {code: data["id"] for code, data in MARKETPLACES.items()}
MARKETPLACE_CURRENCIES = {code: data["currency"] for code, data in MARKETPLACES.items()}
MARKETPLACE_LANGUAGES = {code: data["lang"] for code, data in MARKETPLACES.items()}


@dataclass(frozen=True)
class SpApiConfig:
    refresh_token: str
    lwa_app_id: str
    lwa_client_secret: str
    marketplace: str = "ES"
    seller_id: str = ""

    @property
    def marketplace_id(self) -> str:
        return MARKETPLACE_IDS.get(self.marketplace, MARKETPLACE_ID_ES)

    @property
    def currency(self) -> str:
        return MARKETPLACE_CURRENCIES.get(self.marketplace, "EUR")

    @property
    def language_tag(self) -> str:
        return MARKETPLACE_LANGUAGES.get(self.marketplace, "es_ES")


KEYCHAIN_SERVICE = "mcp-amazon-sp-api"


def _read_keychain(account: str, service: str = KEYCHAIN_SERVICE) -> str | None:
    """Lee una credencial del Keychain de macOS. Devuelve None si no existe."""
    if sys.platform != "darwin":
        return None
    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            value = result.stdout.strip()
            logger.debug("Keychain: credencial '%s' encontrada", account)
            return value
        logger.debug("Keychain: credencial '%s' no encontrada", account)
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _resolve_credential(env_key: str) -> str | None:
    """Resuelve una credencial: 1) env var, 2) Keychain macOS."""
    value = os.getenv(env_key)
    if value:
        return value
    return _read_keychain(env_key)


def load_config(env_file: str | Path | None = ".env") -> SpApiConfig:
    """Lee credenciales: env vars → Keychain macOS → .env. Falla si faltan."""
    if env_file:
        load_dotenv(env_file)

    credentials = {}
    required = {
        "SP_API_REFRESH_TOKEN": "refresh_token",
        "LWA_APP_ID": "lwa_app_id",
        "LWA_CLIENT_SECRET": "lwa_client_secret",
    }

    for env_key, field_name in required.items():
        value = _resolve_credential(env_key)
        if value:
            credentials[field_name] = value
        else:
            credentials[field_name] = None

    missing = [k for k, v in required.items() if not credentials[v]]
    if missing:
        raise OSError(
            f"Faltan credenciales: {', '.join(missing)}. "
            "Configúralas en Keychain (security add-generic-password) o en .env."
        )

    return SpApiConfig(
        refresh_token=credentials["refresh_token"],
        lwa_app_id=credentials["lwa_app_id"],
        lwa_client_secret=credentials["lwa_client_secret"],
        marketplace=os.getenv("SP_API_MARKETPLACE", "ES"),
        seller_id=os.getenv("SP_API_SELLER_ID", ""),
    )
