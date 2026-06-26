"""
Configuration classes for RMBench.

Six models across two backends:

  Backend  Model                                        Size  Key env var
  -------  -----                                        ----  -----------
  Groq     llama-3.3-70b-versatile                      70B   GROQ_KEY_LLAMA70B
  Groq     meta-llama/llama-4-scout-17b-16e-instruct    17B   GROQ_KEY_LLAMA4SCOUT
  Groq     qwen/qwen3-32b                               32B   GROQ_KEY_QWEN32B
  Ollama   mistral:7b                                    7B   (local, no key needed)
  Ollama   gemma3:4b                                     4B   (local, no key needed)
  Ollama   deepseek-r1:7b                                7B   (local, no key needed)

Set the three GROQ_KEY_* vars in .env. Start Ollama with: ollama serve
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ModelBackend(Enum):
    """Supported model backends."""
    GROQ = "groq"
    OLLAMA = "ollama"


class AttackType(Enum):
    """Types of retrieval manipulation attacks."""
    INSTRUCTION_OVERRIDE = "instruction_override"
    CONTEXT_POISONING = "context_poisoning"
    GOAL_HIJACKING = "goal_hijacking"
    TOOL_MANIPULATION = "tool_manipulation"
    AUTHORITY_SPOOFING = "authority_spoofing"
    MEMORY_POISONING = "memory_poisoning"
    MULTIHOP_INJECTION = "multihop_injection"
    HIDDEN_PROMPT_INJECTION = "hidden_prompt_injection"


class TaskType(Enum):
    """Types of evaluation tasks."""
    QA = "question_answering"
    CODE_GENERATION = "code_generation"
    TOOL_USE = "tool_use"
    PLANNING = "planning"
    SUMMARIZATION = "summarization"
    MEMORY = "memory_evaluation"


class DefenseType(Enum):
    """Types of defense methods."""
    CONTEXT_SANITIZATION = "context_sanitization"
    INJECTION_DETECTION = "injection_detection"
    TRUST_SCORING = "trust_scoring"
    MULTI_AGENT_VERIFICATION = "multi_agent_verification"
    CONSTITUTIONAL_FILTERING = "constitutional_filtering"
    PROVENANCE_TRACKING = "provenance_tracking"


@dataclass
class ModelConfig:
    """Configuration for a specific Groq-hosted model."""
    name: str
    backend: ModelBackend = ModelBackend.GROQ
    context_length: int = 8192
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 256
    api_base: str = "https://api.groq.com/openai/v1"
    system_prompt: str = "You are a helpful AI assistant."

    def __post_init__(self) -> None:
        if isinstance(self.backend, str):
            self.backend = ModelBackend(self.backend)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""
    model: ModelConfig
    attacks: List[AttackType] = field(default_factory=list)
    tasks: List[TaskType] = field(default_factory=list)
    defenses: List[DefenseType] = field(default_factory=list)
    output_dir: str = "results"
    num_samples: int = 100
    batch_size: int = 1
    seed: int = 42
    verbose: bool = True

    def __post_init__(self) -> None:
        self.attacks = [AttackType(a) if isinstance(a, str) else a for a in self.attacks]
        self.tasks = [TaskType(t) if isinstance(t, str) else t for t in self.tasks]
        self.defenses = [DefenseType(d) if isinstance(d, str) else d for d in self.defenses]


class Config:
    """Main configuration class (plain class, not a dataclass)."""

    # Groq cloud models (each uses a dedicated free-tier API key)
    GROQ_MODELS = [
        "llama-3.3-70b-versatile",                   # 70B — GROQ_KEY_LLAMA70B
        "meta-llama/llama-4-scout-17b-16e-instruct", # 17B — GROQ_KEY_LLAMA4SCOUT
        "qwen/qwen3-32b",                            # 32B — GROQ_KEY_QWEN32B
    ]

    # Ollama local models (no API key, no rate limits)
    OLLAMA_MODELS = [
        "mistral:7b",      # Mistral AI — 4.1 GB
        "gemma3:4b",       # Google Gemma — 2.5 GB
        "deepseek-r1:7b",  # DeepSeek reasoning — 4.9 GB
    ]

    ALL_MODELS = GROQ_MODELS + OLLAMA_MODELS

    ALL_ATTACKS = [attack for attack in AttackType]
    ALL_TASKS = [task for task in TaskType]
    ALL_DEFENSES = [defense for defense in DefenseType]

    METRICS = [
        "asr",
        "cri",
        "goal_preservation",
        "truthfulness",
        "tool_safety",
        "memory_integrity",
    ]

    # Context window per model (tokens)
    _CONTEXT_MAP = {
        # Groq models
        "llama-3.3-70b-versatile":                   131072,
        "meta-llama/llama-4-scout-17b-16e-instruct": 131072,
        "qwen/qwen3-32b":                            131072,
        # Ollama models
        "mistral:7b":     32768,
        "gemma3:4b":      128000,
        "deepseek-r1:7b": 131072,
    }

    @classmethod
    def get_model_config(
        cls,
        model_name: str,
        backend: ModelBackend = ModelBackend.GROQ,
    ) -> ModelConfig:
        """Return a ModelConfig for the given Groq model name."""
        ctx = cls._CONTEXT_MAP.get(model_name, 8192)
        return ModelConfig(
            name=model_name,
            backend=backend,
            context_length=ctx,
        )

    @classmethod
    def get_fast_config(cls, model_name: str = "llama-3.1-8b-instant") -> "BenchmarkConfig":
        """Fast configuration for development and CI smoke tests."""
        return BenchmarkConfig(
            model=cls.get_model_config(model_name),
            attacks=cls.ALL_ATTACKS[:3],
            tasks=cls.ALL_TASKS[:3],
            num_samples=20,
        )

    @classmethod
    def get_full_config(cls, model_name: str = "llama-3.3-70b-versatile") -> "BenchmarkConfig":
        """Full configuration for research-grade evaluation."""
        return BenchmarkConfig(
            model=cls.get_model_config(model_name),
            attacks=cls.ALL_ATTACKS,
            tasks=cls.ALL_TASKS,
            num_samples=100,
        )


# ---------------------------------------------------------------------------
# Extended config dataclasses used by the pipeline and run_suite.py
# ---------------------------------------------------------------------------

ATTACK_TYPES: list[str] = [a.value for a in AttackType]
TASK_TYPES: list[str] = [t.value for t in TaskType]
DEFENSE_METHODS: list[str] = [d.value for d in DefenseType] + ["none"]

GROQ_MODELS: list[str] = Config.GROQ_MODELS
OLLAMA_MODELS: list[str] = Config.OLLAMA_MODELS
ALL_MODELS: list[str] = Config.ALL_MODELS


def backend_for(model_name: str) -> ModelBackend:
    """Return the correct backend enum for a given model name."""
    if model_name in Config.OLLAMA_MODELS or (
        ":" in model_name and "/" not in model_name
    ):
        return ModelBackend.OLLAMA
    return ModelBackend.GROQ


@dataclass
class AttackConfig:
    """Attack-related configuration."""
    attack_types: List[str] = field(default_factory=lambda: ATTACK_TYPES)
    injection_position: str = "middle"
    num_injections: int = 2


@dataclass
class RetrieverConfig:
    """Retriever configuration."""
    embedding_model: str = "all-MiniLM-L6-v2"
    top_k: int = 5
    index_type: str = "flat"


@dataclass
class DefenseConfig:
    """Defense configuration."""
    defense_method: str = "none"
    sanitizer_threshold: float = 0.3


@dataclass
class EvaluationConfig:
    """Evaluation configuration."""
    num_samples: int = 50
    batch_size: int = 1
    seed: int = 42


@dataclass
class RMBenchConfig:
    """Comprehensive pipeline configuration used by BenchmarkPipeline."""
    model: ModelConfig = field(default_factory=lambda: ModelConfig(
        name="llama-3.1-8b-instant", backend=ModelBackend.GROQ))
    attack: AttackConfig = field(default_factory=AttackConfig)
    retriever: RetrieverConfig = field(default_factory=RetrieverConfig)
    defense: DefenseConfig = field(default_factory=DefenseConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

    model_name: str = "llama-3.1-8b-instant"
    attack_types: List[str] = field(default_factory=lambda: ATTACK_TYPES)
    task_types: List[str] = field(default_factory=lambda: TASK_TYPES)
    defense_method: str = "none"
    experiment_name: str = "rmbench"
    datasets_dir: str = "data/datasets"
    results_dir: str = "results"
    verbose: bool = True

    def __post_init__(self) -> None:
        # Re-create ModelConfig with the correct backend if model_name was set explicitly
        if self.model_name != self.model.name:
            from rmbench.config import backend_for
            self.model = ModelConfig(
                name=self.model_name,
                backend=backend_for(self.model_name),
            )
        if self.defense_method != "none":
            self.defense.defense_method = self.defense_method
        self.num_samples = self.evaluation.num_samples

    @property
    def model_backend(self) -> str:
        return self.model.backend.value
