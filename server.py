"""Remote MCP server exposing read-only CSV analytics tools plus a sample demo site."""
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
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
mcp = FastMCP("Business Intelligence Copilot")


def _read_demo_page(filename: str) -> HTMLResponse:
    """Read a fixed, repository-owned HTML page."""
    page = (ROOT_DIR / "demo" / filename).read_text(encoding="utf-8")
    return HTMLResponse(page)


@mcp.custom_route("/", methods=["GET"])
async def demo_home(request: Request) -> HTMLResponse:
    """Serve the customer-facing sample dashboard."""
    return _read_demo_page("index.html")


@mcp.custom_route("/sample-report", methods=["GET"])
async def sample_report(request: Request) -> HTMLResponse:
    """Serve a print-friendly report generated from fictional bundled sample data."""
    return _read_demo_page("sample-report.html")


@mcp.custom_route("/privacy", methods=["GET"])
async def privacy_policy(request: Request) -> HTMLResponse:
    """Serve the public privacy policy."""
    return _read_demo_page("privacy.html")


@mcp.custom_route("/support", methods=["GET"])
async def support_page(request: Request) -> HTMLResponse:
    """Serve support and security-reporting guidance."""
    return _read_demo_page("support.html")


def _read_only_annotations(title: str) -> ToolAnnotations:
    """Return complete annotations for a read-only tool."""
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )


@mcp.tool(
    title="List sample datasets",
    annotations=_read_only_annotations("List sample datasets"),
)
def list_datasets() -> dict:
    """List fictional CSV datasets bundled with this service, including row counts and column names.
    Use this first to discover which sample dataset names and columns are available.
    This tool does not access user uploads, connected drives, or private business systems.
    """
    return {"datasets": _list()}


@mcp.tool(
    title="Search sample records",
    annotations=_read_only_annotations("Search sample records"),
)
def search_records(dataset: str, query: str, column: str | None = None, limit: int = 10) -> dict:
    """Search a bundled sample CSV for a case-insensitive text match.
    Use dataset from list_datasets; optionally restrict the search to a column.
    The result includes match counts and at most 100 records. Empty column means search all columns.
    This tool cannot search user uploads or external business systems.
    """
    return _search(dataset, query, column, limit)


@mcp.tool(
    title="Analyze a numeric column",
    annotations=_read_only_annotations("Analyze a numeric column"),
)
def analyze_dataset(dataset: str, column: str) -> dict:
    """Calculate count, sum, mean, median, minimum, and maximum for a numeric column in a bundled sample CSV.
    Non-numeric and empty cells are excluded from numeric calculations and counted separately.
    Use dataset and column names returned by list_datasets. This tool does not infer causation or forecast results.
    """
    return _analyze(dataset, column)


@mcp.tool(
    title="Flag unusual numeric values",
    annotations=_read_only_annotations("Flag unusual numeric values"),
)
def detect_anomalies(dataset: str, column: str) -> dict:
    """Flag potential numeric outliers in a bundled sample CSV using the 1.5×IQR rule.
    Returns the fences, flagged rows, and descriptive statistics. Flags are review candidates, not proof of errors.
    Use dataset and column names returned by list_datasets.
    """
    return _anomalies(dataset, column)


@mcp.tool(
    title="Generate a sample data report",
    annotations=_read_only_annotations("Generate a sample data report"),
)
def generate_report(dataset: str) -> dict:
    """Generate a descriptive report for a bundled sample CSV, including columns, numeric summaries, and empty-cell counts.
    This is a descriptive summary of the observed sample only; it does not establish causes or forecast performance.
    """
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
