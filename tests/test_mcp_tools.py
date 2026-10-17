"""Regression tests that call the tools through the MCP layer (FastMCP), not the helpers.

These pin what an MCP client actually receives, so they catch problems in the response
layer (empty arrays, count/record mismatches) that tests of bi_mcp.analytics cannot see.
"""
import asyncio
import json
import unittest

from mcp.server.fastmcp.exceptions import ToolError

import server


def call_tool(name: str, **arguments) -> dict:
    """Call a tool through FastMCP and return the payload a client would read."""
    result = asyncio.run(server.mcp.call_tool(name, arguments))
    # Depending on the mcp version, call_tool returns content blocks, or (content, structured).
    if isinstance(result, tuple):
        content, structured = result
        if structured is not None:
            return structured.get("result", structured) if set(structured) == {"result"} else structured
    else:
        content = result
    return json.loads(content[0].text)


class ListDatasetsTests(unittest.TestCase):
    def test_returns_sales_sample_with_rows_and_columns(self):
        payload = call_tool("list_datasets")
        self.assertEqual(len(payload["datasets"]), 1)
        dataset = payload["datasets"][0]
        self.assertEqual(dataset["name"], "sales_sample")
        self.assertEqual(dataset["rows"], 20)
        self.assertEqual(dataset["columns"], ["order_id", "date", "region", "product", "units", "revenue", "cost"])


class SearchRecordsTests(unittest.TestCase):
    def assert_counts_agree(self, payload):
        self.assertEqual(payload["returned_count"], len(payload["records"]))
        self.assertLessEqual(payload["returned_count"], payload["matched_count"])

    def test_blank_column_searches_all_columns_and_returns_records(self):
        # MCP Playground sends "" for an omitted optional parameter.
        payload = call_tool("search_records", dataset="sales_sample", query="Widget A", column="", limit=10)
        self.assertEqual(payload["matched_count"], 7)
        self.assertEqual(len(payload["records"]), 7)
        self.assert_counts_agree(payload)
        self.assertTrue(all(row["product"] == "Widget A" for row in payload["records"]))

    def test_omitted_column_matches_blank_column(self):
        blank = call_tool("search_records", dataset="sales_sample", query="Widget A", column="")
        omitted = call_tool("search_records", dataset="sales_sample", query="Widget A")
        self.assertEqual(blank["records"], omitted["records"])

    def test_specific_column_restricts_the_search(self):
        in_region = call_tool("search_records", dataset="sales_sample", query="West", column="region")
        self.assertEqual(in_region["matched_count"], 5)
        self.assertEqual(len(in_region["records"]), 5)
        self.assertTrue(all(row["region"] == "West" for row in in_region["records"]))
        # "West" appears only in the region column, so searching another column finds nothing.
        elsewhere = call_tool("search_records", dataset="sales_sample", query="West", column="product")
        self.assertEqual(elsewhere["matched_count"], 0)
        self.assertEqual(elsewhere["records"], [])

    def test_limit_truncates_records_but_not_the_match_count(self):
        payload = call_tool("search_records", dataset="sales_sample", query="Widget A", limit=3)
        self.assertEqual(payload["matched_count"], 7)
        self.assertEqual(len(payload["records"]), 3)
        self.assertTrue(payload["truncated"])
        self.assert_counts_agree(payload)


class AnalyzeAndAnomalyTests(unittest.TestCase):
    def test_analyze_revenue(self):
        payload = call_tool("analyze_dataset", dataset="sales_sample", column="revenue")
        self.assertEqual(payload["numeric_count"], 20)
        self.assertEqual(payload["sum"], 13410)
        self.assertEqual(payload["mean"], 670.5)
        self.assertEqual(payload["max"], 9000)

    def test_anomaly_records_match_the_count(self):
        payload = call_tool("detect_anomalies", dataset="sales_sample", column="revenue")
        self.assertEqual(payload["anomaly_count"], 3)
        self.assertEqual(len(payload["anomalies"]), payload["anomaly_count"])
        self.assertFalse(payload["truncated"])
        self.assertEqual(sorted(item["value"] for item in payload["anomalies"]), [420, 450, 9000])
        self.assertEqual((payload["q1"], payload["q3"], payload["lower_fence"], payload["upper_fence"]), (190, 280, 55, 415))
        flagged = next(item for item in payload["anomalies"] if item["value"] == 9000)
        self.assertEqual(flagged["record"]["order_id"], "1020")


class GenerateReportTests(unittest.TestCase):
    def test_numeric_summaries_cover_every_numeric_column(self):
        payload = call_tool("generate_report", dataset="sales_sample")
        self.assertEqual(payload["row_count"], 20)
        self.assertEqual(len(payload["columns"]), 7)
        summaries = {item["column"]: item for item in payload["numeric_summaries"]}
        self.assertEqual(set(summaries), {"order_id", "units", "revenue", "cost"})
        self.assertEqual(payload["data_quality"], {"empty_cells": 0, "total_cells": 140})

    def test_report_agrees_with_analyze_dataset(self):
        report = {item["column"]: item for item in call_tool("generate_report", dataset="sales_sample")["numeric_summaries"]}
        analysis = call_tool("analyze_dataset", dataset="sales_sample", column="revenue")
        for key in ("numeric_count", "missing_or_non_numeric_count", "sum", "mean", "min", "max"):
            self.assertEqual(report["revenue"][key], analysis[key], key)


class ErrorHandlingTests(unittest.TestCase):
    def test_unknown_dataset_is_a_tool_error(self):
        with self.assertRaises(ToolError):
            call_tool("analyze_dataset", dataset="nope", column="revenue")

    def test_unknown_column_is_a_tool_error(self):
        with self.assertRaises(ToolError):
            call_tool("search_records", dataset="sales_sample", query="x", column="not_a_column")


if __name__ == "__main__":
    unittest.main()
