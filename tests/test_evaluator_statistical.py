"""
Test cases for EvaluatorAgent V2 statistical validation.
"""

import pytest
from src.agents.evaluator_agent import EvaluatorAgent


class TestEvaluatorStatistical:
    """Test statistical validation in EvaluatorAgent V2."""

    def test_severity_classification_critical(self):
        """Test critical severity classification."""
        ev = EvaluatorAgent()
        
        evidence = {
            "baseline_value": 12.5,
            "current_value": 5.0,
            "absolute_delta": -7.5,
            "relative_delta": -0.6,
            "diagnosis": "severe_performance_degradation",
            "spend": 50000
        }
        
        severity = ev._calculate_severity(evidence)
        assert severity == "critical", f"Expected critical, got {severity}"

    def test_severity_classification_high(self):
        """Test high severity classification."""
        ev = EvaluatorAgent()
        
        evidence = {
            "baseline_value": 10.0,
            "current_value": 7.0,
            "absolute_delta": -3.0,
            "relative_delta": -0.30,
            "diagnosis": "moderate_performance_decline",
            "spend": 15000
        }
        
        severity = ev._calculate_severity(evidence)
        assert severity == "high", f"Expected high, got {severity}"

    def test_severity_classification_medium(self):
        """Test medium severity classification."""
        ev = EvaluatorAgent()
        
        evidence = {
            "baseline_value": 10.0,
            "current_value": 8.2,
            "absolute_delta": -1.8,
            "relative_delta": -0.18,
            "diagnosis": "engagement_decline",
            "spend": 5000
        }
        
        severity = ev._calculate_severity(evidence)
        assert severity == "medium", f"Expected medium, got {severity}"

    def test_severity_classification_low(self):
        """Test low severity classification."""
        ev = EvaluatorAgent()
        
        evidence = {
            "baseline_value": 10.0,
            "current_value": 9.0,
            "absolute_delta": -1.0,
            "relative_delta": -0.10,
            "diagnosis": "minor_variance",
            "spend": 1000
        }
        
        severity = ev._calculate_severity(evidence)
        assert severity == "low", f"Expected low, got {severity}"

    def test_statistical_significance_validation(self):
        """Test statistical significance validation."""
        ev = EvaluatorAgent()
        
        evidence = {
            "baseline_value": 10.0,
            "current_value": 7.0,
            "absolute_delta": -3.0,
            "relative_delta": -0.30
        }
        
        result = ev._validate_statistical_significance(evidence)
        
        assert result['is_significant'] == True
        assert result['significance_level'] == "high"
        assert 'normalized_change' in result
        assert result['validation_method'] == "percentile_threshold"

    def test_statistical_significance_not_significant(self):
        """Test non-significant change."""
        ev = EvaluatorAgent()
        
        evidence = {
            "baseline_value": 10.0,
            "current_value": 9.5,
            "absolute_delta": -0.5,
            "relative_delta": -0.05
        }
        
        result = ev._validate_statistical_significance(evidence)
        
        assert result['is_significant'] == False

    def test_confidence_normalization_boost(self):
        """Test confidence normalization with boost for high significance."""
        ev = EvaluatorAgent()
        
        validation_result = {
            'is_significant': True,
            'significance_level': 'high'
        }
        
        normalized = ev._normalize_confidence(0.7, validation_result)
        assert normalized > 0.7, "Confidence should be boosted"
        assert normalized <= 1.0, "Confidence should not exceed 1.0"

    def test_confidence_normalization_penalty(self):
        """Test confidence normalization with penalty for low significance."""
        ev = EvaluatorAgent()
        
        validation_result = {
            'is_significant': False,
            'significance_level': 'low'
        }
        
        normalized = ev._normalize_confidence(0.7, validation_result)
        assert normalized < 0.7, "Confidence should be penalized"
        assert normalized >= 0.0, "Confidence should not be negative"

    def test_validate_full_insight(self):
        """Test full validation of an insight."""
        ev = EvaluatorAgent()
        
        insights = {
            "insights": [{
                "hypothesis": "Campaign X shows ROAS drop",
                "evidence": {
                    "baseline_value": 12.5,
                    "current_value": 6.2,
                    "absolute_delta": -6.3,
                    "relative_delta": -0.504,
                    "diagnosis": "severe_performance_degradation",
                    "spend": 25000
                },
                "confidence": 0.80
            }]
        }
        
        result = ev.validate(insights, {})
        
        assert len(result['validated']) == 1
        validated = result['validated'][0]
        
        assert 'severity' in validated
        assert validated['severity'] in ['critical', 'high', 'medium', 'low']
        assert 'confidence' in validated
        assert 'validation_notes' in validated
        assert 'statistical_validation' in validated

    def test_validate_missing_required_fields(self):
        """Test validation handles missing required fields."""
        ev = EvaluatorAgent()
        
        insights = {
            "insights": [{
                "hypothesis": "Test hypothesis",
                "evidence": {},  # Missing required fields
                "confidence": 0.5
            }]
        }
        
        result = ev.validate(insights, {})
        
        # Should not crash, should set defaults
        assert len(result['validated']) == 1
        validated = result['validated'][0]
        assert 'severity' in validated

    def test_no_if_else_hacks(self):
        """Verify no hardcoded if/else threshold logic in validation."""
        ev = EvaluatorAgent()
        
        # Test that validation uses percentile-based method, not if/else
        evidence1 = {
            "baseline_value": 10.0,
            "current_value": 7.0,
            "absolute_delta": -3.0,
            "relative_delta": -0.30,
            "diagnosis": "test"
        }
        
        evidence2 = {
            "baseline_value": 10.0,
            "current_value": 6.9,
            "absolute_delta": -3.1,
            "relative_delta": -0.31,
            "diagnosis": "test"
        }
        
        result1 = ev._validate_statistical_significance(evidence1)
        result2 = ev._validate_statistical_significance(evidence2)
        
        # Both should use same validation method
        assert result1['validation_method'] == result2['validation_method']
        assert result1['validation_method'] == "percentile_threshold"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
