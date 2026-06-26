"""
RMBench Visualization Generator
==================================
Generates all publication-quality figures from benchmark results.

Figures produced (saved to results/figures/):
    01_asr_heatmap.png          — ASR heatmap: model × attack type
    02_model_comparison.png     — bar chart of all metrics per model
    03_asr_vs_model_size.png    — ASR vs model parameter count
    04_defense_effectiveness.png— radar chart of defense methods
    05_defense_attack_heatmap.png— heatmap: defense × attack ASR reduction
    06_per_task_vulnerability.png— bar chart: ASR per task type
    07_cri_ranking.png          — horizontal bar: CRI ranking of models
    08_attack_severity.png      — severity comparison across attack types
    09_metrics_overview.png     — multi-panel overview figure

Usage:
    python scripts/generate_visualizations.py
    python scripts/generate_visualizations.py --results results/rmbench_results_*.json
    python scripts/generate_visualizations.py --output results/figures
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server/CI use
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Make project importable
sys.path.insert(0, str(Path(__file__).parent.parent))


# ─────────────────────────────────────────────────────────────────────────────
# Style constants
# ─────────────────────────────────────────────────────────────────────────────

PALETTE = {
    "asr":              "#e74c3c",
    "cri":              "#2ecc71",
    "goal_preservation":"#3498db",
    "truthfulness":     "#9b59b6",
    "tool_safety":      "#f39c12",
    "memory_integrity": "#1abc9c",
}
ATTACK_COLORS = plt.cm.Reds(np.linspace(0.35, 0.9, 8))
DEFENSE_COLORS = plt.cm.Blues(np.linspace(0.35, 0.9, 7))
MODEL_COLORS = plt.cm.viridis(np.linspace(0.1, 0.9, 12))

ATTACK_LABELS = {
    "instruction_override":    "Instr. Override",
    "context_poisoning":       "Ctx. Poisoning",
    "goal_hijacking":          "Goal Hijacking",
    "tool_manipulation":       "Tool Manip.",
    "authority_spoofing":      "Auth. Spoofing",
    "memory_poisoning":        "Mem. Poisoning",
    "multihop_injection":      "Multi-hop Inj.",
    "hidden_prompt_injection": "Hidden Inj.",
}

DEFENSE_LABELS = {
    "none":                    "None (Baseline)",
    "context_sanitization":    "Ctx. Sanitization",
    "injection_detection":     "Inj. Detection",
    "trust_scoring":           "Trust Scoring",
    "multi_agent_verification":"Multi-Agent Verif.",
    "constitutional_filtering":"Constitutional",
    "provenance_tracking":     "Provenance Track.",
}

def _short_model_name(m: str) -> str:
    """Return a short display label for a Groq model ID."""
    return (m
            .replace("llama-3.3-70b-versatile",         "Llama3.3-70B")
            .replace("llama-3.1-8b-instant",             "Llama3.1-8B")
            .replace("mixtral-8x7b-32768",               "Mixtral-8x7B")
            .replace("gemma2-9b-it",                     "Gemma2-9B")
            .replace("qwen-qwq-32b",                     "QwQ-32B")
            .replace("deepseek-r1-distill-llama-70b",    "DS-R1-70B"))


plt.rcParams.update({
    "figure.dpi": 150,
    "font.family": "sans-serif",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.3,
})


# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────

def load_results(results_path: str) -> dict:
    with open(results_path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_latest_results(results_dir: str = "results") -> str | None:
    pattern = str(Path(results_dir) / "rmbench_results_*.json")
    files = sorted(glob.glob(pattern))
    return files[-1] if files else None


def build_asr_matrix(all_results: list[dict]) -> tuple[list[str], list[str], np.ndarray]:
    """Build model × attack_type ASR matrix."""
    from collections import defaultdict
    buckets: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        if r.get("defense_method", "none") == "none":
            buckets[r["model"]][r["attack_type"]].append(r)

    models = sorted(buckets.keys())
    attacks = sorted({r["attack_type"] for r in all_results if r.get("defense_method", "none") == "none"})

    matrix = np.zeros((len(models), len(attacks)))
    for i, model in enumerate(models):
        for j, attack in enumerate(attacks):
            samples = buckets[model][attack]
            if samples:
                matrix[i, j] = sum(s["attack_successful"] for s in samples) / len(samples)
    return models, attacks, matrix


def build_defense_asr_matrix(all_results: list[dict], model: str) -> tuple[list[str], list[str], np.ndarray]:
    """Build defense × attack_type ASR matrix for a given model."""
    from collections import defaultdict
    buckets: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in all_results:
        if r.get("model") == model:
            buckets[r.get("defense_method", "none")][r["attack_type"]].append(r)

    defenses = sorted(buckets.keys())
    attacks = sorted({r["attack_type"] for r in all_results if r.get("model") == model})

    matrix = np.zeros((len(defenses), len(attacks)))
    for i, defense in enumerate(defenses):
        for j, attack in enumerate(attacks):
            samples = buckets[defense][attack]
            if samples:
                matrix[i, j] = sum(s["attack_successful"] for s in samples) / len(samples)
    return defenses, attacks, matrix


def build_per_task_asr(all_results: list[dict]) -> dict[str, float]:
    """Average ASR per task type (across all models, no defense)."""
    from collections import defaultdict
    buckets: dict[str, list] = defaultdict(list)
    for r in all_results:
        if r.get("defense_method", "none") == "none":
            buckets[r["task_type"]].append(r)
    return {
        task: sum(s["attack_successful"] for s in samples) / max(len(samples), 1)
        for task, samples in buckets.items()
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1: ASR Heatmap (model × attack)
# ─────────────────────────────────────────────────────────────────────────────

def fig_asr_heatmap(all_results: list[dict], out_dir: Path) -> None:
    models, attacks, matrix = build_asr_matrix(all_results)
    if not models or not attacks:
        return

    attack_labels = [ATTACK_LABELS.get(a, a) for a in attacks]
    # Shorten model names for readability
    model_labels = [_short_model_name(m) for m in models]

    fig, ax = plt.subplots(figsize=(12, max(4, len(models) * 0.55 + 1.5)))
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label="Attack Success Rate (↓ better)", shrink=0.8)

    ax.set_xticks(range(len(attacks)))
    ax.set_yticks(range(len(models)))
    ax.set_xticklabels(attack_labels, rotation=35, ha="right", fontsize=9)
    ax.set_yticklabels(model_labels, fontsize=9)
    ax.set_title("Attack Success Rate (ASR) — Model × Attack Type\nLower = More Robust",
                 fontsize=12, fontweight="bold", pad=12)

    for i in range(len(models)):
        for j in range(len(attacks)):
            val = matrix[i, j]
            color = "white" if val > 0.55 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=7.5, color=color, fontweight="bold")

    fig.tight_layout()
    path = out_dir / "01_asr_heatmap.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2: Model comparison bar chart
# ─────────────────────────────────────────────────────────────────────────────

def fig_model_comparison(per_model_metrics: dict[str, dict], out_dir: Path) -> None:
    metrics_to_show = ["asr", "goal_preservation", "truthfulness", "tool_safety",
                       "memory_integrity", "cri"]
    models = sorted(per_model_metrics.keys(), key=lambda m: per_model_metrics[m].get("asr", 1))
    if not models:
        return

    x = np.arange(len(models))
    width = 0.13
    n_metrics = len(metrics_to_show)
    offsets = np.linspace(-(n_metrics - 1) * width / 2, (n_metrics - 1) * width / 2, n_metrics)

    fig, ax = plt.subplots(figsize=(max(10, len(models) * 1.1), 6))
    for idx, (metric, offset) in enumerate(zip(metrics_to_show, offsets)):
        values = [per_model_metrics[m].get(metric, 0) for m in models]
        bars = ax.bar(x + offset, values, width, label=metric.upper().replace("_", " "),
                      color=PALETTE.get(metric, "#95a5a6"), alpha=0.85, edgecolor="white")

    model_labels = [_short_model_name(m) for m in models]
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Score", fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_title("All Metrics per Model (No Defense)\nASR↓ — All Others↑", fontsize=12, fontweight="bold")
    ax.legend(loc="upper right", fontsize=8, ncol=2)
    ax.axhline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)

    fig.tight_layout()
    path = out_dir / "02_model_comparison.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3: ASR vs approximate model size
# ─────────────────────────────────────────────────────────────────────────────

MODEL_PARAMS = {
    "llama-3.1-8b-instant":             8,
    "mixtral-8x7b-32768":               56,   # 8x7B MoE = ~56B total params
    "gemma2-9b-it":                     9,
    "qwen-qwq-32b":                     32,
    "deepseek-r1-distill-llama-70b":    70,
    "llama-3.3-70b-versatile":          70,
}

def fig_asr_vs_size(per_model_metrics: dict[str, dict], out_dir: Path) -> None:
    points = []
    for model, metrics in per_model_metrics.items():
        params = MODEL_PARAMS.get(model)
        if params is not None:
            points.append((params, metrics.get("asr", 0), model))
    if not points:
        return

    points.sort(key=lambda x: x[0])
    sizes, asrs, names = zip(*points)

    fig, ax = plt.subplots(figsize=(9, 5))
    sc = ax.scatter(sizes, asrs, s=100, c=asrs, cmap="RdYlGn_r",
                    vmin=0, vmax=0.6, zorder=3, edgecolors="white", linewidths=0.8)
    plt.colorbar(sc, ax=ax, label="ASR", shrink=0.8)

    # Fit trend line
    log_sizes = np.log(sizes)
    coeffs = np.polyfit(log_sizes, asrs, 1)
    xs = np.linspace(min(sizes), max(sizes), 200)
    ax.plot(xs, np.polyval(coeffs, np.log(xs)), "k--", alpha=0.4, linewidth=1.2, label="Trend")

    for size, asr, name in points:
        short = name.replace("gpt-oss", "GPT-OSS").split(":")[0] + f":{name.split(':')[1]}" if ":" in name else name
        ax.annotate(short, (size, asr), textcoords="offset points", xytext=(6, 4), fontsize=7.5)

    ax.set_xscale("log")
    ax.set_xlabel("Model Parameters (billions, log scale)", fontsize=10)
    ax.set_ylabel("Attack Success Rate ↓", fontsize=10)
    ax.set_title("ASR vs Model Size\nLarger models tend to be more robust", fontsize=12, fontweight="bold")
    ax.legend(fontsize=9)

    fig.tight_layout()
    path = out_dir / "03_asr_vs_model_size.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4: Defense effectiveness radar
# ─────────────────────────────────────────────────────────────────────────────

def fig_defense_radar(defense_comparison: dict[str, dict], out_dir: Path) -> None:
    metrics_to_show = ["cri", "goal_preservation", "truthfulness", "tool_safety", "memory_integrity"]
    defenses = [d for d in defense_comparison.keys() if d != "none"]
    if not defenses:
        return

    N = len(metrics_to_show)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    # Baseline (no defense)
    baseline = defense_comparison.get("none", {})
    baseline_vals = [baseline.get(m, 0.5) for m in metrics_to_show]
    baseline_vals += baseline_vals[:1]
    ax.plot(angles, baseline_vals, "k--", alpha=0.5, linewidth=1.2, label="No Defense")
    ax.fill(angles, baseline_vals, alpha=0.05, color="gray")

    colors = plt.cm.tab10(np.linspace(0, 0.8, len(defenses)))
    for color, defense in zip(colors, defenses):
        vals = [defense_comparison[defense].get(m, 0.5) for m in metrics_to_show]
        vals += vals[:1]
        label = DEFENSE_LABELS.get(defense, defense)
        ax.plot(angles, vals, linewidth=1.8, color=color, label=label)
        ax.fill(angles, vals, alpha=0.08, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([m.replace("_", " ").title() for m in metrics_to_show], fontsize=9)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0"], fontsize=7)
    ax.set_title("Defense Effectiveness — Radar Chart\nHigher Area = Better Protection",
                 fontsize=12, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=8)

    fig.tight_layout()
    path = out_dir / "04_defense_effectiveness.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 5: Defense × attack ASR heatmap
# ─────────────────────────────────────────────────────────────────────────────

def fig_defense_attack_heatmap(all_results: list[dict], out_dir: Path) -> None:
    # Use the model with the most samples
    from collections import Counter
    model_counts = Counter(r["model"] for r in all_results)
    if not model_counts:
        return
    model = model_counts.most_common(1)[0][0]

    defenses, attacks, matrix = build_defense_asr_matrix(all_results, model)
    if not defenses or not attacks:
        return

    attack_labels  = [ATTACK_LABELS.get(a, a) for a in attacks]
    defense_labels = [DEFENSE_LABELS.get(d, d) for d in defenses]

    fig, ax = plt.subplots(figsize=(12, max(4, len(defenses) * 0.7 + 2)))
    im = ax.imshow(matrix, cmap="RdYlGn_r", aspect="auto", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax, label="ASR (↓ better)", shrink=0.8)

    ax.set_xticks(range(len(attacks)))
    ax.set_yticks(range(len(defenses)))
    ax.set_xticklabels(attack_labels, rotation=35, ha="right", fontsize=9)
    ax.set_yticklabels(defense_labels, fontsize=9)
    ax.set_title(f"ASR: Defense × Attack Type  (model: {model})\nLower = More Effective Defense",
                 fontsize=11, fontweight="bold", pad=10)

    for i in range(len(defenses)):
        for j in range(len(attacks)):
            val = matrix[i, j]
            color = "white" if val > 0.55 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=7.5, color=color, fontweight="bold")

    fig.tight_layout()
    path = out_dir / "05_defense_attack_heatmap.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 6: Per-task vulnerability
# ─────────────────────────────────────────────────────────────────────────────

def fig_per_task_vulnerability(all_results: list[dict], out_dir: Path) -> None:
    per_task = build_per_task_asr(all_results)
    if not per_task:
        return

    tasks = sorted(per_task.keys(), key=lambda t: per_task[t], reverse=True)
    asrs  = [per_task[t] for t in tasks]
    task_labels = [t.replace("_", " ").title() for t in tasks]
    colors = [plt.cm.RdYlGn_r(v) for v in asrs]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(task_labels, asrs, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Attack Success Rate ↓", fontsize=10)
    ax.set_title("Task Vulnerability to Retrieval Manipulation Attacks\nAverage ASR per Task Type",
                 fontsize=12, fontweight="bold")
    ax.axhline(np.mean(asrs), color="steelblue", linestyle="--", linewidth=1.2,
               label=f"Mean ASR = {np.mean(asrs):.3f}")
    ax.legend(fontsize=9)

    for bar, asr in zip(bars, asrs):
        ax.text(bar.get_x() + bar.get_width() / 2, asr + 0.01, f"{asr:.3f}",
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    fig.tight_layout()
    path = out_dir / "06_per_task_vulnerability.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 7: CRI ranking
# ─────────────────────────────────────────────────────────────────────────────

def fig_cri_ranking(per_model_metrics: dict[str, dict], out_dir: Path) -> None:
    models = sorted(per_model_metrics.keys(), key=lambda m: per_model_metrics[m].get("cri", 0))
    if not models:
        return
    cris = [per_model_metrics[m].get("cri", 0) for m in models]

    model_labels = [_short_model_name(m) for m in models]
    colors = [plt.cm.RdYlGn(v) for v in cris]

    fig, ax = plt.subplots(figsize=(8, max(4, len(models) * 0.5 + 1.5)))
    bars = ax.barh(model_labels, cris, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Context Robustness Index (↑ better)", fontsize=10)
    ax.set_title("Model CRI Ranking\nComposite Robustness Index (higher = more robust)",
                 fontsize=12, fontweight="bold")
    ax.axvline(0.5, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)

    for bar, cri in zip(bars, cris):
        ax.text(cri + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{cri:.3f}", va="center", fontsize=9, fontweight="bold")

    fig.tight_layout()
    path = out_dir / "07_cri_ranking.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 8: Attack severity comparison
# ─────────────────────────────────────────────────────────────────────────────

def fig_attack_severity(all_results: list[dict], out_dir: Path) -> None:
    from collections import defaultdict
    buckets: dict[str, list] = defaultdict(list)
    for r in all_results:
        if r.get("defense_method", "none") == "none":
            buckets[r["attack_type"]].append(r)

    attacks = sorted(buckets.keys())
    if not attacks:
        return
    asr_vals = []
    ci_lower, ci_upper = [], []
    for attack in attacks:
        samples = buckets[attack]
        asr = sum(s["attack_successful"] for s in samples) / max(len(samples), 1)
        asr_vals.append(asr)
        # Wilson CI
        n = len(samples)
        p = asr
        z = 1.96
        denom = 1 + z**2 / n if n > 0 else 1
        center = (p + z**2 / (2 * n)) / denom if n > 0 else p
        margin = z * ((p * (1 - p) / n + z**2 / (4 * n**2)) ** 0.5) / denom if n > 0 else 0
        ci_lower.append(max(0, center - margin))
        ci_upper.append(min(1, center + margin))

    yerr = [np.array(asr_vals) - np.array(ci_lower),
            np.array(ci_upper) - np.array(asr_vals)]

    attack_labels = [ATTACK_LABELS.get(a, a) for a in attacks]
    colors = [ATTACK_COLORS[i] for i in range(len(attacks))]

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(attacks))
    bars = ax.bar(x, asr_vals, color=colors, edgecolor="white", linewidth=0.8,
                  yerr=yerr, capsize=4, error_kw={"linewidth": 1.2, "color": "black"})
    ax.set_xticks(x)
    ax.set_xticklabels(attack_labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylabel("Attack Success Rate ↓", fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_title("Attack Type Severity (Average ASR across All Models)\nError bars: 95% Wilson CI",
                 fontsize=12, fontweight="bold")
    ax.axhline(np.mean(asr_vals), color="steelblue", linestyle="--",
               linewidth=1.2, label=f"Mean = {np.mean(asr_vals):.3f}")
    ax.legend(fontsize=9)

    for bar, asr in zip(bars, asr_vals):
        ax.text(bar.get_x() + bar.get_width() / 2, asr + 0.02,
                f"{asr:.3f}", ha="center", fontsize=8.5, fontweight="bold")

    fig.tight_layout()
    path = out_dir / "08_attack_severity.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 9: Multi-panel overview
# ─────────────────────────────────────────────────────────────────────────────

def fig_overview(
    per_model_metrics: dict[str, dict],
    defense_comparison: dict[str, dict],
    all_results: list[dict],
    out_dir: Path,
) -> None:
    fig = plt.figure(figsize=(18, 12))
    fig.suptitle("RMBench: Retrieval Manipulation Benchmark — Overview",
                 fontsize=15, fontweight="bold", y=0.98)

    # ── Panel A: ASR per model ────────────────────────────────────────────────
    ax1 = fig.add_subplot(2, 3, 1)
    models = sorted(per_model_metrics.keys(), key=lambda m: per_model_metrics[m].get("asr", 1))
    asrs  = [per_model_metrics[m].get("asr", 0) for m in models]
    short = [_short_model_name(m) for m in models]
    colors_m = [plt.cm.RdYlGn_r(v / 0.55) for v in asrs]
    ax1.barh(short, asrs, color=colors_m, edgecolor="white", linewidth=0.5)
    ax1.set_xlim(0, 0.65)
    ax1.set_xlabel("ASR ↓", fontsize=9)
    ax1.set_title("A) ASR by Model", fontsize=10, fontweight="bold")
    ax1.axvline(0.3, color="gray", linestyle="--", alpha=0.5, linewidth=0.8)
    for i, (v, s) in enumerate(zip(asrs, short)):
        ax1.text(v + 0.005, i, f"{v:.2f}", va="center", fontsize=7)

    # ── Panel B: CRI per model ────────────────────────────────────────────────
    ax2 = fig.add_subplot(2, 3, 2)
    cris = [per_model_metrics[m].get("cri", 0) for m in models]
    colors_c = [plt.cm.RdYlGn(v) for v in cris]
    ax2.barh(short, cris, color=colors_c, edgecolor="white", linewidth=0.5)
    ax2.set_xlim(0, 1)
    ax2.set_xlabel("CRI ↑", fontsize=9)
    ax2.set_title("B) CRI by Model", fontsize=10, fontweight="bold")
    ax2.axvline(0.7, color="gray", linestyle="--", alpha=0.5, linewidth=0.8)
    for i, (v, s) in enumerate(zip(cris, short)):
        ax2.text(v + 0.005, i, f"{v:.2f}", va="center", fontsize=7)

    # ── Panel C: Attack severity ───────────────────────────────────────────────
    ax3 = fig.add_subplot(2, 3, 3)
    from collections import defaultdict
    atk_buckets: dict[str, list] = defaultdict(list)
    for r in all_results:
        if r.get("defense_method", "none") == "none":
            atk_buckets[r["attack_type"]].append(r)
    attacks_sorted = sorted(atk_buckets.keys(),
                             key=lambda a: sum(s["attack_successful"] for s in atk_buckets[a]) / max(len(atk_buckets[a]), 1),
                             reverse=True)
    atk_asrs = [sum(s["attack_successful"] for s in atk_buckets[a]) / max(len(atk_buckets[a]), 1)
                for a in attacks_sorted]
    atk_labels = [ATTACK_LABELS.get(a, a) for a in attacks_sorted]
    ax3.barh(atk_labels[::-1], atk_asrs[::-1], color=ATTACK_COLORS[:len(attacks_sorted)],
             edgecolor="white", linewidth=0.5)
    ax3.set_xlim(0, 0.8)
    ax3.set_xlabel("ASR ↓", fontsize=9)
    ax3.set_title("C) Attack Severity", fontsize=10, fontweight="bold")

    # ── Panel D: Defense comparison (CRI) ────────────────────────────────────
    ax4 = fig.add_subplot(2, 3, 4)
    def_keys = sorted(defense_comparison.keys(),
                      key=lambda d: defense_comparison[d].get("cri", 0))
    def_cris = [defense_comparison[d].get("cri", 0) for d in def_keys]
    def_labels = [DEFENSE_LABELS.get(d, d) for d in def_keys]
    colors_d = [plt.cm.Blues(0.3 + 0.6 * v) for v in def_cris]
    ax4.barh(def_labels, def_cris, color=colors_d, edgecolor="white", linewidth=0.5)
    ax4.set_xlim(0, 1)
    ax4.set_xlabel("CRI ↑", fontsize=9)
    ax4.set_title("D) Defense Effectiveness (CRI)", fontsize=10, fontweight="bold")
    for i, v in enumerate(def_cris):
        ax4.text(v + 0.005, i, f"{v:.2f}", va="center", fontsize=7.5)

    # ── Panel E: Per-task vulnerability ──────────────────────────────────────
    ax5 = fig.add_subplot(2, 3, 5)
    per_task = build_per_task_asr(all_results)
    task_sorted = sorted(per_task.keys(), key=lambda t: per_task[t], reverse=True)
    task_asrs = [per_task[t] for t in task_sorted]
    task_lbs = [t.replace("_", "\n").title() for t in task_sorted]
    colors_t = [plt.cm.RdYlGn_r(v / 0.6) for v in task_asrs]
    ax5.bar(task_lbs, task_asrs, color=colors_t, edgecolor="white", linewidth=0.5)
    ax5.set_ylim(0, 0.8)
    ax5.set_ylabel("ASR ↓", fontsize=9)
    ax5.set_title("E) Vulnerability by Task", fontsize=10, fontweight="bold")

    # ── Panel F: Truth vs ASR scatter ────────────────────────────────────────
    ax6 = fig.add_subplot(2, 3, 6)
    for i, (model, metrics) in enumerate(per_model_metrics.items()):
        asr = metrics.get("asr", 0)
        truth = metrics.get("truthfulness", 0)
        short_name = model.split(":")[0].replace("gpt-oss", "GPT").replace("gemma3", "Gemma")
        ax6.scatter(asr, truth, s=70, zorder=3, color=MODEL_COLORS[i % len(MODEL_COLORS)])
        ax6.annotate(short_name, (asr, truth), xytext=(4, 4),
                     textcoords="offset points", fontsize=6.5)
    ax6.set_xlabel("ASR (↓ better)", fontsize=9)
    ax6.set_ylabel("Truthfulness (↑ better)", fontsize=9)
    ax6.set_title("F) ASR vs Truthfulness Trade-off", fontsize=10, fontweight="bold")
    ax6.set_xlim(-0.02, 0.65)
    ax6.set_ylim(0.3, 1.05)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    path = out_dir / "09_metrics_overview.png"
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  Saved: {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RMBench Visualization Generator")
    p.add_argument("--results", type=str, default=None,
                   help="Path to rmbench_results_*.json (auto-detected if omitted)")
    p.add_argument("--results-dir", type=str, default="results",
                   help="Directory to search for result files")
    p.add_argument("--output", type=str, default="results/figures",
                   help="Output directory for figures")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Find results file
    results_path = args.results
    if results_path is None:
        results_path = find_latest_results(args.results_dir)
    if results_path is None:
        print("ERROR: No results found. Run `python run_benchmark.py` first.")
        return 1

    print(f"Loading results from: {results_path}")
    data = load_results(results_path)

    all_results      = data.get("all_results", data.get("results", []))
    per_model_metrics = data.get("per_model_metrics", {})
    defense_comparison = data.get("defense_comparison", {})

    if not all_results:
        print("ERROR: No per-sample results found in results file.")
        return 1

    print(f"Loaded {len(all_results)} samples.")
    print(f"Generating figures in: {out_dir}\n")

    fig_asr_heatmap(all_results, out_dir)
    fig_model_comparison(per_model_metrics, out_dir)
    fig_asr_vs_size(per_model_metrics, out_dir)
    fig_defense_radar(defense_comparison, out_dir)
    fig_defense_attack_heatmap(all_results, out_dir)
    fig_per_task_vulnerability(all_results, out_dir)
    fig_cri_ranking(per_model_metrics, out_dir)
    fig_attack_severity(all_results, out_dir)
    fig_overview(per_model_metrics, defense_comparison, all_results, out_dir)

    print(f"\nAll figures saved to: {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
