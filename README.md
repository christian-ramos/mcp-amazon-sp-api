# mcp-amazon-sp-api

MCP server that exposes the [Amazon Selling Partner API](https://developer-docs.amazon.com/sp-api/) to [Claude Desktop](https://claude.ai/download) and any other client that speaks the [Model Context Protocol](https://modelcontextprotocol.io/).

It wraps the [`python-amazon-sp-api`](https://github.com/saleweaver/python-amazon-sp-api) SDK and ships **55+ tools** across 19 SP-API scopes — catalog, orders, listings, reports, inventory, pricing, A+ content, feeds, fulfillment, messaging and more — with automatic pagination, throttle-aware retry and multi-marketplace support.

> Status: production-ready, used daily against the live SP-API. ~400 unit and integration tests, ~95% coverage.

---

## Features

- **55+ MCP tools** covering 19 SP-API scopes (see [Tool catalogue](#tool-catalogue)).
- **Multi-marketplace.** Every tool accepts a `marketplace` parameter (`ES`, `DE`, `FR`, `IT`, `GB`, `NL`, `BE`, `PL`, `SE`, `IE`, `US`, `AE`, `SA`). When omitted, falls back to `SP_API_MARKETPLACE` from `.env`.
- **Safe writes.** Mutating tools require `confirm=True`; without it they return a detailed plan preview so the agent can show the user what would happen.
- **Automatic pagination** on inventory, listings, finances, orders and catalog endpoints.
- **Throttle-aware retry** with exponential backoff for all SP-API calls.
- **Reports pipeline** (create → poll → download → parse) for Brand Analytics, FBA reports and Sales & Traffic.
- **Bulk updates** via `JSON_LISTINGS_FEED` for price/inventory.
- **Credential resolution** order: environment variables → macOS Keychain → `.env`.

## Requirements

- Python ≥ 3.12
- [`uv`](https://docs.astral.sh/uv/) (recommended) or any PEP 517 installer
- Amazon SP-API developer credentials (LWA app + refresh token)

## Installation

```bash
git clone https://github.com/christian-ramos/mcp-amazon-sp-api.git
cd mcp-amazon-sp-api
uv sync
```

`uv sync` will create `.venv/` and install the runtime dependencies declared in `pyproject.toml`. For development extras (pytest, ruff):

```bash
uv sync --group dev
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```dotenv
SP_API_REFRESH_TOKEN=Atzr|...
LWA_APP_ID=amzn1.application-oa2-client...
LWA_CLIENT_SECRET=...
SP_API_SELLER_ID=...
SP_API_MARKETPLACE=ES
```

To obtain these:

1. In Seller Central, go to **Apps & Services → Develop Apps**.
2. Create (or open) your SP-API application and authorize it for your seller account.
3. Note the **LWA client ID** and **LWA client secret**.
4. Generate a **refresh token** by self-authorizing the app for your seller account.
5. Copy your **Seller ID** from **Settings → Account Info → Your Merchant Token**.

### Storing credentials in macOS Keychain (optional)

If you prefer not to keep secrets on disk, store them in the Keychain — the server will pick them up automatically:

```bash
security add-generic-password -s mcp-amazon-sp-api -a SP_API_REFRESH_TOKEN -w 'Atzr|...'
security add-generic-password -s mcp-amazon-sp-api -a LWA_APP_ID -w 'amzn1.application-oa2-client...'
security add-generic-password -s mcp-amazon-sp-api -a LWA_CLIENT_SECRET -w '...'
```

Resolution order is: environment variables → Keychain → `.env`.

## Running

### As a Claude Desktop MCP server

Add the following to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or the equivalent on your platform:

```json
{
  "mcpServers": {
    "amazon-sp-api": {
      "command": "uv",
      "args": [
        "--directory", "/absolute/path/to/mcp-amazon-sp-api",
        "run", "mcp-amazon-sp-api"
      ]
    }
  }
}
```

Restart Claude Desktop. The 55+ tools will appear under the `amazon-sp-api` server.

### Standalone (for debugging)

```bash
uv run mcp-amazon-sp-api
```

This speaks MCP over stdio; you will need an MCP client on the other end (the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is great for this).

## Tool catalogue

Tools are grouped by scope. See `src/mcp_amazon_sp_api/tool_docs.py` for the full per-tool documentation that Claude reads at runtime via the `tool-docs://` MCP resource.

| Scope | Tools |
|---|---|
| Catalog & Orders | `list_products`, `get_product_details`, `get_orders`, `get_order_items` |
| Analytics | `get_sales_summary`, `get_returns_summary`, `get_order_finances`, `estimate_fees`, `get_profitability_report`, `get_sales_rankings` |
| Listings | `get_listing_content`, `list_my_listings`, `get_listing_issues`, `get_product_type_info`, `update_listing_attribute`, `update_listing_batch` |
| Reports infra | `request_report`, `check_report`, `download_report` |
| Brand Analytics | `get_search_terms`, `get_search_performance`, `get_market_basket`, `get_repeat_purchases` |
| FBA Reports | `get_fba_inventory`, `get_fba_returns`, `get_fba_fees_report`, `get_restock_suggestions` |
| Sales & Traffic | `get_sales_and_traffic` |
| Inventory (realtime) | `get_inventory` |
| Pricing | `get_competitive_pricing`, `get_competitor_offers` |
| A+ Content | `list_aplus_content`, `get_aplus_content`, `get_aplus_asin_relations` |
| Pricing cross-marketplace | `get_cross_marketplace_prices`, `update_marketplace_price`, `sync_marketplace_prices` |
| Competitor analysis | `analyze_competitor_prices`, `compare_with_competitors` |
| Listings restrictions | `check_listing_restrictions`, `check_expansion_eligibility` |
| Feeds | `bulk_update_prices`, `check_feed` |
| Fulfillment inbound | `list_fba_shipments`, `get_fba_shipment_items`, `get_inbound_guidance` |
| Messaging | `get_messaging_options`, `send_buyer_message` |
| Solicitations | `check_review_eligibility`, `request_review` |
| Invoices | `get_invoices`, `download_invoice` |
| Sales API | `get_order_metrics` |

## Development

```bash
uv sync --group dev          # install with dev deps
uv run pytest tests/unit     # unit tests (no SP-API credentials needed)
uv run pytest -m integration # integration tests (require live credentials)
uv run ruff check .          # lint
```

Project layout:

```
src/mcp_amazon_sp_api/
├── server.py          # FastMCP entry point — registers all tool packages
├── config.py          # Credentials resolution and marketplace map
├── sp_client.py       # Re-export of clients/
├── clients/           # One module per SP-API scope (BaseClient + mixins)
├── tools/             # MCP tool implementations, grouped by scope
└── tool_docs.py       # Per-tool detailed docs exposed via tool-docs:// resource
```

See [`ROADMAP.md`](ROADMAP.md) for the implementation history and per-phase scope.

## Security notes

- This server holds **production seller credentials** with full SP-API access. Treat `.env` like a password file — never commit it.
- Write tools (`update_listing_attribute`, `update_listing_batch`, `update_marketplace_price`, `sync_marketplace_prices`, `bulk_update_prices`, `send_buyer_message`, `request_review`) **require `confirm=True`**. Without confirmation they return a plan preview rather than executing.
- All requests honour SP-API rate limits via throttle-aware retry.

## Disclaimer

This project is not affiliated with, endorsed by, or supported by Amazon.com, Inc. Trademarks belong to their respective owners.

## License

[MIT](LICENSE) © Christian Ramos
