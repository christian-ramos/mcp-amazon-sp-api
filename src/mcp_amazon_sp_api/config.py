"""Configuración: carga .env y valida credenciales SP-API."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

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


def load_config(env_file: str | Path | None = ".env") -> SpApiConfig:
    """Lee credenciales de variables de entorno. Falla con mensaje claro si faltan."""
    if env_file:
        load_dotenv(env_file)
    required = {
        "SP_API_REFRESH_TOKEN": "refresh_token",
        "LWA_APP_ID": "lwa_app_id",
        "LWA_CLIENT_SECRET": "lwa_client_secret",
    }
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise EnvironmentError(
            f"Faltan variables de entorno: {', '.join(missing)}. "
            "Copia .env.example a .env y rellena tus credenciales."
        )
    return SpApiConfig(
        refresh_token=os.environ["SP_API_REFRESH_TOKEN"],
        lwa_app_id=os.environ["LWA_APP_ID"],
        lwa_client_secret=os.environ["LWA_CLIENT_SECRET"],
        marketplace=os.getenv("SP_API_MARKETPLACE", "ES"),
        seller_id=os.getenv("SP_API_SELLER_ID", ""),
    )
