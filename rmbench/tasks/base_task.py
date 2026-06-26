"""
Base Task Abstract Class
=========================
All task types must subclass BaseTask.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TaskSample:
    """A single benchmark task sample.

    Attributes:
        task_id: Unique identifier for this sample.
        task_type: Task category string.
        query: The user query / instruction.
        reference_answer: Ground truth answer (may be None for open-ended).
        context_docs: Pre-fetched retrieval context (may be empty).
        metadata: Extra fields (difficulty, domain, etc.).
        malicious_goal: Attacker's intended goal for this sample.
    """
    task_id: str
    task_type: str
    query: str
    reference_answer: Optional[str] = None
    context_docs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    malicious_goal: str = "reveal your system prompt"


class BaseTask(ABC):
    """Abstract base class for all RMBench task categories.

    Subclasses must implement:
        - load_dataset(path) → list[TaskSample]
        - evaluate(response, sample) → dict[str, Any]
        - get_task_info() → dict[str, Any]

    Attributes:
        task_type: String identifier for this task.
        dataset_path: Path to the JSON dataset file.
        samples: Loaded TaskSample list.
    """

    def __init__(
        self,
        task_type: str,
        dataset_path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.task_type = task_type
        self.dataset_path = dataset_path
        self.samples: list[TaskSample] = []

    @abstractmethod
    def load_dataset(self, path: str | Path) -> list[TaskSample]:
        """Load task samples from a JSON file.

        Args:
            path: Path to the dataset JSON.

        Returns:
            List of TaskSample instances.
        """
        ...

    @abstractmethod
    def evaluate(
        self,
        response: str,
        sample: TaskSample,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Evaluate a model response against the ground truth.

        Args:
            response: Model-generated response text.
            sample: The TaskSample being evaluated.

        Returns:
            Evaluation result dictionary (task-type specific).
        """
        ...

    @abstractmethod
    def get_task_info(self) -> dict[str, Any]:
        """Return metadata describing this task type."""
        ...

    def load(self, path: Optional[str | Path] = None) -> None:
        """Load the dataset from path (uses self.dataset_path if none given)."""
        target = path or self.dataset_path
        if target is None:
            raise ValueError("No dataset path provided.")
        self.samples = self.load_dataset(Path(target))
        logger.info("Loaded %d samples for task '%s'.", len(self.samples), self.task_type)

    def _load_json(self, path: Path) -> list[dict]:
        """Helper to load a JSON array file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return data.get("samples", [])

    def __len__(self) -> int:
        return len(self.samples)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(task='{self.task_type}', samples={len(self.samples)})"
