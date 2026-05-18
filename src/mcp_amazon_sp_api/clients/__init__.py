"""Clientes SP-API organizados por scope."""

from .aplus_content import AplusContentClient
from .base import BaseClient, load_all_pages, throttle_retry
from .catalog import CatalogClient
from .competitor_analysis import CompetitorAnalysisClient
from .feeds import FeedsClient
from .fees import FeesClient
from .finances import FinancesClient
from .fulfillment_inbound import FulfillmentInboundClient
from .inventory import InventoryClient
from .invoices import InvoicesClient
from .listings import ListingsClient
from .listings_restrictions import ListingsRestrictionsClient
from .messaging import MessagingClient
from .orders import OrdersClient
from .pricing import PricingClient
from .pricing_cross import CrossMarketplacePricingClient
from .reports_base import ReportsBaseClient
from .reports_brand_analytics import BrandAnalyticsClient
from .reports_fba import FbaReportsClient
from .reports_sales import SalesReportsClient
from .sales import SalesApiClient
from .solicitations import SolicitationsClient

__all__ = [
    "AmazonClient",
    "AplusContentClient",
    "BaseClient",
    "BrandAnalyticsClient",
    "CatalogClient",
    "CompetitorAnalysisClient",
    "CrossMarketplacePricingClient",
    "FbaReportsClient",
    "FeedsClient",
    "FeesClient",
    "FinancesClient",
    "FulfillmentInboundClient",
    "InventoryClient",
    "InvoicesClient",
    "ListingsClient",
    "ListingsRestrictionsClient",
    "MessagingClient",
    "OrdersClient",
    "PricingClient",
    "ReportsBaseClient",
    "SalesApiClient",
    "SalesReportsClient",
    "SolicitationsClient",
    "load_all_pages",
    "throttle_retry",
]


class AmazonClient(
    OrdersClient,
    CatalogClient,
    FinancesClient,
    FeesClient,
    ListingsClient,
    BrandAnalyticsClient,
    FbaReportsClient,
    SalesReportsClient,
    InventoryClient,
    PricingClient,
    AplusContentClient,
    CrossMarketplacePricingClient,
    CompetitorAnalysisClient,
    ListingsRestrictionsClient,
    FeedsClient,
    FulfillmentInboundClient,
    MessagingClient,
    SolicitationsClient,
    InvoicesClient,
    SalesApiClient,
):
    """Cliente unificado que expone todos los scopes de SP-API."""
    pass
