"""Configuración: carga .env y valida credenciales SP-API."""

import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

MARKETPLACE_ID_ES = "A1RKKUPIHCS9HS"

MARKETPLACE_IDS = {
    "ES": "A1RKKUPIHCS9HS",
    "US": "ATVPDKIKX0DER",
    "DE": "A1PA6795UKMFR9",
    "FR": "A13V1IB3VIYZZH",
    "IT": "APJ6JRA9NG5V4",
    "GB": "A1F83G8C2ARO7P",
}

MARKETPLACE_CURRENCIES = {
    "ES": "EUR",
    "US": "USD",
    "DE": "EUR",
    "FR": "EUR",
    "IT": "EUR",
    "GB": "GBP",
}


MARKETPLACE_LANGUAGES = {
    "ES": "es_ES",
    "US": "en_US",
    "DE": "de_DE",
    "FR": "fr_FR",
    "IT": "it_IT",
    "GB": "en_GB",
}


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
            capture_output=True, text=True, timeout=5,
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
    source = "dotenv"
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
        raise EnvironmentError(
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
