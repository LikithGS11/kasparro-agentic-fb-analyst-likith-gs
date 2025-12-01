import json

class PlannerAgent:
    """Planner Agent: decomposes a user query into actionable steps."""

    def plan(self, query: str):
        # Very simple decomposition based on keywords.
        steps = [
            "load_and_summarize_data",
            "analyze_roas_trend",
            "identify_top_underperformers",
            "generate_hypotheses",
            "validate_hypotheses",
            "generate_creative_recommendations",
            "save_outputs"
        ]
        # If query mentions 'roas', prioritize ROAS analysis
        if "roas" in query.lower():
            steps.insert(1, "focus_on_roas_time_series")
        return {"steps": steps}

if __name__ == '__main__':
    p = PlannerAgent()
    print(json.dumps(p.plan('Analyze ROAS drop'), indent=2))
