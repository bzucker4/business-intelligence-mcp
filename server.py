"""Remote MCP server exposing read-only CSV analytics tools."""
import os
from mcp.server.fastmcp import FastMCP
from bi_mcp.analytics import list_datasets as _list, search_records as _search, analyze_dataset as _analyze, detect_anomalies as _anomalies, generate_report as _report

mcp = FastMCP("Business Intelligence MCP Connector")

@mcp.tool()
def list_datasets() -> dict:
    """List CSV datasets bundled in the data folder, including row counts and columns."""
    return {"datasets": _list()}

@mcp.tool()
def search_records(dataset: str, query: str, column: str | None = None, limit: int = 10) -> dict:
    """Search CSV records case-insensitively. Optionally restrict search to one column."""
    return _search(dataset, query, column, limit)

@mcp.tool()
def analyze_dataset(dataset: str, column: str) -> dict:
    """Calculate descriptive statistics for a numeric column, ignoring non-numeric cells."""
    return _analyze(dataset, column)

@mcp.tool()
def detect_anomalies(dataset: str, column: str) -> dict:
    """Flag numeric outliers using 1.5×IQR fences; flags are not proof of errors."""
    return _anomalies(dataset, column)

@mcp.tool()
def generate_report(dataset: str) -> dict:
    """Generate an evidence-based summary of CSV columns, numeric values, and empty cells."""
    return _report(dataset)

if __name__ == "__main__":
    hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost")
    from mcp.server.transport_security import TransportSecuritySettings
    security = TransportSecuritySettings(allowed_hosts=[hostname, f"{hostname}:*"])
    mcp.run(transport="streamable-http", host="0.0.0.0", port=int(os.environ.get("PORT", "10000")), transport_security=security)
