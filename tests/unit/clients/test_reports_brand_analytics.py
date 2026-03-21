"""Tests unitarios para BrandAnalyticsClient."""

from unittest.mock import patch

import pytest

from mcp_amazon_sp_api.sp_client import AmazonClient
from mcp_amazon_sp_api.clients.reports_brand_analytics import (
    _parse_tsv, _parse_report, _last_complete_week, _last_complete_month,
    SEARCH_TERMS, SEARCH_QUERY_PERFORMANCE, MARKET_BASKET,
    REPEAT_PURCHASE, ITEM_COMPARISON, ALTERNATE_PURCHASE,
)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

class TestLastCompleteWeek:
    def test_returns_sunday_to_saturday(self):
        start, end = _last_complete_week()
        from datetime import date
        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
        assert s.weekday() == 6  # Sunday
        assert e.weekday() == 5  # Saturday
        assert (e - s).days == 6

class TestLastCompleteMonth:
    def test_returns_first_to_last_day(self):
        start, end = _last_complete_month()
        from datetime import date
        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
        assert s.day == 1
        assert (e + __import__('datetime').timedelta(days=1)).day == 1  # next day is 1st


# ---------------------------------------------------------------------------
# Helpers de parseo
# ---------------------------------------------------------------------------

class TestParseTsv:
    def test_parses_tab_separated(self):
        content = "col1\tcol2\nval1\tval2\nval3\tval4\n"
        rows = _parse_tsv(content)
        assert len(rows) == 2
        assert rows[0]["col1"] == "val1"
        assert rows[1]["col2"] == "val4"

    def test_handles_empty(self):
        assert _parse_tsv("col1\tcol2\n") == []


class TestParseReport:
    def test_json_array(self):
        content = '[{"term": "water bottle", "rank": 1}]'
        data = _parse_report(content)
        assert len(data) == 1
        assert data[0]["term"] == "water bottle"

    def test_json_object_with_data_key(self):
        content = '{"dataByAsin": [{"asin": "B001"}]}'
        data = _parse_report(content)
        assert data[0]["asin"] == "B001"

    def test_json_object_single(self):
        content = '{"asin": "B001"}'
        data = _parse_report(content)
        assert data[0]["asin"] == "B001"

    def test_tsv_fallback(self):
        content = "keyword\trank\nbottle\t1\n"
        data = _parse_report(content)
        assert data[0]["keyword"] == "bottle"


# ---------------------------------------------------------------------------
# Métodos del cliente
# ---------------------------------------------------------------------------

class TestBrandAnalyticsMethods:
    """Verifica que cada método llama a request_and_download_report con el report type correcto."""

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_search_terms_report(self, mock_rad, client):
        mock_rad.return_value = '[{"term": "bottle"}]'
        result = client.get_search_terms_report("2025-01-05", "2025-01-11")
        assert result[0]["term"] == "bottle"
        mock_rad.assert_called_once_with(
            SEARCH_TERMS, "2025-01-05", "2025-01-11",
            poll_interval=15, timeout=300,
            report_options={"reportPeriod": "WEEK"},
        )

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_search_query_performance(self, mock_rad, client):
        mock_rad.return_value = '[{"query": "water bottle", "impressions": 100}]'
        result = client.get_search_query_performance(["B001", "B002"], "2025-01-05", "2025-01-11")
        assert result[0]["impressions"] == 100
        assert mock_rad.call_args[0][0] == SEARCH_QUERY_PERFORMANCE
        assert mock_rad.call_args[1]["report_options"]["asin"] == "B001 B002"
        assert mock_rad.call_args[1]["report_options"]["reportPeriod"] == "WEEK"

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_market_basket_report(self, mock_rad, client):
        mock_rad.return_value = '[{"asin": "B001", "combo": "B002"}]'
        result = client.get_market_basket_report("2025-01-01", "2025-01-31")
        assert len(result) == 1
        assert mock_rad.call_args[0][0] == MARKET_BASKET
        assert mock_rad.call_args[1]["report_options"] == {"reportPeriod": "MONTH"}

    @patch.object(AmazonClient, "request_and_download_report")
    def test_get_repeat_purchase_report(self, mock_rad, client):
        mock_rad.return_value = '[{"asin": "B001", "repeatRate": "0.15"}]'
        result = client.get_repeat_purchase_report("2025-01-01", "2025-01-31")
        assert result[0]["repeatRate"] == "0.15"
        assert mock_rad.call_args[0][0] == REPEAT_PURCHASE
        assert mock_rad.call_args[1]["report_options"] == {"reportPeriod": "MONTH"}

    @patch.object(AmazonClient, "request_and_download_report")
    def test_tsv_content_parsed(self, mock_rad, client):
        mock_rad.return_value = "keyword\trank\nwater bottle\t1\nbottle\t2\n"
        result = client.get_search_terms_report("2025-01-01", "2025-01-31")
        assert len(result) == 2
        assert result[0]["keyword"] == "water bottle"

    @patch.object(AmazonClient, "request_and_download_report")
    def test_propagates_error(self, mock_rad, client):
        mock_rad.side_effect = RuntimeError("Report failed")
        with pytest.raises(RuntimeError, match="Report failed"):
            client.get_search_terms_report("2025-01-01", "2025-01-31")

    @patch.object(AmazonClient, "request_and_download_report")
    def test_custom_poll_and_timeout(self, mock_rad, client):
        mock_rad.return_value = "[]"
        client.get_search_terms_report(
            "2025-01-05", "2025-01-11",
            poll_interval=5, timeout=60,
        )
        mock_rad.assert_called_once_with(
            SEARCH_TERMS, "2025-01-05", "2025-01-11",
            poll_interval=5, timeout=60,
            report_options={"reportPeriod": "WEEK"},
        )
