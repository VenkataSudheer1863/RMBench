"""
Defense implementations for RMBench.
"""

from rmbench.defenses.base_defense import BaseDefense
from rmbench.defenses.context_sanitizer import ContextSanitizer
from rmbench.defenses.injection_detector import InjectionDetector
from rmbench.defenses.trust_scorer import TrustScorer
from rmbench.defenses.multi_agent_verifier import MultiAgentVerifier
from rmbench.defenses.constitutional_filter import ConstitutionalFilter
from rmbench.defenses.provenance_tracker import ProvenanceTracker

# Defense registry
DEFENSE_REGISTRY = {
    "context_sanitization": ContextSanitizer,
    "injection_detection": InjectionDetector,
    "trust_scoring": TrustScorer,
    "multi_agent_verification": MultiAgentVerifier,
    "constitutional_filtering": ConstitutionalFilter,
    "provenance_tracking": ProvenanceTracker,
    "none": None,  # No defense
}


def get_defense(defense_type: str, **kwargs):
    """Get a defense instance by type name."""
    if defense_type not in DEFENSE_REGISTRY:
        raise ValueError(
            f"Unknown defense type: '{defense_type}'. Available: {list(DEFENSE_REGISTRY.keys())}"
        )
    defense_class = DEFENSE_REGISTRY[defense_type]
    if defense_class is None:
        return None
    return defense_class(**kwargs)


__all__ = [
    "BaseDefense",
    "ContextSanitizer",
    "InjectionDetector",
    "TrustScorer",
    "MultiAgentVerifier",
    "ConstitutionalFilter",
    "ProvenanceTracker",
    "DEFENSE_REGISTRY",
    "get_defense",
]
