"""Cliente de Brand Analytics Reports — datos exclusivos de marca registrada.

Brand Analytics requiere:
- reportOptions.reportPeriod: DAY, WEEK, MONTH o QUARTER
- Fechas simples (YYYY-MM-DD), no timestamps ISO
- WEEK: start=domingo, end=sábado. MONTH: start=1, end=último día del mes
- Un request no puede cruzar periodos (ej: WEEK no puede abarcar 2 semanas)
"""

import csv
import io
import json
import logging
from datetime import datetime, timedelta, timezone

from .reports_base import ReportsBaseClient

logger = logging.getLogger(__name__)

# Report types de Brand Analytics
SEARCH_TERMS = "GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT"
SEARCH_QUERY_PERFORMANCE = "GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT"
MARKET_BASKET = "GET_BRAND_ANALYTICS_MARKET_BASKET_REPORT"
REPEAT_PURCHASE = "GET_BRAND_ANALYTICS_REPEAT_PURCHASE_REPORT"
ITEM_COMPARISON = "GET_BRAND_ANALYTICS_ITEM_COMPARISON_REPORT"
ALTERNATE_PURCHASE = "GET_BRAND_ANALYTICS_ALTERNATE_PURCHASE_REPORT"


def _last_complete_week() -> tuple[str, str]:
    """Devuelve (domingo, sábado) de la última semana completa."""
    today = datetime.now(timezone.utc).date()
    days_since_saturday = (today.weekday() + 2) % 7
    if days_since_saturday == 0:
        days_since_saturday = 7
    last_saturday = today - timedelta(days=days_since_saturday)
    last_sunday = last_saturday - timedelta(days=6)
    return last_sunday.isoformat(), last_saturday.isoformat()


def _last_complete_month() -> tuple[str, str]:
    """Devuelve (primer día, último día) del mes anterior."""
    today = datetime.now(timezone.utc).date()
    first_of_this_month = today.replace(day=1)
    last_of_prev_month = first_of_this_month - timedelta(days=1)
    first_of_prev_month = last_of_prev_month.replace(day=1)
    return first_of_prev_month.isoformat(), last_of_prev_month.isoformat()


def _parse_tsv(content: str) -> list[dict]:
    """Parsea contenido TSV a lista de dicts."""
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    return list(reader)


def _parse_report(content: str) -> list[dict]:
    """Parsea contenido de informe (JSON o TSV)."""
    stripped = content.strip()
    if stripped.startswith(("{", "[")):
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # Algunos informes envuelven los datos en una clave
            for key in ("dataByAsin", "dataByDepartmentAndSearchTerm", "data"):
                if key in parsed:
                    return parsed[key]
            return [parsed]
    return _parse_tsv(content)


class BrandAnalyticsClient(ReportsBaseClient):

    def _ba_report(
        self, report_type: str,
        start_date: str | None, end_date: str | None,
        report_period: str,
        poll_interval: float, timeout: float,
    ) -> list[dict]:
        """Helper interno para Brand Analytics reports."""
        if not start_date or not end_date:
            if report_period == "WEEK":
                start_date, end_date = _last_complete_week()
            else:
                start_date, end_date = _last_complete_month()
        content = self.request_and_download_report(
            report_type, start_date, end_date,
            poll_interval=poll_interval, timeout=timeout,
            report_options={"reportPeriod": report_period},
        )
        return _parse_report(content)

    def get_search_terms_report(
        self, start_date: str | None = None, end_date: str | None = None,
        report_period: str = "WEEK",
        poll_interval: float = 15, timeout: float = 300,
    ) -> list[dict]:
        """Top keywords con click share y conversion share."""
        return self._ba_report(
            SEARCH_TERMS, start_date, end_date, report_period,
            poll_interval, timeout,
        )

    def get_search_query_performance(
        self, asins: list[str],
        start_date: str | None = None, end_date: str | None = None,
        report_period: str = "WEEK",
        poll_interval: float = 15, timeout: float = 300,
    ) -> list[dict]:
        """Rendimiento por término de búsqueda: impresiones, clics, carrito, compras.

        Requiere lista de ASINs (máx 200 caracteres separados por espacio).
        """
        if not start_date or not end_date:
            if report_period == "WEEK":
                start_date, end_date = _last_complete_week()
            else:
                start_date, end_date = _last_complete_month()
        content = self.request_and_download_report(
            SEARCH_QUERY_PERFORMANCE, start_date, end_date,
            poll_interval=poll_interval, timeout=timeout,
            report_options={"reportPeriod": report_period, "asin": " ".join(asins)},
        )
        return _parse_report(content)

    def get_market_basket_report(
        self, start_date: str | None = None, end_date: str | None = None,
        report_period: str = "MONTH",
        poll_interval: float = 15, timeout: float = 300,
    ) -> list[dict]:
        """Productos comprados junto con los tuyos (cross-sell)."""
        return self._ba_report(
            MARKET_BASKET, start_date, end_date, report_period,
            poll_interval, timeout,
        )

    def get_repeat_purchase_report(
        self, start_date: str | None = None, end_date: str | None = None,
        report_period: str = "MONTH",
        poll_interval: float = 15, timeout: float = 300,
    ) -> list[dict]:
        """Tasa de recompra por ASIN."""
        return self._ba_report(
            REPEAT_PURCHASE, start_date, end_date, report_period,
            poll_interval, timeout,
        )

    # NOTA: GET_BRAND_ANALYTICS_ITEM_COMPARISON_REPORT y GET_BRAND_ANALYTICS_ALTERNATE_PURCHASE_REPORT
    # no están documentados en la API oficial y devuelven FATAL en producción (posiblemente deprecados).
