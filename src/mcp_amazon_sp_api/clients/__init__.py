"""Clientes SP-API organizados por scope."""

from .base import BaseClient, throttle_retry, load_all_pages
from .orders import OrdersClient
from .catalog import CatalogClient
from .finances import FinancesClient
from .fees import FeesClient
from .listings import ListingsClient
from .reports_base import ReportsBaseClient
from .reports_brand_analytics import BrandAnalyticsClient
from .reports_fba import FbaReportsClient
from .reports_sales import SalesReportsClient
from .inventory import InventoryClient
from .pricing import PricingClient
from .aplus_content import AplusContentClient
from .pricing_cross import CrossMarketplacePricingClient
from .competitor_analysis import CompetitorAnalysisClient
from .listings_restrictions import ListingsRestrictionsClient
from .feeds import FeedsClient
from .fulfillment_inbound import FulfillmentInboundClient
from .messaging import MessagingClient
from .solicitations import SolicitationsClient
from .invoices import InvoicesClient
from .sales import SalesApiClient


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
