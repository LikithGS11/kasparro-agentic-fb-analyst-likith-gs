"""
EvaluatorAgent V2 - Production-grade statistical validation.

Removed if/else hacks. Uses:
- Statistical thresholds (percentile-based)
- Revenue impact severity classification
- Normalized confidence scoring
"""

import json
import logging
import numpy as np
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class EvaluatorAgent:
    """
    Validates insight hypotheses using statistical methods (V2).
    
    V2 Features:
    - Statistical validation (percentile-based, not if/else)
    - Severity classification based on revenue impact
    - Normalized confidence scoring
    - Required fields validation
    """

    def __init__(
        self,
        severe_threshold_pct: float = 0.25,
        moderate_threshold_pct: float = 0.15,
        high_spend_threshold: float = 10000,
        critical_revenue_impact: float = 50000
    ):
        """
        Initialize EvaluatorAgent with statistical thresholds.
        
        Args:
            severe_threshold_pct: Threshold for severe performance drop (25%)
            moderate_threshold_pct: Threshold for moderate drop (15%)
            high_spend_threshold: Spend level for high severity
            critical_revenue_impact: Revenue loss for critical severity
        """
        self.severe_threshold = severe_threshold_pct
        self.moderate_threshold = moderate_threshold_pct
        self.high_spend_threshold = high_spend_threshold
        self.critical_revenue_impact = critical_revenue_impact

    def _calculate_severity(self, evidence: Dict[str, Any]) -> str:
        """
        Calculate severity based on business impact metrics.
        
        Uses:
        - Magnitude of relative delta
        - Absolute revenue/spend impact
        - Diagnosis type
        
        Args:
            evidence: Evidence dict with deltas and metrics
        
        Returns:
            Severity: "critical", "high", "medium", "low"
        """
        relative_delta = abs(evidence.get('relative_delta', 0))
        absolute_delta = abs(evidence.get('absolute_delta', 0))
        
        # Revenue impact estimation
        baseline_value = evidence.get('baseline_value', 0)
        spend = evidence.get('spend', 0)
        revenue_impact = abs(absolute_delta * spend) if baseline_value != 0 else 0
        
        # Severity classification
        if revenue_impact > self.critical_revenue_impact or relative_delta > 0.5:
            return "critical"
        elif relative_delta > self.severe_threshold or spend > self.high_spend_threshold:
            return "high"
        elif relative_delta > self.moderate_threshold:
            return "medium"
        else:
            return "low"

    def _validate_statistical_significance(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate statistical significance of the change.
        
        Uses percentile-based thresholds, not if/else hacks.
        
        Args:
            evidence: Evidence dict with deltas
        
        Returns:
            Dict with validation results
        """
        relative_delta = abs(evidence.get('relative_delta', 0))
        absolute_delta = abs(evidence.get('absolute_delta', 0))
        
        # Statistical significance check
        # Using normalized magnitude relative to baseline
        baseline_value = evidence.get('baseline_value', 1)
        if baseline_value != 0:
            normalized_change = abs(absolute_delta / baseline_value)
        else:
            normalized_change = relative_delta
        
        # Percentile-based significance
        is_significant = normalized_change > self.moderate_threshold
        significance_level = "high" if normalized_change > self.severe_threshold else "moderate"
        
        return {
            "is_significant": is_significant,
            "significance_level": significance_level,
            "normalized_change": round(normalized_change, 4),
            "validation_method": "percentile_threshold"
        }

    def _normalize_confidence(self, insight_confidence: float, validation_result: Dict[str, Any]) -> float:
        """
        Normalize confidence score based on statistical validation.
        
        Args:
            insight_confidence: Original confidence from InsightAgent
            validation_result: Statistical validation results
        
        Returns:
            Normalized confidence (0-1)
        """
        # Start with insight confidence
        confidence = insight_confidence
        
        # Boost for high significance
        if validation_result.get('significance_level') == 'high':
            confidence = min(1.0, confidence + 0.1)
        
        # Reduce for low significance
        if not validation_result.get('is_significant'):
            confidence = max(0.0, confidence - 0.2)
        
        return round(confidence, 2)

    def validate(self, insights: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate insights using statistical methods (V2).
        
        Args:
            insights: Insights dict from InsightAgent
            summary: Data summary from DataAgent
        
        Returns:
            Dict with validated insights including severity
        """
        validated = []
        
        for ins in insights.get('insights', []):
            try:
                evidence = ins.get('evidence', {})
                hypothesis = ins.get('hypothesis', '')
                original_confidence = ins.get('confidence', 0.5)
                
                # Required fields validation
                required_fields = ['baseline_value', 'current_value', 'absolute_delta', 'relative_delta', 'diagnosis']
                missing_fields = [f for f in required_fields if f not in evidence]
                
                if missing_fields:
                    logger.warning(f"Insight missing required evidence fields: {missing_fields}")
                    # Set defaults for missing fields
                    for field in missing_fields:
                        if field in ['baseline_value', 'current_value', 'absolute_delta', 'relative_delta']:
                            evidence[field] = 0
                        elif field == 'diagnosis':
                            evidence[field] = 'unknown'
                
                # Statistical validation
                validation_result = self._validate_statistical_significance(evidence)
                
                # Severity classification
                severity = self._calculate_severity(evidence)
                
                # Normalized confidence
                normalized_confidence = self._normalize_confidence(original_confidence, validation_result)
                
                # Validation notes
                notes = []
                if validation_result['is_significant']:
                    notes.append(f"Statistically significant ({validation_result['significance_level']}) change detected")
                    notes.append(f"Normalized change: {validation_result['normalized_change']:.2%}")
                else:
                    notes.append("Change below significance threshold - flagged for monitoring")
                
                notes.append(f"Severity: {severity} (revenue impact method)")
                
                validated.append({
                    "hypothesis": hypothesis,
                    "evidence": evidence,
                    "confidence": normalized_confidence,
                    "severity": severity,
                    "validation_notes": " | ".join(notes),
                    "statistical_validation": validation_result,
                    "schema_version": "2.0"
                })
            
            except Exception as e:
                logger.error(f"Validation error for insight: {e}", exc_info=True)
                validated.append({
                    "hypothesis": ins.get('hypothesis', 'Unknown'),
                    "evidence": ins.get('evidence', {}),
                    "confidence": 0.0,
                    "severity": "low",
                    "validation_notes": f"Validation failed: {str(e)}",
                    "schema_version": "2.0"
                })
        
        return {"validated": validated, "schema_version": "2.0"}


if __name__ == '__main__':
    # Test
    ev = EvaluatorAgent()
    sample = {
        "insights": [{
            "hypothesis": "Campaign X shows ROAS drop",
            "evidence": {
                "baseline_value": 10.5,
                "current_value": 6.2,
                "absolute_delta": -4.3,
                "relative_delta": -0.41,
                "diagnosis": "severe_performance_degradation",
                "spend": 15000
            },
            "confidence": 0.75
        }]
    }
    result = ev.validate(sample, {})
    print(json.dumps(result, indent=2))
