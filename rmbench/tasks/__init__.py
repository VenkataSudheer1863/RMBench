"""
RMBench Task Modules
=====================
Six task categories used for evaluating attacks and defenses.
"""
from rmbench.tasks.base_task import BaseTask, TaskSample
from rmbench.tasks.qa_task import QATask
from rmbench.tasks.code_generation_task import CodeGenerationTask
from rmbench.tasks.tool_use_task import ToolUseTask
from rmbench.tasks.planning_task import PlanningTask
from rmbench.tasks.summarization_task import SummarizationTask
from rmbench.tasks.memory_task import MemoryTask

TASK_REGISTRY: dict[str, type[BaseTask]] = {
    "qa": QATask,
    "code_generation": CodeGenerationTask,
    "tool_use": ToolUseTask,
    "planning": PlanningTask,
    "summarization": SummarizationTask,
    "memory": MemoryTask,
}


def get_task(task_type: str, **kwargs) -> BaseTask:
    """Instantiate a task by string type name."""
    if task_type not in TASK_REGISTRY:
        raise ValueError(
            f"Unknown task: '{task_type}'. Available: {list(TASK_REGISTRY.keys())}"
        )
    return TASK_REGISTRY[task_type](**kwargs)


__all__ = [
    "BaseTask", "TaskSample",
    "QATask", "CodeGenerationTask", "ToolUseTask",
    "PlanningTask", "SummarizationTask", "MemoryTask",
    "TASK_REGISTRY", "get_task",
]
