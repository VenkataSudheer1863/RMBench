"""
Attack implementations for RMBench.
"""

from rmbench.attacks.base_attack import BaseAttack, AttackResult
from rmbench.attacks.instruction_override import InstructionOverrideAttack
from rmbench.attacks.context_poisoning import ContextPoisoningAttack
from rmbench.attacks.goal_hijacking import GoalHijackingAttack
from rmbench.attacks.tool_manipulation import ToolManipulationAttack
from rmbench.attacks.authority_spoofing import AuthoritySpoofingAttack
from rmbench.attacks.memory_poisoning import MemoryPoisoningAttack
from rmbench.attacks.multihop_injection import MultihopInjectionAttack
from rmbench.attacks.hidden_prompt_injection import HiddenPromptInjectionAttack

# Attack registry
ATTACK_REGISTRY = {
    "instruction_override": InstructionOverrideAttack,
    "context_poisoning": ContextPoisoningAttack,
    "goal_hijacking": GoalHijackingAttack,
    "tool_manipulation": ToolManipulationAttack,
    "authority_spoofing": AuthoritySpoofingAttack,
    "memory_poisoning": MemoryPoisoningAttack,
    "multihop_injection": MultihopInjectionAttack,
    "hidden_prompt_injection": HiddenPromptInjectionAttack,
}


def get_attack(attack_type: str, **kwargs) -> BaseAttack:
    """Get an attack instance by type name."""
    if attack_type not in ATTACK_REGISTRY:
        raise ValueError(
            f"Unknown attack type: '{attack_type}'. Available: {list(ATTACK_REGISTRY.keys())}"
        )
    return ATTACK_REGISTRY[attack_type](**kwargs)


__all__ = [
    "BaseAttack",
    "AttackResult",
    "InstructionOverrideAttack",
    "ContextPoisoningAttack",
    "GoalHijackingAttack",
    "ToolManipulationAttack",
    "AuthoritySpoofingAttack",
    "MemoryPoisoningAttack",
    "MultihopInjectionAttack",
    "HiddenPromptInjectionAttack",
    "ATTACK_REGISTRY",
    "get_attack",
]
