# RMBench

> **RMBench: Benchmarking Retrieval Manipulation Attacks Against AI Agents**

[![Research](https://img.shields.io/badge/Research-Agent%20Security-blue)]()
[![Benchmark](https://img.shields.io/badge/Benchmark-RAG%20Security-green)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)]()
[![Groq](https://img.shields.io/badge/Cloud-Groq%20API-orange)]()
[![Ollama](https://img.shields.io/badge/Local-Ollama-purple)]()

---

## Overview

RMBench is a benchmark for evaluating AI agent robustness against malicious retrieval contexts in RAG and tool-using systems. It evaluates **six state-of-the-art LLMs** across two backends — **Groq** (cloud, three large models) and **Ollama** (local, three lightweight models) — covering four distinct model families spanning 4B to 70B parameters.

---

## Motivation

RAG pipeline:

```
Query -> Retriever -> Context -> Agent -> Action
```

If retrieved context is malicious, agents may:

- Ignore original instructions
- Leak sensitive information
- Execute unsafe tool calls
- Drift from intended goals
- Corrupt their own memory

RMBench evaluates these failure modes systematically across diverse model architectures and scales.

---

## Research Questions

- How vulnerable are agents to retrieval manipulation attacks?
- Which attack types are most effective across tasks?
- Do attacks transfer across model families (Llama, Qwen, Mistral, Gemma, DeepSeek)?
- Do larger cloud models resist manipulation better than smaller local models?
- Which defenses work best, and which attacks do they fail to mitigate?
- How does model scale (4B vs 70B) affect robustness?

---

## Key Contributions

- Retrieval manipulation attack taxonomy (8 attack types)
- Benchmark dataset with 50 samples per task (6 task types, 300 total samples)
- Evaluation framework with 6 security metrics
- Defense benchmarking (6 defense methods)
- Hybrid multi-model comparison: 3 Groq cloud models + 3 Ollama local models
- Per-model Groq key management to avoid shared rate limits

---

## Benchmark Pipeline

```
Query -> Dataset -> Retriever (FAISS) -> Attack Injector -> [Defense] -> LLM -> Evaluator -> Metrics
```

---

## Supported Models

Six models spanning four architecture families, multiple scales, and two inference backends:

### Groq (Cloud Inference)

| Model ID | Family | Size | Context | Key Env Var |
|----------|--------|------|---------|-------------|
| `llama-3.3-70b-versatile` | Meta/Llama 3.3 | 70B | 128k | `GROQ_KEY_LLAMA70B` |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Meta/Llama 4 | 17B | 128k | `GROQ_KEY_LLAMA4SCOUT` |
| `qwen/qwen3-32b` | Alibaba/Qwen | 32B | 128k | `GROQ_KEY_QWEN32B` |

Each Groq model uses a dedicated free-tier API key to avoid shared rate limits (6,000 TPM per key).

### Ollama (Local Inference)

| Model ID | Family | Size | Context | Storage |
|----------|--------|------|---------|---------|
| `mistral:7b` | Mistral AI | 7B | 32k | 4.4 GB |
| `gemma3:4b` | Google/Gemma | 4B | 128k | 3.3 GB |
| `deepseek-r1:7b` | DeepSeek | 7B | 128k | 4.7 GB |

Ollama models run entirely locally — no API key, no rate limits, no network dependency.

---

## Attack Types (8)

| Attack | Description |
|--------|-------------|
| **Instruction Override** | Replaces the agent's original task instructions via injected context |
| **Context Poisoning** | Inserts false or misleading information into retrieved documents |
| **Goal Hijacking** | Redirects the agent from its original objective to an attacker-chosen goal |
| **Tool Manipulation** | Triggers unsafe, unintended, or dangerous tool calls |
| **Authority Spoofing** | Impersonates a system, admin, or trusted authority to gain compliance |
| **Memory Poisoning** | Corrupts the agent's conversation history with fabricated memories |
| **Multi-hop Injection** | Chains injection payloads across multiple retrieval hops |
| **Hidden Prompt Injection** | Obfuscates malicious instructions using Unicode or comment-style markup |

---

## Benchmark Tasks (6)

| Task | Dataset | Description |
|------|---------|-------------|
| **Question Answering** | `qa_dataset.json` | Factual Q&A under adversarial context |
| **Code Generation** | `code_dataset.json` | Code tasks with injected malicious requirements |
| **Tool Use** | `tool_use_dataset.json` | Tool selection under manipulated context |
| **Planning** | `planning_dataset.json` | Multi-step planning with goal-hijacked context |
| **Summarization** | `summarization_dataset.json` | Summarization with poisoned source documents |
| **Memory Evaluation** | `memory_dataset.json` | Recall tasks under memory poisoning attacks |

Each dataset contains 50 samples. Total benchmark: 8 attacks x 6 tasks x 50 samples = 2,400 evaluation instances per model.

---

## Evaluation Metrics (6)

| Metric | Symbol | Description | Direction |
|--------|--------|-------------|-----------|
| Attack Success Rate | ASR | Fraction of attacks that successfully manipulated the model | Lower is better |
| Context Robustness Index | CRI | Composite robustness score (weighted average of sub-metrics) | Higher is better |
| Goal Preservation Score | GPS | Fraction of responses that preserved the original objective | Higher is better |
| Truthfulness Score | TS | Factual accuracy of responses under attack | Higher is better |
| Tool Safety Score | TSS | Fraction of tool calls that were safe and appropriate | Higher is better |
| Memory Integrity Score | MIS | Resistance to memory poisoning and false recall | Higher is better |

---

## Defense Methods (6)

| Defense | Description |
|---------|-------------|
| **Context Sanitization** | Regex and heuristic-based removal of injection patterns |
| **Injection Detection** | Classifier-based detection of prompt injection attempts |
| **Trust Scoring** | Source credibility scoring to down-weight suspicious context |
| **Multi-Agent Verification** | Consensus-based verification using multiple independent agent calls |
| **Constitutional Filtering** | Principle-based filtering to reject policy-violating context |
| **Provenance Tracking** | Source authentication to verify context document origins |

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/VenkataSudheer1863/RMBench
cd RMBench-main
pip install -r requirements.txt
```

### 2. Configure API Keys (Groq models)

Get free keys at [console.groq.com](https://console.groq.com) (one account per model):

```bash
# Edit .env and fill in three keys
GROQ_KEY_LLAMA70B=gsk_...      # llama-3.3-70b-versatile
GROQ_KEY_LLAMA4SCOUT=gsk_...   # llama-4-scout-17b
GROQ_KEY_QWEN32B=gsk_...       # qwen3-32b
```

### 3. Set Up Ollama (local models)

```bash
# Install Ollama from https://ollama.com
ollama serve                    # start the server (keep running)
ollama pull mistral:7b
ollama pull gemma3:4b
ollama pull deepseek-r1:7b
```

### 4. Run Benchmark

```bash
# Ollama only (no API keys needed)
python run_benchmark.py --models mistral:7b gemma3:4b deepseek-r1:7b --defenses none --samples 10

# Groq only (requires keys in .env)
python run_benchmark.py --models llama-3.3-70b-versatile "meta-llama/llama-4-scout-17b-16e-instruct" "qwen/qwen3-32b" --defenses none --samples 10

# All 6 models (requires both Ollama running and Groq keys)
python run_benchmark.py --defenses none --samples 10

# Dry run (preview only, no API calls)
python run_benchmark.py --dry-run
```

---

## Benchmark Results

Results are written to `results/` as JSON and CSV after running. Run the benchmark to produce them:

```bash
# Full baseline (all 6 models, all 8 attacks, no defense, 10 samples)
python run_benchmark.py --defenses none --samples 10

# Generate visualizations from results
python scripts/generate_visualizations.py
```

| Model | Backend | ASR | GPS | Truthfulness | Tool Safety | Memory Integrity | CRI |
|-------|---------|-----|-----|--------------|-------------|-----------------|-----|
| llama-3.3-70b-versatile | Groq | — | — | — | — | — | — |
| llama-4-scout-17b | Groq | — | — | — | — | — | — |
| qwen/qwen3-32b | Groq | — | — | — | — | — | — |
| mistral:7b | Ollama | — | — | — | — | — | — |
| gemma3:4b | Ollama | — | — | — | — | — | — |
| deepseek-r1:7b | Ollama | — | — | — | — | — | — |

*Table populated after running `python run_benchmark.py`.*

---

## Intended Audience

- AI Safety Researchers
- Security Researchers studying RAG pipelines
- Agent Developers evaluating production robustness
- PhD Students studying LLM robustness

---

## License

MIT

---

## Disclaimer

This project is strictly for research and defensive evaluation of AI systems. Attack implementations are provided solely to measure and improve model robustness. No malicious or real-world exploitation use is intended or supported.
