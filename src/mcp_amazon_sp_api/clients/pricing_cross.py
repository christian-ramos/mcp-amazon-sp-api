"""Cliente de precios cross-marketplace — sincronización estilo BIL."""

import logging

from sp_api.api.listings_items.listings_items_2021_08_01 import ListingsItemsV20210801
from sp_api.base import SellingApiException

from ..config import EU_MARKETPLACES
from .base import BaseClient, throttle_retry

logger = logging.getLogger(__name__)


class CrossMarketplacePricingClient(BaseClient):
    def _listings_api(self) -> ListingsItemsV20210801:
        return ListingsItemsV20210801(credentials=self._credentials, marketplace=self._marketplace)

    @throttle_retry()
    def get_prices_all_marketplaces(
        self,
        sku: str,
        marketplaces: list[str] | None = None,
    ) -> list[dict]:
        """Obtiene el precio de un SKU en múltiples marketplaces.

        Args:
            sku: SKU del producto.
            marketplaces: Códigos de marketplace (ej: ["ES", "DE", "FR"]). None = todos EU.
        """
        targets = marketplaces or list(EU_MARKETPLACES.keys())
        results = []

        for code in targets:
            mp = EU_MARKETPLACES.get(code.upper())
            if not mp:
                results.append(
                    {"marketplace": code, "error": f"Marketplace '{code}' no soportado"}
                )
                continue

            try:
                api = self._listings_api()
                resp = api.get_listings_item(
                    sellerId=self._seller_id,
                    sku=sku,
                    marketplaceIds=[mp["id"]],
                    includedData=["offers"],
                )
                payload = resp.payload or {}
                offers = payload.get("offers", [])
                if offers:
                    offer = offers[0]
                    price_info = offer.get("buyingPrice", {}).get("listingPrice", {})
                    results.append(
                        {
                            "marketplace": code,
                            "marketplaceId": mp["id"],
                            "currency": price_info.get("currencyCode", mp["currency"]),
                            "price": price_info.get("amount"),
                            "fulfillmentChannel": offer.get("fulfillmentChannel"),
                            "status": payload.get("status"),
                        }
                    )
                else:
                    results.append(
                        {
                            "marketplace": code,
                            "marketplaceId": mp["id"],
                            "price": None,
                            "status": "NO_OFFER",
                        }
                    )
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                results.append({"marketplace": code, "error": str(e)})
            except Exception as e:
                results.append({"marketplace": code, "error": str(e)})

        return results

    @throttle_retry()
    def update_price(
        self,
        sku: str,
        product_type: str,
        price: float,
        marketplace: str,
    ) -> dict:
        """Actualiza el precio de un SKU en un marketplace específico.

        Args:
            sku: SKU del producto.
            product_type: Tipo de producto (ej: "WATER_BOTTLE").
            price: Nuevo precio.
            marketplace: Código de marketplace (ej: "DE").
        """
        mp = EU_MARKETPLACES.get(marketplace.upper())
        if not mp:
            raise RuntimeError(f"Marketplace '{marketplace}' no soportado")

        patches = [
            {
                "op": "replace",
                "path": "/attributes/purchasable_offer",
                "value": [
                    {
                        "marketplace_id": mp["id"],
                        "currency": mp["currency"],
                        "our_price": [{"schedule": [{"value_with_tax": price}]}],
                    }
                ],
            }
        ]

        try:
            api = self._listings_api()
            resp = api.patch_listings_item(
                sellerId=self._seller_id,
                sku=sku,
                marketplaceIds=[mp["id"]],
                body={
                    "productType": product_type,
                    "patches": patches,
                },
            )
            return resp.payload or {}
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error actualizando precio en %s: %s", marketplace, e)
            raise RuntimeError(
                f"Error SP-API al actualizar precio en {marketplace}: {e}"
            ) from e

    def sync_prices(
        self,
        sku: str,
        product_type: str,
        base_price: float,
        target_marketplaces: list[str],
        adjustment_pct: float = 0.0,
    ) -> list[dict]:
        """Sincroniza precio a múltiples marketplaces con ajuste opcional.

        Args:
            sku: SKU del producto.
            product_type: Tipo de producto.
            base_price: Precio base.
            target_marketplaces: Lista de códigos (ej: ["DE", "FR", "IT"]).
            adjustment_pct: Ajuste porcentual (ej: 5.0 = +5%, -3.0 = -3%).
        """
        adjusted_price = round(base_price * (1 + adjustment_pct / 100), 2)
        results = []

        for mp_code in target_marketplaces:
            try:
                resp = self.update_price(sku, product_type, adjusted_price, mp_code)
                results.append(
                    {
                        "marketplace": mp_code,
                        "price": adjusted_price,
                        "status": resp.get("status", "ACCEPTED"),
                        "issues": resp.get("issues", []),
                    }
                )
            except RuntimeError as e:
                results.append(
                    {
                        "marketplace": mp_code,
                        "price": adjusted_price,
                        "error": str(e),
                    }
                )

        return results
