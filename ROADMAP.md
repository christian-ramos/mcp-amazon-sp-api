# MCP Amazon SP-API — Roadmap de implementación

MCP server en Python que conecta Amazon Seller Central (España) con Claude Desktop.
Pensado para vendedores que operan en uno o varios marketplaces de Amazon (EU/US) con catálogo en FBA y/o FBM.

## Estado actual

**Fases completadas:** 1 (Base), 2 (Análisis), 4 (Listings), 5 (Reports: Brand Analytics), 6 (Reports: FBA), 7 (Reports: Ventas y Tráfico), 8 (Inventario), 9 (Precios y competencia), 10 (A+ Content), 11 (Precios cross-marketplace), 12 (Análisis de competencia), 13 (Listings Restrictions), 14 (Feeds), 15 (Fulfillment Inbound), 16 (Messaging), 17 (Solicitations), 18 (Invoices), 19 (Sales API)

**55 MCP tools operativas**, 397 tests unitarios + integración sandbox, 95% cobertura.

### Arquitectura

```
src/mcp_amazon_sp_api/
├── config.py                    # SpApiConfig, load_config(), constantes marketplace
├── server.py                    # FastMCP server + 16 tools (entry point)
├── sp_client.py                 # Re-export de clients/
└── clients/
    ├── __init__.py              # AmazonClient (herencia múltiple de todos los scopes)
    ├── base.py                  # BaseClient + throttle_retry + load_all_pages
    ├── orders.py                # OrdersClient (get_orders, get_order_items)
    ├── catalog.py               # CatalogClient (get_catalog_item, search_catalog_items)
    ├── finances.py              # FinancesClient (get_financial_events, get_financial_events_for_order)
    ├── fees.py                  # FeesClient (get_fees_estimate, get_my_fees_estimates)
    ├── listings.py              # ListingsClient (get/patch/search listing_item, product_type_definitions)
    ├── reports_base.py          # ReportsBaseClient (create/status/download report, request_and_download)
    ├── reports_brand_analytics.py # BrandAnalyticsClient (search terms, performance, basket, repeat, comparison)
    ├── reports_fba.py           # FbaReportsClient (inventory, health, returns, reimbursements, storage fees, restock)
    ├── reports_sales.py         # SalesReportsClient (sales & traffic by ASIN)
    ├── inventory.py             # InventoryClient (get_inventory_summary — stock en tiempo real)
    ├── pricing.py               # PricingClient (competitive pricing, item offers, product pricing)
    ├── aplus_content.py         # AplusContentClient (search, get document, ASIN relations)
    ├── pricing_cross.py         # CrossMarketplacePricingClient (precios multi-marketplace, sync estilo BIL)
    ├── competitor_analysis.py   # CompetitorAnalysisClient (buscar competidores, comparar precios)
    ├── listings_restrictions.py # ListingsRestrictionsClient (restricciones, elegibilidad expansión)
    ├── feeds.py                 # FeedsClient (submit feed, status, result, bulk prices/inventory)
    ├── fulfillment_inbound.py   # FulfillmentInboundClient (shipments, items, inbound guidance)
    ├── messaging.py             # MessagingClient (acciones de mensajería, enviar mensajes)
    ├── solicitations.py         # SolicitationsClient (solicitar reviews)
    ├── invoices.py              # InvoicesClient (facturas, documentos)
    └── sales.py                 # SalesApiClient (order metrics agregadas)

tests/
├── conftest.py                  # .env.test, sandbox env, skip_without_credentials
├── unit/
│   ├── test_config.py
│   ├── clients/                 # Un archivo por scope
│   │   ├── conftest.py          # fake_config, make_response, make_api_error
│   │   ├── test_base.py         # throttle_retry, load_all_pages
│   │   ├── test_orders.py
│   │   ├── test_catalog.py
│   │   ├── test_finances.py
│   │   ├── test_fees.py
│   │   └── test_listings.py
│   └── tools/                   # Un archivo por scope
│       ├── conftest.py          # mock_client autouse, parse()
│       ├── test_common.py       # _json helper
│       ├── test_tools_orders.py
│       ├── test_tools_catalog.py
│       ├── test_tools_finances.py
│       ├── test_tools_fees.py
│       └── test_tools_listings.py
└── integration/                 # Un archivo por scope, contra sandbox real
    ├── conftest.py              # client, listings_client fixtures
    ├── test_orders.py
    ├── test_catalog.py
    ├── test_finances.py
    ├── test_fees.py
    └── test_listings.py
```

### Convenciones establecidas

- **Un cliente por scope** en `clients/`, herencia múltiple en `AmazonClient`
- **Un archivo de test por scope** en `unit/clients/`, `unit/tools/`, e `integration/`
- Scopes grandes (como Reports) se dividen en **subscopes** (un cliente por subscope)
- Cada método del cliente: `@throttle_retry()`, try/except `SellingApiException`, log error, raise `RuntimeError`
- Cada tool MCP: try/except genérico, retorna JSON string con `_json()`, nunca lanza excepción
- `ensure_ascii=False` en JSON para caracteres españoles
- Logging a stderr (nunca stdout — corrompe protocolo MCP stdio)
- `.env.test` con `AWS_ENV=SANDBOX` y `SP_API_MARKETPLACE=US` para tests de integración

### Testing

- **Tests unitarios**: SP-API mockeada con `unittest.mock`, sin red
- **Tests de integración**: Contra sandbox real de SP-API, se saltan sin credenciales
- **Documentación sandbox**: https://developer-docs.amazon.com/sp-api/docs/sp-api-sandbox#the-selling-partner-api-static-sandbox
- **Test cases del sandbox**: Definidos en los modelos Swagger (`x-amzn-api-sandbox`) en https://github.com/amzn/selling-partner-api-models
- **Ejecutar**: `pytest tests/unit/` (rápido) | `pytest tests/integration/ -m integration` (sandbox) | `pytest tests/` (todo)

### Limitaciones conocidas de la librería python-amazon-sp-api (v2.1.8)

- **ProductFees sandbox**: La librería hardcodea `Identifier=ASIN` en `create_fees_body()`. El sandbox requiere un valor específico (`"UmaS1"`). En producción no afecta (Identifier es un correlation ID libre). Tests de integración usan `_request` directo.
- **search_listings_items sandbox**: La librería envía `identifiers` como lista Python en vez de comma-separated string. El sandbox no matchea. En producción funciona. Tests de integración usan `_request` directo.
- **Finances list_financial_events sandbox**: El test case requiere `NextToken="jehgri34yo7jr9e8f984tr9i4o"` — no acepta PostedAfter como parámetro único. El wrapper `get_financial_events` funciona en producción.

---

## Fases pendientes

### Fase 5: Reports — Brand Analytics

**Prioridad: Alta**
Brand Analytics da datos exclusivos de marca registrada que no se obtienen de otra API.

**Concepto clave**: Reports es asíncrono. El flujo es: crear informe → esperar → descargar. Esto afecta al diseño de las tools (necesitan polling o un enfoque request/download separado).

#### Subscope: reports_base (infraestructura)

**Cliente**: `clients/reports_base.py` → `ReportsBaseClient`

Métodos del cliente:
- `create_report(report_type, start_date, end_date, marketplace_ids?)` → `str` (reportId)
- `get_report_status(report_id)` → `dict` (status, reportDocumentId cuando DONE)
- `download_report(report_document_id)` → `str | dict` (contenido del informe)
- `request_and_download_report(report_type, start_date, end_date, poll_interval=15, timeout=300)` → helper que encapsula crear + poll + descargar

La librería usa: `Reports.create_report()`, `Reports.get_report()`, `Reports.get_report_document(download=True)`

Tools MCP:
- `request_report(report_type, days_back, ...)` → crea el informe y devuelve reportId + instrucciones
- `check_report(report_id)` → estado del informe
- `download_report(report_id)` → descarga si está listo

**Testing**:
- Unit: mockear create_report, get_report, get_report_document
- Integración sandbox: buscar test cases en `reports_2021-06-30.json` del repo de modelos

**Archivos**:
- `clients/reports_base.py`
- `tests/unit/clients/test_reports_base.py`
- `tests/unit/tools/test_tools_reports_base.py`
- `tests/integration/test_reports_base.py`

#### Subscope: reports_brand_analytics

**Cliente**: `clients/reports_brand_analytics.py` → `BrandAnalyticsClient` (hereda de `ReportsBaseClient`)

Métodos (wrappers de alto nivel que llaman a `request_and_download_report`):
- `get_search_terms_report(start_date, end_date)` → Top keywords con click share y conversion share
- `get_search_query_performance(start_date, end_date)` → Rendimiento por término de búsqueda (impresiones, clics, carrito, compras)
- `get_market_basket_report(start_date, end_date)` → Productos comprados juntos
- `get_repeat_purchase_report(start_date, end_date)` → Tasa de recompra por ASIN
- `get_item_comparison_report(start_date, end_date)` → ASINs con los que te comparan
- `get_alternate_purchase_report(start_date, end_date)` → Qué compran cuando no compran el tuyo

Report types:
```
GET_BRAND_ANALYTICS_SEARCH_TERMS_REPORT
GET_BRAND_ANALYTICS_SEARCH_QUERY_PERFORMANCE_REPORT
GET_BRAND_ANALYTICS_SEARCH_CATALOG_PERFORMANCE_REPORT
GET_BRAND_ANALYTICS_MARKET_BASKET_REPORT
GET_BRAND_ANALYTICS_REPEAT_PURCHASE_REPORT
GET_BRAND_ANALYTICS_ITEM_COMPARISON_REPORT
GET_BRAND_ANALYTICS_ALTERNATE_PURCHASE_REPORT
```

Tools MCP:
- `get_search_terms(days_back=30)` → keywords con mayor volumen + click/conversion share
- `get_search_performance(days_back=30)` → rendimiento de tus ASINs en búsquedas
- `get_market_basket(days_back=30)` → cross-sell analysis
- `get_repeat_purchases(days_back=30)` → fidelización
- `get_competitor_comparison(days_back=30)` → comparaciones y compras alternativas

**Archivos**:
- `clients/reports_brand_analytics.py`
- `tests/unit/clients/test_reports_brand_analytics.py`
- `tests/unit/tools/test_tools_brand_analytics.py`
- `tests/integration/test_brand_analytics.py`

---

### Fase 6: Reports — FBA e Inventario

**Prioridad: Alta**

#### Subscope: reports_fba

**Cliente**: `clients/reports_fba.py` → `FbaReportsClient`

Métodos:
- `get_fba_inventory_report()` → Stock actual en FBA por SKU (GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA)
- `get_fba_inventory_health()` → Salud del inventario: edad, exceso, restock (GET_FBA_FULFILLMENT_INVENTORY_HEALTH_DATA)
- `get_fba_returns_report(start_date, end_date)` → Devoluciones con motivo detallado (GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA)
- `get_fba_reimbursements(start_date, end_date)` → Reembolsos de Amazon FBA (GET_FBA_REIMBURSEMENTS_DATA)
- `get_fba_storage_fees()` → Tarifas de almacenamiento (GET_FBA_STORAGE_FEE_CHARGES_DATA)
- `get_fba_longterm_storage_fees()` → Tarifas de almacenamiento largo plazo (GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA)
- `get_restock_recommendations()` → Recomendaciones de restock (GET_RESTOCK_INVENTORY_RECOMMENDATIONS_REPORT)

Report types relevantes:
```
GET_FBA_MYI_UNSUPPRESSED_INVENTORY_DATA
GET_FBA_FULFILLMENT_INVENTORY_HEALTH_DATA
GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA
GET_FBA_REIMBURSEMENTS_DATA
GET_FBA_STORAGE_FEE_CHARGES_DATA
GET_FBA_FULFILLMENT_LONGTERM_STORAGE_FEE_CHARGES_DATA
GET_RESTOCK_INVENTORY_RECOMMENDATIONS_REPORT
GET_FBA_INVENTORY_AGED_DATA
GET_STRANDED_INVENTORY_UI_DATA
```

Tools MCP:
- `get_fba_inventory()` → stock actual con estado
- `get_fba_inventory_health()` → edad, exceso, stranded
- `get_fba_returns(days_back=30)` → devoluciones con motivos (complementa get_returns_summary de Finances)
- `get_fba_fees_report()` → tarifas almacenamiento actual + largo plazo
- `get_restock_suggestions()` → qué reabastecer y cuánto

**Archivos**:
- `clients/reports_fba.py`
- `tests/unit/clients/test_reports_fba.py`
- `tests/unit/tools/test_tools_fba.py`
- `tests/integration/test_fba.py`

---

### Fase 7: Reports — Ventas y Tráfico

**Prioridad: Media**

#### Subscope: reports_sales

**Cliente**: `clients/reports_sales.py` → `SalesReportsClient`

Métodos:
- `get_sales_and_traffic_report(start_date, end_date, granularity="DAY")` → sesiones, page views, Buy Box %, conversión, por ASIN y día (GET_SALES_AND_TRAFFIC_REPORT)

Tools MCP:
- `get_sales_and_traffic(days_back=30)` → métricas de rendimiento por ASIN (sesiones, conversión, Buy Box %)

**Nota**: La Sales API (`Sales.get_order_metrics`) también da métricas agregadas pero con menos detalle. Evaluar si es suficiente o si el informe da más valor.

**Archivos**:
- `clients/reports_sales.py`
- `tests/unit/clients/test_reports_sales.py`
- `tests/unit/tools/test_tools_sales.py`
- `tests/integration/test_sales.py`

---

### Fase 8: Inventario en tiempo real

**Prioridad: Media**

**Cliente**: `clients/inventory.py` → `InventoryClient`

Usa la Inventories API (no Reports — datos en tiempo real):
- `get_inventory_summary(skus?, granularity="Marketplace")` → stock disponible, inbound, reserved

Tools MCP:
- `get_inventory(sku="")` → stock actual por SKU o todos

**Archivos**:
- `clients/inventory.py`
- `tests/unit/clients/test_inventory.py`
- `tests/unit/tools/test_tools_inventory.py`
- `tests/integration/test_inventory.py`

---

### Fase 9: Precios y competencia

**Prioridad: Media**

**Cliente**: `clients/pricing.py` → `PricingClient`

Usa Products API V0:
- `get_competitive_pricing(asin_list)` → precios competitivos + Buy Box + sales rankings
- `get_item_offers(asin)` → todas las ofertas de otros vendedores para un ASIN
- `get_product_pricing(asin_list)` → tu precio vs competencia

Tools MCP:
- `get_competitive_pricing(asins)` → precios Buy Box, landed price, rankings
- `get_competitor_offers(asin)` → quién más vende este ASIN, a qué precio, FBA/FBM

**Archivos**:
- `clients/pricing.py`
- `tests/unit/clients/test_pricing.py`
- `tests/unit/tools/test_tools_pricing.py`
- `tests/integration/test_pricing.py`

---

### Fase 10: A+ Content

**Prioridad: Baja**

**Cliente**: `clients/aplus_content.py` → `AplusContentClient`

Usa AplusContent API:
- `search_content_documents(marketplace_id)` → listar documentos A+ existentes
- `get_content_document(content_reference_key)` → leer contenido A+
- `create_content_document(body)` → crear nuevo contenido A+
- `update_content_document(content_reference_key, body)` → actualizar
- `submit_for_approval(content_reference_key)` → enviar a aprobación
- `get_asin_relations(content_reference_key)` → ver qué ASINs usan este A+

Tools MCP:
- `list_aplus_content()` → ver documentos A+ existentes
- `get_aplus_content(content_key)` → leer detalle de un A+
- `get_aplus_asin_relations(content_key)` → qué ASINs usan este A+

**Nota**: Crear/editar A+ content es complejo (módulos con imágenes, layouts). Empezar solo con lectura; escritura como sub-fase posterior.

**Archivos**:
- `clients/aplus_content.py`
- `tests/unit/clients/test_aplus_content.py`
- `tests/unit/tools/test_tools_aplus.py`
- `tests/integration/test_aplus.py`

---

### Fase 11: Precios cross-marketplace

**Prioridad: Media**

Gestión de precios en múltiples marketplaces europeos desde Claude Desktop.
BIL (Build International Listings) de Seller Central no tiene API, pero se puede replicar su funcionalidad usando la Listings Items API para leer/actualizar precios por marketplace.

**Cliente**: `clients/pricing_cross.py` → `CrossMarketplacePricingClient`

Usa Listings Items API (ya disponible) + Products API:
- `get_prices_all_marketplaces(sku)` → precio actual del SKU en cada marketplace (ES, DE, FR, IT, etc.)
- `update_price(sku, product_type, price, marketplace)` → actualizar precio en un marketplace específico
- `sync_prices(sku, product_type, base_price, base_marketplace, target_marketplaces, adjustment_pct?)` → sincronizar precio base a otros marketplaces con ajuste opcional (%, fijo)
- `get_exchange_rates()` → tasas de cambio actuales (si aplica entre regiones)

Tools MCP:
- `get_cross_marketplace_prices(sku)` → ver precios del SKU en todos los marketplaces
- `update_marketplace_price(sku, product_type, price, marketplace)` → cambiar precio en un marketplace
- `sync_marketplace_prices(sku, product_type, base_price, targets, adjustment_pct)` → sincronizar precios estilo BIL

**Nota**: Dentro de la UE todos los marketplaces usan EUR (excepto UK/SE/PL). La sincronización es directa sin conversión de divisa en la mayoría de casos.

**Archivos**:
- `clients/pricing_cross.py`
- `tests/unit/clients/test_pricing_cross.py`
- `tests/unit/tools/test_tools_pricing_cross.py`
- `tests/integration/test_pricing_cross.py`

---

### Fase 12: Análisis de competencia

**Prioridad: Alta**

Buscar productos similares de la competencia y comparar precios, rankings y fulfillment.
Combina Catalog Items API (búsqueda) + Products Pricing API (precios de cada ASIN encontrado).

**Cliente**: `clients/competitor_analysis.py` → `CompetitorAnalysisClient`

Métodos:
- `analyze_competitor_prices(keywords, max_results=10)` → busca ASINs similares, obtiene precio, Buy Box, FBA/FBM, ranking
- `compare_with_competitors(my_asin, keywords, max_results=10)` → lo anterior + incluye tu ASIN como referencia para comparar

Tools MCP:
- `analyze_competitor_prices(keywords, max_results)` → resumen comparativo: ASINs, precios, rankings, FBA/FBM
- `compare_with_competitors(my_asin, keywords, max_results)` → tu producto vs competidores

**Archivos**:
- `clients/competitor_analysis.py`
- `tests/unit/clients/test_competitor_analysis.py`
- `tests/unit/tools/test_tools_competitor_analysis.py`
- `tests/integration/test_competitor_analysis.py`

---

### Fase 13: Listings Restrictions

**Prioridad: Media**

Verificar si puedes vender un ASIN en un marketplace antes de expandirte.

**Cliente**: `clients/listings_restrictions.py` → `ListingsRestrictionsClient`

Usa Listings Restrictions API:
- `get_listings_restrictions(asin, condition_type?)` → restricciones para vender un ASIN en tu marketplace
- `check_expansion_eligibility(asin, target_marketplaces)` → verificar elegibilidad en múltiples marketplaces

Tools MCP:
- `check_listing_restrictions(asin, condition)` → ver si puedes vender un ASIN
- `check_expansion_eligibility(asin, marketplaces)` → elegibilidad en otros marketplaces

**Archivos**:
- `clients/listings_restrictions.py`
- `tests/unit/clients/test_listings_restrictions.py`
- `tests/unit/tools/test_tools_listings_restrictions.py`
- `tests/integration/test_listings_restrictions.py`

---

### Fase 14: Feeds (actualizaciones masivas)

**Prioridad: Media**

Actualizaciones en bulk de precios, stock o listings usando Feeds API.
Similar a Reports pero para escritura: crear feed → subir contenido → esperar procesamiento.

**Cliente**: `clients/feeds.py` → `FeedsClient`

Usa Feeds API:
- `create_feed(feed_type, content)` → crear feed y subir contenido
- `get_feed_status(feed_id)` → estado del feed
- `get_feed_result(feed_id)` → resultado del procesamiento (errores/éxitos por item)
- `bulk_update_prices(updates)` → wrapper: actualizar precios de múltiples SKUs de una vez
- `bulk_update_inventory(updates)` → wrapper: actualizar stock de múltiples SKUs

Feed types relevantes:
```
POST_FLAT_FILE_PRICEANDQUANTITYONLY_UPDATE_DATA — precios y stock
POST_FLAT_FILE_LISTINGS_DATA — crear/actualizar listings
JSON_LISTINGS_FEED — listings en formato JSON (moderno)
```

Tools MCP:
- `bulk_update_prices(updates_json)` → actualizar precios de varios SKUs a la vez
- `check_feed(feed_id)` → estado y resultado de un feed

**Archivos**:
- `clients/feeds.py`
- `tests/unit/clients/test_feeds.py`
- `tests/unit/tools/test_tools_feeds.py`
- `tests/integration/test_feeds.py`

---

### Fase 15: Fulfillment Inbound (envíos a FBA)

**Prioridad: Media**

Gestionar envíos de inventario a los almacenes FBA.

**Cliente**: `clients/fulfillment_inbound.py` → `FulfillmentInboundClient`

Usa Fulfillment Inbound API:
- `list_inbound_shipments(status?)` → listar envíos entrantes con estado
- `get_shipment_items(shipment_id)` → items de un envío específico
- `get_inbound_guidance(asin_list)` → recomendaciones de envío por ASIN

Tools MCP:
- `list_fba_shipments(status)` → ver envíos a FBA y su estado
- `get_fba_shipment_items(shipment_id)` → detalle de items en un envío
- `get_inbound_guidance(asins)` → guía de envío por ASIN (elegibilidad, prep)

**Archivos**:
- `clients/fulfillment_inbound.py`
- `tests/unit/clients/test_fulfillment_inbound.py`
- `tests/unit/tools/test_tools_fulfillment_inbound.py`
- `tests/integration/test_fulfillment_inbound.py`

---

### Fase 16: Messaging (mensajes a compradores)

**Prioridad: Media**

Enviar mensajes permitidos a compradores (confirmación envío, solicitar info, etc.).

**Cliente**: `clients/messaging.py` → `MessagingClient`

Usa Messaging API:
- `get_messaging_actions(order_id)` → acciones de mensajería disponibles para un pedido
- `send_message(order_id, message_type, body)` → enviar mensaje al comprador

Tipos de mensaje útiles:
- Confirmación de envío
- Solicitud de información del comprador
- Mensaje de cortesía post-venta

Tools MCP:
- `get_messaging_options(order_id)` → ver qué mensajes puedes enviar para un pedido
- `send_buyer_message(order_id, message_type, body)` → enviar mensaje

**Archivos**:
- `clients/messaging.py`
- `tests/unit/clients/test_messaging.py`
- `tests/unit/tools/test_tools_messaging.py`
- `tests/integration/test_messaging.py`

---

### Fase 17: Solicitations (solicitar reviews)

**Prioridad: Media**

Solicitar reviews de producto y feedback del vendedor a compradores.

**Cliente**: `clients/solicitations.py` → `SolicitationsClient`

Usa Solicitations API:
- `get_solicitation_actions(order_id)` → ver qué solicitudes puedes enviar
- `create_product_review_solicitation(order_id)` → solicitar review de producto

Tools MCP:
- `check_review_eligibility(order_id)` → ver si puedes solicitar review para un pedido
- `request_review(order_id)` → enviar solicitud de review

**Nota**: Amazon limita a 1 solicitud por pedido, entre 5 y 30 días después de la entrega.

**Archivos**:
- `clients/solicitations.py`
- `tests/unit/clients/test_solicitations.py`
- `tests/unit/tools/test_tools_solicitations.py`
- `tests/integration/test_solicitations.py`

---

### Fase 18: Invoices (facturación)

**Prioridad: Baja**

Gestión de facturas de pedidos.

**Cliente**: `clients/invoices.py` → `InvoicesClient`

Usa Invoices API:
- `get_invoices(order_id?)` → obtener facturas
- `get_invoice_document(invoice_id)` → descargar documento de factura

Tools MCP:
- `get_invoices(order_id)` → ver facturas de un pedido
- `download_invoice(invoice_id)` → descargar factura

**Archivos**:
- `clients/invoices.py`
- `tests/unit/clients/test_invoices.py`
- `tests/unit/tools/test_tools_invoices.py`
- `tests/integration/test_invoices.py`

---

### Fase 19: Sales API (métricas agregadas)

**Prioridad: Baja**

Alternativa ligera a Sales & Traffic Reports para métricas de ventas sin esperar informes.

**Cliente**: `clients/sales.py` → `SalesClient`

Usa Sales API:
- `get_order_metrics(interval, granularity)` → ventas agregadas por día/semana/mes

Tools MCP:
- `get_order_metrics(days_back, granularity)` → métricas de ventas sin esperar informes

**Archivos**:
- `clients/sales.py`
- `tests/unit/clients/test_sales_api.py`
- `tests/unit/tools/test_tools_sales_api.py`
- `tests/integration/test_sales_api.py`

---

### Fase 20: Notificaciones (opcional)

**Prioridad: Baja**

**Cliente**: `clients/notifications.py` → `NotificationsClient`

Requiere infraestructura AWS (SQS/EventBridge) para recibir notificaciones.

Tipos útiles:
- `BRANDED_ITEM_CONTENT_CHANGE` — cambios en listings de tu marca
- `ITEM_PRODUCT_TYPE_CHANGE` — cambios de product type
- `LISTINGS_ITEM_STATUS_CHANGE` — cambios de estado de listing
- `PRICING_HEALTH` — alertas de precio
- `FBA_OUTBOUND_SHIPMENT_STATUS` — estado de envíos FBA

**Nota**: Requiere setup de destinos AWS. Solo implementar si se necesita monitoreo en tiempo real.

---

## Resumen de prioridades

| Fase | Scope | Prioridad | Dependencias |
|------|-------|-----------|-------------|
| 5 | Reports: Brand Analytics | Alta | reports_base |
| 6 | Reports: FBA e Inventario | Alta | reports_base |
| 7 | Reports: Ventas y Tráfico | Media | reports_base |
| 8 | Inventario en tiempo real | Media | ninguna |
| 9 | Precios y competencia | Media | ninguna |
| 10 | A+ Content | Baja | ninguna |
| 11 | Precios cross-marketplace | Media | Listings (Fase 4) |
| 12 | Análisis de competencia | Alta | Catalog (Fase 1) + Pricing (Fase 9) |
| 13 | Listings Restrictions | Media | ninguna |
| 14 | Feeds (bulk updates) | Media | ninguna |
| 15 | Fulfillment Inbound | Media | ninguna |
| 16 | Messaging | Media | Orders (Fase 1) |
| 17 | Solicitations | Media | Orders (Fase 1) |
| 18 | Invoices | Baja | Orders (Fase 1) |
| 19 | Sales API | Baja | ninguna |
| 20 | Notificaciones | Baja | AWS SQS/EventBridge |

**Fase 12 es la siguiente**: alta prioridad, combina APIs ya implementadas.

## Patrón de implementación por fase

Para cada fase, seguir estos pasos:

1. **Investigar sandbox**: Descargar el modelo Swagger del endpoint desde https://github.com/amzn/selling-partner-api-models y buscar `x-amzn-api-sandbox` para encontrar los test cases exactos (parámetros de request y response)
2. **Verificar librería**: Comprobar firmas y comportamiento de `python-amazon-sp-api` para el endpoint. La librería puede añadir params extra que rompan el sandbox (documentar si ocurre)
3. **Cliente** (`clients/{scope}.py`): Implementar métodos con `@throttle_retry()`, error handling, logging
4. **Registrar en AmazonClient** (`clients/__init__.py`): Añadir herencia del nuevo client
5. **Tools MCP** (`server.py`): Añadir tools con try/except, `_json()`, docstrings con Args
6. **Tests unitarios**: `tests/unit/clients/test_{scope}.py` + `tests/unit/tools/test_tools_{scope}.py`
7. **Tests de integración**: `tests/integration/test_{scope}.py` con params exactos del sandbox
8. **Verificar**: `pytest tests/ --cov` — mantener cobertura ≥ 95%
