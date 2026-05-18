"""Cliente de análisis de competencia — buscar productos similares y comparar precios."""

import logging

from .base import BaseClient

logger = logging.getLogger(__name__)


class CompetitorAnalysisClient(BaseClient):

    def analyze_competitor_prices(
        self, keywords: str, max_results: int = 10,
    ) -> list[dict]:
        """Busca productos similares y obtiene precios, rankings y fulfillment.

        Args:
            keywords: Términos de búsqueda (ej: "stainless steel water bottle 500ml").
            max_results: Máximo de productos a analizar (default 10, máx 20).
        """
        max_results = min(max_results, 20)

        # 1. Buscar ASINs similares
        items = self.search_catalog_items(keywords=keywords)[:max_results]
        if not items:
            return []

        # 2. Obtener precios competitivos en batch (máx 20 ASINs por llamada)
        asins = [item.get("asin") for item in items if item.get("asin")]
        if not asins:
            return []

        pricing_map = {}
        try:
            pricing_data = self.get_competitive_pricing(asins)
            for p in pricing_data:
                pricing_map[p.get("ASIN")] = p
        except Exception as e:
            logger.warning("No se pudo obtener pricing batch: %s", e)

        # 3. Combinar catálogo + pricing
        results = []
        for item in items:
            asin = item.get("asin")
            summaries = item.get("summaries", [{}])
            summary = summaries[0] if summaries else {}
            sales_ranks = item.get("salesRanks", [])

            entry = {
                "asin": asin,
                "title": summary.get("itemName"),
                "brand": summary.get("brand"),
                "classification": summary.get("classification", {}).get("displayName"),
            }

            # Pricing data
            price_info = pricing_map.get(asin, {})
            product = price_info.get("Product", {})
            competitive = product.get("CompetitivePricing", {})
            prices = competitive.get("CompetitivePrices", [])
            offer_counts = competitive.get("NumberOfOfferListings", [])

            if prices:
                best = prices[0].get("Price", {})
                entry["landedPrice"] = best.get("LandedPrice", {})
                entry["listingPrice"] = best.get("ListingPrice", {})

            total_offers = 0
            for oc in offer_counts:
                total_offers += oc.get("Count", 0)
            entry["totalOffers"] = total_offers

            # Sales rankings (del catálogo o del pricing)
            rankings = []
            rank_source = sales_ranks or product.get("SalesRankings", [])
            for rank_group in rank_source:
                if isinstance(rank_group, dict):
                    # Formato catálogo: {"ranks": [...]}
                    for r in rank_group.get("ranks", []):
                        rankings.append({
                            "category": r.get("title"),
                            "rank": r.get("rank"),
                        })
                    # Formato pricing: {"ProductCategoryId": ..., "Rank": ...}
                    if "Rank" in rank_group:
                        rankings.append({
                            "category": rank_group.get("ProductCategoryId"),
                            "rank": rank_group.get("Rank"),
                        })
            entry["salesRankings"] = rankings

            results.append(entry)

        # Ordenar por precio (más barato primero)
        def sort_key(x):
            lp = x.get("listingPrice") or x.get("landedPrice") or {}
            try:
                return float(lp.get("Amount", 999999))
            except (ValueError, TypeError):
                return 999999

        results.sort(key=sort_key)
        return results

    def compare_with_competitors(
        self, my_asin: str, keywords: str, max_results: int = 10,
    ) -> dict:
        """Compara tu producto con competidores similares.

        Args:
            my_asin: Tu ASIN para comparar.
            keywords: Términos de búsqueda para encontrar competidores.
            max_results: Máximo de competidores a analizar.
        """
        # Obtener datos de mi producto
        my_product = None
        try:
            catalog_item = self.get_catalog_item(my_asin)
            summaries = catalog_item.get("summaries", [{}])
            summary = summaries[0] if summaries else {}

            my_product = {
                "asin": my_asin,
                "title": summary.get("itemName"),
                "brand": summary.get("brand"),
            }

            # Mi pricing
            my_pricing = self.get_competitive_pricing([my_asin])
            if my_pricing:
                product = my_pricing[0].get("Product", {})
                competitive = product.get("CompetitivePricing", {})
                prices = competitive.get("CompetitivePrices", [])
                if prices:
                    best = prices[0].get("Price", {})
                    my_product["listingPrice"] = best.get("ListingPrice", {})
                    my_product["landedPrice"] = best.get("LandedPrice", {})

                rankings = []
                for r in product.get("SalesRankings", []):
                    rankings.append({
                        "category": r.get("ProductCategoryId"),
                        "rank": r.get("Rank"),
                    })
                my_product["salesRankings"] = rankings

        except Exception as e:
            logger.warning("No se pudo obtener datos de %s: %s", my_asin, e)
            my_product = {"asin": my_asin, "error": str(e)}

        # Obtener competidores
        competitors = self.analyze_competitor_prices(keywords, max_results)

        # Filtrar mi propio ASIN de la lista de competidores
        competitors = [c for c in competitors if c.get("asin") != my_asin]

        return {
            "myProduct": my_product,
            "competitors": competitors,
            "totalCompetitors": len(competitors),
        }
