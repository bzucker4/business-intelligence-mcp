"""Safe, read-only analytics helpers for CSV datasets."""
from __future__ import annotations
import csv
import math
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_ROWS = 100_000
MAX_SEARCH_RESULTS = 100


def _dataset_path(name: str) -> Path:
    """Resolve only a simple CSV filename inside the project's data directory."""
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", name):
        raise ValueError("Dataset name must contain only letters, numbers, underscores, or hyphens.")
    path = (DATA_DIR / f"{name}.csv").resolve()
    if path.parent != DATA_DIR.resolve() or not path.is_file():
        raise ValueError(f"Dataset '{name}' was not found. Use list_datasets to see available datasets.")
    return path


def load_dataset(name: str) -> tuple[list[str], list[dict[str, str]]]:
    path = _dataset_path(name)
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError("Dataset must have a header row.")
        headers = [str(h) for h in reader.fieldnames]
        rows = []
        for row in reader:
            if len(rows) >= MAX_ROWS:
                raise ValueError(f"Dataset exceeds the {MAX_ROWS:,}-row safety limit.")
            rows.append({str(k): (v or "") for k, v in row.items() if k is not None})
    return headers, rows


def _number(value: str) -> float | None:
    try:
        number = float(str(value).replace(",", "").strip())
        return number if math.isfinite(number) else None
    except (ValueError, TypeError):
        return None


def list_datasets() -> list[dict[str, Any]]:
    # Use directory iteration rather than glob so packaged CSV files are discovered consistently.
    if not DATA_DIR.is_dir():
        return []
    results = []
    for path in sorted(DATA_DIR.iterdir(), key=lambda item: item.name.casefold()):
        if path.is_file() and path.suffix.casefold() == ".csv":
            headers, rows = load_dataset(path.stem)
            results.append({"name": path.stem, "rows": len(rows), "columns": headers})
    return results


def search_records(dataset: str, query: str, column: str | None = None, limit: int = 10) -> dict[str, Any]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string.")
    if len(query) > 300:
        raise ValueError("Query must be 300 characters or fewer.")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= MAX_SEARCH_RESULTS:
        raise ValueError(f"Limit must be an integer between 1 and {MAX_SEARCH_RESULTS}.")
    headers, rows = load_dataset(dataset)
    # MCP clients may submit an empty string for an omitted optional field.
    if column is not None and not column.strip():
        column = None
    if column is not None and column not in headers:
        raise ValueError(f"Unknown column '{column}'. Available columns: {headers}")
    needle = query.casefold()
    matches = []
    for row in rows:
        values = [row.get(column, "")] if column else row.values()
        if any(needle in str(value).casefold() for value in values):
            matches.append(row)
    returned = list(matches[:limit])
    return {"dataset": dataset, "query": query, "matched_count": len(matches), "returned_count": len(returned), "records": returned, "truncated": len(matches) > limit}


def analyze_dataset(dataset: str, column: str) -> dict[str, Any]:
    headers, rows = load_dataset(dataset)
    if column not in headers:
        raise ValueError(f"Unknown column '{column}'. Available columns: {headers}")
    parsed = [_number(row.get(column, "")) for row in rows]
    values = [v for v in parsed if v is not None]
    if not values:
        raise ValueError(f"Column '{column}' contains no usable numeric values.")
    ordered = sorted(values)
    n = len(ordered)
    median = ordered[n // 2] if n % 2 else (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    mean = sum(values) / n
    return {"dataset": dataset, "column": column, "row_count": len(rows), "numeric_count": n, "missing_or_non_numeric_count": len(rows) - n, "sum": round(sum(values), 4), "mean": round(mean, 4), "median": round(median, 4), "min": min(values), "max": max(values)}


def detect_anomalies(dataset: str, column: str) -> dict[str, Any]:
    stats = analyze_dataset(dataset, column)
    _, rows = load_dataset(dataset)
    values = [(i + 2, row, _number(row.get(column, ""))) for i, row in enumerate(rows)]
    ordered = sorted(v for _, _, v in values if v is not None)
    def median(nums: list[float]) -> float:
        n = len(nums)
        return nums[n // 2] if n % 2 else (nums[n // 2 - 1] + nums[n // 2]) / 2
    mid = len(ordered) // 2
    lower = ordered[:mid]
    upper = ordered[(mid + 1 if len(ordered) % 2 else mid):]
    q1 = median(lower) if lower else ordered[0]
    q3 = median(upper) if upper else ordered[-1]
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    anomalies = [{"csv_row": rownum, "value": value, "record": row} for rownum, row, value in values if value is not None and (value < low or value > high)]
    return {"dataset": dataset, "column": column, "method": "1.5×IQR fences", "q1": q1, "q3": q3, "iqr": iqr, "lower_fence": low, "upper_fence": high, "anomaly_count": len(anomalies), "anomalies": anomalies[:100], "truncated": len(anomalies) > 100, "note": "Statistical flags are review candidates, not proof of an error.", "summary": stats}


def generate_report(dataset: str) -> dict[str, Any]:
    headers, rows = load_dataset(dataset)
    numeric = []
    for header in headers:
        vals = [_number(row.get(header, "")) for row in rows]
        valid = [v for v in vals if v is not None]
        if valid:
            numeric.append({"column": header, "numeric_count": len(valid), "missing_or_non_numeric_count": len(rows) - len(valid), "sum": round(sum(valid), 4), "mean": round(sum(valid) / len(valid), 4), "min": min(valid), "max": max(valid)})
    return {"dataset": dataset, "row_count": len(rows), "columns": headers, "numeric_summaries": numeric, "data_quality": {"empty_cells": sum(1 for row in rows for h in headers if not row.get(h, "").strip()), "total_cells": len(rows) * len(headers)}, "interpretation": "This report summarizes the supplied CSV only. It does not establish causes, forecasts, or business conclusions beyond the observed data."}
