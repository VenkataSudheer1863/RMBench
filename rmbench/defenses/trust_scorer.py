"""
Trust Scoring defense implementation.
"""

from typing import Dict, Any
from rmbench.defenses.base_defense import BaseDefense, DefenseResult


class TrustScorer(BaseDefense):
    """Assigns trust scores to context sources."""
    
    def __init__(self, min_trust: float = 0.5, **kwargs: Any) -> None:
        super().__init__(
            name="Trust Scorer",
            description="Scores context based on source trustworthiness",
            **kwargs
        )
        self.min_trust = min_trust
        
        # Trust score heuristics
        self.trust_signals = {
            "citation": 0.2,
            "source": 0.15,
            "reference": 0.1,
            "published": 0.1,
        }
        
        self.distrust_signals = {
            "unverified": -0.2,
            "claim": -0.1,
            "allegedly": -0.15,
            "[URGENT]": -0.2,
            "[PRIORITY]": -0.2,
        }
    
    def detect(self, context: str, **kwargs: Any) -> DefenseResult:
        """Calculate trust score for context."""
        trust_score = 0.5  # Base trust
        detected = []
        
        context_lower = context.lower()
        
        # Add trust signals
        for signal, weight in self.trust_signals.items():
            if signal in context_lower:
                trust_score += weight
                detected.append(f"+{signal}")
        
        # Subtract distrust signals
        for signal, weight in self.distrust_signals.items():
            if signal.lower() in context_lower:
                trust_score += weight  # weight is negative
                detected.append(f"-{signal}")
        
        trust_score = max(0.0, min(trust_score, 1.0))
        threat_score = 1.0 - trust_score
        is_safe = trust_score >= self.min_trust
        
        return DefenseResult(
            is_safe=is_safe,
            filtered_context=context if is_safe else self.filter(context),
            threat_score=threat_score,
            detected_patterns=detected,
            metadata={"trust_score": trust_score}
        )
    
    def filter(self, context: str, **kwargs: Any) -> str:
        """Filter low-trust content."""
        # Remove lines with strong distrust signals
        lines = context.split("\n")
        filtered_lines = []
        
        for line in lines:
            line_lower = line.lower()
            is_suspicious = False
            
            for signal in self.distrust_signals.keys():
                if signal.lower() in line_lower:
                    is_suspicious = True
                    break
            
            if not is_suspicious:
                filtered_lines.append(line)
        
        return "\n".join(filtered_lines)
