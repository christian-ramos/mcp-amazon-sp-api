"""Tests unitarios para ListingsRestrictionsClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from .conftest import make_response, make_api_error


class TestGetListingsRestrictions:
    @patch.object(AmazonClient, "_restrictions_api")
    def test_returns_restrictions(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_restrictions.return_value = make_response({
            "restrictions": [
                {"marketplaceId": "A1RKKUPIHCS9HS", "conditionType": "used_acceptable",
                 "reasons": [{"message": "Cannot list in this condition"}]},
            ],
        })
        result = client.get_listings_restrictions("B001")
        assert len(result) == 1
        assert result[0]["conditionType"] == "used_acceptable"

    @patch.object(AmazonClient, "_restrictions_api")
    def test_no_restrictions(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_restrictions.return_value = make_response({"restrictions": []})
        result = client.get_listings_restrictions("B001")
        assert result == []

    @patch.object(AmazonClient, "_restrictions_api")
    def test_passes_condition_type(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_restrictions.return_value = make_response({"restrictions": []})
        client.get_listings_restrictions("B001", condition_type="new_new")
        kwargs = mock_api.get_listings_restrictions.call_args[1]
        assert kwargs["conditionType"] == "new_new"

    @patch.object(AmazonClient, "_restrictions_api")
    def test_no_condition_type_omitted(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_restrictions.return_value = make_response({"restrictions": []})
        client.get_listings_restrictions("B001")
        kwargs = mock_api.get_listings_restrictions.call_args[1]
        assert "conditionType" not in kwargs

    @patch.object(AmazonClient, "_restrictions_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_restrictions.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_listings_restrictions("BAD_ASIN")


class TestCheckExpansionEligibility:
    @patch.object(AmazonClient, "_restrictions_api")
    def test_checks_multiple_marketplaces(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_restrictions.side_effect = [
            make_response({"restrictions": []}),
            make_response({"restrictions": [{"conditionType": "new_new", "reasons": [{"message": "Restricted"}]}]}),
        ]
        result = client.check_expansion_eligibility("B001", ["DE", "FR"])
        assert len(result) == 2
        assert result[0]["restricted"] is False
        assert result[1]["restricted"] is True

    @patch.object(AmazonClient, "_restrictions_api")
    def test_handles_api_error_gracefully(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_listings_restrictions.side_effect = make_api_error(500)
        result = client.check_expansion_eligibility("B001", ["DE"])
        assert "error" in result[0]

    def test_unsupported_marketplace(self, client):
        result = client.check_expansion_eligibility("B001", ["XX"])
        assert "error" in result[0]
        assert "no soportado" in result[0]["error"]
