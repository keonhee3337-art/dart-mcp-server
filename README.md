# DART MCP Server

A custom [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that exposes Korean public company financial data from [DART](https://dart.fss.or.kr) (Korea Financial Supervisory Service) as tools for Claude Code and AI agents.

Built by **Keonhee Kim**, Business Administration student at Sungkyunkwan University (SKKU), South Korea.

**This is a moat.** Competitors building Korean financial AI tools need to integrate DART from scratch. This server is already built, tested, and connected to Claude Code.

---

## What It Does

This MCP server lets Claude Code (or any MCP-compatible AI agent) query real-time Korean stock market and corporate financial data directly in conversation — no browser, no manual API calls, no code changes required.

```
# In Claude Code:
> search DART for 삼성전자
→ corp_code: 00126380, stock_code: 005930 (KOSPI)

> get financials for Samsung Electronics, 2023
→ consolidated income statement, balance sheet, cash flow statement

> get recent disclosures for SK Hynix
→ last 10 DART filings with dates and direct DART URLs

> get company info for 00126380
→ CEO, address, industry, founded date, fiscal year end
```

---

## Tools

| Tool | Input | Returns |
|------|-------|---------|
| `search_company` | Company name (Korean or English) | corp_code, stock_code, KOSPI/KOSDAQ exchange |
| `get_financials` | corp_code + year + period | Income statement, balance sheet, cash flow (CFS/OFS) |
| `get_company_info` | corp_code | CEO, address, industry code, founded date, IR/website URL |
| `get_disclosures` | corp_code + date range | Recent filings: earnings, announcements, regulatory, with direct DART links |

**Supported companies:** All Korean public companies listed on KOSPI and KOSDAQ (~2,500+ companies).

**Data source:** Korea Financial Supervisory Service DART Open API (free, official government data).

---

## Architecture

```
Claude Code / AI Agent
    │
    │  MCP stdio transport
    ▼
DART MCP Server (server.py)
    │
    ├── search_company()    → dart_fss.get_corp_list().find_by_corp_name()
    ├── get_financials()    → corp.get_financial_statements(bsns_year, reprt_code)
    ├── get_company_info()  → corp.load() → company profile fields
    └── get_disclosures()   → dart.filings.search(corp_code, bgn_de, end_de)
    │
    ▼
DART FSS Open API (dart.fss.or.kr)
    │
    ▼
Official Korean corporate financial data
```

**Transport:** MCP stdio (standard input/output) — no HTTP server, no port conflicts, works with Claude Code's MCP config out of the box.

---

## Stack

- **MCP SDK** — `mcp` Python package (stdio transport, tool definitions)
- **dart-fss** — Python wrapper for DART FSS Open API
- **Python 3.10+**
- **~300 lines of Python** — demonstrates how compact a fully functional MCP server can be

---

## Setup

### 1. Get a DART API Key (free)

Register at [opendart.fss.or.kr](https://opendart.fss.or.kr) → 신청/인증 (Application/Authentication) → API Key issuance.
Approval is typically same-day for Korean applicants.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add to Claude Code `.mcp.json`

```json
{
  "mcpServers": {
    "dart": {
      "command": "python3",
      "args": ["/absolute/path/to/dart-mcp-server/server.py"],
      "env": {
        "DARTFSS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### 4. Reload Claude Code

The `dart` MCP server appears in `/mcp` status as **connected**. All four tools are immediately available.

---

## Usage Examples

```bash
# Find a company's corp_code first
search DART for 삼성전자
search DART for SK하이닉스
search DART for 카카오

# Get financial statements
get financials for corp_code 00126380, year 2023
get financials for 00126380, year 2022, report_type q3

# Company profile
get company info for 00126380

# Recent filings
get recent disclosures for 00126380
get disclosures for 00126380 since 20240101
```

---

## Notes

- **Korean names work best:** `삼성전자` returns more precise results than `Samsung Electronics`
- **corp_code is the primary key:** 8-digit DART identifier. Always run `search_company` first to get it.
- **CFS vs OFS:** The server tries consolidated financial statements (CFS) first, falls back to standalone (OFS) if consolidated is unavailable
- **Rate limits:** Free DART API key has rate limits. For bulk queries, add delays between calls.
- **Data availability:** Not all companies have all years/periods available via the API

---

## Why I Built This

General AI tools (Claude, ChatGPT, Gemini) don't have access to real-time Korean corporate financial data. This server fills that gap.

The broader lesson: **any data source can become an AI tool through MCP**. The pattern here — a Python server exposing an external API as structured tools for Claude Code — applies to any domain: regulatory databases, proprietary datasets, internal systems.

For the Korean market specifically, DART is the authoritative source for all public company financials, disclosures, and corporate actions. Having it as an AI-native tool opens workflows that previously required manual web browsing of the DART portal.

---

## Related Projects

- **FinAgent** — Multi-agent financial analysis system (LangGraph + RAG + Text2SQL). Uses Korean financial data as a core data source. [Live demo](https://keonhee-finagent.streamlit.app) · [GitHub](https://github.com/keonhee3337-art/FinAgent)
- **DART Financial App** — Samsung Electronics data via DART API → SQLite → RAG → GPT-4o → Streamlit. [Live demo](https://keonhee-strategy.streamlit.app)

---

## About

**Keonhee Kim** — Business Administration, Sungkyunkwan University (SKKU), South Korea.

Builds agentic AI systems with Korean market focus: LangGraph pipelines, RAG, custom MCP servers, FastAPI backends. This project demonstrates custom MCP tooling — turning any structured data source into an AI-native tool with minimal code.

**Stack:** Python · MCP SDK · dart-fss · DART FSS API · LangGraph · RAG

[GitHub](https://github.com/keonhee3337-art) · [FinAgent demo](https://keonhee-finagent.streamlit.app)

---

## License

MIT
