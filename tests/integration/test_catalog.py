"""Integración: CatalogItems API — sandbox sin test cases de éxito específicos."""

import pytest
from tests.conftest import skip_without_credentials

pytestmark = [pytest.mark.integration, skip_without_credentials]


class TestCatalogSandbox:
    def test_search_rejects_arbitrary_keywords(self, client):
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.search_catalog_items(keywords="water bottle")

    def test_get_catalog_item_rejects_arbitrary_asin(self, client):
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_catalog_item("B000000000")
