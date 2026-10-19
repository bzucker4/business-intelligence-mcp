# Business Intelligence Copilot

A small-business data-analysis demonstration powered by a read-only Model Context Protocol (MCP) server. It analyzes only the fictional CSV file bundled with the service; it does **not** accept uploads or connect to customer business systems.

## Live demo

- **Interactive overview:** https://business-intelligence-mcp-gq49.onrender.com/
- **Printable sample report:** https://business-intelligence-mcp-gq49.onrender.com/sample-report
- **MCP endpoint (Streamable HTTP):** https://business-intelligence-mcp-gq49.onrender.com/mcp
- **Privacy policy:** https://business-intelligence-mcp-gq49.onrender.com/privacy
- **Support:** https://business-intelligence-mcp-gq49.onrender.com/support
- **Source code and issue tracker:** https://github.com/bzucker4/business-intelligence-mcp

## What it does

The server exposes five read-only tools:

| Tool | Purpose |
| --- | --- |
| `list_datasets` | Lists bundled CSV datasets, row counts, and column names. |
| `search_records` | Searches sample records case-insensitively, optionally within one column. |
| `analyze_dataset` | Calculates numeric count, sum, mean, median, minimum, and maximum. |
| `detect_anomalies` | Flags numeric outliers using 1.5×IQR fences. Flags are not proof of errors. |
| `generate_report` | Summarizes dataset dimensions, numeric columns, and empty cells. |

Tool annotations explicitly mark the tools read-only, non-destructive, repeatable, and limited to the local bundled sample dataset.

## Three example prompts

These prompts are designed to work against the bundled `sales_sample` dataset.

1. **Discover the dataset:** “List the available datasets and report the row and column counts.”  
   Expected result: one dataset named `sales_sample`, with 20 rows and 7 columns.

2. **Analyze revenue:** “Analyze the revenue column in sales_sample and report its sum, mean, and median.”  
   Expected result: sum **13,410**, mean **670.5**, and median **215**. The high mean is affected by the 9,000 revenue record; the median is less sensitive to that value.

3. **Search and review outliers:** “Find records containing Widget A, then flag unusual revenue values in sales_sample and explain why flagged values should be reviewed rather than automatically treated as errors.”  
   Expected result: 7 Widget A matches. The IQR method flags revenue values 420, 450, and 9,000 for review. A statistical flag is not evidence of a data-entry error.

## Privacy and scope

- The deployed dataset is fictional and included in the repository.
- The service does not accept file uploads, read Claude conversations or uploaded files, or connect to private business systems.
- The current deployment has no authentication. Anyone who can reach the public endpoint can call the sample-data tools. Do not add private data to the deployed `data/` directory.
- Review the [privacy policy](https://business-intelligence-mcp-gq49.onrender.com/privacy) before use.

## Local setup and tests

Python 3.10+ is recommended.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python server.py
```

Local pages:
- Demo: http://localhost:10000/
- Sample report: http://localhost:10000/sample-report
- Privacy: http://localhost:10000/privacy
- Support: http://localhost:10000/support
- MCP endpoint: http://localhost:10000/mcp

Use the official [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) for protocol-level testing. Opening `/mcp` in a browser is not a sufficient MCP test.

## Deployment

Render uses the repository's `render.yaml`:
- Build command: `pip install -r requirements.txt`
- Start command: `python server.py`
- Health check: `/`

After a deployment, verify the homepage, printable report, privacy page, support page, and the remote MCP protocol with MCP Inspector.

## Troubleshooting

- **Build failure:** inspect Render build logs and confirm `requirements.txt` is at the repository root.
- **Startup failure:** confirm the start command is `python server.py` and inspect service logs.
- **Host rejected:** verify `RENDER_EXTERNAL_HOSTNAME` matches the assigned hostname.
- **Slow first request:** a free instance may sleep while idle.
- **Dataset not found:** use the CSV filename without `.csv`; only CSV files in the deployed `data/` directory are listed.
- **Tool connection failure:** test the full `/mcp` endpoint using MCP Inspector and inspect the server logs.

Validate outputs against source records before making business decisions.
