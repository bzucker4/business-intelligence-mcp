# Business Intelligence MCP Connector

A beginner-friendly, read-only MCP server for analyzing CSV datasets bundled in `data/`.

## Tools
- `list_datasets`: list CSV datasets, row counts, and columns.
- `search_records`: case-insensitive search with bounded results.
- `analyze_dataset`: descriptive statistics for a numeric column.
- `detect_anomalies`: flags outliers using the 1.5×IQR rule. Flags are not proof of errors.
- `generate_report`: dataset dimensions, numeric summaries, and empty-cell counts.

## Safety
This demo has no authentication. Anyone who can reach its public endpoint can call its tools. Use sample data only until authentication and access controls are added. The server only reads CSVs included in the deployed `data/` folder.

## Local test (optional)
Python 3.10+ recommended.
```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python server.py
```
Local MCP endpoint: `http://localhost:10000/mcp`. Use the official [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) for protocol-level testing; a browser GET is not enough.

## Deploy from a Chromebook
1. Push all project files and folders to this repository, preserving paths.
2. On Render, choose **New → Web Service** and connect this repository.
3. Set build command to `pip install -r requirements.txt` and start command to `python server.py`.
4. Choose the free plan if available, then deploy.
5. Confirm the service is live and inspect logs. Render supplies `PORT` and `RENDER_EXTERNAL_HOSTNAME` automatically.
6. The remote endpoint is your actual Render service URL plus `/mcp`, e.g. `https://YOUR-SERVICE.onrender.com/mcp` (replace the example hostname).
7. Verify with MCP Inspector/client, then add the URL in ChatGPT's custom connector settings if available on your account/workspace.

## Troubleshooting
- Build failure: check logs and confirm `requirements.txt` is at the repository root.
- Startup failure: confirm `python server.py` and inspect logs.
- Host rejected: verify Render's `RENDER_EXTERNAL_HOSTNAME` matches the assigned hostname.
- Slow first request: free instances may sleep while idle.
- Dataset not found: use the CSV filename without `.csv`; only files in `data/` are listed.

Validate results before making business decisions.