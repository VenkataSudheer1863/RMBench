"""
RMBench Full Suite Runner
==========================
Runs the complete benchmark suite across all attack types and task types
for one or more models (Groq or Ollama), then aggregates results into a
comparison table.

Groq models require keys in .env: GROQ_KEY_LLAMA70B, GROQ_KEY_LLAMA4SCOUT, GROQ_KEY_QWEN32B
Ollama models require Ollama running (ollama serve) and models pulled.

Usage:
    python benchmark/run_suite.py --models mistral:7b gemma3:4b
    python benchmark/run_suite.py --models llama-3.3-70b-versatile --defenses none context_sanitization
    python benchmark/run_suite.py --models mistral:7b "qwen/qwen3-32b" --defenses none --samples 10
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rmbench.config import (
    RMBenchConfig, ModelConfig, AttackConfig, DefenseConfig, EvaluationConfig,
    ATTACK_TYPES, TASK_TYPES, DEFENSE_METHODS, ALL_MODELS, backend_for,
)
from rmbench.pipeline.benchmark_pipeline import BenchmarkPipeline
from rmbench.utils.logging_utils import setup_logging
from rmbench.utils.result_utils import merge_results, save_results

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rmbench-suite",
        description="Run full RMBench suite across multiple models and defenses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported models:
  Groq:   llama-3.3-70b-versatile
          meta-llama/llama-4-scout-17b-16e-instruct
          qwen/qwen3-32b
  Ollama: mistral:7b
          gemma3:4b
          deepseek-r1:7b

Examples:
  # All Ollama models, no defense
  python benchmark/run_suite.py --models mistral:7b gemma3:4b deepseek-r1:7b --defenses none

  # All 6 models, baseline
  python benchmark/run_suite.py --defenses none --samples 10

  # One Groq model with two defenses
  python benchmark/run_suite.py --models llama-3.3-70b-versatile --defenses none context_sanitization
        """,
    )
    parser.add_argument(
        "--models", nargs="+",
        default=ALL_MODELS,
        help="Model ID(s) to evaluate (Groq or Ollama). Default: all 6.",
    )
    parser.add_argument("--attacks", nargs="+", default=ATTACK_TYPES)
    parser.add_argument("--tasks", nargs="+", default=TASK_TYPES)
    parser.add_argument("--defenses", nargs="+", default=["none"])
    parser.add_argument("--samples", "--num-samples", type=int, default=10,
                        help="Samples per attack-task combination (default: 10)")
    parser.add_argument("--output-dir", type=str, default="results/suite")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING"], default="INFO")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def run_one_combination(
    model: str,
    attacks: list[str],
    tasks: list[str],
    defense: str,
    num_samples: int,
    output_dir: str,
) -> dict:
    slug = f"{model.replace('/', '_').replace(':', '_')}_{defense}"
    config = RMBenchConfig(
        model=ModelConfig(name=model, backend=backend_for(model)),
        attack=AttackConfig(attack_types=attacks),
        defense=DefenseConfig(defense_method=defense),
        evaluation=EvaluationConfig(num_samples=num_samples),
        task_types=tasks,
        results_dir=output_dir,
        experiment_name=slug,
        model_name=model,
        attack_types=attacks,
        defense_method=defense,
    )
    pipeline = BenchmarkPipeline(config)
    return pipeline.run()


def print_comparison_table(all_results: dict[str, dict]) -> None:
    if not RICH:
        for label, r in all_results.items():
            m = r.get("metrics", {})
            print(f"{label}: ASR={m.get('asr', 0):.3f}  CRI={m.get('cri', 0):.3f}")
        return
    table = Table(title="RMBench Suite Results", show_header=True)
    table.add_column("Model + Defense", style="cyan", no_wrap=True)
    for metric in ["asr", "goal_preservation", "truthfulness", "tool_safety", "memory_integrity", "cri"]:
        table.add_column(metric.upper().replace("_", " "), justify="right")

    for label, result in sorted(all_results.items()):
        metrics = result.get("metrics", {})
        row = [label]
        for metric in ["asr", "goal_preservation", "truthfulness", "tool_safety", "memory_integrity", "cri"]:
            val = metrics.get(metric, 0.0)
            if metric == "asr":
                color = "red" if val >= 0.35 else ("yellow" if val >= 0.2 else "green")
            else:
                color = "green" if val >= 0.75 else ("yellow" if val >= 0.5 else "red")
            row.append(f"[{color}]{val:.3f}[/{color}]")
        table.add_row(*row)

    console.print(table)


def main() -> int:
    args = parse_args()
    setup_logging(level=args.log_level)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    console.rule("[bold blue]RMBench Full Suite")
    console.print(f"Models:    {args.models}")
    console.print(f"Attacks:   {args.attacks}")
    console.print(f"Tasks:     {args.tasks}")
    console.print(f"Defenses:  {args.defenses}")
    console.print(f"Samples:   {args.samples} per attack-task combo")
    console.print(f"Output:    {args.output_dir}\n")

    total_runs = len(args.models) * len(args.defenses)
    console.print(f"Total combinations: [bold]{total_runs}[/bold]")

    if args.dry_run:
        console.print("[yellow]Dry run mode — not executing.[/yellow]")
        for model in args.models:
            for defense in args.defenses:
                backend = backend_for(model).value
                console.print(f"  {model} ({backend}) / {defense}")
        return 0

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    all_results: dict[str, dict] = {}
    result_files: list[str] = []

    for model in args.models:
        for defense in args.defenses:
            label = f"{model} / {defense}"
            console.rule(f"[bold]{label}[/bold]")
            try:
                result = run_one_combination(
                    model=model,
                    attacks=args.attacks,
                    tasks=args.tasks,
                    defense=defense,
                    num_samples=args.samples,
                    output_dir=args.output_dir,
                )
                all_results[label] = result
                slug = f"{model.replace('/', '_').replace(':', '_')}_{defense}_{timestamp}.json"
                fpath = str(Path(args.output_dir) / slug)
                save_results(result, fpath)
                result_files.append(fpath)
                m = result.get("metrics", {})
                console.print(
                    f"  ASR={m.get('asr', 0):.3f}  "
                    f"GPS={m.get('goal_preservation', 0):.3f}  "
                    f"CRI={m.get('cri', 0):.3f}"
                )
            except EnvironmentError as exc:
                console.print(f"[red]Config error ({label}): {exc}[/red]")
            except Exception as exc:
                console.print(f"[red]FAILED: {label} — {exc}[/red]")

    if all_results:
        console.print("\n")
        print_comparison_table(all_results)

    if result_files:
        merged = merge_results(result_files)
        merged_path = Path(args.output_dir) / f"suite_merged_{timestamp}.json"
        save_results(merged, str(merged_path))
        console.print(f"\nMerged results: [green]{merged_path}[/green]")

    if HAS_PANDAS and all_results:
        rows = []
        for label, result in all_results.items():
            row = {"experiment": label}
            row.update(result.get("metrics", {}))
            rows.append(row)
        if rows:
            csv_path = Path(args.output_dir) / f"comparison_table_{timestamp}.csv"
            import pandas as pd
            pd.DataFrame(rows).to_csv(str(csv_path), index=False)
            console.print(f"Comparison CSV: [green]{csv_path}[/green]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
