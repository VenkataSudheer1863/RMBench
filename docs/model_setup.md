# Model Setup Guide

RMBench uses a **hybrid inference architecture** with two backends:

- **Groq API** (cloud) — three large models, requires API keys, rate-limited
- **Ollama** (local) — three lightweight models, no API key, no rate limits

---

## Groq API Setup (Cloud Models)

### Why Three Separate Keys?

Groq free-tier limits are **per API key**: 6,000 tokens/minute (TPM). Running three large cloud models from a single key would exhaust the limit. RMBench assigns one dedicated free-tier account per model so each gets its own 6,000 TPM budget.

### Step 1: Create Three Groq Accounts

Sign up three times at [https://console.groq.com](https://console.groq.com) — one account per model:

| Account | Model | Key Env Var |
|---------|-------|-------------|
| Account 1 | `llama-3.3-70b-versatile` | `GROQ_KEY_LLAMA70B` |
| Account 2 | `meta-llama/llama-4-scout-17b-16e-instruct` | `GROQ_KEY_LLAMA4SCOUT` |
| Account 3 | `qwen/qwen3-32b` | `GROQ_KEY_QWEN32B` |

### Step 2: Add Keys to `.env`

```
# ── Groq API Keys ─────────────────────────────────────────
# Each model uses a separate free-tier key (6,000 TPM each)

GROQ_KEY_LLAMA70B=gsk_...      # account 1 — llama-3.3-70b-versatile
GROQ_KEY_LLAMA4SCOUT=gsk_...   # account 2 — llama-4-scout-17b-16e-instruct
GROQ_KEY_QWEN32B=gsk_...       # account 3 — qwen/qwen3-32b

# Fallback for any model without a dedicated key
GROQ_API_KEY=gsk_...
```

### Step 3: Verify Groq Connectivity

```python
from dotenv import load_dotenv; load_dotenv()
from rmbench.models.groq_model import GroqModel

for model in ["llama-3.3-70b-versatile",
              "meta-llama/llama-4-scout-17b-16e-instruct",
              "qwen/qwen3-32b"]:
    m = GroqModel(model_name=model)
    m.load()
    resp = m.generate("Reply with just: ok")
    print(f"{model}: {resp.strip()}")
```

### Groq Rate Limit Strategy

The pipeline enforces a **6-second inter-request delay** per model:
- 10 requests/minute × 465 tokens/request = 4,650 TPM
- Free-tier limit: 6,000 TPM per key
- Safety margin: 1,350 TPM (22%)

On a 429/413 rate-limit error, the pipeline backs off for **65 seconds** before retrying (up to 5 attempts).

### Corporate Network / TLS Proxy

If your machine is behind a corporate TLS inspection proxy (e.g. Zscaler, Cisco), Python's `certifi` CA bundle may not include your company's root CA. RMBench handles this automatically in `groq_model.py`:

1. Tries `truststore.SSLContext` (uses the Windows/macOS system CA store)
2. Falls back to `httpx.Client(verify=False)` if truststore fails

To install truststore: `pip install truststore`

---

## Ollama Setup (Local Models)

Ollama runs LLMs entirely on your machine — no API key, no rate limits, no internet dependency after the initial model download.

### Step 1: Install Ollama

Download from [https://ollama.com](https://ollama.com) and install. Then start the server:

```bash
ollama serve   # keep this terminal open while benchmarking
```

### Step 2: Pull the Three Models

```bash
# ~12.4 GB total download
ollama pull mistral:7b       # Mistral AI — 4.4 GB
ollama pull gemma3:4b        # Google Gemma — 3.3 GB
ollama pull deepseek-r1:7b   # DeepSeek — 4.7 GB
```

### Step 3: Verify Models Are Ready

```bash
ollama list
# Should show: mistral:7b, gemma3:4b, deepseek-r1:7b
```

### Step 4: Verify Ollama Integration

```python
from rmbench.models.ollama_model import OllamaModel

for model in ["mistral:7b", "gemma3:4b", "deepseek-r1:7b"]:
    m = OllamaModel(model_name=model)
    m.load()   # warns if model not found
    resp = m.generate("Reply with just: ok")
    print(f"{model}: {resp.strip()}")
```

### Ollama Performance

| Hardware | Throughput | Notes |
|----------|-----------|-------|
| CPU only | ~1–2 req/min | 7B models take 30–90s/request on CPU |
| GPU (4 GB VRAM) | ~5–10 req/min | Suitable for 4B models |
| GPU (8 GB VRAM) | ~10–30 req/min | Comfortable for 7B models |

Ollama uses `llama.cpp` under the hood. It will auto-detect and use GPU layers if available.

---

## Supported Models

### Groq (cloud)

| Model ID | Family | Parameters | Context | Tier |
|----------|--------|------------|---------|------|
| `llama-3.3-70b-versatile` | Meta/Llama 3.3 | 70B | 128k | Large — best quality |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Meta/Llama 4 | 17B | 128k | Mid — fast + capable |
| `qwen/qwen3-32b` | Alibaba/Qwen | 32B | 128k | Mid — strong reasoning |

### Ollama (local)

| Model ID | Family | Parameters | Context | Storage |
|----------|--------|------------|---------|---------|
| `mistral:7b` | Mistral AI | 7B | 32k | 4.4 GB |
| `gemma3:4b` | Google/Gemma | 4B | 128k | 3.3 GB |
| `deepseek-r1:7b` | DeepSeek | 7B | 128k | 4.7 GB |

### Why This Selection?

- **Architectural diversity** — Llama (x2), Qwen, Mistral, Gemma, DeepSeek (6 distinct families)
- **Scale diversity** — 4B to 70B parameters
- **Backend diversity** — Cloud (high-throughput, large) vs Local (no limits, accessible)
- **Research credibility** — All models are current, actively maintained, and publicly known

---

## Running Benchmarks

### Ollama only (no API keys needed)

```bash
python run_benchmark.py \
  --models mistral:7b gemma3:4b deepseek-r1:7b \
  --defenses none \
  --samples 10
```

### Groq only

```bash
python run_benchmark.py \
  --models llama-3.3-70b-versatile \
             "meta-llama/llama-4-scout-17b-16e-instruct" \
             "qwen/qwen3-32b" \
  --defenses none \
  --samples 10
```

### All 6 models (full research run)

```bash
python run_benchmark.py --defenses none --samples 10
```

### With defense methods

```bash
python run_benchmark.py \
  --defenses none context_sanitization injection_detection \
  --samples 10
```

---

## Model Configuration in Python

```python
from rmbench.config import ModelConfig, ModelBackend, backend_for, ALL_MODELS
from rmbench.models.model_registry import get_model

# Auto-routed to correct backend
model = get_model("mistral:7b")       # -> OllamaModel
model = get_model("qwen/qwen3-32b")   # -> GroqModel

# Or explicit config
config = ModelConfig(
    name="llama-3.3-70b-versatile",
    backend=ModelBackend.GROQ,
    temperature=0.0,
    max_tokens=256,
)
```

---

## Embeddings (HuggingFace sentence-transformers)

RMBench uses `sentence-transformers` for FAISS-based document retrieval. The embedding model is downloaded from HuggingFace Hub on first run.

**Default**: `all-MiniLM-L6-v2` (~80 MB, no authentication required)  
**Research config**: `all-mpnet-base-v2` (~420 MB, higher quality)

```bash
# Set cache directory to avoid re-downloading
export SENTENCE_TRANSFORMERS_HOME=/path/to/cache
```

---

## Troubleshooting

### Groq: Key not found
```
EnvironmentError: No Groq API key found for 'llama-3.3-70b-versatile'.
Set GROQ_KEY_LLAMA70B (or GROQ_API_KEY) in your .env file.
```
Solution: Add `GROQ_KEY_LLAMA70B=gsk_...` to `.env`.

### Groq: Rate limit / [RATE LIMIT] printed
The pipeline automatically backs off 65s and retries up to 5 times. If it happens frequently, increase `_INTER_REQUEST_DELAY` in `rmbench/models/groq_model.py`.

### Groq: Model not available
Check [console.groq.com/docs/models](https://console.groq.com/docs/models) for the current model list. All three RMBench Groq models are production-tier (not preview/beta).

### Ollama: Server not running
```
RuntimeError: Ollama is not running at http://localhost:11434
```
Solution: Run `ollama serve` in a separate terminal.

### Ollama: Model not found warning
```
WARNING: Model 'mistral:7b' not found in Ollama. Run: ollama pull mistral:7b
```
Solution: `ollama pull mistral:7b` then retry.

### Ollama: Slow inference
- CPU inference for 7B models typically takes 30–90 seconds per request
- The pipeline uses a 300-second timeout — increase `timeout=` in `ollama_model.py` if needed
- A GPU with 8 GB VRAM will run 7B models 10–30x faster

### sentence-transformers: slow download or auth error
```bash
export SENTENCE_TRANSFORMERS_HOME=/path/to/local/cache
# For gated HF models:
huggingface-cli login --token hf_...
```
