"""Tools: precios competitivos y ofertas."""

from ..helpers import get_client, logger, to_json


def get_competitive_pricing(asins: str, marketplace: str = "") -> str:
    """Precios competitivos, Buy Box y rankings por ASIN."""
    try:
        client = get_client(marketplace)
        asin_list = [a.strip() for a in asins.split(",") if a.strip()][:20]
        data = client.get_competitive_pricing(asin_list)

        result = []
        for item in data:
            product = item.get("Product", {})
            competitive = product.get("CompetitivePricing", {})
            prices = competitive.get("CompetitivePrices", [])
            rankings = competitive.get("NumberOfOfferListings", [])
            sales_ranks = product.get("SalesRankings", [])

            pricing_info = []
            for p in prices:
                price_data = p.get("Price", {})
                pricing_info.append({
                    "condition": p.get("condition"),
                    "belongsToRequester": p.get("belongsToRequester"),
                    "landedPrice": price_data.get("LandedPrice", {}),
                    "listingPrice": price_data.get("ListingPrice", {}),
                    "shipping": price_data.get("Shipping", {}),
                })

            result.append({
                "asin": item.get("ASIN"),
                "status": item.get("status"),
                "competitivePrices": pricing_info,
                "numberOfOffers": rankings,
                "salesRankings": sales_ranks,
            })
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_competitive_pricing: %s", e)
        return to_json({"error": str(e)})

def get_competitor_offers(asin: str, marketplace: str = "") -> str:
    """Ofertas de todos los vendedores para un ASIN."""
    try:
        client = get_client(marketplace)
        data = client.get_item_offers(asin)

        summary = data.get("Summary", {})
        offers = data.get("Offers", [])

        result = {
            "asin": asin,
            "totalOffers": summary.get("TotalOfferCount", 0),
            "lowestPrices": summary.get("LowestPrices", []),
            "buyBoxPrices": summary.get("BuyBoxPrices", []),
            "buyBoxEligibleOffers": summary.get("BuyBoxEligibleOfferCounts", []),
            "offers": [
                {
                    "sellerId": o.get("SellerId"),
                    "condition": o.get("SubCondition"),
                    "listingPrice": o.get("ListingPrice", {}),
                    "shipping": o.get("Shipping", {}),
                    "isFba": o.get("IsFulfilledByAmazon"),
                    "isBuyBoxWinner": o.get("IsBuyBoxWinner"),
                    "isFeaturedMerchant": o.get("IsFeaturedMerchant"),
                }
                for o in offers[:20]
            ],
        }
        return to_json(result)
    except Exception as e:
        logger.error("Error en get_competitor_offers: %s", e)
        return to_json({"error": str(e)})


def register(mcp):
    mcp.tool()(get_competitive_pricing)
    mcp.tool()(get_competitor_offers)
