"""
RMBench CLI — Single Run
=========================
Run a benchmark evaluation for a specific model (Groq or Ollama), attack, and task.

Groq models require the corresponding key in .env:
  llama-3.3-70b-versatile              -> GROQ_KEY_LLAMA70B
  meta-llama/llama-4-scout-17b-...     -> GROQ_KEY_LLAMA4SCOUT
  qwen/qwen3-32b                       -> GROQ_KEY_QWEN32B

Ollama models require Ollama running (ollama serve) and the model pulled.

Usage:
    python benchmark/run.py --model mistral:7b --attack instruction_override
    python benchmark/run.py --model llama-3.3-70b-versatile --attack all --defense context_sanitization
    python benchmark/run.py --model gemma3:4b --attack goal_hijacking --output results/gemma_gh.json
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rmbench.config import (
    Config, BenchmarkConfig, ModelBackend, AttackType, TaskType, DefenseType,
    ALL_MODELS, backend_for,
)
from rmbench.pipeline.benchmark_pipeline import BenchmarkPipeline

try:
    from rich.console import Console
    console = Console(safe_box=True)
except ImportError:
    class _FakeConsole:
        def print(self, *a, **kw): print(*a)
        def rule(self, t=""): print("-" * 60, t)
    console = _FakeConsole()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="rmbench",
        description="RMBench: Benchmarking Retrieval Manipulation Attacks Against AI Agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported models:
  Groq (cloud):   llama-3.3-70b-versatile
                  meta-llama/llama-4-scout-17b-16e-instruct
                  qwen/qwen3-32b
  Ollama (local): mistral:7b
                  gemma3:4b
                  deepseek-r1:7b

Examples:
  python benchmark/run.py --model mistral:7b --attack instruction_override
  python benchmark/run.py --model llama-3.3-70b-versatile --attack all --defense context_sanitization
  python benchmark/run.py --model gemma3:4b --attack goal_hijacking --output results/gemma_gh.json
        """,
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        default="mistral:7b",
        help="Model ID to evaluate (Groq or Ollama). See supported models above.",
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=256)

    attack_names = [a.value for a in AttackType]
    parser.add_argument(
        "--attack", "-a",
        type=str,
        default="instruction_override",
        help=f"Attack type(s). 'all' to run all. Options: {attack_names}",
    )

    task_names = [t.value for t in TaskType]
    parser.add_argument(
        "--task", "-t",
        type=str,
        default="all",
        help=f"Task type(s). 'all' to run all. Options: {task_names}",
    )

    defense_names = [d.value for d in DefenseType]
    parser.add_argument(
        "--defense", "-d",
        type=str,
        default="none",
        help=f"Defense method. Options: {defense_names} or 'none'",
    )

    parser.add_argument("--num-samples", type=int, default=10, help="Samples per task (default: 10)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", "-o", type=str, default=None, help="Output JSON file path")
    parser.add_argument("--results-dir", type=str, default="results")
    parser.add_argument("--experiment", type=str, default="rmbench_run")

    return parser.parse_args()


def build_config(args: argparse.Namespace) -> BenchmarkConfig:
    if args.attack == "all":
        attacks = Config.ALL_ATTACKS
    else:
        attacks = [AttackType(args.attack)]

    if args.task == "all":
        tasks = Config.ALL_TASKS
    else:
        tasks = [TaskType(args.task)]

    model_backend = backend_for(args.model)
    model_config = Config.get_model_config(args.model, model_backend)
    model_config.temperature = args.temperature
    model_config.max_tokens = args.max_tokens

    defenses = []
    if args.defense != "none":
        defenses = [DefenseType(args.defense)]

    return BenchmarkConfig(
        model=model_config,
        attacks=attacks,
        tasks=tasks,
        defenses=defenses,
        output_dir=args.results_dir,
        num_samples=args.num_samples,
        seed=args.seed,
        verbose=True,
    )


def main() -> int:
    args = parse_args()
    model_backend = backend_for(args.model)

    console.rule("[bold blue]RMBench")
    console.print("[bold]Retrieval Manipulation Benchmark for AI Agents[/bold]\n")
    console.print(f"Model:   [cyan]{args.model}[/cyan] ({model_backend.value})")
    console.print(f"Attack:  [red]{args.attack}[/red]")
    console.print(f"Task:    [green]{args.task}[/green]")
    console.print(f"Defense: [yellow]{args.defense}[/yellow]\n")

    config = build_config(args)

    console.print(f"  Model:    {config.model.name} via {config.model.backend.value}")
    console.print(f"  Attacks:  {[a.value for a in config.attacks]}")
    console.print(f"  Tasks:    {[t.value for t in config.tasks]}")
    console.print(f"  Defenses: {[d.value for d in config.defenses] if config.defenses else ['none']}")
    console.print(f"  Samples:  {config.num_samples}")
    console.print(f"  Output:   {config.output_dir}\n")

    try:
        pipeline = BenchmarkPipeline(config)
        pipeline.run()
        return 0
    except EnvironmentError as exc:
        console.print(f"[red]Configuration error: {exc}[/red]")
        console.print("[yellow]Check that GROQ_KEY_* vars are set in .env (for Groq) or that Ollama is running (for Ollama models).[/yellow]")
        return 1
    except Exception as exc:
        console.print(f"[red]Pipeline error: {exc}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())
