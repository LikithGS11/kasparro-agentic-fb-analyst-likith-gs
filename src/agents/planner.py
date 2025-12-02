import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Planner Agent: Decomposes a user query into actionable steps.
    
    V2 Features:
    - Computes dataset complexity (missing values, variance, ad count)
    - Chooses deeper or shallower plans based on complexity
    - Adapts steps when signals are missing
    - Logs decision reasoning
    - Maintains backward compatibility with V1 logic
    """

    # Base pipeline steps (V1 core logic)
    BASE_STEPS = [
        "load_and_summarize_data",
        "analyze_roas_trend",
        "identify_top_underperformers",
        "generate_hypotheses",
        "validate_hypotheses",
        "generate_creative_recommendations",
        "save_outputs"
    ]

    # Extended steps for high-complexity datasets
    EXTENDED_STEPS = [
        "compute_data_complexity",
        "detect_anomalies",
        "analyze_audience_overlap",
        "perform_cohort_analysis",
        "generate_advanced_hypotheses"
    ]

    def __init__(self, complexity_threshold: float = 0.5, log_reasoning: bool = True):
        """
        Initialize PlannerAgent.
        
        Args:
            complexity_threshold: Score above which to use extended steps (0-1)
            log_reasoning: Whether to log complexity analysis reasoning
        """
        self.complexity_threshold = complexity_threshold
        self.log_reasoning = log_reasoning

    def compute_complexity(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute dataset complexity score based on:
        - Number of missing values across metrics
        - Variance in ROAS and CTR across campaigns
        - Number of unique campaigns
        
        Args:
            summary: Data summary dict from DataAgent
        
        Returns:
            Dict with complexity_score (0-1), metrics, reasoning
        """
        complexity_score = 0.0
        reasoning = []
        
        try:
            # Factor 1: Campaign count (normalized to 0-0.3)
            campaigns = summary.get('campaigns', [])
            campaign_count = len(campaigns)
            campaign_score = min(0.3, campaign_count / 20.0)  # 20 campaigns = max score
            reasoning.append(f"Campaign count: {campaign_count} (score: {campaign_score:.2f})")
            
            # Factor 2: Missing data in overall metrics (0-0.4)
            overall_metrics = summary.get('overall_metrics', {})
            missing_metrics = sum(1 for v in overall_metrics.values() if v is None)
            missing_score = min(0.4, missing_metrics / 4.0)  # 4 metrics possible
            reasoning.append(f"Missing metrics: {missing_metrics}/4 (score: {missing_score:.2f})")
            
            # Factor 3: Performance drops detected (0-0.3)
            top_drops = summary.get('top_drops', {})
            drop_count = (
                len(top_drops.get('roas_drop_campaigns', [])) +
                len(top_drops.get('ctr_drop_campaigns', []))
            )
            drop_score = min(0.3, drop_count / 10.0)  # 10 drops = max score
            reasoning.append(f"Performance drops: {drop_count} (score: {drop_score:.2f})")
            
            # Total complexity
            complexity_score = campaign_score + missing_score + drop_score
            complexity_score = min(1.0, complexity_score)  # Cap at 1.0
            
        except Exception as e:
            logger.warning(f"Error computing complexity: {e}. Using default score.")
            complexity_score = 0.5

        return {
            "complexity_score": complexity_score,
            "campaign_count": campaign_count if 'campaigns' in locals() else 0,
            "missing_metrics": missing_metrics if 'missing_metrics' in locals() else 0,
            "performance_drops": drop_count if 'drop_count' in locals() else 0,
            "reasoning": reasoning
        }

    def plan(self, query: str, summary: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate execution plan based on query and optional dataset summary.
        
        V2 Enhancement: If summary provided, compute complexity and adapt steps.
        V1 Compatibility: Without summary, uses keyword-based logic.
        
        Args:
            query: User query string
            summary: Optional data summary for complexity-based planning
        
        Returns:
            Plan dict with steps, complexity_analysis, and reasoning
        """
        steps = self.BASE_STEPS.copy()
        complexity_analysis = None
        adaptation_reasoning = ""

        # V2: Complexity-based adaptation (if summary provided)
        if summary is not None:
            complexity_analysis = self.compute_complexity(summary)
            complexity_score = complexity_analysis["complexity_score"]
            
            if self.log_reasoning:
                logger.info(f"Dataset Complexity Analysis: {complexity_score:.2f}")
                for reason in complexity_analysis["reasoning"]:
                    logger.info(f"  → {reason}")
            
            # Adapt based on complexity
            if complexity_score > self.complexity_threshold:
                # High complexity: add extended analytical steps
                steps_to_insert = self.EXTENDED_STEPS[:2]  # anomaly detection + audience overlap
                steps.insert(3, "detect_anomalies")
                steps.insert(4, "analyze_audience_overlap")
                adaptation_reasoning = (
                    f"High complexity dataset ({complexity_score:.2f}). "
                    "Added anomaly detection and audience overlap analysis."
                )
            elif complexity_score < 0.2:
                # Low complexity: streamline to core steps
                adaptation_reasoning = (
                    f"Low complexity dataset ({complexity_score:.2f}). "
                    "Using streamlined analysis pipeline."
                )
            else:
                adaptation_reasoning = (
                    f"Moderate complexity ({complexity_score:.2f}). "
                    "Using standard analysis pipeline."
                )
            
            if self.log_reasoning:
                logger.info(f"Adaptation: {adaptation_reasoning}")

        # V1: Keyword-based priority (always applied)
        if "roas" in query.lower():
            if "focus_on_roas_time_series" not in steps:
                steps.insert(1, "focus_on_roas_time_series")
        
        if "ctr" in query.lower():
            if "analyze_ctr_patterns" not in steps:
                steps.insert(1, "analyze_ctr_patterns")
        
        if "creative" in query.lower():
            if "prioritize_creative_analysis" not in steps:
                steps.insert(4, "prioritize_creative_analysis")

        plan_dict = {
            "steps": steps,
            "query": query,
        }
        
        # V2: Include complexity analysis if available
        if complexity_analysis is not None:
            plan_dict["complexity_analysis"] = complexity_analysis
            plan_dict["adaptation_reasoning"] = adaptation_reasoning
        
        return plan_dict


if __name__ == '__main__':
    # Example usage without summary (V1 compatible)
    planner = PlannerAgent()
    print("\n=== V1 Mode (no summary) ===")
    print(json.dumps(planner.plan('Analyze ROAS drop'), indent=2))
    
    # Example with summary (V2 adaptive)
    sample_summary = {
        "campaigns": ["C1", "C2", "C3", "C4", "C5"],
        "overall_metrics": {
            "avg_ctr": 0.025,
            "avg_roas": 2.1,
            "total_spend": 5000,
            "total_revenue": 10500
        },
        "top_drops": {
            "roas_drop_campaigns": [
                {"campaign": "C1", "change": -0.2},
                {"campaign": "C2", "change": -0.15}
            ],
            "ctr_drop_campaigns": [
                {"campaign": "C3", "change": -0.18}
            ]
        }
    }
    print("\n=== V2 Mode (with summary) ===")
    print(json.dumps(planner.plan('Analyze performance', summary=sample_summary), indent=2))
