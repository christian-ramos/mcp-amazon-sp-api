"""Fixtures y helpers compartidos para tests de clientes SP-API."""

from types import SimpleNamespace

import pytest
from sp_api.base import SellingApiException

from mcp_amazon_sp_api.config import SpApiConfig
from mcp_amazon_sp_api.sp_client import AmazonClient


FAKE_CONFIG = SpApiConfig(
    refresh_token="Atzr|fake_token",
    lwa_app_id="amzn1.application-oa2-client.fake",
    lwa_client_secret="fake_secret",
    seller_id="A1SELLER",
)


def make_response(payload: dict) -> SimpleNamespace:
    """Simula la respuesta de python-amazon-sp-api."""
    return SimpleNamespace(payload=payload)


def make_throttle_error() -> SellingApiException:
    err = SellingApiException([{"message": "Rate exceeded"}], headers={})
    err.code = 429
    return err


def make_api_error(code: int = 403) -> SellingApiException:
    err = SellingApiException([{"message": "Error"}], headers={})
    err.code = code
    return err


@pytest.fixture
def client():
    return AmazonClient(FAKE_CONFIG)
