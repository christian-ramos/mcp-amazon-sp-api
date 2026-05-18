"""Cliente de Reports Ventas y Tráfico — sesiones, conversión, Buy Box %."""

import logging

from .reports_base import ReportsBaseClient
from .reports_brand_analytics import _parse_report

logger = logging.getLogger(__name__)

SALES_AND_TRAFFIC = "GET_SALES_AND_TRAFFIC_REPORT"


class SalesReportsClient(ReportsBaseClient):

    def get_sales_and_traffic_report(
        self, start_date: str, end_date: str,
        poll_interval: float = 15, timeout: float = 600,
    ) -> list[dict]:
        """Sesiones, page views, Buy Box %, conversión por ASIN y día."""
        content = self.request_and_download_report(
            SALES_AND_TRAFFIC, start_date, end_date,
            poll_interval=poll_interval, timeout=timeout,
        )
        return _parse_report(content)
