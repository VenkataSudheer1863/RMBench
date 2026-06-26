#!/bin/bash

# ============================================================
# RMBench - List Supported Models
#
# Shows all 6 models, their backends, families, sizes, and
# required setup for each.
# ============================================================

echo "========================================="
echo "RMBench - Supported Models"
echo "========================================="
echo ""
echo "GROQ (cloud inference — requires API keys in .env)"
echo "-------------------------------------------------"
echo "  Model ID                                      Family       Size  Key Env Var"
echo "  --------------------------------------------  -----------  ----  -------------------------"
echo "  llama-3.3-70b-versatile                       Meta/Llama3  70B   GROQ_KEY_LLAMA70B"
echo "  meta-llama/llama-4-scout-17b-16e-instruct     Meta/Llama4  17B   GROQ_KEY_LLAMA4SCOUT"
echo "  qwen/qwen3-32b                                Alibaba/Qwen 32B   GROQ_KEY_QWEN32B"
echo ""
echo "OLLAMA (local inference — requires: ollama serve)"
echo "--------------------------------------------------"
echo "  Model ID          Family        Size   Storage  Pull Command"
echo "  ----------------  ------------  -----  -------  ----------------------------"
echo "  mistral:7b        Mistral AI    7B     4.4 GB   ollama pull mistral:7b"
echo "  gemma3:4b         Google/Gemma  4B     3.3 GB   ollama pull gemma3:4b"
echo "  deepseek-r1:7b    DeepSeek      7B     4.7 GB   ollama pull deepseek-r1:7b"
echo ""
echo "Setup:"
echo "  Groq keys: add GROQ_KEY_LLAMA70B, GROQ_KEY_LLAMA4SCOUT, GROQ_KEY_QWEN32B to .env"
echo "  Ollama:    ollama serve && ollama pull mistral:7b gemma3:4b deepseek-r1:7b"
echo ""
echo "Run benchmark:"
echo "  # Ollama only (no API keys needed)"
echo "  python run_benchmark.py --models mistral:7b gemma3:4b deepseek-r1:7b --defenses none --samples 10"
echo ""
echo "  # All 6 models"
echo "  python run_benchmark.py --defenses none --samples 10"
echo ""

# Show currently available Ollama models if server is running
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "Currently downloaded Ollama models:"
    python - <<'EOF'
import urllib.request, json
data = json.loads(urllib.request.urlopen("http://localhost:11434/api/tags", timeout=5).read())
for m in data.get("models", []):
    size_gb = m.get("size", 0) / 1e9
    print(f"  {m.get('name',''):<25} {size_gb:.1f} GB")
EOF
else
    echo "Ollama server not running — start with: ollama serve"
fi
