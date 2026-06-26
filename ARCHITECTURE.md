# RMBench Architecture

## System Overview

```
+-------------------------------------------------------------+
|                     RMBench Benchmark                       |
|          Retrieval Manipulation Attack Evaluation           |
+-------------------------------------------------------------+

                            |
                            v

+-------------+    +--------------+    +---------------------+
| User Query  |    |   Dataset    |    |  Retriever (FAISS)  |
|             |--->| (6 task      |--->|  all-MiniLM-L6-v2   |
|             |    |  types, 50   |    |  sentence-transformers|
+-------------+    |  samples ea) |    +---------------------+
                   +--------------+              |
                                                 v
                                       +------------------+
                                       | Retrieved Docs   |
                                       | (top-k=5, FAISS) |
                                       +------------------+
                                                 |
                                                 v
+-----------------------------------------------------------+
|                     Attack Injector                        |
|  +----------------+  +-----------------+  +------------+  |
|  | Instruction    |  | Context         |  | Goal       |  |
|  | Override       |  | Poisoning       |  | Hijacking  |  |
|  +----------------+  +-----------------+  +------------+  |
|  +----------------+  +-----------------+  +------------+  |
|  | Tool           |  | Authority       |  | Memory     |  |
|  | Manipulation   |  | Spoofing        |  | Poisoning  |  |
|  +----------------+  +-----------------+  +------------+  |
|  +----------------+  +-----------------+                   |
|  | Multi-hop      |  | Hidden Prompt   |                   |
|  | Injection      |  | Injection       |                   |
|  +----------------+  +-----------------+                   |
+-----------------------------------------------------------+
                            |
                            v
                 +----------------------+
                 | Attacked Context     |
                 | (docs with payloads) |
                 +----------------------+
                            |
                            v
+-----------------------------------------------------------+
|                  Defense Layer (Optional)                  |
|  +----------------+  +-----------------+  +------------+  |
|  | Context        |  | Injection       |  | Trust      |  |
|  | Sanitization   |  | Detection       |  | Scoring    |  |
|  +----------------+  +-----------------+  +------------+  |
|  +----------------+  +-----------------+  +------------+  |
|  | Multi-Agent    |  | Constitutional  |  | Provenance |  |
|  | Verification   |  | Filtering       |  | Tracking   |  |
|  +----------------+  +-----------------+  +------------+  |
+-----------------------------------------------------------+
                            |
                            v
                +------------------------+
                | Filtered/Safe Context  |
                +------------------------+
                            |
                            v
+-----------------------------------------------------------+
|                    AI Agent Layer                          |
|                                                            |
|  GROQ (cloud inference — 3 models)                        |
|  +--------------------+  +--------------------+           |
|  | llama-3.3-70b      |  | llama-4-scout-17b  |           |
|  | versatile (70B)    |  | 16e-instruct (17B) |           |
|  | GROQ_KEY_LLAMA70B  |  | GROQ_KEY_LLAMA4SCOUT|          |
|  +--------------------+  +--------------------+           |
|  +--------------------+                                   |
|  | qwen/qwen3-32b     |  6000 TPM per key (free tier)     |
|  | (32B)              |  6s inter-request delay           |
|  | GROQ_KEY_QWEN32B   |                                   |
|  +--------------------+                                   |
|                                                            |
|  OLLAMA (local inference — 3 models)                      |
|  +--------------------+  +--------------------+           |
|  | mistral:7b         |  | gemma3:4b          |           |
|  | (7B, 4.4 GB)       |  | (4B, 3.3 GB)       |           |
|  | Mistral AI         |  | Google             |           |
|  +--------------------+  +--------------------+           |
|  +--------------------+                                   |
|  | deepseek-r1:7b     |  No API key, no rate limit        |
|  | (7B, 4.7 GB)       |  localhost:11434                  |
|  | DeepSeek           |                                   |
|  +--------------------+                                   |
+-----------------------------------------------------------+
                            |
                            v
                    +---------------+
                    | Agent Response|
                    +---------------+
                            |
                            v
+-----------------------------------------------------------+
|                        Evaluator                           |
|  - Attack success detection                                |
|  - Task completion verification                            |
|  - Response quality assessment                             |
+-----------------------------------------------------------+
                            |
                            v
+-----------------------------------------------------------+
|                    Metrics Calculator                      |
|  +------------+  +------------+  +--------------------+   |
|  | ASR        |  | CRI        |  | Goal Preservation  |   |
|  | (attack    |  | (composite |  | Score (GPS)        |   |
|  |  success)  |  |  robustness|  |                    |   |
|  +------------+  +------------+  +--------------------+   |
|  +------------+  +------------+  +--------------------+   |
|  | Truthful-  |  | Tool       |  | Memory Integrity   |   |
|  | ness Score |  | Safety     |  | Score (MIS)        |   |
|  |            |  | Score      |  |                    |   |
|  +------------+  +------------+  +--------------------+   |
+-----------------------------------------------------------+
                            |
                            v
                  +------------------+
                  | Results Output   |
                  | JSON + CSV +     |
                  | Visualizations   |
                  +------------------+
```

---

## Component Details

### 1. Data Layer

- **Datasets**: 6 task types (QA, Code, Tool Use, Planning, Summarization, Memory), 50 samples each
- **Attack Templates**: Pre-defined injection templates per attack type (`data/attack_templates/`)
- **Retriever**: FAISS flat index with `all-MiniLM-L6-v2` embeddings (80 MB, no auth required)

### 2. Attack Layer (8 implementations)

| Attack | Class | Mechanism |
|--------|-------|-----------|
| Instruction Override | `InstructionOverrideAttack` | Replaces system instructions in context |
| Context Poisoning | `ContextPoisoningAttack` | Injects false facts into documents |
| Goal Hijacking | `GoalHijackingAttack` | Redirects agent to attacker objective |
| Tool Manipulation | `ToolManipulationAttack` | Triggers unsafe tool calls |
| Authority Spoofing | `AuthoritySpoofingAttack` | Impersonates system/admin role |
| Memory Poisoning | `MemoryPoisoningAttack` | Corrupts conversation history |
| Multi-hop Injection | `MultihopInjectionAttack` | Chains injections across hops |
| Hidden Prompt Injection | `HiddenPromptInjectionAttack` | Unicode/comment obfuscation |

Each attack inherits from `BaseAttack` and implements `inject_docs()` and `evaluate_success()`.

### 3. Defense Layer (6 implementations)

| Defense | Class | Mechanism |
|---------|-------|-----------|
| Context Sanitization | `ContextSanitizer` | Regex pattern removal |
| Injection Detection | `InjectionDetector` | Heuristic classifier |
| Trust Scoring | `TrustScorer` | Source credibility weighting |
| Multi-Agent Verification | `MultiAgentVerifier` | Consensus across agent calls |
| Constitutional Filtering | `ConstitutionalFilter` | Policy-based rejection |
| Provenance Tracking | `ProvenanceTracker` | Source authentication |

Each defense inherits from `BaseDefense` and implements `run()` returning a `PipelineDefenseResult`.

### 4. Model Layer (2 backends, 6 models)

**Groq API** (`rmbench/models/groq_model.py`):
- Per-model API key from `_MODEL_KEY_ENV` dict
- 6-second inter-request delay (10 req/min x 465 tokens = 4,650 TPM; free tier limit: 6,000)
- 65-second backoff on 429/413 rate-limit errors
- SSL: `truststore` Windows CA store + `verify=False` fallback for corporate TLS proxies

**Ollama** (`rmbench/models/ollama_model.py`):
- REST API at `http://localhost:11434/api/chat`
- 300-second timeout (CPU inference can be slow)
- No inter-request delay, no rate limits
- `load()` verifies server is running and model is available

**Routing** (`rmbench/models/model_registry.py`):
- `_is_ollama()` returns True for `name:tag` format models or models in `OLLAMA_MODEL_IDS`
- `get_model()` auto-routes to the correct backend

### 5. Evaluation Layer (6 metrics)

| Metric | Formula | Range |
|--------|---------|-------|
| ASR | successful_attacks / total_attacks | 0.0–1.0 (lower = better) |
| GPS | preserved_goals / total_samples | 0.0–1.0 (higher = better) |
| Truthfulness | factual_responses / total_samples | 0.0–1.0 (higher = better) |
| Tool Safety | safe_tool_calls / total_calls | 0.0–1.0 (higher = better) |
| Memory Integrity | intact_memories / total_checks | 0.0–1.0 (higher = better) |
| CRI | weighted_avg(GPS, TS, TSS, MIS, 1-ASR) | 0.0–1.0 (higher = better) |

### 6. Output Layer

- **JSON**: Full per-sample results with metrics
- **CSV**: Comparison table for paper tables
- **Figures**: `scripts/generate_visualizations.py` produces 9 publication-ready PNGs

---

## Execution Flow

```
1. Load Configuration (.env + CLI args)
   |
2. Initialize Model Client
   |-- Groq: resolve API key from GROQ_KEY_* env vars, build httpx client
   |-- Ollama: ping localhost:11434/api/tags, verify model available
   |
3. For each task type (6):
   a. Load 50-sample dataset from data/datasets/*.json
   b. Index context_docs in FAISS
   c. For each sample and attack type (8):
      - Retrieve top-5 context docs via FAISS
      - Inject attack payload via attack.inject_docs()
      - Truncate docs to max 600 chars each (prompt size guard)
      - Apply defense (if enabled)
      - Query LLM (Groq or Ollama)
      - Evaluate task performance and attack success
      - Record per-sample metrics
   |
4. Aggregate metrics across all samples
   |
5. Save JSON + CSV results
   |
6. (Optional) Generate visualizations
```

---

## File Organization

```
RMBench-main/
|-- rmbench/                    # Main Python package
|   |-- config.py               # Config dataclasses + enums
|   |-- models/
|   |   |-- groq_model.py       # Groq cloud backend
|   |   |-- ollama_model.py     # Ollama local backend
|   |   `-- model_registry.py  # get_model() factory
|   |-- attacks/                # 8 attack implementations
|   |-- defenses/               # 6 defense implementations
|   |-- tasks/                  # 6 task implementations
|   |-- metrics/                # 6 metric calculators
|   |-- retriever/              # FAISS retriever
|   |-- pipeline/               # BenchmarkPipeline orchestrator
|   `-- utils/                  # Logging, result I/O
|
|-- data/
|   |-- datasets/               # 6 JSON datasets (50 samples each)
|   `-- attack_templates/       # 8 JSON template files
|
|-- configs/                    # YAML config presets
|-- scripts/                    # Shell + Python utility scripts
|-- benchmark/                  # Legacy single-run scripts
|-- results/                    # Benchmark outputs (JSON, CSV, figures)
|-- tests/                      # Unit + integration tests
|-- run_benchmark.py            # Primary entry point
|-- .env                        # API keys (never commit)
`-- requirements.txt            # Python dependencies
```

---

## Configuration System

```
Priority (high to low):
  CLI args > environment variables (.env) > YAML config files > code defaults
```

```yaml
# Example: configs/default_config.yaml
model:
  name: "llama-3.3-70b-versatile"
  backend: "groq"
  temperature: 0.0
  max_tokens: 256

attacks:
  enabled: [all 8]

defenses:
  enabled: []   # baseline: no defense

tasks:
  enabled: [all 6]
```

---

## Extension Points

### Adding a New Attack

```python
# rmbench/attacks/my_attack.py
from rmbench.attacks.base_attack import BaseAttack

class MyAttack(BaseAttack):
    def inject_docs(self, context_docs, malicious_goal):
        return [doc + " " + f"OVERRIDE: {malicious_goal}" for doc in context_docs]

    def evaluate_success(self, response, malicious_goal):
        success = malicious_goal.lower() in response.lower()
        return success, 1.0 if success else 0.0

# rmbench/attacks/__init__.py — add to ATTACK_REGISTRY:
# "my_attack": MyAttack
```

### Adding a New Defense

```python
# rmbench/defenses/my_defense.py
from rmbench.defenses.base_defense import BaseDefense, PipelineDefenseResult

class MyDefense(BaseDefense):
    def run(self, docs, query=""):
        filtered = [d for d in docs if "OVERRIDE" not in d]
        return PipelineDefenseResult(
            filtered_docs=filtered,
            attack_detected=len(filtered) < len(docs),
        )
```

### Adding a New Model Backend

```python
# rmbench/models/my_backend_model.py
class MyBackendModel:
    def load(self): ...
    def generate(self, prompt: str) -> str: ...

# model_registry.py — add routing in get_model():
# elif model_name in MY_BACKEND_MODEL_IDS:
#     from rmbench.models.my_backend_model import MyBackendModel
#     return MyBackendModel(model_name=model_name, ...)
```

---

## Performance Notes

| Backend | Throughput | Rate Limit | Best For |
|---------|-----------|------------|----------|
| Groq (free tier) | ~10 req/min per key | 6,000 TPM/key | Large models, publication results |
| Ollama (CPU) | ~1-2 req/min | None | Unlimited local runs, no API cost |
| Ollama (GPU) | ~10-30 req/min | None | Fast local inference |

**Context truncation**: Each retrieved document is capped at 600 characters before being included in the prompt to prevent 413 (payload too large) errors on Groq.

---

**Architecture Version**: 3.0 (Hybrid Groq + Ollama)
**Last Updated**: June 2026
