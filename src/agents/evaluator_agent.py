import json
import math

class EvaluatorAgent:
    """Validate insight hypotheses using numeric checks from summary."""

    def validate(self, insights, summary):
        validated = []
        for ins in insights.get('insights', []):
            conf = ins.get('confidence_estimate', 0.5)
            notes = []
            # simple rule: if evidence has >10% drop, boost confidence
            evidence = ins.get('evidence', {})
            val = conf
            if 'roas_change' in evidence:
                change = evidence['roas_change']
                if change is not None and change < -0.2:
                    val = min(1.0, val + 0.2)
                    notes.append('Large ROAS drop observed (< -20%)')
                elif change is not None and change < -0.1:
                    val = min(1.0, val + 0.1)
                    notes.append('Moderate ROAS drop observed (< -10%)')
            if 'ctr_change' in evidence:
                change = evidence['ctr_change']
                if change is not None and change < -0.2:
                    val = min(1.0, val + 0.2)
                    notes.append('Large CTR drop observed (< -20%)')
                elif change is not None and change < -0.1:
                    val = min(1.0, val + 0.1)
                    notes.append('Moderate CTR drop observed (< -10%)')
            validated.append({
                "hypothesis": ins.get('hypothesis'),
                "confidence": round(val, 2),
                "validation_notes": '; '.join(notes) if notes else 'No strong numerical evidence; manual check suggested'
            })
        return {"validated": validated}

if __name__ == '__main__':
    ev = EvaluatorAgent()
    s = {"insights":[{"hypothesis":"x","evidence":{"ctr_change":-0.15},"confidence_estimate":0.5}]}
    print(json.dumps(ev.validate(s, {}), indent=2))
