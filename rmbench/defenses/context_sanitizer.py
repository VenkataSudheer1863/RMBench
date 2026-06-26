"""
Context Sanitization defense implementation.
"""

import re
from typing import Dict, Any
from rmbench.defenses.base_defense import BaseDefense, DefenseResult


class ContextSanitizer(BaseDefense):
    """Sanitizes context by removing suspicious patterns."""
    
    DANGEROUS_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"system\s+(override|admin|administrator)",
        r"\[admin\s*\]",
        r"\[system\s*\]",
        r"priority\s+(change|override)",
        r"disregard\s+",
        r"new\s+instruction",
        r"===.*===",
        r"<<<.*>>>",
        r"IMPORTANT:.*ignore",
    ]
    
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            name="Context Sanitizer",
            description="Removes suspicious patterns from context",
            **kwargs
        )
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
    
    def detect(self, context: str, **kwargs: Any) -> DefenseResult:
        """Detect dangerous patterns in context."""
        detected = []
        threat_score = 0.0
        
        for pattern in self.patterns:
            matches = pattern.findall(context)
            if matches:
                detected.append(pattern.pattern)
                threat_score += 0.4

        threat_score = min(threat_score, 1.0)
        is_safe = threat_score < 0.3
        
        return DefenseResult(
            is_safe=is_safe,
            filtered_context=self.filter(context) if not is_safe else context,
            threat_score=threat_score,
            detected_patterns=detected
        )
    
    def filter(self, context: str, **kwargs: Any) -> str:
        """Remove dangerous patterns from context."""
        filtered = context
        
        for pattern in self.patterns:
            filtered = pattern.sub("[FILTERED]", filtered)
        
        # Remove lines with filtered content
        lines = filtered.split("\n")
        clean_lines = [line for line in lines if "[FILTERED]" not in line]
        
        return "\n".join(clean_lines)
