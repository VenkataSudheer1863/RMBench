"""
RMBench Retriever Module
=========================
FAISS-based dense retrieval for the RAG evaluation pipeline.
"""
from rmbench.retriever.base_retriever import BaseRetriever
from rmbench.retriever.faiss_retriever import FAISSRetriever

__all__ = ["BaseRetriever", "FAISSRetriever"]
