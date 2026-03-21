"""Cliente de Listings Restrictions API — elegibilidad para vender ASINs."""

import logging

from sp_api.api import ListingsRestrictions
from sp_api.base import Marketplaces, SellingApiException

from .base import BaseClient, throttle_retry
from .pricing_cross import EU_MARKETPLACES

logger = logging.getLogger(__name__)


class ListingsRestrictionsClient(BaseClient):

    def _restrictions_api(self, marketplace: Marketplaces | None = None) -> ListingsRestrictions:
        return ListingsRestrictions(
            credentials=self._credentials,
            marketplace=marketplace or self._marketplace,
        )

    @throttle_retry()
    def get_listings_restrictions(
        self, asin: str, condition_type: str | None = None,
    ) -> list[dict]:
        """Obtiene restricciones para vender un ASIN en tu marketplace.

        Args:
            asin: ASIN del producto.
            condition_type: Condición (ej: "new_new", "used_acceptable"). None = todas.
        """
        kwargs: dict = {
            "asin": asin,
            "sellerId": self._seller_id,
            "marketplaceIds": [self._marketplace_id],
        }
        if condition_type:
            kwargs["conditionType"] = condition_type

        try:
            resp = self._restrictions_api().get_listings_restrictions(**kwargs)
            payload = resp.payload or {}
            return payload.get("restrictions", [])
        except SellingApiException as e:
            if getattr(e, "code", None) == 429:
                raise
            logger.error("Error obteniendo restricciones para %s: %s", asin, e)
            raise RuntimeError(f"Error SP-API al obtener restricciones de {asin}: {e}") from e

    def check_expansion_eligibility(
        self, asin: str, target_marketplaces: list[str],
    ) -> list[dict]:
        """Verifica elegibilidad para vender un ASIN en múltiples marketplaces.

        Args:
            asin: ASIN del producto.
            target_marketplaces: Códigos de marketplace (ej: ["DE", "FR", "IT"]).
        """
        results = []

        for code in target_marketplaces:
            mp = EU_MARKETPLACES.get(code.upper())
            if not mp:
                results.append({"marketplace": code, "error": f"Marketplace '{code}' no soportado"})
                continue

            try:
                api = self._restrictions_api(mp["marketplace"])
                resp = api.get_listings_restrictions(
                    asin=asin,
                    sellerId=self._seller_id,
                    marketplaceIds=[mp["id"]],
                )
                payload = resp.payload or {}
                restrictions = payload.get("restrictions", [])

                results.append({
                    "marketplace": code,
                    "marketplaceId": mp["id"],
                    "restricted": len(restrictions) > 0,
                    "restrictions": [
                        {
                            "conditionType": r.get("conditionType"),
                            "reasons": [reason.get("message") for reason in r.get("reasons", [])],
                        }
                        for r in restrictions
                    ],
                })
            except SellingApiException as e:
                if getattr(e, "code", None) == 429:
                    raise
                results.append({"marketplace": code, "error": str(e)})
            except Exception as e:
                results.append({"marketplace": code, "error": str(e)})

        return results
