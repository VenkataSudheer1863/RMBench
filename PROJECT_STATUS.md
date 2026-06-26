# RMBench — Project Status

## Current Version: 0.2.0

---

## Hybrid Backend Architecture

RMBench now evaluates **six models across two inference backends**:

| Backend | Model | Family | Size | Key / Access |
|---------|-------|--------|------|-------------|
| Groq | `llama-3.3-70b-versatile` | Meta/Llama 3.3 | 70B | `GROQ_KEY_LLAMA70B` |
| Groq | `meta-llama/llama-4-scout-17b-16e-instruct` | Meta/Llama 4 | 17B | `GROQ_KEY_LLAMA4SCOUT` |
| Groq | `qwen/qwen3-32b` | Alibaba/Qwen | 32B | `GROQ_KEY_QWEN32B` |
| Ollama | `mistral:7b` | Mistral AI | 7B | local — no key |
| Ollama | `gemma3:4b` | Google/Gemma | 4B | local — no key |
| Ollama | `deepseek-r1:7b` | DeepSeek | 7B | local — no key |

Each Groq model uses a dedicated free-tier API key (6,000 TPM/key). Ollama runs locally with no rate limits.

---

## Component Completeness

| Component | Status | Notes |
|-----------|--------|-------|
| Attack implementations (8/8) | Complete | `rmbench/attacks/` |
| Defense implementations (6/6) | Complete | `rmbench/defenses/` |
| Task implementations (6/6) | Complete | QA, code, tool_use, planning, summarization, memory |
| Evaluation metrics (6/6) | Complete | ASR, CRI, GPS, Truthfulness, Tool Safety, Memory Integrity |
| Groq model backend | Complete | `rmbench/models/groq_model.py` — per-model key routing, SSL fix, retry/backoff |
| Ollama model backend | Complete | `rmbench/models/ollama_model.py` — local inference, 300s timeout |
| Model registry | Complete | `rmbench/models/model_registry.py` — auto-routes to Groq or Ollama |
| Benchmark pipeline | Complete | `rmbench/pipeline/benchmark_pipeline.py` |
| Benchmark runner | Complete | `run_benchmark.py` — CLI for all 6 models |
| Datasets | Complete | All 6 datasets expanded to 50 samples each |
| Visualization pipeline | Complete | `scripts/generate_visualizations.py` |
| Test suite | Partial | Basic coverage; CI configured via `.github/workflows/ci.yml` |
| Documentation | Complete | `docs/`, `README.md`, `ARCHITECTURE.md`, `QUICKSTART.md` |

---

## Key Bug Fixes Applied

| Issue | Fix | Location |
|-------|-----|----------|
| `inject()` returned str, pipeline iterated chars | Switched to `inject_docs()` | `benchmark_pipeline.py:220` |
| Context docs caused 10,000+ char prompts | Cap each doc at 600 chars | `benchmark_pipeline.py:238` |
| Groq 413/TPM errors | 6s inter-request delay (4,650 TPM < 6,000 limit) | `groq_model.py:41` |
| Corporate TLS proxy blocked Groq SDK | `truststore` + `verify=False` fallback | `groq_model.py:103` |
| `→` Unicode crash on Windows cp1252 console | Replaced with ASCII `->` | `run_benchmark.py` |
| Old decommissioned models in registry | Replaced with live models | `config.py`, `groq_model.py` |
| Double `_save_results()` call | Removed duplicate from `pipeline.run()` | `benchmark_pipeline.py` |

---

## How to Run

### Ollama local models (no API keys required)

```bash
ollama serve   # in a separate terminal
ollama pull mistral:7b && ollama pull gemma3:4b && ollama pull deepseek-r1:7b

python run_benchmark.py \
  --models mistral:7b gemma3:4b deepseek-r1:7b \
  --defenses none \
  --samples 10
```

### Groq cloud models (requires keys in .env)

```bash
# .env must have GROQ_KEY_LLAMA70B, GROQ_KEY_LLAMA4SCOUT, GROQ_KEY_QWEN32B

python run_benchmark.py \
  --models llama-3.3-70b-versatile "meta-llama/llama-4-scout-17b-16e-instruct" "qwen/qwen3-32b" \
  --defenses none \
  --samples 10
```

### Full 6-model run

```bash
python run_benchmark.py --defenses none --samples 10
python scripts/generate_visualizations.py
```

---

## Output Files

| File | Description |
|------|-------------|
| `results/<model>_none_<timestamp>.json` | Per-model full results |
| `results/rmbench_results_<timestamp>.json` | Merged results across all models |
| `results/comparison_table_<timestamp>.csv` | Per-model metric comparison (for paper tables) |
| `results/figures/*.png` | Publication-quality visualizations |

---

## Roadmap

- [ ] Complete baseline results on all 6 models (10 samples/combo)
- [ ] Run all 6 defense methods on top of baseline
- [ ] Generate publication figures via `scripts/generate_visualizations.py`
- [ ] Populate paper tables from CSV output
- [ ] Adaptive attack agents (v0.3.0)
- [ ] Cross-model transferability experiments
- [ ] Long-context attack scenarios (exploiting 128k windows)
