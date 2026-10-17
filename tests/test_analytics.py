import unittest
from bi_mcp.analytics import list_datasets, search_records, analyze_dataset, detect_anomalies, generate_report

class AnalyticsTests(unittest.TestCase):
    def test_list_datasets(self):
        names = [item["name"] for item in list_datasets()]
        self.assertIn("sales_sample", names)

    def test_search(self):
        result = search_records("sales_sample", "Widget A", column="product")
        self.assertGreater(result["matched_count"], 0)
        self.assertTrue(all("Widget A" in row["product"] for row in result["records"]))

    def test_search_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            search_records("../secret", "x")

    def test_numeric_analysis(self):
        result = analyze_dataset("sales_sample", "revenue")
        self.assertEqual(result["numeric_count"], 20)
        self.assertEqual(result["max"], 9000)
        self.assertAlmostEqual(result["sum"], 13410)

    def test_anomaly_detection_flags_outlier(self):
        result = detect_anomalies("sales_sample", "revenue")
        self.assertGreaterEqual(result["anomaly_count"], 1)
        self.assertTrue(any(item["value"] == 9000 for item in result["anomalies"]))

    def test_report(self):
        result = generate_report("sales_sample")
        self.assertEqual(result["row_count"], 20)
        self.assertIn("revenue", [item["column"] for item in result["numeric_summaries"]])
        self.assertEqual(result["data_quality"]["empty_cells"], 0)

    def test_bad_column(self):
        with self.assertRaises(ValueError):
            analyze_dataset("sales_sample", "not_a_column")

if __name__ == "__main__":
    unittest.main()
