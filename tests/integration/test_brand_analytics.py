"""Tests de integración para Brand Analytics Reports (sandbox SP-API).

Brand Analytics requiere marca registrada (Brand Registry).
El sandbox de Reports NO incluye test cases para Brand Analytics report types.
Estos tests solo se ejecutan en producción — en sandbox se documentan como skip.

La infraestructura base de reports (create/get/download) ya se valida
en test_reports_base.py con los test cases del sandbox.
"""

import pytest

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestBrandAnalyticsSandbox:

    def test_search_terms_report_not_in_sandbox(self, client):
        """Brand Analytics reports no están disponibles en sandbox."""
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.get_search_terms_report(
                "2024-03-10T20:11:24.000Z", "2024-03-11T20:11:24.000Z",
                poll_interval=1, timeout=5,
            )
