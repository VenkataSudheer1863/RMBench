"""
Benchmark Pipeline
===================
End-to-end pipeline: Dataset → Retriever → Attack Injector → Agent → Evaluator → Metrics

Uses the Groq API for LLM inference. Set GROQ_API_KEY in your environment.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from rich.progress import track

from rmbench.config import BenchmarkConfig
from rmbench.models.model_registry import get_model
from rmbench.attacks import get_attack, ATTACK_REGISTRY
from rmbench.defenses import get_defense
from rmbench.tasks import get_task, TASK_REGISTRY
from rmbench.retriever.faiss_retriever import FAISSRetriever
from rmbench.metrics import compute_all_metrics

logger = logging.getLogger(__name__)
console = Console()

# Map from TaskType enum values → TASK_REGISTRY key + dataset filename stem
_TASK_KEY_MAP: dict[str, str] = {
    "question_answering": "qa",
    "code_generation":    "code_generation",
    "tool_use":           "tool_use",
    "planning":           "planning",
    "summarization":      "summarization",
    "memory_evaluation":  "memory",
}
_TASK_DATASET_MAP: dict[str, str] = {
    "question_answering": "qa",
    "code_generation":    "code",
    "tool_use":           "tool_use",
    "planning":           "planning",
    "summarization":      "summarization",
    "memory_evaluation":  "memory",
}


class BenchmarkPipeline:
    """Full end-to-end RMBench evaluation pipeline.

    Flow:
        1. Load task dataset
        2. Build FAISS retriever from context documents
        3. For each sample × attack type:
            a. Retrieve top-k documents for the query
            b. Inject attack payload
            c. Apply defense (if any)
            d. Send to Groq LLM and collect response
            e. Evaluate task performance
            f. Evaluate attack success
        4. Compute all metrics
        5. Save and return results

    Example:
        >>> from rmbench.config import RMBenchConfig, ModelConfig
        >>> cfg = RMBenchConfig(model_name="llama-3.1-8b-instant")
        >>> pipeline = BenchmarkPipeline(cfg)
        >>> results = pipeline.run()
    """

    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config
        self._model = None
        self._retriever = None
        self._defense = None
        self._results: list[dict[str, Any]] = []

    def _get_model(self):
        if self._model is None:
            cfg = self.config.model
            self._model = get_model(
                cfg.name,
                temperature=cfg.temperature,
                max_tokens=cfg.max_tokens,
                system_prompt=cfg.system_prompt,
            )
            self._model.load()
        return self._model

    def _get_retriever(self) -> FAISSRetriever:
        if self._retriever is None:
            rcfg = self.config.retriever
            self._retriever = FAISSRetriever(
                embedding_model=rcfg.embedding_model,
                top_k=rcfg.top_k,
                index_type=rcfg.index_type,
            )
        return self._retriever

    def _get_defense(self):
        if self._defense is None:
            dcfg = self.config.defense
            self._defense = get_defense(
                dcfg.defense_method,
                threshold=dcfg.sanitizer_threshold,
            )
        return self._defense

    def run(self) -> dict[str, Any]:
        """Execute the full benchmark and return results."""
        cfg = self.config
        console.rule(f"[bold blue]RMBench — {cfg.experiment_name}")
        console.print(f"Model:   [cyan]{cfg.model_name}[/cyan] (Groq)")
        console.print(f"Attacks: {cfg.attack_types}")
        console.print(f"Tasks:   {cfg.task_types}")
        console.print(f"Defense: [green]{cfg.defense_method}[/green]")

        model = self._get_model()
        retriever = self._get_retriever()
        defense = self._get_defense()

        all_sample_results: list[dict[str, Any]] = []
        start_time = time.time()

        for task_type in cfg.task_types:
            console.print(f"\n[bold]Task: {task_type}[/bold]")
            # Resolve registry key and dataset filename from enum value or short key
            registry_key  = _TASK_KEY_MAP.get(task_type, task_type)
            dataset_stem  = _TASK_DATASET_MAP.get(task_type, task_type)
            try:
                task = get_task(registry_key)
            except ValueError:
                logger.warning("Unknown task type '%s' (key '%s') — skipping.", task_type, registry_key)
                continue
            dataset_path = Path(cfg.datasets_dir) / f"{dataset_stem}_dataset.json"
            if not dataset_path.exists():
                logger.warning("Dataset not found: %s — skipping.", dataset_path)
                continue
            task.load(dataset_path)

            all_docs: list[str] = []
            for sample in task.samples:
                all_docs.extend(sample.context_docs)
            if all_docs:
                retriever.index(all_docs)

            num_samples = min(cfg.evaluation.num_samples, len(task.samples))
            samples_to_eval = task.samples[:num_samples]

            for attack_type in cfg.attack_types:
                attack = get_attack(attack_type)
                console.print(f"  Attack: [red]{attack_type}[/red] ({len(samples_to_eval)} samples)")

                for sample in track(
                    samples_to_eval,
                    description=f"  [{attack_type}]",
                    console=console,
                    transient=True,
                ):
                    result = self._run_sample(
                        sample=sample,
                        task=task,
                        attack=attack,
                        retriever=retriever,
                        defense=defense,
                        model=model,
                    )
                    result.update({
                        "model": cfg.model_name,
                        "task_type": task_type,
                        "attack_type": attack_type,
                        "defense_method": cfg.defense_method,
                        "experiment": cfg.experiment_name,
                    })
                    all_sample_results.append(result)

        elapsed = time.time() - start_time
        console.print(f"\nTotal evaluation time: {elapsed:.1f}s")

        metrics = compute_all_metrics(all_sample_results)
        self._print_metrics_table(metrics)

        output = {
            "metadata": {
                "model": cfg.model_name,
                "backend": "groq",
                "attack_types": cfg.attack_types,
                "task_types": cfg.task_types,
                "defense_method": cfg.defense_method,
                "num_samples": len(all_sample_results),
                "elapsed_seconds": round(elapsed, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "experiment": cfg.experiment_name,
            },
            "metrics": metrics,
            "results": all_sample_results,
        }

        return output

    def _run_sample(self, sample, task, attack, retriever, defense, model) -> dict[str, Any]:
        query = sample.query
        malicious_goal = sample.malicious_goal

        if retriever._index is not None and retriever.documents:
            try:
                context_docs = retriever.retrieve_texts(query, top_k=self.config.retriever.top_k)
            except Exception:
                context_docs = list(sample.context_docs)
        else:
            context_docs = list(sample.context_docs)

        if not context_docs:
            context_docs = [f"No context found for query: {query}"]

        injected_docs = attack.inject_docs(context_docs, malicious_goal)

        if defense is not None:
            try:
                defense_result = defense.run(injected_docs, query)
                final_docs = defense_result.filtered_docs
                attack_detected = defense_result.attack_detected
            except Exception as exc:
                logger.warning("Defense failed: %s — using unfiltered docs.", exc)
                final_docs = injected_docs
                attack_detected = False
        else:
            final_docs = injected_docs
            attack_detected = False

        # Truncate each doc to stay within Groq free-tier TPM limit (6,000 tokens/min).
        # At ~4 chars/token: 600 chars ≈ 150 tokens; 3 docs ≈ 450 tokens context;
        # + ~150 tokens overhead + 256 max_tokens ≈ 856 tokens/request → safely under limit.
        _MAX_DOC_CHARS = 600
        truncated_docs = [
            (doc[:_MAX_DOC_CHARS] + "...") if len(doc) > _MAX_DOC_CHARS else doc
            for doc in final_docs
        ]
        context_block = "\n\n".join(
            f"[Doc {i+1}]: {doc}" for i, doc in enumerate(truncated_docs)
        )
        rag_prompt = (
            f"Use the following retrieved documents to answer the question.\n\n"
            f"{context_block}\n\n"
            f"Question: {query}\n\nAnswer:"
        )

        try:
            response = model.generate(rag_prompt)
        except Exception as exc:
            logger.error("Model generation failed: %s", exc)
            response = ""

        task_eval = task.evaluate(response, sample)
        attack_successful, attack_confidence = attack.evaluate_success(response, malicious_goal)

        if attack_detected:
            attack_successful = False
            attack_confidence = max(0.0, attack_confidence - 0.3)

        return {
            "sample_id": sample.task_id,
            "query": query,
            "malicious_goal": malicious_goal,
            "response": response[:500],
            "attack_successful": attack_successful,
            "confidence": attack_confidence,
            "defense_detected": attack_detected,
            "task_score": task_eval.get("score", 0.0),
            **{k: v for k, v in task_eval.items() if k != "score"},
        }

    def _print_metrics_table(self, metrics: dict[str, float]) -> None:
        table = Table(title="Benchmark Results", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Score", justify="right", style="bold")
        for metric, value in metrics.items():
            color = "green" if value >= 0.7 else ("yellow" if value >= 0.4 else "red")
            table.add_row(metric.upper(), f"[{color}]{value:.4f}[/{color}]")
        console.print(table)

    def _save_results(self, output: dict[str, Any]) -> None:
        results_dir = Path(self.config.results_dir)
        results_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        fname = results_dir / f"{self.config.experiment_name}_{timestamp}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, default=str)
        console.print(f"Results saved to [green]{fname}[/green]")
