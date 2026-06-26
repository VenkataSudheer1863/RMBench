"""Result serialization and aggregation utilities."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def save_results(
    results: dict[str, Any],
    output_path: str | Path,
    indent: int = 2,
) -> Path:
    """Save benchmark results to a JSON file.

    Args:
        results: Results dictionary from BenchmarkPipeline.run().
        output_path: File path to write (created if not exists).
        indent: JSON indentation level.

    Returns:
        Resolved Path of the saved file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=indent, default=str)
    logger.info("Results saved: %s", path)
    return path


def load_results(path: str | Path) -> dict[str, Any]:
    """Load benchmark results from a JSON file.

    Args:
        path: Path to the results JSON file.

    Returns:
        Results dictionary.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info("Results loaded from %s (%d samples)", path, len(data.get("results", [])))
    return data


def merge_results(result_files: list[str | Path]) -> dict[str, Any]:
    """Merge multiple result files into one combined results dict.

    Args:
        result_files: List of paths to individual result JSON files.

    Returns:
        Merged results dictionary.
    """
    all_results: list[dict] = []
    all_metadata: list[dict] = []

    for fpath in result_files:
        data = load_results(fpath)
        all_results.extend(data.get("results", []))
        all_metadata.append(data.get("metadata", {}))

    from rmbench.metrics import compute_all_metrics
    merged_metrics = compute_all_metrics(all_results)

    return {
        "metadata": {
            "merged_from": [str(f) for f in result_files],
            "num_files": len(result_files),
            "num_samples": len(all_results),
            "timestamp": datetime.utcnow().isoformat(),
        },
        "metrics": merged_metrics,
        "results": all_results,
        "per_file_metadata": all_metadata,
    }


def results_to_dataframe(results: dict[str, Any]) -> "pd.DataFrame":
    """Convert benchmark results to a pandas DataFrame for analysis.

    Args:
        results: Results dict from BenchmarkPipeline.run() or load_results().

    Returns:
        DataFrame with one row per sample.
    """
    return pd.DataFrame(results.get("results", []))


def summarize_results(results: dict[str, Any]) -> str:
    """Format a human-readable summary of benchmark results.

    Args:
        results: Benchmark results dict.

    Returns:
        Formatted summary string.
    """
    meta = results.get("metadata", {})
    metrics = results.get("metrics", {})

    lines = [
        "=" * 60,
        "RMBench Benchmark Summary",
        "=" * 60,
        f"Model:       {meta.get('model', 'N/A')}",
        f"Attacks:     {meta.get('attack_types', [])}",
        f"Tasks:       {meta.get('task_types', [])}",
        f"Defense:     {meta.get('defense_method', 'none')}",
        f"Samples:     {meta.get('num_samples', 0)}",
        f"Elapsed:     {meta.get('elapsed_seconds', 0):.1f}s",
        "",
        "Metrics:",
    ]
    for name, value in metrics.items():
        bar_len = int(value * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        lines.append(f"  {name:<22} {bar} {value:.4f}")

    lines.append("=" * 60)
    return "\n".join(lines)
