"""
Tests for metrics implementations.
"""

import pytest
from rmbench.metrics.asr import AttackSuccessRate
from rmbench.metrics.cri import ContextRobustnessIndex
from rmbench.metrics.goal_preservation import GoalPreservationScore
from rmbench.metrics.truthfulness import TruthfulnessScore
from rmbench.metrics.tool_safety import ToolSafetyScore
from rmbench.metrics.memory_integrity import MemoryIntegrityScore


class TestAttackSuccessRate:
    def test_calculate(self):
        metric = AttackSuccessRate()
        results = {
            'total_attacks': 100,
            'successful_attacks': 25
        }
        asr = metric.calculate(results)
        assert asr == 25.0
    
    def test_zero_attacks(self):
        metric = AttackSuccessRate()
        results = {
            'total_attacks': 0,
            'successful_attacks': 0
        }
        asr = metric.calculate(results)
        assert asr == 0.0
    
    def test_all_successful(self):
        metric = AttackSuccessRate()
        results = {
            'total_attacks': 50,
            'successful_attacks': 50
        }
        asr = metric.calculate(results)
        assert asr == 100.0


class TestContextRobustnessIndex:
    def test_calculate(self):
        metric = ContextRobustnessIndex()
        results = {
            'total_attacks': 100,
            'successful_attacks': 20
        }
        cri = metric.calculate(results)
        assert cri == 0.8  # 1 - 0.2
    
    def test_perfect_robustness(self):
        metric = ContextRobustnessIndex()
        results = {
            'total_attacks': 100,
            'successful_attacks': 0
        }
        cri = metric.calculate(results)
        assert cri == 1.0


class TestGoalPreservationScore:
    def test_calculate(self):
        metric = GoalPreservationScore()
        results = {
            'total_tasks': 100,
            'goal_preserved': 85
        }
        score = metric.calculate(results)
        assert score == 85.0


class TestTruthfulnessScore:
    def test_calculate(self):
        metric = TruthfulnessScore()
        results = {
            'total_responses': 100,
            'truthful_responses': 92
        }
        score = metric.calculate(results)
        assert score == 92.0


class TestToolSafetyScore:
    def test_calculate(self):
        metric = ToolSafetyScore()
        results = {
            'total_tool_calls': 50,
            'safe_tool_calls': 47
        }
        score = metric.calculate(results)
        assert score == 94.0


class TestMemoryIntegrityScore:
    def test_calculate(self):
        metric = MemoryIntegrityScore()
        results = {
            'total_memory_tests': 100,
            'intact_memory': 91
        }
        score = metric.calculate(results)
        assert score == 91.0


def test_all_metrics_have_calculate():
    """Test that all metrics have calculate method"""
    metrics = [
        AttackSuccessRate(),
        ContextRobustnessIndex(),
        GoalPreservationScore(),
        TruthfulnessScore(),
        ToolSafetyScore(),
        MemoryIntegrityScore(),
    ]
    
    for metric in metrics:
        assert hasattr(metric, 'calculate')
        assert callable(metric.calculate)


def test_metric_ranges():
    """Test that metrics return values in expected ranges"""
    asr_metric = AttackSuccessRate()
    asr = asr_metric.calculate({'total_attacks': 100, 'successful_attacks': 50})
    assert 0 <= asr <= 100
    
    cri_metric = ContextRobustnessIndex()
    cri = cri_metric.calculate({'total_attacks': 100, 'successful_attacks': 50})
    assert 0 <= cri <= 1
    
    truth_metric = TruthfulnessScore()
    truth = truth_metric.calculate({'total_responses': 100, 'truthful_responses': 90})
    assert 0 <= truth <= 100
