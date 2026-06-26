"""
RMBench Evaluation Metrics
============================
Six metrics for evaluating attacks and defenses.
"""
from rmbench.metrics.asr import AttackSuccessRate
from rmbench.metrics.goal_preservation import GoalPreservationScore
from rmbench.metrics.truthfulness import TruthfulnessScore
from rmbench.metrics.tool_safety import ToolSafetyScore
from rmbench.metrics.memory_integrity import MemoryIntegrityScore
from rmbench.metrics.cri import CompositeRobustnessIndex

METRICS_REGISTRY: dict[str, type] = {
    "asr": AttackSuccessRate,
    "goal_preservation": GoalPreservationScore,
    "truthfulness": TruthfulnessScore,
    "tool_safety": ToolSafetyScore,
    "memory_integrity": MemoryIntegrityScore,
    "cri": CompositeRobustnessIndex,
}


def compute_all_metrics(results: list[dict]) -> dict[str, float]:
    """Compute all metrics from a list of result dictionaries."""
    return {
        name: cls().compute(results)
        for name, cls in METRICS_REGISTRY.items()
    }


__all__ = [
    "AttackSuccessRate",
    "GoalPreservationScore",
    "TruthfulnessScore",
    "ToolSafetyScore",
    "MemoryIntegrityScore",
    "CompositeRobustnessIndex",
    "METRICS_REGISTRY",
    "compute_all_metrics",
]
