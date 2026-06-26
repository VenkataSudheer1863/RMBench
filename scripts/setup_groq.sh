#!/bin/bash

# ============================================================
# RMBench - Setup Verification Script
#
# Checks Python dependencies, Groq API keys, and Ollama status.
# Run from the RMBench-main directory.
# ============================================================

set -e

echo "========================================="
echo "RMBench - Environment Setup Check"
echo "========================================="
echo ""

# Install Python dependencies
echo "Checking Python dependencies..."
pip install -r requirements.txt -q
echo "  Dependencies: OK"
echo ""

# Load .env if it exists
if [ -f ".env" ]; then
    echo "Loading .env..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "  .env loaded"
    echo ""
fi

# ── Groq API Keys ───────────────────────────────────────────

echo "Checking Groq API keys..."

check_groq_key() {
    local key_name="$1"
    local model="$2"
    local key_value="${!key_name}"

    if [ -z "$key_value" ]; then
        echo "  WARNING: $key_name is not set (required for $model)"
        return 1
    else
        echo "  $key_name: set (${key_value:0:8}...)"
        return 0
    fi
}

GROQ_OK=true
check_groq_key "GROQ_KEY_LLAMA70B"    "llama-3.3-70b-versatile"                   || GROQ_OK=false
check_groq_key "GROQ_KEY_LLAMA4SCOUT" "meta-llama/llama-4-scout-17b-16e-instruct" || GROQ_OK=false
check_groq_key "GROQ_KEY_QWEN32B"     "qwen/qwen3-32b"                            || GROQ_OK=false

if [ "$GROQ_OK" = true ]; then
    echo ""
    echo "Testing Groq API connectivity (llama-3.3-70b-versatile)..."
    python - <<'EOF'
import os, sys
from dotenv import load_dotenv
load_dotenv()
try:
    import httpx, truststore, ssl as _ssl
    ssl_ctx = truststore.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
    http_client = httpx.Client(verify=ssl_ctx)
except Exception:
    try:
        import httpx
        http_client = httpx.Client(verify=False)
    except Exception:
        http_client = None

try:
    from groq import Groq
    key = os.environ.get("GROQ_KEY_LLAMA70B") or os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=key, **({"http_client": http_client} if http_client else {}))
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Reply with just: ok"}],
        max_tokens=5,
    )
    print(f"  Groq API: OK  (response: {resp.choices[0].message.content!r})")
except Exception as e:
    print(f"  Groq API: FAILED — {e}", file=sys.stderr)
    sys.exit(1)
EOF
else
    echo ""
    echo "  Skipping Groq API test (one or more keys missing)."
    echo "  Get free keys at: https://console.groq.com"
    echo "  Add to .env: GROQ_KEY_LLAMA70B, GROQ_KEY_LLAMA4SCOUT, GROQ_KEY_QWEN32B"
fi

echo ""

# ── Ollama ─────────────────────────────────────────────────

echo "Checking Ollama..."

if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  Ollama server: running"
    echo ""
    echo "  Checking local models..."
    python - <<'EOF'
import urllib.request, json
try:
    data = json.loads(urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5).read())
    names = [m.get("name","") for m in data.get("models", [])]
    for model in ["mistral:7b", "gemma3:4b", "deepseek-r1:7b"]:
        base = model.split(":")[0]
        found = any(base in n for n in names)
        status = "OK" if found else "NOT FOUND (run: ollama pull " + model + ")"
        print(f"  {model}: {status}")
except Exception as e:
    print(f"  Could not check Ollama models: {e}")
EOF
else
    echo "  Ollama server: NOT running"
    echo "  Start it with: ollama serve"
    echo "  Then pull models: ollama pull mistral:7b gemma3:4b deepseek-r1:7b"
fi

echo ""
echo "========================================="
echo "Setup check complete!"
echo "========================================="
echo ""
echo "Quick start commands:"
echo ""
echo "  # Ollama only (no API keys)"
echo "  python run_benchmark.py --models mistral:7b gemma3:4b deepseek-r1:7b --defenses none --samples 5"
echo ""
echo "  # All 6 models"
echo "  python run_benchmark.py --defenses none --samples 10"
echo ""
echo "  # Dry run (preview only)"
echo "  python run_benchmark.py --dry-run"
