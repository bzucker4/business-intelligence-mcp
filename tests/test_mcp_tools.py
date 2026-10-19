"""Protocol-layer regression tests for the tools exposed by FastMCP."""
import asyncio
import json
import unittest

from mcp.server.fastmcp.exceptions import ToolError

import server


def call_tool(name: str, **arguments) -> dict:
    """Call a tool through FastMCP and return the structured result."""
    result = asyncio.run(server.mcp.call_tool(name, arguments))
    if isinstance(result, tuple):
        content, structured = result
        if structured is not None:
            return structured.get("result", structured) if set(structured) == {"result"} else structured
    else:
        content = result
    return json.loads(content[0].text)


class ToolMetadataTests(unittest.TestCase):
    def test_all_tools_have_read_only_annotations_and_titles(self):
        async def list_tools():
            return await server.mcp.list_tools()

        tools = asyncio.run(list_tools())
        expected = {
            "list_datasets": "List sample datasets",
            "search_records": "Search sample records",
            "analyze_dataset": "Analyze a numeric column",
            "detect_anomalies": "Flag unusual numeric values",
            "generate_report": "Generate a sample data report",
        }
        self.assertEqual({tool.name for tool in tools}, set(expected))
        for tool in tools:
            self.assertEqual(tool.annotations.title, expected[tool.name])
            self.assertTrue(tool.annotations.readOnlyHint)
            self.assertFalse(tool.annotations.destructiveHint)
            self.assertTrue(tool.annotations.idempotentHint)
            self.assertFalse(tool.annotations.openWorldHint)


class ListDatasetsTests(unittest.TestCase):
    def test_returns_sales_sample_with_rows_and_columns(self):
        payload = call_tool("list_datasets")
        self.assertEqual(len(payload["datasets"]), 1)
        dataset = payload["datasets"][0]
        self.assertEqual(dataset["name"], "sales_sample")
        self.assertEqual(dataset["rows"], 20)
        self.assertEqual(dataset["columns"], ["order_id", "date", "region", "product", "units", "revenue", "cost"])


class SearchRecordsTests(unittest.TestCase):
    def test_blank_column_searches_all_columns_and_returns_records(self):
        payload = call_tool("search_records", dataset="sales_sample", query="Widget A", column="", limit=10)
        self.assertEqual(payload["matched_count"], 7)
        self.assertEqual(len(payload["records"]), 7)
        self.assertEqual(payload["returned_count"], len(payload["records"]))
        self.assertTrue(all(row["product"] == "Widget A" for row in payload["records"]))

    def test_omitted_column_matches_blank_column(self):
        blank = call_tool("search_records", dataset="sales_sample", query="Widget A", column="")
        omitted = call_tool("search_records", dataset="sales_sample", query="Widget A")
        self.assertEqual(blank["records"], omitted["records"])

    def test_specific_column_restricts_the_search(self):
        payload = call_tool("search_records", dataset="sales_sample", query="West", column="region")
        self.assertEqual(payload["matched_count"], 5)
        self.assertTrue(all(row["region"] == "West" for row in payload["records"]))

    def test_limit_truncates_records_but_not_match_count(self):
        payload = call_tool("search_records", dataset="sales_sample", query="Widget A", limit=3)
        self.assertEqual(payload["matched_count"], 7)
        self.assertEqual(len(payload["records"]), 3)
        self.assertTrue(payload["truncated"])


class AnalyticsTests(unittest.TestCase):
    def test_revenue_statistics(self):
        payload = call_tool("analyze_dataset", dataset="sales_sample", column="revenue")
        self.assertEqual(payload["numeric_count"], 20)
        self.assertEqual(payload["sum"], 13410)
        self.assertEqual(payload["mean"], 670.5)
        self.assertEqual(payload["median"], 215)
        self.assertEqual(payload["max"], 9000)

    def test_anomaly_records_match_count(self):
        payload = call_tool("detect_anomalies", dataset="sales_sample", column="revenue")
        self.assertEqual(payload["anomaly_count"], 3)
        self.assertEqual(sorted(item["value"] for item in payload["anomalies"]), [420, 450, 9000])
        self.assertEqual((payload["q1"], payload["q3"], payload["lower_fence"], payload["upper_fence"]), (190, 280, 55, 415))
        self.assertIn("not proof of an error", payload["note"])

    def test_report_agrees_with_numeric_analysis(self):
        report = call_tool("generate_report", dataset="sales_sample")
        self.assertEqual(report["row_count"], 20)
        self.assertEqual(report["data_quality"], {"empty_cells": 0, "total_cells": 140})
        revenue = next(item for item in report["numeric_summaries"] if item["column"] == "revenue")
        analysis = call_tool("analyze_dataset", dataset="sales_sample", column="revenue")
        for key in ("numeric_count", "missing_or_non_numeric_count", "sum", "mean", "min", "max"):
            self.assertEqual(revenue[key], analysis[key], key)


class ErrorHandlingTests(unittest.TestCase):
    def test_unknown_dataset_is_a_tool_error(self):
        with self.assertRaises(ToolError):
            call_tool("analyze_dataset", dataset="nope", column="revenue")

    def test_unknown_column_is_a_tool_error(self):
        with self.assertRaises(ToolError):
            call_tool("search_records", dataset="sales_sample", query="x", column="not_a_column")


if __name__ == "__main__":
    unittest.main()
