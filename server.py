"""Remote MCP server exposing read-only CSV analytics tools plus a sample demo site."""
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import HTMLResponse

from bi_mcp.analytics import (
    list_datasets as _list,
    search_records as _search,
    analyze_dataset as _analyze,
    detect_anomalies as _anomalies,
    generate_report as _report,
)

ROOT_DIR = Path(__file__).resolve().parent
mcp = FastMCP("Business Intelligence MCP Connector")


@mcp.custom_route("/", methods=["GET"])
async def demo_home(request: Request) -> HTMLResponse:
    """Serve the customer-facing sample dashboard at the service root."""
    page = (ROOT_DIR / "demo" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(page)


@mcp.custom_route("/sample-report", methods=["GET"])
async def sample_report(request: Request) -> HTMLResponse:
    """Serve a print-friendly sample report using only the bundled fictional CSV."""
    page = (ROOT_DIR / "demo" / "sample-report.html").read_text(encoding="utf-8")
    return HTMLResponse(page)


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
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = int(os.environ.get("PORT", "10000"))
    mcp.settings.transport_security = TransportSecuritySettings(
        allowed_hosts=[hostname, f"{hostname}:*"]
    )
    # FastMCP.run() reads host, port, and transport security from mcp.settings.
    mcp.run(transport="streamable-http")
