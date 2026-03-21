"""Tests unitarios para config.py."""

import pytest

from mcp_amazon_sp_api.config import MARKETPLACE_ID_ES, SpApiConfig, load_config


class TestSpApiConfig:
    def test_creates_with_defaults(self):
        config = SpApiConfig(refresh_token="tok", lwa_app_id="app", lwa_client_secret="sec")
        assert config.marketplace == "ES"

    def test_creates_with_custom_marketplace(self):
        config = SpApiConfig(refresh_token="tok", lwa_app_id="app", lwa_client_secret="sec", marketplace="DE")
        assert config.marketplace == "DE"

    def test_is_frozen(self):
        config = SpApiConfig(refresh_token="tok", lwa_app_id="app", lwa_client_secret="sec")
        with pytest.raises(AttributeError):
            config.refresh_token = "other"


class TestLoadConfig:
    def test_loads_from_env(self, env_credentials):
        config = load_config(env_file=None)
        assert config.refresh_token == "Atzr|fake_token"
        assert config.lwa_app_id == "amzn1.application-oa2-client.fake"
        assert config.lwa_client_secret == "fake_secret"
        assert config.marketplace == "ES"

    def test_fails_when_all_missing(self, monkeypatch):
        monkeypatch.delenv("SP_API_REFRESH_TOKEN", raising=False)
        monkeypatch.delenv("LWA_APP_ID", raising=False)
        monkeypatch.delenv("LWA_CLIENT_SECRET", raising=False)
        with pytest.raises(EnvironmentError, match="Faltan variables de entorno"):
            load_config(env_file=None)

    def test_fails_when_one_missing(self, monkeypatch):
        monkeypatch.setenv("SP_API_REFRESH_TOKEN", "tok")
        monkeypatch.setenv("LWA_APP_ID", "app")
        monkeypatch.delenv("LWA_CLIENT_SECRET", raising=False)
        with pytest.raises(EnvironmentError, match="LWA_CLIENT_SECRET"):
            load_config(env_file=None)

    def test_error_message_mentions_env_example(self, monkeypatch):
        monkeypatch.delenv("SP_API_REFRESH_TOKEN", raising=False)
        monkeypatch.delenv("LWA_APP_ID", raising=False)
        monkeypatch.delenv("LWA_CLIENT_SECRET", raising=False)
        with pytest.raises(EnvironmentError, match=r"\.env\.example"):
            load_config(env_file=None)


class TestConstants:
    def test_marketplace_id_es(self):
        assert MARKETPLACE_ID_ES == "A1RKKUPIHCS9HS"
