#!/bin/bash

# ============================================================
# RMBench - Experiment Runner
#
# Runs benchmark experiments via the Groq API.
# Requires GROQ_API_KEY to be set in the environment.
# ============================================================

set -e

echo "========================================="
echo "RMBench - Experiment Runner (Groq)"
echo "========================================="
echo ""

# Validate API key
if [ -z "$GROQ_API_KEY" ]; then
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
fi

if [ -z "$GROQ_API_KEY" ]; then
    echo "Error: GROQ_API_KEY is not set."
    echo "  cp .env.example .env  # then fill in your key"
    exit 1
fi

echo "✓ GROQ_API_KEY is set"
echo ""

# Configuration
RESULTS_DIR="results/experiments_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"
echo "Results will be saved to: $RESULTS_DIR"
echo ""

# Available models
ALL_MODELS=(
    "llama-3.1-8b-instant"
    "mixtral-8x7b-32768"
    "gemma2-9b-it"
    "qwen-qwq-32b"
    "deepseek-r1-distill-llama-70b"
    "llama-3.3-70b-versatile"
)

# Ask user which experiment to run
echo "Select experiment:"
echo "1) Baseline (no defenses)"
echo "2) With context sanitization"
echo "3) With injection detection"
echo "4) With all defenses (research config)"
echo "5) Run all experiments"
echo ""
read -p "Enter choice [1-5]: " exp_choice

# Ask which models to use
echo ""
echo "Select models:"
echo "1) Fast only         (llama-3.1-8b-instant)"
echo "2) Balanced          (mixtral-8x7b-32768, gemma2-9b-it)"
echo "3) Capable           (qwen-qwq-32b, deepseek-r1-distill-llama-70b)"
echo "4) Research          (llama-3.3-70b-versatile)"
echo "5) All six models"
echo "6) Custom selection"
echo ""
read -p "Enter choice [1-6]: " model_choice

case $model_choice in
    1) MODELS=("llama-3.1-8b-instant") ;;
    2) MODELS=("mixtral-8x7b-32768" "gemma2-9b-it") ;;
    3) MODELS=("qwen-qwq-32b" "deepseek-r1-distill-llama-70b") ;;
    4) MODELS=("llama-3.3-70b-versatile") ;;
    5) MODELS=("${ALL_MODELS[@]}") ;;
    6)
        echo "Available: ${ALL_MODELS[*]}"
        read -p "Enter model IDs (space-separated): " -a MODELS
        ;;
    *) echo "Invalid choice"; exit 1 ;;
esac

echo ""
echo "Models selected: ${MODELS[*]}"
echo ""

run_experiment() {
    local exp_name=$1
    local extra_args=$2
    local model=$3

    echo ""
    echo "========================================="
    echo "Running: $exp_name with $model"
    echo "========================================="

    log_file="$RESULTS_DIR/${exp_name}_${model//-/_}_log.txt"

    python benchmark/run_suite.py \
        --models "$model" \
        $extra_args \
        --output-dir "$RESULTS_DIR" \
        2>&1 | tee "$log_file"

    echo "✓ Completed: $exp_name with $model"
}

case $exp_choice in
    1)
        for model in "${MODELS[@]}"; do
            run_experiment "baseline" "--defenses none" "$model"
        done
        ;;
    2)
        for model in "${MODELS[@]}"; do
            run_experiment "with_sanitization" "--defenses none context_sanitization" "$model"
        done
        ;;
    3)
        for model in "${MODELS[@]}"; do
            run_experiment "with_injection_detection" "--defenses none injection_detection" "$model"
        done
        ;;
    4)
        for model in "${MODELS[@]}"; do
            run_experiment "with_all_defenses" \
                "--defenses none context_sanitization injection_detection trust_scoring multi_agent_verification constitutional_filtering provenance_tracking \
                 --config configs/research_config.yaml" "$model"
        done
        ;;
    5)
        for model in "${MODELS[@]}"; do
            run_experiment "baseline" "--defenses none" "$model"
            run_experiment "with_sanitization" "--defenses none context_sanitization" "$model"
            run_experiment "with_injection_detection" "--defenses none injection_detection" "$model"
            run_experiment "with_all_defenses" \
                "--defenses none context_sanitization injection_detection trust_scoring multi_agent_verification constitutional_filtering provenance_tracking" \
                "$model"
        done
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "========================================="
echo "All experiments complete!"
echo "========================================="
echo ""
echo "Results directory: $RESULTS_DIR"
echo ""
echo "Generate report:"
echo "  python -c 'from rmbench.utils.result_utils import generate_report; generate_report(\"$RESULTS_DIR\")'"
