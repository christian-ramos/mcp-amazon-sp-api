"""Tests de decoradores: throttle_retry, load_all_pages."""

from unittest.mock import patch

import pytest
from sp_api.base import SellingApiException

from mcp_amazon_sp_api.sp_client import throttle_retry, load_all_pages
from .conftest import make_throttle_error, make_api_error


class TestThrottleRetry:
    def test_returns_on_first_success(self):
        @throttle_retry(max_retries=3)
        def ok():
            return "done"
        assert ok() == "done"

    @patch("mcp_amazon_sp_api.clients.base.time.sleep")
    def test_retries_on_429(self, mock_sleep):
        call_count = 0

        @throttle_retry(max_retries=3, base_delay=0.1)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise make_throttle_error()
            return "recovered"

        assert flaky() == "recovered"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @patch("mcp_amazon_sp_api.clients.base.time.sleep")
    def test_raises_after_max_retries(self, mock_sleep):
        @throttle_retry(max_retries=2, base_delay=0.1)
        def always_throttled():
            raise make_throttle_error()

        with pytest.raises(SellingApiException):
            always_throttled()
        assert mock_sleep.call_count == 2

    def test_raises_non_429_immediately(self):
        @throttle_retry(max_retries=3)
        def forbidden():
            raise make_api_error(403)

        with pytest.raises(SellingApiException):
            forbidden()

    @patch("mcp_amazon_sp_api.clients.base.time.sleep")
    def test_exponential_backoff(self, mock_sleep):
        call_count = 0

        @throttle_retry(max_retries=3, base_delay=1.0)
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise make_throttle_error()
            return "ok"

        flaky()
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0]


class TestLoadAllPages:
    def test_accumulates_pages(self):
        call_count = 0

        @load_all_pages
        def paginated(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return ([1, 2], "token2")
            elif call_count == 2:
                return ([3, 4], "token3")
            else:
                return ([5], None)

        assert paginated() == [1, 2, 3, 4, 5]
        assert call_count == 3

    def test_single_page(self):
        @load_all_pages
        def single_page(**kwargs):
            return ([1, 2, 3], None)
        assert single_page() == [1, 2, 3]
