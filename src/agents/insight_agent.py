import json

class InsightAgent:
    """Generates hypotheses from data summary using simple heuristics."""

    def generate(self, summary):
        insights = []
        drops = summary.get('top_drops', {})
        # If ROAS drops exist -> hypothesis: audience or creative issues
        if drops.get('roas_drop_campaigns'):
            for item in drops['roas_drop_campaigns']:
                camp = item['campaign']
                insights.append({
                    "hypothesis": f"ROAS drop in campaign {camp} is due to lower conversion efficiency or increased CPC.",
                    "evidence": {"campaign": camp, "roas_change": item['change']},
                    "expected_impact": "Moderate to High",
                    "confidence_estimate": 0.6
                })
        # If CTR drops exist -> creative underperformance
        if drops.get('ctr_drop_campaigns'):
            for item in drops['ctr_drop_campaigns']:
                camp = item['campaign']
                insights.append({
                    "hypothesis": f"CTR drop in campaign {camp} indicates creative fatigue or poor messaging fit.",
                    "evidence": {"campaign": camp, "ctr_change": item['change']},
                    "expected_impact": "High on engagement",
                    "confidence_estimate": 0.7
                })
        # Fallback hypothesis if no clear drops
        if not insights:
            insights.append({
                "hypothesis": "No large campaign-level drops detected; investigate audience targeting and bid strategies.",
                "evidence": {},
                "expected_impact": "Uncertain",
                "confidence_estimate": 0.4
            })
        return {"insights": insights}

if __name__ == '__main__':
    # sample usage
    s = {"top_drops": {"roas_drop_campaigns": [{"campaign":"C1","change":-0.2}]}}
    ia = InsightAgent()
    print(json.dumps(ia.generate(s), indent=2))
