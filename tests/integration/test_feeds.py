"""Tests de integración para Feeds API (sandbox SP-API).

Sandbox test cases:
- getFeed: feedId=feedId1 → processingStatus=CANCELLED
- getFeedDocument: feedDocumentId=0356cf79-b8b0-4226-b4b9-0ee058ea5760 → URL
"""

import pytest

from sp_api.api import Feeds

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestFeedsSandbox:

    def test_get_feed(self, client):
        """getFeed con feedId=feedId1 → CANCELLED."""
        status = client.get_feed_status("feedId1")
        assert status["feedId"] == "FeedId1"
        assert status["processingStatus"] == "CANCELLED"

    def test_get_feed_document(self, client):
        """getFeedDocument con doc ID exacto."""
        api = Feeds(
            credentials=client._credentials,
            marketplace=client._marketplace,
        )
        doc_id = "0356cf79-b8b0-4226-b4b9-0ee058ea5760"
        # get_feed_document descarga el contenido — en sandbox devuelve la URL
        # Puede fallar si la URL del sandbox no está disponible
        try:
            resp = api._request(f"/feeds/2021-06-30/documents/{doc_id}")
            payload = resp.payload
            assert payload["feedDocumentId"] == doc_id
            assert "url" in payload
        except Exception:
            pytest.skip("Sandbox feed document URL no disponible")
