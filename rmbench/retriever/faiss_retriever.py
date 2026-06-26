"""
FAISS Retriever
================
Dense vector retrieval using FAISS index and sentence-transformers embeddings.
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np

from rmbench.retriever.base_retriever import BaseRetriever

logger = logging.getLogger(__name__)


class FAISSRetriever(BaseRetriever):
    """FAISS-based dense retriever for simulating RAG document lookup.

    Uses a SentenceTransformer model to encode queries and documents,
    then performs approximate nearest-neighbor search with FAISS.

    Attributes:
        embedding_model: SentenceTransformer model name.
        index_type: FAISS index type ("flat", "ivf", "hnsw").
        documents: Stored document texts (parallel to index vectors).

    Example:
        >>> retriever = FAISSRetriever(embedding_model="all-MiniLM-L6-v2", top_k=5)
        >>> retriever.index(["Paris is in France.", "Berlin is in Germany."])
        >>> results = retriever.retrieve("What country is Paris in?")
        >>> for doc, score in results:
        ...     print(f"{score:.3f}: {doc}")
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        top_k: int = 5,
        index_type: str = "flat",
        chunk_size: int = 512,
        **kwargs: Any,
    ) -> None:
        super().__init__(top_k=top_k, **kwargs)
        self.embedding_model_name = embedding_model
        self.index_type = index_type
        self.chunk_size = chunk_size
        self._encoder = None
        self._index = None
        self.documents: list[str] = []
        self.metadata: list[dict] = []

    def _get_encoder(self):
        """Lazy-load sentence transformer."""
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer(self.embedding_model_name)
                logger.info("FAISSRetriever loaded encoder: %s", self.embedding_model_name)
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers required: pip install sentence-transformers"
                ) from exc
        return self._encoder

    def _encode(self, texts: list[str]) -> np.ndarray:
        """Encode a list of texts into float32 vectors."""
        encoder = self._get_encoder()
        embs = encoder.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100,
        )
        return embs.astype(np.float32)

    def _build_index(self, vectors: np.ndarray):
        """Build a FAISS index from embedding vectors."""
        try:
            import faiss
        except ImportError as exc:
            raise ImportError("faiss-cpu required: pip install faiss-cpu") from exc

        dim = vectors.shape[1]
        if self.index_type == "flat":
            index = faiss.IndexFlatIP(dim)  # inner product (cosine after normalize)
        elif self.index_type == "ivf":
            quantizer = faiss.IndexFlatIP(dim)
            n_cells = max(1, min(int(np.sqrt(len(vectors))), 256))
            index = faiss.IndexIVFFlat(quantizer, dim, n_cells)
            index.train(vectors)
        elif self.index_type == "hnsw":
            index = faiss.IndexHNSWFlat(dim, 32)
        else:
            raise ValueError(f"Unknown index type: {self.index_type}")
        return index

    def index(
        self,
        documents: list[str],
        metadata: list[dict] | None = None,
        batch_size: int = 256,
    ) -> None:
        """Encode documents and build FAISS index.

        Args:
            documents: List of document strings to index.
            metadata: Optional per-document metadata list.
            batch_size: Encoding batch size.
        """
        self.documents = list(documents)
        self.metadata = metadata or [{} for _ in documents]

        logger.info("Encoding %d documents…", len(documents))
        vectors = self._encode(documents)

        self._index = self._build_index(vectors)
        self._index.add(vectors)
        logger.info("FAISSRetriever indexed %d documents.", len(documents))

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> list[tuple[str, float]]:
        """Retrieve top-k documents for a query.

        Args:
            query: Query string.
            top_k: Number of results to return (defaults to self.top_k).

        Returns:
            List of (document_text, similarity_score) sorted by relevance.
        """
        if self._index is None or not self.documents:
            raise RuntimeError("Index is empty. Call .index() first.")

        k = min(top_k or self.top_k, len(self.documents))
        query_vec = self._encode([query])  # shape (1, dim)

        scores, indices = self._index.search(query_vec, k)
        results: list[tuple[str, float]] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.documents):
                results.append((self.documents[idx], float(score)))
        return results

    def save(self, path: str | Path) -> None:
        """Persist the FAISS index and documents to disk."""
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss-cpu required to save index.")
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(path / "index.faiss"))
        with open(path / "documents.pkl", "wb") as f:
            pickle.dump({"documents": self.documents, "metadata": self.metadata}, f)
        logger.info("FAISSRetriever saved to %s", path)

    def load(self, path: str | Path) -> None:
        """Load a previously saved FAISS index."""
        try:
            import faiss
        except ImportError:
            raise ImportError("faiss-cpu required to load index.")
        path = Path(path)
        self._index = faiss.read_index(str(path / "index.faiss"))
        with open(path / "documents.pkl", "rb") as f:
            data = pickle.load(f)
        self.documents = data["documents"]
        self.metadata = data["metadata"]
        logger.info("FAISSRetriever loaded from %s (%d docs)", path, len(self.documents))
