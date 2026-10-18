# Business Intelligence Copilot

A small-business sales analysis demo powered by a read-only Model Context Protocol (MCP) server. The web preview and printable report use only the bundled fictional `sales_sample.csv` dataset.

## Customer-facing demo

- **Demo overview:** the service root URL, for example `https://YOUR-SERVICE.onrender.com/`
- **Printable sample report:** `https://YOUR-SERVICE.onrender.com/sample-report` (use **Print / Save PDF** in the report toolbar)
- **MCP endpoint:** `https://YOUR-SERVICE.onrender.com/mcp`

The overview is a sample-data showcase, not a live analytics dashboard. It does not accept uploads or display customer data. The report labels the data as illustrative and explains the limits of the findings.

## MCP tools

- `list_datasets`: list CSV datasets, row counts, and columns.
- `search_records`: case-insensitive search with bounded results.
- `analyze_dataset`: descriptive statistics for a numeric column.
- `detect_anomalies`: flags outliers using the 1.5×IQR rule. Flags are not proof of errors.
- `generate_report`: dataset dimensions, numeric summaries, and empty-cell counts.

## Safety

**This demo has no authentication.** Anyone who can reach the public MCP endpoint can call its tools. Use sample data only until authentication and access controls are added. The server only reads CSV files included in the deployed `data/` folder. Do not upload or expose private customer data.

## Local test (optional)

Python 3.10+ recommended.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python server.py
```

Local web demo: `http://localhost:10000/`  
Local report: `http://localhost:10000/sample-report`  
Local MCP endpoint: `http://localhost:10000/mcp`

Use the official [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) for protocol-level testing; a browser GET to the MCP endpoint is not enough.

## Deploy from a Chromebook

1. Push all project files and folders to this repository, preserving paths.
2. On Render, choose **New → Web Service** and connect this repository, or let the existing connected service redeploy from the main branch.
3. Set build command to `pip install -r requirements.txt` and start command to `python server.py`.
4. Confirm the service is live and inspect logs. Render supplies `PORT` and `RENDER_EXTERNAL_HOSTNAME` automatically.
5. Open the service root to verify the demo, then open `/sample-report` and `/mcp` as appropriate.
6. The remote MCP endpoint is the service URL plus `/mcp`. Use that URL in ChatGPT or Claude connector settings.

## Troubleshooting

- Build failure: check logs and confirm `requirements.txt` is at the repository root.
- Startup failure: confirm `python server.py` and inspect logs.
- Host rejected: verify `RENDER_EXTERNAL_HOSTNAME` matches the assigned hostname.
- Slow first request: free instances may sleep while idle.
- Dataset not found: use the CSV filename without `.csv`; only files in the deployed `data/` folder are listed.

Validate results against source records before making business decisions.
