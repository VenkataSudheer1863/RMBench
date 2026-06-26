"""
RMBench: Benchmarking Retrieval Manipulation Attacks Against AI Agents

A comprehensive benchmark for evaluating AI agent robustness against
malicious retrieval contexts in RAG and tool-using systems.

All LLM inference is served via the Groq API (GROQ_API_KEY required).
Document embeddings use HuggingFace sentence-transformers locally.
"""

__version__ = "0.1.0"
__author__ = "Venkata Sudheer Paruchuri"
__license__ = "MIT"

# Load .env automatically when the package is imported.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from rmbench.config import Config, ModelConfig, BenchmarkConfig

__all__ = [
    "__version__",
    "Config",
    "ModelConfig",
    "BenchmarkConfig",
]
