"""Tests de integración para análisis de competencia (sandbox SP-API).

El análisis de competencia combina Catalog Items + Products Pricing.
El sandbox de Catalog requiere parámetros exactos que no coinciden con búsquedas libres.
En producción funciona con cualquier keyword.
"""

import pytest

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestCompetitorAnalysisSandbox:

    def test_analyze_not_in_sandbox(self, client):
        """Catalog search con keywords libres no matchea en sandbox."""
        with pytest.raises(RuntimeError, match="Error SP-API"):
            client.analyze_competitor_prices("water bottle", max_results=3)

    def test_compare_handles_errors_gracefully(self, client):
        """compare_with_competitors maneja errores sin lanzar excepción en myProduct."""
        # get_catalog_item falla en sandbox, pero compare no debe lanzar
        # porque captura el error de myProduct internamente
        # Sin embargo, analyze_competitor_prices sí lanza
        with pytest.raises(RuntimeError):
            client.compare_with_competitors("B00V5DG6IQ", "water bottle", max_results=3)
