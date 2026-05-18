"""Fixtures compartidos entre tests unitarios e integración."""

from pathlib import Path
from unittest.mock import patch

import pytest
from dotenv import dotenv_values, load_dotenv

# Cargar .env.test ANTES de importar sp_api para que AWS_ENV=SANDBOX
# se aplique cuando sp_api.base.marketplaces evalúe los endpoints.
ENV_TEST_PATH = Path(__file__).resolve().parent.parent / ".env.test"
load_dotenv(ENV_TEST_PATH, override=True)

# SEGURIDAD: bloquear acceso al Keychain en TODOS los tests.
# Evita que cualquier test pueda leer credenciales reales por accidente.
_keychain_block = patch("mcp_amazon_sp_api.config._read_keychain", return_value=None)
_keychain_block.start()

from mcp_amazon_sp_api.config import SpApiConfig  # noqa: E402  (must follow Keychain patch)

FAKE_CONFIG = SpApiConfig(
    refresh_token="Atzr|fake_token",
    lwa_app_id="amzn1.application-oa2-client.fake",
    lwa_client_secret="fake_secret",
)


@pytest.fixture
def fake_config():
    return FAKE_CONFIG


@pytest.fixture
def env_credentials(monkeypatch):
    """Inyecta credenciales fake en variables de entorno."""
    monkeypatch.setenv("SP_API_REFRESH_TOKEN", "Atzr|fake_token")
    monkeypatch.setenv("LWA_APP_ID", "amzn1.application-oa2-client.fake")
    monkeypatch.setenv("LWA_CLIENT_SECRET", "fake_secret")
    monkeypatch.delenv("SP_API_MARKETPLACE", raising=False)


def has_real_credentials() -> bool:
    """Comprueba si hay credenciales reales en .env.test (sin placeholders)."""
    if not ENV_TEST_PATH.exists():
        return False
    values = dotenv_values(ENV_TEST_PATH)
    required = ("SP_API_REFRESH_TOKEN", "LWA_APP_ID", "LWA_CLIENT_SECRET")
    return all(
        values.get(k) and not values[k].endswith("...")
        for k in required
    )


skip_without_credentials = pytest.mark.skipif(
    not has_real_credentials(),
    reason="Requiere credenciales reales en .env.test (SP_API_REFRESH_TOKEN, LWA_APP_ID, LWA_CLIENT_SECRET)",
)
