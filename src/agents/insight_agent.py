import json
import logging
import numpy as np
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)


class InsightAgent:
    """
    Generates hypotheses from data summary using adaptive heuristics.
    
    V2 Features:
    - IQR-based outlier removal for robust signal detection
    - Dynamic threshold scaling based on data variance
    - Automatic confidence scoring (high/low confidence)
    - Generalized insights to avoid overfitting to synthetic data
    - Schema version 2.0 compliance
    """

    def __init__(
        self,
        iqr_multiplier: float = 1.5,
        min_confidence: float = 0.4,
        max_confidence: float = 0.95,
        use_percentile_method: bool = True
    ):
        """
        Initialize InsightAgent.
        
        Args:
            iqr_multiplier: IQR multiplier for outlier detection (1.5 is standard)
            min_confidence: Minimum confidence floor
            max_confidence: Maximum confidence ceiling
            use_percentile_method: Use 90th percentile instead of IQR (more robust for small datasets)
        """
        self.iqr_multiplier = iqr_multiplier
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence
        self.use_percentile_method = use_percentile_method

    def _detect_outliers(self, values: List[float]) -> Tuple[List[float], int]:
        """
        Remove outliers using IQR or percentile method.
        
        Args:
            values: List of numeric values
        
        Returns:
            Tuple of (filtered_values, num_outliers_removed)
        """
        if not values or len(values) < 2:
            return values, 0
        
        try:
            arr = np.array([v for v in values if v is not None and isinstance(v, (int, float))])
            if len(arr) == 0:
                return [], 0
            
            if self.use_percentile_method:
                # More robust for small datasets: remove values beyond 90th percentile
                p90 = np.percentile(arr, 90)
                p10 = np.percentile(arr, 10)
                filtered = [v for v in arr if p10 <= v <= p90]
            else:
                # Classic IQR method
                q1 = np.percentile(arr, 25)
                q3 = np.percentile(arr, 75)
                iqr = q3 - q1
                lower_bound = q1 - self.iqr_multiplier * iqr
                upper_bound = q3 + self.iqr_multiplier * iqr
                filtered = [v for v in arr if lower_bound <= v <= upper_bound]
            
            num_removed = len(arr) - len(filtered)
            return filtered, num_removed
        
        except Exception as e:
            logger.warning(f"Outlier detection failed: {e}. Using raw values.")
            return values, 0

    def _compute_adaptive_threshold(self, values: List[float]) -> float:
        """
        Compute dynamic threshold based on variance in values.
        
        Robust datasets (low variance) get stricter thresholds,
        Noisy datasets (high variance) get relaxed thresholds.
        
        Args:
            values: List of numeric values (already filtered for outliers)
        
        Returns:
            Adaptive threshold (typically 0.08 to 0.15)
        """
        try:
            arr = np.array([v for v in values if v is not None and isinstance(v, (int, float))])
            if len(arr) < 2:
                return 0.10  # Default threshold
            
            # Coefficient of variation (CV = std / mean)
            mean_val = np.mean(arr)
            if mean_val == 0:
                return 0.10
            
            cv = np.std(arr) / abs(mean_val)
            
            # Map CV to threshold
            if cv < 0.1:
                threshold = 0.08  # Very stable, use strict threshold
            elif cv < 0.3:
                threshold = 0.10  # Moderate variance, standard threshold
            else:
                threshold = 0.15  # High variance, relaxed threshold
            
            logger.debug(f"Adaptive threshold: {threshold:.2f} (CV: {cv:.2f})")
            return threshold
        
        except Exception as e:
            logger.warning(f"Adaptive threshold computation failed: {e}. Using default.")
            return 0.10

    def _calculate_confidence(
        self,
        change_pct: float,
        threshold: float,
        is_outlier_removed: bool = False,
        evidence_count: int = 1
    ) -> float:
        """
        Calculate confidence score for insight.
        
        Factors:
        - Magnitude of change relative to threshold
        - Whether outliers were removed (more robust = higher confidence)
        - Number of data points supporting evidence
        
        Args:
            change_pct: Percentage change value
            threshold: Adaptive threshold
            is_outlier_removed: Whether outliers were filtered
            evidence_count: Number of supporting data points
        
        Returns:
            Confidence score (0-1, bounded by min/max_confidence)
        """
        if change_pct is None:
            return self.min_confidence
        
        change_magnitude = abs(change_pct)
        
        # Base confidence: how far beyond threshold
        if change_magnitude < threshold:
            base_confidence = 0.4 + (change_magnitude / threshold) * 0.2  # 0.4-0.6
        elif change_magnitude < threshold * 2:
            base_confidence = 0.6 + ((change_magnitude - threshold) / threshold) * 0.15  # 0.6-0.75
        else:
            base_confidence = 0.75 + min(0.2, (change_magnitude - threshold * 2) / (threshold * 2)) * 0.2  # 0.75-0.95
        
        # Boost for robust signal (outliers removed)
        if is_outlier_removed:
            base_confidence = min(self.max_confidence, base_confidence + 0.05)
        
        # Boost for multiple data points
        if evidence_count > 1:
            evidence_boost = min(0.1, (evidence_count - 1) * 0.02)
            base_confidence = min(self.max_confidence, base_confidence + evidence_boost)
        
        return max(self.min_confidence, min(self.max_confidence, base_confidence))

    def generate(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate insights from data summary with V2 enhancements.
        
        Args:
            summary: Data summary dict from DataAgent
        
        Returns:
            Dict with insights list (schema v2.0)
        """
        insights = []
        
        try:
            drops = summary.get('top_drops', {})
            
            # Extract and filter ROAS drops
            roas_drops = drops.get('roas_drop_campaigns', [])
            if roas_drops:
                roas_changes = [item['change'] for item in roas_drops if item.get('change') is not None]
                filtered_roas, roas_outliers = self._detect_outliers(roas_changes)
                roas_threshold = self._compute_adaptive_threshold(filtered_roas)
                
                logger.debug(
                    f"ROAS: {len(roas_changes)} drops, removed {roas_outliers} outliers, "
                    f"threshold={roas_threshold:.2f}"
                )
                
                for item in roas_drops:
                    camp = item['campaign']
                    change = item['change']
                    
                    if change is None or change >= -roas_threshold:
                        continue  # Not significant
                    
                    # Generalized hypothesis (avoid dataset-specific language)
                    confidence = self._calculate_confidence(
                        change,
                        roas_threshold,
                        is_outlier_removed=(roas_outliers > 0)
                    )
                    
                    insights.append({
                        "hypothesis": (
                            f"Campaign '{camp}' shows decreased return on ad spend. "
                            "This may reflect changes in audience targeting, bid strategies, "
                            "or competitive dynamics."
                        ),
                        "evidence": {
                            "campaign": camp,
                            "roas_change": change,
                            "change_percentile": f"{abs(change)*100:.1f}%"
                        },
                        "expected_impact": "Moderate to High",
                        "confidence": round(confidence, 2),
                        "confidence_level": "high" if confidence > 0.7 else "moderate" if confidence > 0.5 else "low",
                        "analysis_type": "roas_performance",
                        "schema_version": "2.0"
                    })
            
            # Extract and filter CTR drops
            ctr_drops = drops.get('ctr_drop_campaigns', [])
            if ctr_drops:
                ctr_changes = [item['change'] for item in ctr_drops if item.get('change') is not None]
                filtered_ctr, ctr_outliers = self._detect_outliers(ctr_changes)
                ctr_threshold = self._compute_adaptive_threshold(filtered_ctr)
                
                logger.debug(
                    f"CTR: {len(ctr_changes)} drops, removed {ctr_outliers} outliers, "
                    f"threshold={ctr_threshold:.2f}"
                )
                
                for item in ctr_drops:
                    camp = item['campaign']
                    change = item['change']
                    
                    if change is None or change >= -ctr_threshold:
                        continue  # Not significant
                    
                    confidence = self._calculate_confidence(
                        change,
                        ctr_threshold,
                        is_outlier_removed=(ctr_outliers > 0)
                    )
                    
                    insights.append({
                        "hypothesis": (
                            f"Campaign '{camp}' shows declining click-through rate. "
                            "This suggests potential fatigue in ad creative, messaging misalignment, "
                            "or audience saturation."
                        ),
                        "evidence": {
                            "campaign": camp,
                            "ctr_change": change,
                            "change_percentile": f"{abs(change)*100:.1f}%"
                        },
                        "expected_impact": "High on engagement",
                        "confidence": round(confidence, 2),
                        "confidence_level": "high" if confidence > 0.7 else "moderate" if confidence > 0.5 else "low",
                        "analysis_type": "ctr_performance",
                        "schema_version": "2.0"
                    })
            
            # Fallback if no drops detected
            if not insights:
                insights.append({
                    "hypothesis": (
                        "No significant performance drops detected across campaigns. "
                        "Consider analyzing audience targeting refinement, seasonal trends, "
                        "or bid optimization opportunities."
                    ),
                    "evidence": {
                        "campaigns_analyzed": len(summary.get('campaigns', [])),
                        "note": "Stable performance period"
                    },
                    "expected_impact": "Uncertain",
                    "confidence": 0.5,
                    "confidence_level": "low",
                    "analysis_type": "baseline",
                    "schema_version": "2.0"
                })
        
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            insights.append({
                "hypothesis": "Unable to generate insights due to processing error.",
                "evidence": {"error": str(e)},
                "expected_impact": "Unknown",
                "confidence": 0.0,
                "confidence_level": "low",
                "analysis_type": "error",
                "schema_version": "2.0"
            })
        
        return {"insights": insights, "schema_version": "2.0"}


if __name__ == '__main__':
    # Sample usage
    sample_summary = {
        "campaigns": ["C1", "C2", "C3"],
        "top_drops": {
            "roas_drop_campaigns": [
                {"campaign": "C1", "change": -0.25},
                {"campaign": "C2", "change": -0.12}
            ],
            "ctr_drop_campaigns": [
                {"campaign": "C3", "change": -0.20}
            ]
        }
    }
    
    ia = InsightAgent()
    result = ia.generate(sample_summary)
    print(json.dumps(result, indent=2))
