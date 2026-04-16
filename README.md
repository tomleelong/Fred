# FRED MCP Server

A [Cloudflare Workers](https://developers.cloudflare.com/workers/) remote MCP server that exposes [FRED](https://fred.stlouisfed.org/) (Federal Reserve Economic Data) as MCP tools.

## Tools

| Tool | Description |
|------|-------------|
| `search_series` | Search FRED for economic data series by keyword |
| `get_series` | Get metadata for a specific FRED series |
| `get_observations` | Get time series observations (data points) |
| `get_category` | Get info about a FRED category |
| `get_category_children` | List child categories |

## Setup

### 1. Get a FRED API key

Register at [fredaccount.stlouisfed.org](https://fredaccount.stlouisfed.org) and request an API key (32-char alphanumeric).

### 2. Install

```bash
npm install
```

### 3. Local development

Create `.dev.vars` from the example and set your key:

```bash
cp .dev.vars.example .dev.vars
# edit .dev.vars — FRED_API_KEY=your_key_here
npm run dev
```

The worker serves on `http://localhost:8787`:

- `POST /mcp` — streamable HTTP MCP transport (preferred)
- `GET  /sse` — legacy SSE transport

Smoke-test with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
# Connect to http://localhost:8787/mcp
```

## Deploy

```bash
# Set the production secret (one-time)
npx wrangler secret put FRED_API_KEY

# Deploy
npm run deploy
```

Wrangler prints the production URL, e.g. `https://fred-mcp.<account>.workers.dev`.

## Connect from Claude.ai

Add a custom connector pointing at `https://fred-mcp.<account>.workers.dev/mcp`.

## Popular FRED series

- `GDP` — Gross Domestic Product
- `UNRATE` — Unemployment Rate
- `CPIAUCSL` — Consumer Price Index
- `DFF` — Federal Funds Rate
- `SP500` — S&P 500 Index
- `T10Y2Y` — 10-Year minus 2-Year Treasury Spread

## FRED API reference

- [API Docs](https://fred.stlouisfed.org/docs/api/fred/)
- Rate limit: 120 requests/minute
