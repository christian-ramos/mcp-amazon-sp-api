"""Tests de tools MCP: A+ Content."""

from mcp_amazon_sp_api.server import list_aplus_content, get_aplus_content, get_aplus_asin_relations
from .conftest import parse


class TestListAplusContent:
    def test_returns_documents(self, mock_client):
        mock_client.search_content_documents.return_value = [
            {
                "contentReferenceKey": "KEY-1",
                "contentMetadata": {"name": "Water Bottle A+", "status": "APPROVED", "badgeSet": [], "updateTime": "2025-01-15"},
            },
            {
                "contentReferenceKey": "KEY-2",
                "contentMetadata": {"name": "Bottle A+", "status": "DRAFT", "badgeSet": [], "updateTime": "2025-02-01"},
            },
        ]
        result = parse(list_aplus_content())
        assert result["totalDocuments"] == 2
        assert result["documents"][0]["name"] == "Water Bottle A+"
        assert result["documents"][1]["status"] == "DRAFT"

    def test_empty_list(self, mock_client):
        mock_client.search_content_documents.return_value = []
        result = parse(list_aplus_content())
        assert result["totalDocuments"] == 0

    def test_error_handling(self, mock_client):
        mock_client.search_content_documents.side_effect = RuntimeError("No brand")
        assert "error" in parse(list_aplus_content())


class TestGetAplusContent:
    def test_returns_document_detail(self, mock_client):
        mock_client.get_content_document.return_value = {
            "contentRecord": {
                "contentReferenceKey": "KEY-1",
                "contentModuleList": [{"contentModuleType": "STANDARD_IMAGE_TEXT_OVERLAY"}],
            },
        }
        result = parse(get_aplus_content(content_key="KEY-1"))
        assert result["contentRecord"]["contentReferenceKey"] == "KEY-1"

    def test_error_handling(self, mock_client):
        mock_client.get_content_document.side_effect = RuntimeError("Not found")
        assert "error" in parse(get_aplus_content(content_key="KEY-BAD"))


class TestGetAplusAsinRelations:
    def test_returns_asins(self, mock_client):
        mock_client.get_content_asin_relations.return_value = [
            {"asin": "B001", "badgeSet": []},
            {"asin": "B002", "badgeSet": []},
        ]
        result = parse(get_aplus_asin_relations(content_key="KEY-1"))
        assert result["totalAsins"] == 2
        assert result["contentReferenceKey"] == "KEY-1"

    def test_error_handling(self, mock_client):
        mock_client.get_content_asin_relations.side_effect = RuntimeError("Fail")
        assert "error" in parse(get_aplus_asin_relations(content_key="KEY-BAD"))
