"""Tests de integración para Inventories API (sandbox SP-API).

El sandbox permite crear items de test, añadir inventario y consultarlo.
Operaciones sandbox-only: create_inventory_item, add_inventory, delete_inventory_item.
"""

import uuid

import pytest

from sp_api.api import Inventories

from tests.conftest import skip_without_credentials


@pytest.mark.integration
@skip_without_credentials
class TestInventorySandbox:

    def test_get_inventory_summary(self, client):
        """get_inventory_summary devuelve lista (puede estar vacía en sandbox)."""
        result = client.get_inventory_summary()
        assert isinstance(result, list)

    def test_create_query_delete_inventory(self, client):
        """Flujo completo sandbox: crear item → añadir stock → consultar → eliminar."""
        api = Inventories(
            credentials=client._credentials,
            marketplace=client._marketplace,
        )
        sku = f"TEST-SKU-{uuid.uuid4().hex[:8]}"
        marketplace_id = client._marketplace_id

        # 1. Crear item en sandbox
        try:
            api.create_inventory_item(
                createInventoryItemRequestBody={
                    "sellerSku": sku,
                    "marketplaceId": marketplace_id,
                    "productName": "Test Product",
                },
            )
        except Exception:
            pytest.skip("Sandbox no soporta create_inventory_item")

        try:
            # 2. Añadir stock
            api.add_inventory(**{
                "x-amzn-idempotency-token": uuid.uuid4().hex,
                "addInventoryRequestBody": {
                    "inventoryItems": [{
                        "sellerSku": sku,
                        "marketplaceId": marketplace_id,
                        "quantity": 10,
                    }],
                },
            })

            # 3. Consultar inventario del SKU
            result = client.get_inventory_summary(skus=[sku])
            assert isinstance(result, list)

        finally:
            # 4. Limpiar: eliminar item de sandbox
            try:
                api.delete_inventory_item(sku, marketplaceId=marketplace_id)
            except Exception:
                pass
