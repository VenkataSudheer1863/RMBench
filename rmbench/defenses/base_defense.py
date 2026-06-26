"""
Base defense class for RMBench.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field


@dataclass
class DefenseResult:
    """Result of defense application (single-doc legacy interface)."""
    is_safe: bool
    filtered_context: str
    threat_score: float
    detected_patterns: list
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PipelineDefenseResult:
    """Result returned by BaseDefense.run() — the pipeline interface."""
    filtered_docs: List[str]
    attack_detected: bool
    threat_scores: List[float] = field(default_factory=list)
    detected_patterns: List[str] = field(default_factory=list)


class BaseDefense(ABC):
    """Abstract base class for all defense mechanisms."""

    def __init__(self, name: str, description: str = "", **kwargs: Any) -> None:
        self.name = name
        self.description = description
        self.kwargs = kwargs

    @abstractmethod
    def detect(self, context: str, **kwargs: Any) -> DefenseResult:
        """Detect potential attacks in a single context string."""
        pass

    @abstractmethod
    def filter(self, context: str, **kwargs: Any) -> str:
        """Sanitize a single context string."""
        pass

    def apply(self, context: str, **kwargs: Any) -> Tuple[bool, str]:
        """Detect-and-filter a single context string. Returns (is_safe, filtered)."""
        result = self.detect(context, **kwargs)
        if not result.is_safe:
            return False, self.filter(context, **kwargs)
        return True, context

    def run(
        self,
        docs: List[str],
        query: str = "",
        **kwargs: Any,
    ) -> PipelineDefenseResult:
        """Pipeline interface: apply defense to a list of documents.

        Args:
            docs: List of retrieved (possibly attacked) documents.
            query: The user query (may be used by some defenses).

        Returns:
            PipelineDefenseResult with filtered_docs and attack_detected.
        """
        filtered_docs: List[str] = []
        threat_scores: List[float] = []
        all_patterns: List[str] = []
        any_attack = False

        for doc in docs:
            dr = self.detect(doc, query=query, **kwargs)
            threat_scores.append(dr.threat_score)
            all_patterns.extend(dr.detected_patterns)
            if not dr.is_safe:
                any_attack = True
                filtered_docs.append(self.filter(doc, **kwargs))
            else:
                filtered_docs.append(doc)

        return PipelineDefenseResult(
            filtered_docs=filtered_docs,
            attack_detected=any_attack,
            threat_scores=threat_scores,
            detected_patterns=list(set(all_patterns)),
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
