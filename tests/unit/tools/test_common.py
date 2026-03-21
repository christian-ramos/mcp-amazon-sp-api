"""Tests de helpers comunes del server."""

from datetime import datetime

from mcp_amazon_sp_api.server import _json


class TestJsonHelper:
    def test_ensure_ascii_false(self):
        result = _json({"name": "España"})
        assert "España" in result
        assert "\\u" not in result

    def test_formats_with_indent(self):
        assert "\n" in _json({"a": 1})

    def test_handles_non_serializable(self):
        assert "2025" in _json({"date": datetime(2025, 1, 1)})
