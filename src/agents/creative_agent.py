import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CreativeAgent:
    """Generates diagnosis-aware creative recommendations."""

    def __init__(self):
        self.templates: Dict[str, Dict[str, Any]] = {
            "creative_fatigue": {
                "rationale": "CTR is falling while reach holds; rotate hooks and refresh visuals to reset fatigue.",
                "headlines": [
                    "Fresh angle for {camp}: new hook to stop the scroll",
                    "{camp} refresh: new creative, same offer",
                    "Reboot {camp}: highlight a different benefit"
                ],
                "messages": [
                    "Test a contrasting visual and a curiosity-first opener; keep offer intact but rewrite the first line.",
                    "Swap the hero image to feature social proof and tighten the value prop in 12 words.",
                    "Lead with a question, add a specific outcome, close with urgency; keep CTA consistent."
                ],
                "ctas": ["See the update", "Try the new look", "Check the refresh"]
            },
            "audience_saturation": {
                "rationale": "CTR and impressions down; broaden or rotate audience entry points to reduce overlap.",
                "headlines": [
                    "New angle for {camp}: reach the next cohort",
                    "Expand {camp}: speak to a fresh segment",
                    "{camp}: alternate hook to escape overlap"
                ],
                "messages": [
                    "Split tests with age/interest variants; mirror language to the new cohort and rotate the offer framing.",
                    "Use audience-specific proof and a tailored pain point; reduce reliance on current lookalikes.",
                    "Launch a net-new hook focused on a different job-to-be-done; cap frequency with tighter exclusions."
                ],
                "ctas": ["Explore options", "Find your fit", "See tailored picks"]
            },
            "placement_underperformance": {
                "rationale": "Performance varies by placement; tailor aspect ratios and hooks to winning surfaces.",
                "headlines": [
                    "{camp}: placement-tuned creative for feed",
                    "Story-first cut for {camp}",
                    "Reframe {camp} for reels and short-form"
                ],
                "messages": [
                    "Produce a 1:1 feed-first cut with on-frame captions; lead with value in first 1.5s.",
                    "Ship a 9:16 story cut with native stickers; front-load offer and social proof.",
                    "Create a fast-paced 9:16 variant; hook in first beat, add price anchor, end with CTA sticker."
                ],
                "ctas": ["View in feed", "Watch now", "Swipe to see"]
            },
            "competition_likelihood": {
                "rationale": "ROAS down with steady spend; differentiate offer and tighten value communication.",
                "headlines": [
                    "{camp}: why choose us now",
                    "Beat alternatives: {camp} value proof",
                    "Switch to {camp}: clearer value, clearer offer"
                ],
                "messages": [
                    "Call out 2 clear differentiators and add a price/value comparison; keep CTA single and direct.",
                    "Use competitor contrast bullet, add guarantee and delivery speed; keep copy under 40 words.",
                    "Lead with strongest proof point, then urgency; remove secondary CTAs to focus on one action."
                ],
                "ctas": ["Choose this offer", "Lock in value", "See why we win"]
            },
            "performance_degradation": {
                "rationale": "General performance drop; refocus on core offer, proof, and frictionless CTA.",
                "headlines": [
                    "{camp}: tighten offer and proof",
                    "Recover {camp}: clarity + proof",
                    "{camp} reset: single promise, single CTA"
                ],
                "messages": [
                    "Clarify the primary benefit in the first line, add a single proof point, and trim any secondary asks.",
                    "Highlight the strongest testimonial, restate the offer with a concrete number, and reduce copy to essentials.",
                    "Use one-liner benefit, one proof, one CTA; remove optional steps and emphasize speed to value."
                ],
                "ctas": ["Get the offer", "See proof", "Start now"]
            }
        }

    def generate(
        self,
        df: Optional[Any] = None,
        summary: Optional[Dict[str, Any]] = None,
        insights: Optional[Dict[str, Any]] = None,
        top_n: int = 3
    ) -> Dict[str, Any]:
        """Generate creatives using diagnoses from insights or summary."""
        summary = summary or {}
        diagnoses = self._extract_campaign_diagnoses(insights, summary)

        creative_sets = []
        for entry in diagnoses:
            campaign = entry["campaign"]
            diagnosis = entry["diagnosis"]
            rationale = entry["rationale"]
            template_key = diagnosis if diagnosis in self.templates else "performance_degradation"
            generated = self._generate_diagnosis_specific_creatives(campaign, template_key, top_n)

            creative_sets.append({
                "campaign": campaign,
                "diagnosis": diagnosis,
                "rationale": rationale,
                "creatives": generated["creatives"],
                "issue": diagnosis.replace("_", " "),
                "recommended_headlines": generated["recommended_headlines"],
                "recommended_messages": generated["recommended_messages"],
                "cta": generated["cta"],
                "schema_version": "2.0"
            })

        if not creative_sets:
            creative_sets.append({
                "campaign": None,
                "diagnosis": "no_significant_drop",
                "rationale": "No campaigns with actionable diagnosis were found.",
                "creatives": [],
                "issue": "No action",
                "recommended_headlines": [],
                "recommended_messages": [],
                "cta": None,
                "schema_version": "2.0"
            })

        return {"creatives": creative_sets, "schema_version": "2.0"}

    def _extract_campaign_diagnoses(
        self,
        insights: Optional[Dict[str, Any]],
        summary: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Pull diagnoses from insights; fallback to summary drops if missing."""
        diagnoses: List[Dict[str, Any]] = []

        for ins in (insights or {}).get("insights", []):
            evidence = ins.get("evidence", {}) or {}
            diagnosis = evidence.get("diagnosis")
            campaign = evidence.get("campaign") or evidence.get("campaign_name") or ins.get("hypothesis", "").split(":")[0]
            if not diagnosis or not campaign:
                continue
            diagnoses.append({
                "campaign": campaign,
                "diagnosis": diagnosis,
                "rationale": evidence.get("rationale") or ins.get("validation_notes") or "Diagnosis supplied by InsightAgent."
            })

        if diagnoses:
            return diagnoses

        top_drops = summary.get("top_drops", {})
        ctr_drops = top_drops.get("ctr_drop_campaigns", [])
        roas_drops = top_drops.get("roas_drop_campaigns", [])

        for item in ctr_drops:
            diagnosis = "creative_fatigue" if item.get("impressions_change", 0) >= 0 else "audience_saturation"
            diagnoses.append({
                "campaign": item.get("campaign"),
                "diagnosis": diagnosis,
                "rationale": "CTR decline detected; inferred diagnosis from CTR and impressions trend."
            })

        for item in roas_drops:
            diagnoses.append({
                "campaign": item.get("campaign"),
                "diagnosis": "performance_degradation",
                "rationale": "ROAS decline detected; defaulting to performance_degradation guidance."
            })

        return diagnoses

    def _generate_diagnosis_specific_creatives(
        self,
        campaign: str,
        diagnosis: str,
        top_n: int
    ) -> Dict[str, Any]:
        """Create diagnosis-specific creative variants."""
        template = self.templates.get(diagnosis, self.templates["performance_degradation"])
        headlines = [h.format(camp=campaign) for h in template["headlines"]][:top_n]
        messages = template["messages"][:top_n]
        ctas = template["ctas"][:top_n] if template["ctas"] else [None]

        creatives: List[Dict[str, str]] = []
        for idx in range(min(len(headlines), len(messages))):
            creatives.append({
                "headline": headlines[idx],
                "message": messages[idx],
                "cta": ctas[idx % len(ctas)]
            })

        return {
            "creatives": creatives,
            "recommended_headlines": headlines,
            "recommended_messages": messages,
            "cta": ctas[0] if ctas else None
        }


if __name__ == "__main__":
    agent = CreativeAgent()
    sample_insights = {
        "insights": [
            {
                "hypothesis": "C1: CTR decline due to fatigue",
                "evidence": {"campaign": "C1", "diagnosis": "creative_fatigue", "rationale": "CTR down, impressions steady."}
            }
        ]
    }
    sample_summary = {
        "top_drops": {
            "ctr_drop_campaigns": [
                {"campaign": "C2", "relative_delta": -0.2, "impressions_change": -0.1}
            ]
        }
    }
    print(json.dumps(agent.generate(summary=sample_summary, insights=sample_insights), indent=2))
