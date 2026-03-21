"""Tests de integración para A+ Content API (sandbox SP-API).

A+ Content API no tiene test cases en el sandbox (x-amzn-api-sandbox).
Requiere marca registrada (Brand Registry).
"""

import pytest

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestAplusContentSandbox:

    def test_search_content_documents(self, client):
        """search_content_documents — puede devolver lista vacía o error si no hay marca."""
        try:
            result = client.search_content_documents()
            assert isinstance(result, list)
        except RuntimeError:
            pytest.skip("Sandbox no soporta A+ Content (requiere Brand Registry)")
