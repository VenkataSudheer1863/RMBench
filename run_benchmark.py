"""
RMBench Benchmark Runner
===================================
Runs the full benchmark evaluation pipeline across all
attack x task x model x defense combinations.

Backends
--------
  Groq (cloud)  — llama-3.3-70b-versatile, meta-llama/llama-4-scout-17b-16e-instruct,
                   qwen/qwen3-32b
                   Requires GROQ_KEY_LLAMA70B / GROQ_KEY_LLAMA4SCOUT / GROQ_KEY_QWEN32B in .env
  Ollama (local) — mistral:7b, gemma3:4b, deepseek-r1:7b
                   Requires Ollama running: ollama serve

Outputs (written to results/):
    <model>_none_<timestamp>.json      -- full per-sample results per model
    rmbench_results_<timestamp>.json   -- merged results across all models
    comparison_table_<timestamp>.csv   -- CSV for analysis

Usage:
    python run_benchmark.py
    python run_benchmark.py --models mistral:7b gemma3:4b --samples 10
    python run_benchmark.py --models llama-3.3-70b-versatile --defenses none --samples 10
    python run_benchmark.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from rmbench.config import (
    RMBenchConfig, ModelConfig, AttackConfig, DefenseConfig, EvaluationConfig,
    ModelBackend, ALL_MODELS, backend_for,
)
from rmbench.attacks import ATTACK_REGISTRY
from rmbench.defenses import DEFENSE_REGISTRY
from rmbench.pipeline.benchmark_pipeline import BenchmarkPipeline
from rmbench.utils.logging_utils import setup_logging
from rmbench.utils.result_utils import save_results, merge_results

try:
    from rich.console import Console
    from rich.table import Table
    RICH = True
    console = Console(safe_box=True)
except ImportError:
    RICH = False
    class _FakeConsole:
        def print(self, *a, **kw): print(*a)
        def rule(self, t=""): print("-" * 60, t)
    console = _FakeConsole()


DEFAULT_MODELS = ALL_MODELS
ATTACK_TYPES   = list(ATTACK_REGISTRY.keys())
DEFENSE_TYPES  = [d for d in DEFENSE_REGISTRY.keys() if d != "none"]


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="RMBench Benchmark Runner (Groq + Ollama)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported models: {DEFAULT_MODELS}

Ollama quick start (local, no API key):
  python run_benchmark.py --models mistral:7b gemma3:4b deepseek-r1:7b --defenses none --samples 10

Groq quick start (cloud, needs keys in .env):
  python run_benchmark.py --models llama-3.3-70b-versatile --defenses none --samples 10

Full research run (all 6 models):
  python run_benchmark.py --defenses none --samples 10

Dry run (preview only, no API calls):
  python run_benchmark.py --dry-run
        """,
    )
    p.add_argument("--models",   nargs="+", default=DEFAULT_MODELS,
                   help="Model ID(s) to evaluate (default: all 6)")
    p.add_argument("--attacks",  nargs="+", default=ATTACK_TYPES,
                   help="Attack types to include (default: all 8)")
    p.add_argument("--defenses", nargs="+", default=["none"] + DEFENSE_TYPES,
                   help="Defense methods; include 'none' for undefended baseline")
    p.add_argument("--samples",  type=int, default=15,
                   help="Samples per task per attack combination (default: 15)")
    p.add_argument("--seed",     type=int, default=42)
    p.add_argument("--output",   type=str, default="results",
                   help="Output directory (default: results/)")
    p.add_argument("--dry-run",  action="store_true",
                   help="Print the run plan without making any API calls")
    return p.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Single combination runner
# ─────────────────────────────────────────────────────────────────────────────

def run_one(
    model: str,
    attacks: list[str],
    defense: str,
    num_samples: int,
    output_dir: str,
) -> dict:
    """Run one (model, defense) combination through BenchmarkPipeline."""
    config = RMBenchConfig(
        model=ModelConfig(name=model, backend=backend_for(model)),
        attack=AttackConfig(attack_types=attacks),
        defense=DefenseConfig(defense_method=defense),
        evaluation=EvaluationConfig(num_samples=num_samples),
        results_dir=output_dir,
        experiment_name=f"{model.replace('/', '_').replace(':', '_')}_{defense}",
        model_name=model,
        attack_types=attacks,
        defense_method=defense,
    )
    pipeline = BenchmarkPipeline(config)
    return pipeline.run()


# ─────────────────────────────────────────────────────────────────────────────
# Display
# ─────────────────────────────────────────────────────────────────────────────

METRIC_COLS = ["asr", "goal_preservation", "truthfulness", "tool_safety", "memory_integrity", "cri"]


def print_comparison(all_results: dict[str, dict]) -> None:
    if not RICH:
        for label, r in all_results.items():
            m = r.get("metrics", {})
            print(f"{label}: ASR={m.get('asr', 0):.3f}  CRI={m.get('cri', 0):.3f}")
        return
    table = Table(title="RMBench Results — Groq API (real inference)", show_header=True)
    table.add_column("Model / Defense", style="cyan", no_wrap=True)
    for col in METRIC_COLS:
        table.add_column(col.upper().replace("_", " "), justify="right")
    for label, r in sorted(all_results.items()):
        m = r.get("metrics", {})
        row = [label]
        for col in METRIC_COLS:
            val = m.get(col, 0.0)
            if col == "asr":
                color = "red" if val >= 0.35 else ("yellow" if val >= 0.2 else "green")
            else:
                color = "green" if val >= 0.75 else ("yellow" if val >= 0.5 else "red")
            row.append(f"[{color}]{val:.3f}[/{color}]")
        table.add_row(*row)
    console.print(table)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    setup_logging("INFO")
    args = parse_args()

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    total_combos = len(args.models) * len(args.defenses)
    total_samples = total_combos * len(args.attacks) * 6 * args.samples  # 6 tasks

    console.rule("[bold blue]RMBench Benchmark (Groq API)")
    console.print(f"Models:         {args.models}")
    console.print(f"Attacks:        {args.attacks}")
    console.print(f"Defenses:       {args.defenses}")
    console.print(f"Samples/combo:  {args.samples}")
    console.print(f"Combinations:   {total_combos}")
    console.print(f"Est. instances: ~{total_samples}")
    console.print(f"Output:         {args.output}\n")

    if args.dry_run:
        console.print("[yellow]Dry run — no API calls will be made.[/yellow]")
        console.print(f"Would run {total_combos} model/defense combinations:")
        for model in args.models:
            for defense in args.defenses:
                console.print(f"  {model} / {defense}")
        return 0

    all_results: dict[str, dict] = {}
    result_files: list[str] = []
    done = 0

    for model in args.models:
        for defense in args.defenses:
            done += 1
            label = f"{model} / {defense}"
            console.print(f"\n[{done}/{total_combos}] [cyan]{label}[/cyan]")
            try:
                result = run_one(
                    model=model,
                    attacks=args.attacks,
                    defense=defense,
                    num_samples=args.samples,
                    output_dir=str(out_dir),
                )
                all_results[label] = result
                slug = f"{model.replace('-', '_')}_{defense}_{timestamp}.json"
                fpath = str(out_dir / slug)
                save_results(result, fpath)
                result_files.append(fpath)
                m = result.get("metrics", {})
                console.print(
                    f"  ASR={m.get('asr', 0):.3f}  "
                    f"GPS={m.get('goal_preservation', 0):.3f}  "
                    f"CRI={m.get('cri', 0):.3f}"
                )
            except EnvironmentError as exc:
                console.print(f"  [red]Config error: {exc}[/red]")
                console.print("  [yellow]Ensure GROQ_API_KEY is set in your .env file.[/yellow]")
                return 1
            except Exception as exc:
                console.print(f"  [red]Failed ({label}): {exc}[/red]")
                continue

    if not all_results:
        console.print("[red]No results collected.[/red]")
        return 1

    console.rule("[bold green]Summary")
    print_comparison(all_results)

    if result_files:
        merged = merge_results(result_files)
        full_path = out_dir / f"rmbench_results_{timestamp}.json"
        save_results(merged, str(full_path))
        console.print(f"\nFull results -> [green]{full_path}[/green]")

    try:
        import pandas as pd
        rows = []
        for label, r in all_results.items():
            row = {"experiment": label}
            row.update(r.get("metrics", {}))
            rows.append(row)
        if rows:
            csv_path = out_dir / f"comparison_table_{timestamp}.csv"
            pd.DataFrame(rows).to_csv(str(csv_path), index=False)
            console.print(f"CSV           -> [green]{csv_path}[/green]")
    except ImportError:
        pass

    console.rule("[bold]Done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
