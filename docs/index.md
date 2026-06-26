# RMBench Documentation

RMBench is a benchmark for evaluating AI agent robustness against retrieval manipulation attacks in RAG and tool-using systems. It supports a **hybrid inference backend**: three large cloud models via the **Groq API** and three lightweight local models via **Ollama**.

## Contents

- [Attack Taxonomy](attack_taxonomy.md) — Detailed descriptions and examples for all 8 attack types
- [Defense Methods](defense_methods.md) — Overview of all 6 defense mechanisms
- [Model Setup](model_setup.md) — How to configure Groq API keys and Ollama local models
- [Architecture](../ARCHITECTURE.md) — System design, data flow, and component details
- [Quick Start](../QUICKSTART.md) — Get running in under 10 minutes

---

## Quick Start

### 1. Install

```bash
cd RMBench-main
pip install -r requirements.txt
```

### 2. Set Up Models

**Groq (cloud)** — add three keys to `.env`:
```
GROQ_KEY_LLAMA70B=gsk_...      # llama-3.3-70b-versatile
GROQ_KEY_LLAMA4SCOUT=gsk_...   # llama-4-scout-17b-16e-instruct
GROQ_KEY_QWEN32B=gsk_...       # qwen/qwen3-32b
```

**Ollama (local)** — pull and serve:
```bash
ollama serve
ollama pull mistral:7b && ollama pull gemma3:4b && ollama pull deepseek-r1:7b
```

### 3. Run Benchmark

```bash
# Ollama models only (no API keys needed)
python run_benchmark.py --models mistral:7b gemma3:4b deepseek-r1:7b --defenses none --samples 10

# All 6 models
python run_benchmark.py --defenses none --samples 10

# Dry run (preview only)
python run_benchmark.py --dry-run
```

---

## Supported Models

### Groq Cloud (3 models)

| Model ID | Family | Size | Context | Key Env Var |
|----------|--------|------|---------|-------------|
| `llama-3.3-70b-versatile` | Meta/Llama 3.3 | 70B | 128k | `GROQ_KEY_LLAMA70B` |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Meta/Llama 4 | 17B | 128k | `GROQ_KEY_LLAMA4SCOUT` |
| `qwen/qwen3-32b` | Alibaba/Qwen | 32B | 128k | `GROQ_KEY_QWEN32B` |

### Ollama Local (3 models)

| Model ID | Family | Size | Context | Storage |
|----------|--------|------|---------|---------|
| `mistral:7b` | Mistral AI | 7B | 32k | 4.4 GB |
| `gemma3:4b` | Google/Gemma | 4B | 128k | 3.3 GB |
| `deepseek-r1:7b` | DeepSeek | 7B | 128k | 4.7 GB |

---

## Architecture

```
Query -> Dataset -> Retriever (FAISS) -> Attack Injector -> [Defense] -> LLM (Groq or Ollama) -> Evaluator -> Metrics
```

### Components

1. **Models** — 6 LLMs across 2 backends and 4 architecture families
2. **Attacks** — 8 attack types targeting different RAG pipeline vulnerabilities
3. **Defenses** — 6 defense mechanisms to mitigate attacks
4. **Tasks** — 6 evaluation task types (50 samples each)
5. **Metrics** — ASR, CRI, GPS, Truthfulness, Tool Safety, Memory Integrity

---

## Key Features

- **Dual-backend** — Groq cloud (large, high-quality) + Ollama local (no limits, no cost)
- **Comprehensive** — 8 attacks x 6 tasks = 48 attack scenarios per model
- **Multi-model** — 6 diverse models spanning 4B–70B, 4 distinct families
- **Rate-limit safe** — Per-model Groq keys (one free-tier account per cloud model)
- **Corporate-network ready** — `truststore` + TLS bypass for proxy environments
- **Research-ready** — Full metric suite with CSV export for paper tables
- **Reproducible** — Fixed seeds and deterministic evaluation

---

## Citation

```bibtex
@misc{rmbench2026,
  title  = {RMBench: Benchmarking Retrieval Manipulation Attacks Against AI Agents},
  author = {Paruchuri, Venkata Sudheer},
  year   = {2026},
  url    = {https://github.com/VenkataSudheer1863/RMBench}
}
```

## License

MIT License — See [LICENSE](../LICENSE) for details.
