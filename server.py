"""
DART MCP Server
Exposes DART (Data Analysis, Retrieval and Transfer) financial data
for Korean public companies as MCP tools usable by Claude Code.

Tools:
  - search_company      : search for a Korean public company by name
  - get_financials      : get financial statements for a company
  - get_company_info    : get basic company profile
  - get_disclosures     : get recent DART disclosure filings
"""

import asyncio
import os
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import dart_fss as dart

# --- Init ---
app = Server("dart-mcp")

def get_api_key():
    key = os.getenv("DARTFSS_API_KEY") or os.getenv("DART_API_KEY")
    if not key:
        raise ValueError("DARTFSS_API_KEY not set in environment")
    return key


# --- Tool definitions ---

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_company",
            description=(
                "Search for a Korean public company by name in the DART system. "
                "Returns corp_code (used for other tools), company name, stock code, and exchange. "
                "Example: search_company('삼성전자') or search_company('Samsung Electronics')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Company name to search (Korean or English)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_financials",
            description=(
                "Get financial statements for a Korean public company from DART. "
                "Returns income statement, balance sheet, or cash flow data for a given year. "
                "Requires corp_code from search_company. "
                "Example: get_financials(corp_code='00126380', year=2023, report_type='annual')"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "corp_code": {
                        "type": "string",
                        "description": "8-digit DART corp_code from search_company"
                    },
                    "year": {
                        "type": "integer",
                        "description": "Fiscal year (e.g. 2023)"
                    },
                    "report_type": {
                        "type": "string",
                        "enum": ["annual", "q1", "q2", "q3"],
                        "description": "Report period. Default: annual",
                        "default": "annual"
                    }
                },
                "required": ["corp_code", "year"]
            }
        ),
        Tool(
            name="get_company_info",
            description=(
                "Get basic company profile from DART: founded date, CEO, address, industry, "
                "fiscal year end, stock exchange, website. "
                "Requires corp_code from search_company."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "corp_code": {
                        "type": "string",
                        "description": "8-digit DART corp_code from search_company"
                    }
                },
                "required": ["corp_code"]
            }
        ),
        Tool(
            name="get_disclosures",
            description=(
                "Get recent DART disclosure filings for a Korean public company. "
                "Returns filing type, date, title, and URL. "
                "Useful for tracking earnings releases, major announcements, regulatory filings. "
                "Requires corp_code from search_company."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "corp_code": {
                        "type": "string",
                        "description": "8-digit DART corp_code from search_company"
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYYMMDD format (default: 90 days ago)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max number of filings to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["corp_code"]
            }
        ),
    ]


# --- Tool handlers ---

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        dart.set_api_key(get_api_key())

        if name == "search_company":
            return await _search_company(arguments)
        elif name == "get_financials":
            return await _get_financials(arguments)
        elif name == "get_company_info":
            return await _get_company_info(arguments)
        elif name == "get_disclosures":
            return await _get_disclosures(arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except ValueError as e:
        return [TextContent(type="text", text=f"Configuration error: {e}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


async def _search_company(args: dict) -> list[TextContent]:
    query = args["query"]
    corp_list = dart.get_corp_list()
    results = corp_list.find_by_corp_name(query, exactly=False)

    if not results:
        return [TextContent(type="text", text=f"No companies found matching '{query}'")]

    output = []
    for corp in results[:10]:  # cap at 10 results
        output.append({
            "corp_code": corp.corp_code,
            "corp_name": corp.corp_name,
            "stock_code": getattr(corp, "stock_code", None),
            "modify_date": getattr(corp, "modify_date", None),
        })

    return [TextContent(type="text", text=json.dumps(output, ensure_ascii=False, indent=2))]


async def _get_financials(args: dict) -> list[TextContent]:
    corp_code = args["corp_code"]
    year = args["year"]
    report_type = args.get("report_type", "annual")

    period_map = {
        "annual": "11011",
        "q1": "11013",
        "q2": "11012",
        "q3": "11014",
    }
    reprt_code = period_map.get(report_type, "11011")

    corp_list = dart.get_corp_list()
    corp = corp_list.find_by_corp_code(corp_code)

    if not corp:
        return [TextContent(type="text", text=f"Company not found for corp_code: {corp_code}")]

    try:
        fs = corp.get_financial_statements(
            bsns_year=str(year),
            reprt_code=reprt_code,
            fs_div="CFS"  # consolidated financial statements
        )

        if fs is None or (hasattr(fs, 'empty') and fs.empty):
            # fallback to separate financial statements
            fs = corp.get_financial_statements(
                bsns_year=str(year),
                reprt_code=reprt_code,
                fs_div="OFS"
            )

        if fs is None or (hasattr(fs, 'empty') and fs.empty):
            return [TextContent(type="text", text=f"No financial data found for {corp_code} ({year})")]

        # Convert to readable format
        if hasattr(fs, 'to_dict'):
            data = fs.to_dict(orient="records")
        elif hasattr(fs, '__iter__'):
            data = [str(item) for item in fs]
        else:
            data = str(fs)

        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2, default=str))]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to retrieve financials: {e}")]


async def _get_company_info(args: dict) -> list[TextContent]:
    corp_code = args["corp_code"]
    corp_list = dart.get_corp_list()
    corp = corp_list.find_by_corp_code(corp_code)

    if not corp:
        return [TextContent(type="text", text=f"Company not found for corp_code: {corp_code}")]

    try:
        info = corp.load()
        result = {
            "corp_code": corp_code,
            "corp_name": getattr(corp, "corp_name", None),
        }
        if info:
            for field in ["ceo_nm", "adres", "hm_url", "ir_url", "phn_no",
                          "fax_no", "induty_code", "est_dt", "acc_mt"]:
                result[field] = getattr(info, field, None)

        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2, default=str))]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to retrieve company info: {e}")]


async def _get_disclosures(args: dict) -> list[TextContent]:
    corp_code = args["corp_code"]
    limit = args.get("limit", 10)

    from datetime import datetime, timedelta
    start_date = args.get("start_date")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

    end_date = datetime.now().strftime("%Y%m%d")

    try:
        filings = dart.filings.search(
            corp_code=corp_code,
            bgn_de=start_date,
            end_de=end_date,
            page_count=limit
        )

        if not filings or not hasattr(filings, 'list'):
            return [TextContent(type="text", text="No disclosures found")]

        results = []
        for item in filings.list[:limit]:
            results.append({
                "rcept_no": getattr(item, "rcept_no", None),
                "corp_name": getattr(item, "corp_name", None),
                "report_nm": getattr(item, "report_nm", None),
                "rcept_dt": getattr(item, "rcept_dt", None),
                "flr_nm": getattr(item, "flr_nm", None),
                "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={getattr(item, 'rcept_no', '')}",
            })

        return [TextContent(type="text", text=json.dumps(results, ensure_ascii=False, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Failed to retrieve disclosures: {e}")]


# --- Entry point ---

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
