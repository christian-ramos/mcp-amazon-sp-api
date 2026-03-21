"""Tests de integración para FBA Reports (sandbox SP-API).

Los report types FBA no tienen test cases específicos en el sandbox de Reports.
La infraestructura base (create/get/download) se valida en test_reports_base.py.
"""

import pytest

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestFbaReportsSandbox:

    def test_fba_inventory_report_not_in_sandbox(self, client):
        """FBA inventory reports no están disponibles en sandbox."""
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_fba_inventory_report(poll_interval=1, timeout=5)
