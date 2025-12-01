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

DATA_PATH = "data/synthetic_fb_ads_undergarments.csv"
OUTPUT_INSIGHTS = "reports/insights.json"
OUTPUT_CREATIVES = "reports/creatives.json"
OUTPUT_REPORT = "reports/report.md"
LOG_PATH = "logs/"

def log_event(name, content):
    os.makedirs(LOG_PATH, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = os.path.join(LOG_PATH, f"{ts}_{name}.json")
    with open(filepath, "w") as f:
        json.dump(content, f, indent=2)

def make_report(summary, insights, validated, creatives):
    lines = []
    lines.append("# Facebook Ads Performance Report\n")
    lines.append(f"**Date Range:** {summary['date_range']}\n")

    lines.append("## Overall Metrics")
    for k, v in summary["overall_metrics"].items():
        lines.append(f"- **{k}**: {v}")

    lines.append("\n## Key Insights")
    for s in insights["insights"]:
        lines.append(f"- **Hypothesis:** {s['hypothesis']}")
        lines.append(f"  - Evidence: {s['evidence']}")
        lines.append(f"  - Expected Impact: {s['expected_impact']}\n")

    lines.append("\n## Validated Insights")
    for v in validated["validated"]:
        lines.append(f"- {v['hypothesis']}")
        lines.append(f"  - Confidence: {v['confidence']}")
        lines.append(f"  - Notes: {v['validation_notes']}\n")

    lines.append("\n## Creative Recommendations")
    for c in creatives["creatives"]:
        lines.append(f"- **Campaign:** {c['campaign']}")
        lines.append(f"  - Headlines: {c['recommended_headlines']}")
        lines.append(f"  - Messages: {c['recommended_messages']}")
        lines.append(f"  - CTA: {c['cta']}\n")

    return "\n".join(lines)

def main(user_query):
    print("\n🚀 Running Agentic FB Performance Analysis...\n")

    # Load short-term memory for iterative learning
    memory = load_memory()

    planner = PlannerAgent()
    plan = planner.plan(user_query)
    log_event("planner_output", plan)

    data_agent = DataAgent(DATA_PATH)
    df = data_agent.load()
    summary = data_agent.summarize()
    log_event("data_summary", summary)

    insight_agent = InsightAgent()
    insights = insight_agent.generate(summary)
    log_event("insights_raw", insights)

    evaluator = EvaluatorAgent()
    validated = evaluator.validate(insights, summary)
    log_event("validated_insights", validated)

    creative_agent = CreativeAgent()
    creatives = creative_agent.generate(df=df, summary=summary)
    log_event("creative_output", creatives)

    save_json(insights, OUTPUT_INSIGHTS)
    save_json(creatives, OUTPUT_CREATIVES)

    report_text = make_report(summary, insights, validated, creatives)
    with open(OUTPUT_REPORT, "w") as f:
        f.write(report_text)

    # Update short-term memory with new insights
    update_memory(validated["validated"], memory)

    print("✅ Analysis Complete!")
    print("📁 insights.json, creatives.json, and report.md generated inside /reports/")
    print("📁 Logs stored inside /logs/\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agentic FB Performance Analyzer")
    parser.add_argument("query", type=str, help="User query e.g. 'Analyze ROAS drop'")
    args = parser.parse_args()

    main(args.query)
