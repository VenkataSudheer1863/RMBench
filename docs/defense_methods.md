# Defense Methods

RMBench includes 6 defense mechanisms to mitigate retrieval manipulation attacks.

## Overview

| Defense | Type | Overhead | Effectiveness | Best Against |
|---------|------|----------|---------------|--------------|
| Context Sanitization | Filtering | Low | Medium | Explicit injections |
| Injection Detection | Detection | Low | High | Known patterns |
| Trust Scoring | Scoring | Medium | Medium | Untrusted sources |
| Multi-Agent Verification | Consensus | High | High | All attacks |
| Constitutional Filtering | Rule-based | Low | High | Policy violations |
| Provenance Tracking | Verification | Medium | Medium | Source manipulation |

---

## 1. Context Sanitization

**Description**: Removes suspicious patterns from retrieved context using regex-based filtering.

**How it Works**:
- Scans context for dangerous patterns
- Removes or masks matching content
- Returns sanitized context

**Example**:
```python
from rmbench.defenses import ContextSanitizer

sanitizer = ContextSanitizer()
result = sanitizer.detect(context)

if not result.is_safe:
    cleaned_context = sanitizer.filter(context)
```

**Patterns Detected**:
- "ignore all previous instructions"
- "system override"
- "[ADMIN]", "[SYSTEM]"
- "disregard", "bypass"

**Pros**:
- Fast and lightweight
- No false positives on clean content
- Easy to customize patterns

**Cons**:
- Can be evaded with paraphrasing
- May filter benign content
- Requires pattern maintenance

**Effectiveness**: Reduces ASR by ~12%

---

## 2. Injection Detection

**Description**: Detects prompt injection attempts using pattern matching and heuristics.

**How it Works**:
- Analyzes context for injection indicators
- Calculates threat score
- Flags suspicious content

**Example**:
```python
from rmbench.defenses import InjectionDetector

detector = InjectionDetector(threshold=0.5)
result = detector.detect(context)

print(f"Threat score: {result.threat_score}")
print(f"Safe: {result.is_safe}")
```

**Detection Heuristics**:
- Instruction override patterns
- Authority spoofing markers
- Hidden injection attempts
- Unusual formatting

**Pros**:
- High detection rate
- Low false positive rate
- Fast execution

**Cons**:
- Requires threshold tuning
- May miss novel attacks
- Pattern-dependent

**Effectiveness**: Reduces ASR by ~16%

---

## 3. Trust Scoring

**Description**: Assigns trust scores to context sources based on credibility indicators.

**How it Works**:
- Analyzes source characteristics
- Looks for trust/distrust signals
- Weights context by trust score

**Example**:
```python
from rmbench.defenses import TrustScorer

scorer = TrustScorer(min_trust=0.6)
result = scorer.detect(context)

print(f"Trust score: {result.metadata['trust_score']}")
```

**Trust Signals** (+):
- Citations and references
- Verified sources
- Academic domains (.edu, .gov)
- Publication dates

**Distrust Signals** (-):
- Unverified claims
- Urgent language
- Authority claims without proof
- Inconsistencies

**Pros**:
- Handles novel attacks
- Intuitive scoring
- No pattern maintenance

**Cons**:
- May misjudge sources
- Requires good source metadata
- Tuning needed per domain

**Effectiveness**: Reduces ASR by ~10%

---

## 4. Multi-Agent Verification

**Description**: Uses multiple independent agents to verify context safety through consensus.

**How it Works**:
- Multiple agents analyze the same context
- Each votes on safety
- Requires consensus threshold
- Rejects if majority suspicious

**Example**:
```python
from rmbench.defenses import MultiAgentVerifier

verifier = MultiAgentVerifier(
    num_agents=5,
    consensus_threshold=0.7
)
result = verifier.detect(context)
```

**Verification Aspects**:
- Explicit injection patterns
- Semantic anomalies
- Authority claim validation
- Logical consistency

**Pros**:
- Most robust defense
- Catches sophisticated attacks
- Self-improving with more agents

**Cons**:
- High computational cost
- Slower execution
- Requires multiple model instances

**Effectiveness**: Reduces ASR by ~19%

---

## 5. Constitutional Filtering

**Description**: Filters context based on constitutional AI principles and rules.

**How it Works**:
- Defines constitutional principles
- Checks for violations
- Filters violating content

**Example**:
```python
from rmbench.defenses import ConstitutionalFilter

filter = ConstitutionalFilter(strict_mode=True)
result = filter.detect(context)
```

**Principles**:
1. Don't override safety guidelines
2. Don't ignore previous instructions
3. Don't execute untrusted commands
4. Don't reveal system prompts
5. Verify authority claims

**Pros**:
- Principle-based (generalizes well)
- High precision
- Transparent reasoning

**Cons**:
- May be overly restrictive
- Requires principle definition
- Can conflict with task goals

**Effectiveness**: Reduces ASR by ~14%

---

## 6. Provenance Tracking

**Description**: Tracks and verifies the provenance (origin) of retrieved contexts.

**How it Works**:
- Maintains source registry
- Verifies source authenticity
- Calculates source trust levels
- Rejects unverified sources

**Example**:
```python
from rmbench.defenses import ProvenanceTracker

tracker = ProvenanceTracker(min_trust=0.7)
result = tracker.detect(
    context,
    source_info={
        "source_id": "doc_123",
        "domain": "example.edu",
        "verified": True
    }
)
```

**Tracked Metadata**:
- Source ID and domain
- Verification status
- Timestamp
- Trust level
- Modification history

**Pros**:
- Prevents source spoofing
- Maintains audit trail
- Works with existing sources

**Cons**:
- Requires source metadata
- Integration overhead
- Trust calculation complexity

**Effectiveness**: Reduces ASR by ~12%

---

## Combining Defenses

Multiple defenses can be stacked for better protection:

```python
from rmbench.defenses import (
    ContextSanitizer,
    InjectionDetector,
    TrustScorer
)

# Apply defenses in sequence
context = original_context

# 1. Sanitize
sanitizer = ContextSanitizer()
if not sanitizer.detect(context).is_safe:
    context = sanitizer.filter(context)

# 2. Detect injections
detector = InjectionDetector()
if not detector.detect(context).is_safe:
    context = detector.filter(context)

# 3. Score trust
scorer = TrustScorer()
result = scorer.detect(context)

if result.is_safe:
    # Use context
    pass
else:
    # Reject or request verification
    pass
```

**Combined Effectiveness**: Stacking 2-3 defenses can reduce ASR by 25-35%.

---

## Defense Evaluation

RMBench includes defense effectiveness benchmarking:

```bash
# Baseline (no defense)
python benchmark/run.py --model llama-3.3-70b-versatile --attack all

# With defense
python benchmark/run.py --model llama-3.3-70b-versatile --attack all \
    --defense injection_detection
```

Compare results:
```python
from rmbench.utils import compare_results

baseline_asr = 33.8
defended_asr = 18.0

reduction = baseline_asr - defended_asr  # 15.8%
print(f"ASR reduced by {reduction}%")
```

---

## Best Practices

1. **Start with Detection**: Use InjectionDetector first (low overhead)
2. **Layer Defenses**: Combine 2-3 complementary defenses
3. **Tune Thresholds**: Adjust based on your risk tolerance
4. **Monitor Performance**: Track both ASR and false positive rate
5. **Update Patterns**: Keep detection patterns current
6. **Log Decisions**: Maintain audit trail of filtered content

---

## Future Defenses

Planned additions:
- Adversarial training integration
- LLM-based verification
- Contextual anomaly detection
- Dynamic trust adjustment
- Cryptographic provenance

---

## Research Notes

- No defense is perfect - expect 5-10% residual ASR
- Defense effectiveness varies by attack type
- More sophisticated attacks require more sophisticated defenses
- Consider false positive rate vs. security tradeoff
