"""Fixtures para tests de integración (sandbox SP-API)."""

import os

import pytest

from mcp_amazon_sp_api.config import load_config
from mcp_amazon_sp_api.sp_client import AmazonClient
from tests.conftest import ENV_TEST_PATH


@pytest.fixture(scope="module")
def client():
    return AmazonClient(load_config(env_file=ENV_TEST_PATH))


@pytest.fixture(scope="module")
def listings_client():
    """Cliente con seller_id para Listings."""
    os.environ["SP_API_SELLER_ID"] = "TEST_CASE_200"
    return AmazonClient(load_config(env_file=ENV_TEST_PATH))
