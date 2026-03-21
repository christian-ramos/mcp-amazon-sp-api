"""Tests de integración para Sales & Traffic Reports (sandbox SP-API).

El report type GET_SALES_AND_TRAFFIC_REPORT no tiene test case en el sandbox.
La infraestructura base (create/get/download) se valida en test_reports_base.py.
"""

import pytest

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestSalesReportsSandbox:

    def test_sales_and_traffic_not_in_sandbox(self, client):
        """Sales & Traffic report no está disponible en sandbox."""
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_sales_and_traffic_report(
                "2024-03-10T20:11:24.000Z", "2024-03-11T20:11:24.000Z",
                poll_interval=1, timeout=5,
            )
