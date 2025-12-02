import random
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CreativeAgent:
    """Generates creative recommendations for campaigns with low CTR."""

    def generate(self, df=None, summary=None, top_n=3):
        # df: optional full dataframe, summary: required summary dict
        creatives = []
        ctr_drops = summary.get('top_drops', {}).get('ctr_drop_campaigns', [])
        for item in ctr_drops:
            camp = item['campaign']
            # produce templates using campaign name
            headlines = [
                f"{camp}: Limited Time Offer — Shop Now",
                f"Don't Miss Out on {camp} Deals",
                f"New Arrivals in {camp} — See What’s Hot"
            ]
            messages = [
                f"Exclusive discount on {camp}. Grab before it's gone! Limited stock.",
                f"Top-rated {camp} products — customer favorite. Fast shipping.",
                f"Upgrade your collection with {camp}. Special bundles available."
            ]
            cta_options = ["Shop Now", "Buy Today", "Explore Deals"]
            creatives.append({
                "campaign": camp,
                "issue": "Low CTR",
                "recommended_headlines": headlines[:top_n],
                "recommended_messages": messages[:top_n],
                "cta": random.choice(cta_options)
            })
        # fallback if none
        if not creatives:
            creatives.append({
                "campaign": None,
                "issue": "No low-CTR campaigns found",
                "recommended_headlines": [],
                "recommended_messages": [],
                "cta": None
            })
        return {"creatives": creatives}

if __name__ == '__main__':
    ca = CreativeAgent()
    sample_summary = {
        "top_drops": {
            "ctr_drop_campaigns": [
                {"campaign": "Summer Sale", "change": -0.25}
            ],
            "roas_drop_campaigns": [
                {"campaign": "Premium Tier", "change": -0.15}
            ]
        }
    }
    result = ca.generate(summary=sample_summary)
    print(json.dumps(result, indent=2))
