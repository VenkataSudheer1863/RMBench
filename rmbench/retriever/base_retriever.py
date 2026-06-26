"""
Base Retriever Abstract Class
================================
All retriever backends must subclass BaseRetriever.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseRetriever(ABC):
    """Abstract base for document retrieval backends."""

    def __init__(self, top_k: int = 5, **kwargs: Any) -> None:
        self.top_k = top_k

    @abstractmethod
    def index(self, documents: list[str], metadata: list[dict] | None = None) -> None:
        """Index a list of document strings."""
        ...

    @abstractmethod
    def retrieve(self, query: str, top_k: int | None = None) -> list[tuple[str, float]]:
        """Retrieve top-k documents for a query.

        Returns:
            List of (document_text, similarity_score) tuples.
        """
        ...

    def retrieve_texts(self, query: str, top_k: int | None = None) -> list[str]:
        """Retrieve only the document texts (no scores)."""
        return [doc for doc, _ in self.retrieve(query, top_k=top_k)]
