"""
V2 Agentic FB Performance Analyzer Pipeline.

Orchestrates the analysis pipeline with:
- Production-grade error handling & retry logic
- Structured logging per agent
- Dynamic planning based on data complexity
- Schema v2.0 governance
- Drift detection and baseline comparison
"""

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.append('.')

from src.agents.planner import PlannerAgent
from src.agents.data_agent import DataAgent
from src.agents.insight_agent import InsightAgent
from src.agents.evaluator_agent import EvaluatorAgent
from src.agents.creative_agent import CreativeAgent
from src.utils.memory import load_memory, save_memory, update_memory
from src.utils.helpers import save_json
from src.utils.safety import (
    safe_call, DataError, InsightError, PlannerError, CreativeError, EvaluatorError,
    FALLBACK_SUMMARY, FALLBACK_INSIGHTS, FALLBACK_CREATIVES, FALLBACK_VALIDATED
)
from src.utils.logger_config import configure_logging, get_pipeline_logger, AgentExecutionTracer
from src.utils.schema_validator import SchemaValidator, upgrade_insights_to_v2, upgrade_creatives_to_v2
from src.utils.drift_detector import DriftDetector

# Configuration
DATA_PATH = "data/synthetic_fb_ads_undergarments.csv"
OUTPUT_INSIGHTS = "reports/insights.json"
OUTPUT_CREATIVES = "reports/creatives.json"
OUTPUT_REPORT = "reports/report.md"
LOG_PATH = "logs/"


# ============================================================================
# SAFE AGENT CALLS WITH ERROR HANDLING
# ============================================================================

@safe_call(error_type=PlannerError, max_retries=1, fallback={"steps": ["load_and_summarize_data"]})
def safe_plan(planner, user_query, summary=None):
    """Safely execute planning with complexity analysis."""
    return planner.plan(user_query, summary=summary)


@safe_call(error_type=DataError, max_retries=2, fallback=FALLBACK_SUMMARY)
def safe_load_and_summarize(data_agent):
    """Safely load and summarize data with retries."""
    df = data_agent.load()
    summary = data_agent.summarize()
    return summary


@safe_call(error_type=InsightError, max_retries=1, fallback=FALLBACK_INSIGHTS)
def safe_generate_insights(insight_agent, summary):
    """Safely generate insights with fallback."""
    return insight_agent.generate(summary)


@safe_call(error_type=EvaluatorError, max_retries=1, fallback=FALLBACK_VALIDATED)
def safe_validate_insights(evaluator, insights, summary):
    """Safely validate insights with fallback."""
    return evaluator.validate(insights, summary)


@safe_call(error_type=CreativeError, max_retries=1, fallback=FALLBACK_CREATIVES)
def safe_generate_creatives(creative_agent, df, summary):
    """Safely generate creatives with fallback."""
    return creative_agent.generate(df=df, summary=summary)


# ============================================================================
# REPORT GENERATION
# ============================================================================

def make_report(summary, insights, validated, creatives):
    """
    Generate markdown report from analysis results.
    Enhanced to handle V2 schema with confidence levels.
    """
    lines = []
    lines.append("# Facebook Ads Performance Report\n")
    lines.append(f"**Date Range:** {summary.get('date_range', 'N/A')}\n")
    
    # Overall metrics
    lines.append("## Overall Metrics")
    for k, v in summary.get("overall_metrics", {}).items():
        lines.append(f"- **{k}**: {v}")
    
    # Key insights with confidence
    lines.append("\n## Key Insights")
    for s in insights.get("insights", []):
        confidence = s.get('confidence', s.get('confidence_estimate', 'N/A'))
        confidence_level = s.get('confidence_level', 'unknown')
        lines.append(f"- **Hypothesis:** {s.get('hypothesis', 'N/A')}")
        lines.append(f"  - Confidence: {confidence} [{confidence_level}]")
        lines.append(f"  - Evidence: {s.get('evidence', {})}")
        lines.append(f"  - Expected Impact: {s.get('expected_impact', 'N/A')}\n")
    
    # Validated insights
    lines.append("\n## Validated Insights")
    for v in validated.get("validated", []):
        lines.append(f"- {v.get('hypothesis', 'N/A')}")
        lines.append(f"  - Confidence: {v.get('confidence', 'N/A')}")
        lines.append(f"  - Notes: {v.get('validation_notes', 'N/A')}\n")
    
    # Creative recommendations
    lines.append("\n## Creative Recommendations")
    for c in creatives.get("creatives", []):
        campaign = c.get('campaign', 'Unknown')
        lines.append(f"- **Campaign:** {campaign}")
        lines.append(f"  - Issue: {c.get('issue', 'N/A')}")
        lines.append(f"  - Headlines: {c.get('recommended_headlines', [])}")
        lines.append(f"  - Messages: {c.get('recommended_messages', [])}")
        lines.append(f"  - CTA: {c.get('cta', 'N/A')}\n")
    
    return "\n".join(lines)


# ============================================================================
# SCHEMA VALIDATION & PERSISTENCE
# ============================================================================

def validate_and_persist_outputs(insights, creatives, validator):
    """
    Validate outputs against V2 schema and upgrade if needed.
    
    Args:
        insights: Raw insights dict
        creatives: Raw creatives dict
        validator: SchemaValidator instance
    
    Returns:
        Tuple of (validated_insights, validated_creatives)
    """
    logger = get_pipeline_logger()
    
    # Upgrade insights if needed
    if insights.get("schema_version") != "2.0":
        logger.info("Upgrading insights to schema v2.0...")
        insights = upgrade_insights_to_v2(insights)
    
    # Upgrade creatives if needed
    if creatives.get("schema_version") != "2.0":
        logger.info("Upgrading creatives to schema v2.0...")
        creatives = upgrade_creatives_to_v2(creatives)
    
    # Validate
    insights_valid, insights_errors = validator.validate_insights(insights)
    creatives_valid, creatives_errors = validator.validate_creatives(creatives)
    
    if not insights_valid:
        logger.warning(f"Insights validation errors: {insights_errors}")
    else:
        logger.info("✓ Insights passed schema v2.0 validation")
    
    if not creatives_valid:
        logger.warning(f"Creatives validation errors: {creatives_errors}")
    else:
        logger.info("✓ Creatives passed schema v2.0 validation")
    
    return insights, creatives


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main(user_query, enable_drift_detection=True):
    """
    Main pipeline orchestrator with V2 enhancements.
    
    Args:
        user_query: User's analysis request
        enable_drift_detection: Whether to detect metric drift from baseline
    """
    # Initialize
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = configure_logging(run_id, log_level="INFO")
    logger = get_pipeline_logger()
    
    logger.info("=" * 70)
    logger.info("🚀 AGENTIC FB PERFORMANCE ANALYZER V2 STARTING")
    logger.info("=" * 70)
    logger.info(f"Run ID: {run_id}")
    logger.info(f"User Query: {user_query}")
    
    # Load memory for context
    memory = load_memory()
    logger.info("✓ Memory loaded")
    
    # Initialize validators and detectors
    validator = SchemaValidator()
    drift_detector = DriftDetector() if enable_drift_detection else None
    
    # ===== STEP 1: PLANNING =====
    logger.info("\n[STEP 1/6] PLANNING")
    logger.info("-" * 70)
    
    planner = PlannerAgent(log_reasoning=True)
    plan = safe_plan(planner, user_query)
    logger.info(f"Generated plan with {len(plan.get('steps', []))} steps")
    
    if "complexity_analysis" in plan:
        logger.info(f"Dataset complexity: {plan['complexity_analysis']['complexity_score']:.2f}")
        logger.info(f"Adaptation: {plan.get('adaptation_reasoning', 'N/A')}")
    
    # ===== STEP 2: DATA LOADING & SUMMARY =====
    logger.info("\n[STEP 2/6] DATA LOADING & ANALYSIS")
    logger.info("-" * 70)
    
    data_agent = DataAgent(DATA_PATH)
    summary = safe_load_and_summarize(data_agent)
    logger.info(f"Loaded {len(summary.get('campaigns', []))} campaigns")
    logger.info(f"Date range: {summary.get('date_range', 'N/A')}")
    logger.info(f"ROAS drop campaigns: {len(summary.get('top_drops', {}).get('roas_drop_campaigns', []))}")
    logger.info(f"CTR drop campaigns: {len(summary.get('top_drops', {}).get('ctr_drop_campaigns', []))}")
    
    # Detect drift if baseline exists
    if drift_detector:
        logger.info("\n[DRIFT DETECTION]")
        current_stats = drift_detector.compute_stats(summary)
        drift_result = drift_detector.detect_drift(current_stats)
        
        if drift_result.get('has_drift'):
            logger.warning(f"⚠️  Drift detected (severity: {drift_result['severity'].upper()})")
            for detection in drift_result['detections']:
                logger.warning(f"  → {detection['type']}: {detection['drift_pct']}% drift")
        else:
            logger.info("✓ No significant drift from baseline")
    
    # ===== STEP 3: INSIGHT GENERATION =====
    logger.info("\n[STEP 3/6] INSIGHT GENERATION")
    logger.info("-" * 70)
    
    insight_agent = InsightAgent()
    insights = safe_generate_insights(insight_agent, summary)
    logger.info(f"Generated {len(insights.get('insights', []))} insights")
    
    for idx, insight in enumerate(insights.get('insights', [])):
        conf = insight.get('confidence', insight.get('confidence_estimate', 0))
        conf_level = insight.get('confidence_level', 'unknown')
        logger.debug(f"  [{idx+1}] {insight.get('hypothesis', 'N/A')[:60]}... [confidence: {conf}, {conf_level}]")
    
    # ===== STEP 4: INSIGHT VALIDATION =====
    logger.info("\n[STEP 4/6] INSIGHT VALIDATION")
    logger.info("-" * 70)
    
    evaluator = EvaluatorAgent()
    validated = safe_validate_insights(evaluator, insights, summary)
    logger.info(f"Validated {len(validated.get('validated', []))} insights")
    
    high_conf_count = sum(1 for v in validated.get('validated', []) if v.get('confidence', 0) > 0.7)
    logger.info(f"High-confidence insights: {high_conf_count}")
    
    # ===== STEP 5: CREATIVE GENERATION =====
    logger.info("\n[STEP 5/6] CREATIVE GENERATION")
    logger.info("-" * 70)
    
    creative_agent = CreativeAgent()
    df = data_agent.df if hasattr(data_agent, 'df') else None
    creatives = safe_generate_creatives(creative_agent, df, summary)
    logger.info(f"Generated {len(creatives.get('creatives', []))} creative sets")
    
    # ===== STEP 6: OUTPUT PERSISTENCE & VALIDATION =====
    logger.info("\n[STEP 6/6] OUTPUT PERSISTENCE & VALIDATION")
    logger.info("-" * 70)
    
    # Validate and upgrade schemas
    insights, creatives = validate_and_persist_outputs(insights, creatives, validator)
    
    # Save outputs
    save_json(insights, OUTPUT_INSIGHTS)
    logger.info(f"✓ Saved insights to {OUTPUT_INSIGHTS}")
    
    save_json(creatives, OUTPUT_CREATIVES)
    logger.info(f"✓ Saved creatives to {OUTPUT_CREATIVES}")
    
    # Generate and save report
    report_text = make_report(summary, insights, validated, creatives)
    with open(OUTPUT_REPORT, "w") as f:
        f.write(report_text)
    logger.info(f"✓ Saved report to {OUTPUT_REPORT}")
    
    # Save baseline for drift detection (on first run or periodic refresh)
    if drift_detector and not drift_detector.baseline:
        current_stats = drift_detector.compute_stats(summary)
        drift_detector.save_baseline(current_stats)
        logger.info("✓ Baseline statistics saved for future drift detection")
    
    # Update memory
    update_memory(validated.get("validated", []), memory)
    logger.info("✓ Memory updated with validated insights")
    
    # ===== COMPLETION =====
    logger.info("\n" + "=" * 70)
    logger.info("✅ PIPELINE COMPLETE - ALL STEPS SUCCESSFUL")
    logger.info("=" * 70)
    logger.info(f"Log file: {log_file}")
    logger.info(f"Run ID: {run_id}")
    logger.info("\n📁 Outputs:")
    logger.info(f"  • Reports: {OUTPUT_INSIGHTS}, {OUTPUT_CREATIVES}, {OUTPUT_REPORT}")
    logger.info(f"  • Logs: {log_file}")
    
    print("\n" + "=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    print(f"📁 outputs saved:")
    print(f"   • {OUTPUT_INSIGHTS}")
    print(f"   • {OUTPUT_CREATIVES}")
    print(f"   • {OUTPUT_REPORT}")
    print(f"📊 Logs: {log_file}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Agentic FB Performance Analyzer V2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.orchestrator.run "Analyze ROAS drop"
  python -m src.orchestrator.run "Focus on CTR performance"
        """
    )
    parser.add_argument("query", type=str, help="User query (e.g., 'Analyze ROAS drop')")
    parser.add_argument(
        "--no-drift",
        action="store_true",
        help="Disable drift detection (faster runs)"
    )
    
    args = parser.parse_args()
    
    try:
        main(args.query, enable_drift_detection=not args.no_drift)
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger = get_pipeline_logger()
        logger.critical(f"Pipeline failed with critical error: {e}", exc_info=True)
        print(f"\n✗ Pipeline failed: {e}")
        sys.exit(1)
