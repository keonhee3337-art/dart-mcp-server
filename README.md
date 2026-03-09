# DART MCP Server

A custom [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that exposes Korean public company financial data from [DART](https://dart.fss.or.kr) (Financial Supervisory Service Open API) as tools for Claude Code and AI agents.

Built by a SKKU Business Administration student to demonstrate custom MCP tooling with Korean market domain knowledge.

## What It Does

This MCP server lets Claude (or any MCP-compatible agent) query real Korean stock market data directly in conversation — no browser, no manual API calls.

```
> search DART for 삼성전자
→ corp_code: 00126380, stock_code: 005930 (KOSPI)

> get financials for Samsung, 2023
→ consolidated income statement, balance sheet, cash flow

> get recent disclosures for SK Hynix
→ last 10 filings with dates and DART URLs
```

## Tools

| Tool | Description |
|------|-------------|
| `search_company` | Search Korean public companies by name (Korean or English) |
| `get_financials` | Get income statement / balance sheet for a given year |
| `get_company_info` | Company profile: CEO, address, industry, founded date |
| `get_disclosures` | Recent DART filings: earnings, announcements, regulatory |

## Stack

- **MCP SDK** — `mcp` Python package (stdio transport)
- **dart-fss** — Python wrapper for DART FSS Open API
- **Python 3.10+**

## Setup

### 1. Get a DART API Key

Register at [https://opendart.fss.or.kr](https://opendart.fss.or.kr) → API Key issuance (free).

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set environment variable

```bash
export DARTFSS_API_KEY=your_api_key_here
```

### 4. Add to Claude Code `.mcp.json`

```json
{
  "mcpServers": {
    "dart": {
      "command": "python3",
      "args": ["/path/to/dart-mcp-server/server.py"],
      "env": {
        "DARTFSS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### 5. Reload Claude Code

The `dart` MCP server will appear in `/mcp` status as **connected**.

## Usage Examples

```
# Search
search DART for 삼성전자
search DART for SK하이닉스

# Financials
get financials for corp_code 00126380, year 2023

# Company profile
get company info for 00126380

# Disclosures
get recent disclosures for 00126380
```

## Notes

- DART search works best with Korean company names (`삼성전자` not `Samsung Electronics`)
- `corp_code` is the 8-digit DART identifier — get it from `search_company` first
- Financial data availability depends on DART's API; not all years/periods are available for all companies
- Free DART API key has rate limits — use responsibly

## Why I Built This

Standard AI tools don't have access to real-time Korean financial disclosures. This fills that gap — a Claude Code tool that can look up Samsung's latest earnings or check if SK Hynix filed anything this quarter, directly in conversation.

It also demonstrates the MCP pattern: any data source can become an AI tool with ~300 lines of Python.

## License

MIT
