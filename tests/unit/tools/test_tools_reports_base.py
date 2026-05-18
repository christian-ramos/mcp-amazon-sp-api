"""Tests de tools MCP: reports base (request, check, download)."""

from mcp_amazon_sp_api.tools.reports import check_report, download_report, request_report

from .conftest import parse


class TestRequestReport:
    def test_creates_report_and_returns_id(self, mock_client):
        mock_client.create_report.return_value = "RPT-123"
        result = parse(request_report(
            report_type="GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT",
            days_back=30,
        ))
        assert result["reportId"] == "RPT-123"
        assert result["status"] == "IN_QUEUE"
        assert "nextStep" in result

    def test_passes_report_type(self, mock_client):
        mock_client.create_report.return_value = "RPT-1"
        parse(request_report(report_type="GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA"))
        args = mock_client.create_report.call_args
        assert args[0][0] == "GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA"

    def test_error_handling(self, mock_client):
        mock_client.create_report.side_effect = RuntimeError("API down")
        result = parse(request_report(report_type="TYPE"))
        assert "error" in result


class TestCheckReport:
    def test_done_with_next_step(self, mock_client):
        mock_client.get_report_status.return_value = {
            "reportId": "RPT-1",
            "processingStatus": "DONE",
            "reportDocumentId": "DOC-1",
        }
        result = parse(check_report(report_id="RPT-1"))
        assert result["processingStatus"] == "DONE"
        assert "download_report" in result["nextStep"]

    def test_in_progress(self, mock_client):
        mock_client.get_report_status.return_value = {
            "reportId": "RPT-1",
            "processingStatus": "IN_PROGRESS",
            "reportDocumentId": None,
        }
        result = parse(check_report(report_id="RPT-1"))
        assert result["processingStatus"] == "IN_PROGRESS"
        assert "Espera" in result["nextStep"]

    def test_fatal_with_retry_message(self, mock_client):
        mock_client.get_report_status.return_value = {
            "reportId": "RPT-1",
            "processingStatus": "FATAL",
            "reportDocumentId": None,
        }
        result = parse(check_report(report_id="RPT-1"))
        assert result["processingStatus"] == "FATAL"
        assert "request_report" in result["nextStep"]

    def test_error_handling(self, mock_client):
        mock_client.get_report_status.side_effect = RuntimeError("Not found")
        result = parse(check_report(report_id="RPT-BAD"))
        assert "error" in result


class TestDownloadReport:
    def test_downloads_done_report(self, mock_client):
        mock_client.get_report_status.return_value = {
            "reportId": "RPT-1",
            "processingStatus": "DONE",
            "reportDocumentId": "DOC-1",
        }
        mock_client.download_report.return_value = "col1\tcol2\nval1\tval2"
        result = parse(download_report(report_id="RPT-1"))
        assert result["content"] == "col1\tcol2\nval1\tval2"

    def test_rejects_not_done(self, mock_client):
        mock_client.get_report_status.return_value = {
            "reportId": "RPT-1",
            "processingStatus": "IN_PROGRESS",
            "reportDocumentId": None,
        }
        result = parse(download_report(report_id="RPT-1"))
        assert "error" in result
        assert "IN_PROGRESS" in result["error"]

    def test_error_handling(self, mock_client):
        mock_client.get_report_status.side_effect = RuntimeError("Fail")
        result = parse(download_report(report_id="RPT-BAD"))
        assert "error" in result
