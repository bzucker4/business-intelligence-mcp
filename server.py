"""Remote MCP server exposing read-only CSV analytics tools."""
import os
import json
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from bi_mcp.analytics import (
    list_datasets as _list,
    search_records as _search,
    analyze_dataset as _analyze,
    detect_anomalies as _anomalies,
    generate_report as _report,
)

mcp = FastMCP("Business Intelligence MCP Connector")

@mcp.tool()
def list_datasets() -> dict:
    """List CSV datasets bundled in the data folder, including row counts and columns."""
    return json.dumps({"datasets": _list()}, ensure_ascii=False)

@mcp.tool()
def search_records(dataset: str, query: str, column: str | None = None, limit: int = 10) -> dict:
    """Search CSV records case-insensitively. Optionally restrict search to one column."""
    return json.dumps(_search(dataset, query, column, limit), ensure_ascii=False)

@mcp.tool()
def analyze_dataset(dataset: str, column: str) -> dict:
    """Calculate descriptive statistics for a numeric column, ignoring non-numeric cells."""
    return json.dumps(_analyze(dataset, column), ensure_ascii=False)

@mcp.tool()
def detect_anomalies(dataset: str, column: str) -> dict:
    """Flag numeric outliers using 1.5×IQR fences; flags are not proof of errors."""
    return json.dumps(_anomalies(dataset, column), ensure_ascii=False)

@mcp.tool()
def generate_report(dataset: str) -> dict:
    """Generate an evidence-based summary of CSV columns, numeric values, and empty cells."""
    return json.dumps(_report(dataset), ensure_ascii=False)

@mcp.tool()
def diagnose_data() -> dict:
    """Diagnose the deployed CSV directory and report which files the running server can see."""
    from pathlib import Path
    from bi_mcp import analytics
    data_dir = Path(analytics.DATA_DIR)
    files = sorted(p.name for p in data_dir.iterdir() if p.is_file()) if data_dir.is_dir() else []
    return json.dumps({
        "server_file": str(Path(__file__).resolve()),
        "data_dir": str(data_dir.resolve()),
        "data_dir_exists": data_dir.is_dir(),
        "csv_files": [name for name in files if name.lower().endswith(".csv")],
        "sales_sample_exists": (data_dir / "sales_sample.csv").is_file(),
        "datasets_function_result": _list(),
    }, ensure_ascii=False)

if __name__ == "__main__":
    hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "localhost")
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = int(os.environ.get("PORT", "10000"))
    mcp.settings.transport_security = TransportSecuritySettings(
        allowed_hosts=[hostname, f"{hostname}:*"]
    )
    # FastMCP.run() reads host, port, and transport security from mcp.settings.
    mcp.run(transport="streamable-http")
