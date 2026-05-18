"""Tests unitarios para ReportsBaseClient."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient

from .conftest import make_api_error, make_response


class TestCreateReport:
    @patch.object(AmazonClient, "_reports_api")
    def test_returns_report_id(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api._request.return_value = make_response({"reportId": "RPT-123"})
        report_id = client.create_report(
            "GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT",
            "2025-01-01T00:00:00Z",
            "2025-01-31T00:00:00Z",
        )
        assert report_id == "RPT-123"

    @patch.object(AmazonClient, "_reports_api")
    def test_passes_body_correctly(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api._request.return_value = make_response({"reportId": "RPT-1"})
        client.create_report(
            "GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA",
            "2025-01-01",
            "2025-01-31",
        )
        data = mock_api._request.call_args[1]["data"]
        assert data["reportType"] == "GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA"
        assert data["dataStartTime"] == "2025-01-01"
        assert data["dataEndTime"] == "2025-01-31"

    @patch.object(AmazonClient, "_reports_api")
    def test_custom_marketplace_ids(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api._request.return_value = make_response({"reportId": "RPT-1"})
        client.create_report(
            "REPORT_TYPE", "2025-01-01", "2025-01-31",
            marketplace_ids=["A1RKKUPIHCS9HS"],
        )
        data = mock_api._request.call_args[1]["data"]
        assert data["marketplaceIds"] == ["A1RKKUPIHCS9HS"]

    @patch.object(AmazonClient, "_reports_api")
    def test_raises_if_no_report_id(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api._request.return_value = make_response({})
        with pytest.raises(RuntimeError, match="no devolvió reportId"):
            client.create_report("TYPE", "2025-01-01", "2025-01-31")

    @patch.object(AmazonClient, "_reports_api")
    def test_raises_runtime_error_on_api_failure(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api._request.side_effect = make_api_error(400)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.create_report("TYPE", "2025-01-01", "2025-01-31")

    @patch.object(AmazonClient, "_reports_api")
    def test_passes_report_options(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api._request.return_value = make_response({"reportId": "RPT-1"})
        client.create_report(
            "REPORT_TYPE", "2025-01-01", "2025-01-07",
            report_options={"reportPeriod": "WEEK"},
        )
        data = mock_api._request.call_args[1]["data"]
        assert data["reportOptions"] == {"reportPeriod": "WEEK"}


class TestGetReportStatus:
    @patch.object(AmazonClient, "_reports_api")
    def test_returns_status(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_report.return_value = make_response({
            "reportId": "RPT-1",
            "processingStatus": "DONE",
            "reportDocumentId": "DOC-1",
        })
        status = client.get_report_status("RPT-1")
        assert status["processingStatus"] == "DONE"
        assert status["reportDocumentId"] == "DOC-1"

    @patch.object(AmazonClient, "_reports_api")
    def test_in_progress_no_doc_id(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_report.return_value = make_response({
            "reportId": "RPT-1",
            "processingStatus": "IN_PROGRESS",
        })
        status = client.get_report_status("RPT-1")
        assert status["processingStatus"] == "IN_PROGRESS"
        assert status["reportDocumentId"] is None

    @patch.object(AmazonClient, "_reports_api")
    def test_raises_on_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_report.side_effect = make_api_error(404)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_report_status("RPT-BAD")


class TestDownloadReport:
    @patch.object(AmazonClient, "_reports_api")
    def test_returns_document_content(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_report_document.return_value = make_response({
            "document": "col1\tcol2\nval1\tval2\n",
        })
        content = client.download_report("DOC-1")
        assert "col1" in content
        mock_api.get_report_document.assert_called_once_with("DOC-1", download=True)

    @patch.object(AmazonClient, "_reports_api")
    def test_raises_if_no_document(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_report_document.return_value = make_response({})
        with pytest.raises(RuntimeError, match="No se pudo descargar"):
            client.download_report("DOC-BAD")

    @patch.object(AmazonClient, "_reports_api")
    def test_raises_on_api_error(self, mock_api_factory, client):
        mock_api = MagicMock()
        mock_api_factory.return_value = mock_api
        mock_api.get_report_document.side_effect = make_api_error(500)
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.download_report("DOC-ERR")


class TestRequestAndDownloadReport:
    @patch.object(AmazonClient, "download_report")
    @patch.object(AmazonClient, "get_report_status")
    @patch.object(AmazonClient, "create_report")
    def test_full_flow_immediate_done(self, mock_create, mock_status, mock_download, client):
        mock_create.return_value = "RPT-1"
        mock_status.return_value = {
            "reportId": "RPT-1",
            "processingStatus": "DONE",
            "reportDocumentId": "DOC-1",
        }
        mock_download.return_value = "report content here"

        result = client.request_and_download_report(
            "REPORT_TYPE", "2025-01-01", "2025-01-31",
        )
        assert result == "report content here"
        mock_create.assert_called_once()
        mock_download.assert_called_once_with("DOC-1")

    @patch("mcp_amazon_sp_api.clients.reports_base.time.sleep")
    @patch.object(AmazonClient, "download_report")
    @patch.object(AmazonClient, "get_report_status")
    @patch.object(AmazonClient, "create_report")
    def test_polls_until_done(self, mock_create, mock_status, mock_download, mock_sleep, client):
        mock_create.return_value = "RPT-1"
        mock_status.side_effect = [
            {"reportId": "RPT-1", "processingStatus": "IN_QUEUE", "reportDocumentId": None},
            {"reportId": "RPT-1", "processingStatus": "IN_PROGRESS", "reportDocumentId": None},
            {"reportId": "RPT-1", "processingStatus": "DONE", "reportDocumentId": "DOC-1"},
        ]
        mock_download.return_value = "data"

        result = client.request_and_download_report(
            "REPORT_TYPE", "2025-01-01", "2025-01-31", poll_interval=5,
        )
        assert result == "data"
        assert mock_status.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("mcp_amazon_sp_api.clients.reports_base.time.sleep")
    @patch.object(AmazonClient, "get_report_status")
    @patch.object(AmazonClient, "create_report")
    def test_raises_on_fatal(self, mock_create, mock_status, mock_sleep, client):
        mock_create.return_value = "RPT-1"
        mock_status.return_value = {
            "reportId": "RPT-1", "processingStatus": "FATAL", "reportDocumentId": None,
        }
        with pytest.raises(RuntimeError, match="FATAL"):
            client.request_and_download_report("TYPE", "2025-01-01", "2025-01-31")

    @patch("mcp_amazon_sp_api.clients.reports_base.time.sleep")
    @patch.object(AmazonClient, "get_report_status")
    @patch.object(AmazonClient, "create_report")
    def test_raises_on_cancelled(self, mock_create, mock_status, mock_sleep, client):
        mock_create.return_value = "RPT-1"
        mock_status.return_value = {
            "reportId": "RPT-1", "processingStatus": "CANCELLED", "reportDocumentId": None,
        }
        with pytest.raises(RuntimeError, match="CANCELLED"):
            client.request_and_download_report("TYPE", "2025-01-01", "2025-01-31")

    @patch("mcp_amazon_sp_api.clients.reports_base.time.sleep")
    @patch.object(AmazonClient, "get_report_status")
    @patch.object(AmazonClient, "create_report")
    def test_raises_on_timeout(self, mock_create, mock_status, mock_sleep, client):
        mock_create.return_value = "RPT-1"
        mock_status.return_value = {
            "reportId": "RPT-1", "processingStatus": "IN_PROGRESS", "reportDocumentId": None,
        }
        with pytest.raises(RuntimeError, match="Timeout"):
            client.request_and_download_report(
                "TYPE", "2025-01-01", "2025-01-31",
                poll_interval=10, timeout=25,
            )
