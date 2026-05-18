"""Tests unitarios para AplusContentClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient

from .conftest import make_api_error, make_response


class TestSearchContentDocuments:
    @patch.object(AmazonClient, "_aplus_api")
    def test_returns_documents(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_content_documents.return_value = make_response({
            "contentMetadataRecords": [
                {"contentReferenceKey": "KEY-1", "contentMetadata": {"name": "A+ Doc 1"}},
                {"contentReferenceKey": "KEY-2", "contentMetadata": {"name": "A+ Doc 2"}},
            ],
            "nextPageToken": None,
        })
        result = client.search_content_documents()
        assert len(result) == 2
        assert result[0]["contentReferenceKey"] == "KEY-1"

    @patch.object(AmazonClient, "_aplus_api")
    def test_paginates(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_content_documents.side_effect = [
            make_response({
                "contentMetadataRecords": [{"contentReferenceKey": "KEY-1"}],
                "nextPageToken": "page2",
            }),
            make_response({
                "contentMetadataRecords": [{"contentReferenceKey": "KEY-2"}],
                "nextPageToken": None,
            }),
        ]
        result = client.search_content_documents()
        assert len(result) == 2
        assert mock_api.search_content_documents.call_count == 2

    @patch.object(AmazonClient, "_aplus_api")
    def test_passes_marketplace_id(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_content_documents.return_value = make_response({
            "contentMetadataRecords": [],
            "nextPageToken": None,
        })
        client.search_content_documents()
        kwargs = mock_api.search_content_documents.call_args[1]
        assert "marketplaceId" in kwargs

    @patch.object(AmazonClient, "_aplus_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.search_content_documents.side_effect = make_api_error(403)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.search_content_documents()


class TestGetContentDocument:
    @patch.object(AmazonClient, "_aplus_api")
    def test_returns_document(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_content_document.return_value = make_response({
            "contentRecord": {"contentReferenceKey": "KEY-1"},
            "contentType": "EBC",
        })
        result = client.get_content_document("KEY-1")
        assert result["contentRecord"]["contentReferenceKey"] == "KEY-1"

    @patch.object(AmazonClient, "_aplus_api")
    def test_passes_included_data_set(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_content_document.return_value = make_response({})
        client.get_content_document("KEY-1")
        kwargs = mock_api.get_content_document.call_args[1]
        assert "CONTENTS" in kwargs["includedDataSet"]
        assert "METADATA" in kwargs["includedDataSet"]

    @patch.object(AmazonClient, "_aplus_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_content_document.side_effect = make_api_error(404)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_content_document("KEY-BAD")


class TestGetContentAsinRelations:
    @patch.object(AmazonClient, "_aplus_api")
    def test_returns_asins(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.list_content_document_asin_relations.return_value = make_response({
            "asinMetadataSet": [
                {"asin": "B001", "badgeSet": []},
                {"asin": "B002", "badgeSet": ["BRAND_NOT_ELIGIBLE"]},
            ],
        })
        result = client.get_content_asin_relations("KEY-1")
        assert len(result) == 2
        assert result[0]["asin"] == "B001"

    @patch.object(AmazonClient, "_aplus_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.list_content_document_asin_relations.side_effect = make_api_error(404)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_content_asin_relations("KEY-BAD")
