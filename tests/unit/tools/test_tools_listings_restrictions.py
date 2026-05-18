"""Tests de tools MCP: Listings Restrictions."""

from mcp_amazon_sp_api.tools.listings_restrictions import (
    check_expansion_eligibility,
    check_listing_restrictions,
)

from .conftest import parse


class TestCheckListingRestrictions:
    def test_no_restrictions(self, mock_client):
        mock_client.get_listings_restrictions.return_value = []
        result = parse(check_listing_restrictions(asin="B001"))
        assert result["restricted"] is False
        assert result["restrictions"] == []

    def test_with_restrictions(self, mock_client):
        mock_client.get_listings_restrictions.return_value = [
            {"conditionType": "used_acceptable", "reasons": [{"message": "Not allowed"}]},
        ]
        result = parse(check_listing_restrictions(asin="B001"))
        assert result["restricted"] is True

    def test_passes_condition(self, mock_client):
        mock_client.get_listings_restrictions.return_value = []
        parse(check_listing_restrictions(asin="B001", condition="new_new"))
        mock_client.get_listings_restrictions.assert_called_once_with("B001", condition_type="new_new")

    def test_empty_condition_passes_none(self, mock_client):
        mock_client.get_listings_restrictions.return_value = []
        parse(check_listing_restrictions(asin="B001", condition=""))
        mock_client.get_listings_restrictions.assert_called_once_with("B001", condition_type=None)

    def test_error_handling(self, mock_client):
        mock_client.get_listings_restrictions.side_effect = RuntimeError("Fail")
        assert "error" in parse(check_listing_restrictions(asin="B001"))


class TestCheckExpansionEligibility:
    def test_returns_eligible_and_restricted(self, mock_client):
        mock_client.check_expansion_eligibility.return_value = [
            {"marketplace": "DE", "restricted": False, "restrictions": []},
            {"marketplace": "FR", "restricted": True, "restrictions": [{"conditionType": "new_new"}]},
            {"marketplace": "IT", "restricted": False, "restrictions": []},
        ]
        result = parse(check_expansion_eligibility(asin="B001", marketplaces="DE,FR,IT"))
        assert result["eligible"] == ["DE", "IT"]
        assert result["restricted"] == ["FR"]

    def test_error_handling(self, mock_client):
        mock_client.check_expansion_eligibility.side_effect = RuntimeError("Fail")
        assert "error" in parse(check_expansion_eligibility(asin="B001", marketplaces="DE"))
