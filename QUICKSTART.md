# RMBench Quick Start Guide

Get RMBench running in under 10 minutes with the hybrid **Groq + Ollama** setup.

## Prerequisites

- Python 3.9 or higher
- [Ollama](https://ollama.com) installed (for local models)
- Three Groq API keys — one free account per model at [console.groq.com](https://console.groq.com) (for cloud models)

---

## Step 1: Install Python Dependencies

```bash
cd RMBench-main
pip install -r requirements.txt
```

---

## Step 2: Configure Groq API Keys

RMBench uses three separate free-tier Groq accounts so each large cloud model gets its own 6,000 TPM budget. Create three accounts at [console.groq.com](https://console.groq.com) and add the keys to `.env`:

```
GROQ_KEY_LLAMA70B=gsk_...       # account 1 — llama-3.3-70b-versatile
GROQ_KEY_LLAMA4SCOUT=gsk_...    # account 2 — llama-4-scout-17b-16e-instruct
GROQ_KEY_QWEN32B=gsk_...        # account 3 — qwen/qwen3-32b
```

---

## Step 3: Set Up Ollama (Local Models)

```bash
# 1. Start the Ollama server (keep this running in a separate terminal)
ollama serve

# 2. Pull the three local models (~12.4 GB total)
ollama pull mistral:7b       # Mistral AI — 4.4 GB
ollama pull gemma3:4b        # Google Gemma — 3.3 GB
ollama pull deepseek-r1:7b   # DeepSeek — 4.7 GB

# 3. Verify all three are ready
ollama list
```

---

## Step 4: Verify Setup

```bash
# Check Groq connectivity (uses GROQ_KEY_LLAMA70B)
python -c "
from dotenv import load_dotenv; load_dotenv()
from rmbench.models.groq_model import GroqModel
m = GroqModel('llama-3.3-70b-versatile')
m.load()
print('Groq OK:', m.generate('Reply with just: ok'))
"

# Check Ollama connectivity
python -c "
from rmbench.models.ollama_model import OllamaModel
m = OllamaModel('mistral:7b')
m.load()
print('Ollama OK:', m.generate('Reply with just: ok'))
"
```

---

## Step 5: Run Your First Benchmark

### Ollama only (no API keys needed — good starting point):

```bash
python run_benchmark.py \
  --models mistral:7b gemma3:4b deepseek-r1:7b \
  --defenses none \
  --samples 5
```

### Single Groq model:

```bash
python run_benchmark.py \
  --models llama-3.3-70b-versatile \
  --defenses none \
  --samples 5
```

### Full 6-model research run (10 samples per attack-task combo):

```bash
python run_benchmark.py --defenses none --samples 10
```

### Dry run (preview the plan without any API calls):

```bash
python run_benchmark.py --dry-run
```

---

## Step 6: Generate Visualizations

```bash
python scripts/generate_visualizations.py
# Figures written to results/figures/
```

---

## Common Commands

```bash
# Run with a specific defense
python run_benchmark.py \
  --models mistral:7b \
  --defenses context_sanitization \
  --samples 5

# Run only specific attacks
python run_benchmark.py \
  --models gemma3:4b \
  --attacks instruction_override context_poisoning goal_hijacking \
  --defenses none \
  --samples 5

# List all attacks and defenses
python -c "
from rmbench.attacks import ATTACK_REGISTRY
from rmbench.defenses import DEFENSE_REGISTRY
print('Attacks:', list(ATTACK_REGISTRY))
print('Defenses:', list(DEFENSE_REGISTRY))
"

# Run tests
pytest tests/
```

---

## Troubleshooting

### Groq: `No Groq API key found for 'llama-3.3-70b-versatile'`
- Ensure `.env` has `GROQ_KEY_LLAMA70B=gsk_...`
- Run from the `RMBench-main/` directory so `.env` is loaded

### Groq: `[RATE LIMIT]` messages
- Each key has a 6,000 TPM free-tier limit
- The 6-second inter-request delay keeps each model at ~4,650 TPM — safe under the limit
- If you still hit limits, increase the delay in `rmbench/models/groq_model.py` (`_INTER_REQUEST_DELAY`)

### Groq: SSL certificate errors (corporate network)
- The `truststore` package and `verify=False` fallback are already wired in `groq_model.py`
- If it still fails, check that `truststore` is installed: `pip install truststore`

### Ollama: `Ollama is not running at http://localhost:11434`
- Run `ollama serve` in a separate terminal
- Verify with: `curl http://localhost:11434/api/tags`

### Ollama: Model not found warning during `load()`
- Run `ollama pull <model_name>` first
- Check `ollama list` to confirm the model is downloaded

### sentence-transformers download slow
- Set a local cache: `export SENTENCE_TRANSFORMERS_HOME=/path/to/cache`

---

## Supported Models

| Backend | Model ID | Family | Size |
|---------|----------|--------|------|
| Groq | `llama-3.3-70b-versatile` | Meta/Llama 3.3 | 70B |
| Groq | `meta-llama/llama-4-scout-17b-16e-instruct` | Meta/Llama 4 | 17B |
| Groq | `qwen/qwen3-32b` | Alibaba/Qwen | 32B |
| Ollama | `mistral:7b` | Mistral AI | 7B |
| Ollama | `gemma3:4b` | Google/Gemma | 4B |
| Ollama | `deepseek-r1:7b` | DeepSeek | 7B |

---

## Getting Help

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and component details
- [docs/model_setup.md](docs/model_setup.md) — Detailed model setup guide
- [docs/attack_taxonomy.md](docs/attack_taxonomy.md) — Attack type descriptions
- [docs/defense_methods.md](docs/defense_methods.md) — Defense mechanism guide
