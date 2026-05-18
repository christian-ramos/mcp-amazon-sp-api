"""Integración: Listings Items API (2021-08-01) y Product Type Definitions API.
Sandbox test cases (listingsItems_2021-08-01.json):
  get_listings_item: cualquier seller/sku → 200; sku="BadSKU" → 400
  patch_listings_item: cualquier seller/sku → ACCEPTED; sku="BadSKU" → 400
  search_listings_items: identifiers=["GM-ZDPI-9B4E","HW-ZDPI-9B4E","TC-ZDPI-9B4E"],
                         identifiersType="SKU", pageSize=1

Sandbox test cases (definitionsProductTypes_2020-09-01.json):
  search: {} → LUGGAGE; keywords=["Invalid Request"] → 400
  get: cualquier productType → definición; productType="INVALID" → 400
"""

import pytest

from tests.conftest import skip_without_credentials

pytestmark = [pytest.mark.integration, skip_without_credentials]


class TestGetListingItemSandbox:
    def test_returns_listing_data(self, listings_client):
        listing = listings_client.get_listing_item("TEST_CASE_200")
        assert "summaries" in listing
        assert "offers" in listing
        assert "issues" in listing

    def test_listing_has_sku(self, listings_client):
        assert listings_client.get_listing_item("TEST_CASE_200")["sku"] == "GM-ZDPI-9B4E"

    def test_listing_has_summary_fields(self, listings_client):
        summary = listings_client.get_listing_item("TEST_CASE_200")["summaries"][0]
        for field in ("asin", "productType", "status", "itemName"):
            assert field in summary

    def test_listing_has_offers(self, listings_client):
        offers = listings_client.get_listing_item("TEST_CASE_200")["offers"]
        assert len(offers) > 0
        assert "price" in offers[0]

    def test_listing_has_issues(self, listings_client):
        issues = listings_client.get_listing_item("TEST_CASE_200")["issues"]
        assert len(issues) > 0
        for field in ("code", "severity", "message"):
            assert field in issues[0]

    def test_bad_sku_raises_error(self, listings_client):
        with pytest.raises(RuntimeError, match="Error SP-API"):
            listings_client.get_listing_item("BadSKU")


class TestPatchListingItemSandbox:
    def test_patch_returns_accepted(self, listings_client):
        patches = [{"op": "replace", "path": "/attributes/item_name", "value": [{"value": "Test Title", "language_tag": "en_US", "marketplace_id": "ATVPDKIKX0DER"}]}]
        result = listings_client.patch_listing_item("TEST_CASE_200", "LUGGAGE", patches)
        assert result["status"] == "ACCEPTED"
        assert "submissionId" in result

    def test_patch_returns_empty_issues(self, listings_client):
        patches = [{"op": "replace", "path": "/attributes/product_description", "value": [{"value": "Test desc", "language_tag": "en_US", "marketplace_id": "ATVPDKIKX0DER"}]}]
        assert listings_client.patch_listing_item("TEST_CASE_200", "LUGGAGE", patches)["issues"] == []

    def test_bad_sku_raises_error(self, listings_client):
        with pytest.raises(RuntimeError, match="Error SP-API"):
            listings_client.patch_listing_item("BadSKU", "LUGGAGE", [])


class TestSearchListingsItemsSandbox:
    """La librería envía identifiers como list en vez de comma-separated,
    rompiendo el sandbox match. Usamos _request directo. En producción funciona."""

    def _search(self, listings_client):
        api = listings_client._listings_api()
        return api._request(
            "/listings/2021-08-01/items/TEST_CASE_200",
            params={"method": "GET", "identifiersType": "SKU", "identifiers": "GM-ZDPI-9B4E,HW-ZDPI-9B4E,TC-ZDPI-9B4E", "marketplaceIds": "ATVPDKIKX0DER", "includedData": "summaries,offers,fulfillmentAvailability,issues", "pageSize": 1},
            add_marketplace=False,
        )

    def test_search_returns_items(self, listings_client):
        items = self._search(listings_client).payload.get("items", [])
        assert len(items) > 0

    def test_search_result_has_summary(self, listings_client):
        item = self._search(listings_client).payload["items"][0]
        assert "sku" in item
        assert "asin" in item["summaries"][0]


class TestProductTypeDefinitionsSandbox:
    def test_search_returns_product_types(self, listings_client):
        types = listings_client.search_product_types(keywords="LUGGAGE")
        assert types[0]["name"] == "LUGGAGE"

    def test_get_definition_returns_schema(self, listings_client):
        defn = listings_client.get_product_type_definition("LUGGAGE")
        assert "schema" in defn or "productType" in defn

    def test_invalid_product_type_raises_error(self, listings_client):
        with pytest.raises(RuntimeError, match="Error SP-API"):
            listings_client.get_product_type_definition("INVALID")
