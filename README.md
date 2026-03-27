# FRED MCP Server

A [FastMCP](https://gofastmcp.com) server that exposes [FRED](https://fred.stlouisfed.org/) (Federal Reserve Economic Data) API as MCP tools.

## Tools

| Tool | Description |
|------|-------------|
| `search_series` | Search FRED for economic data series by keyword |
| `get_series` | Get metadata for a specific FRED series |
| `get_observations` | Get time series observations (data points) |
| `get_category` | Get info about a FRED category |
| `get_category_children` | List child categories |

## Setup

### 1. Get a FRED API Key

Register at [fredaccount.stlouisfed.org](https://fredaccount.stlouisfed.org) and request an API key.

### 2. Install

```bash
uv sync
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your FRED_API_KEY
```

### 4. Run locally

```bash
uv run fred-mcp
```

## Usage with Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "fred": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--directory", "/path/to/Fred", "fred-mcp"],
      "env": {
        "FRED_API_KEY": "your_key_here"
      }
    }
  }
}
```

## Deploy to Prefect Horizon

1. Push this repo to GitHub
2. Go to [horizon.prefect.io](https://horizon.prefect.io)
3. Connect your GitHub account
4. Select this repository
5. Set `FRED_API_KEY` as an environment variable
6. Deploy — auto-redeploys on push to `main`

## Popular FRED Series

- `GDP` — Gross Domestic Product
- `UNRATE` — Unemployment Rate
- `CPIAUCSL` — Consumer Price Index
- `DFF` — Federal Funds Rate
- `SP500` — S&P 500 Index
- `T10Y2Y` — 10-Year minus 2-Year Treasury Spread

## FRED API Reference

- [API Docs](https://fred.stlouisfed.org/docs/api/fred/)
- Rate limit: 120 requests/minute
