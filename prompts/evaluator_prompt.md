# Evaluator Agent Logic

The Evaluator Agent validates insight hypotheses using numeric conditions and thresholds.

## Validation Process
1. Receives hypotheses from Insight Agent
2. Applies rule-based checks based on hypothesis content
3. Adjusts confidence scores based on evidence strength
4. Provides validation notes explaining the assessment

## Rule-Based Checks
- Low CTR hypotheses: Check if average CTR < threshold
- ROAS hypotheses: Check if average ROAS < threshold
- Audience fatigue: Compare CTR trends across time periods
- Evidence strength: Boost confidence for large drops (>20%, >10%)

## Confidence Adjustment
- Base confidence from hypothesis
- +0.2 for strong evidence (large drops)
- +0.1 for moderate evidence
- -0.1/-0.2 for weak or contradictory evidence
- Clamped to [0.0, 1.0] range

## Output Structure
Returns validated array with hypothesis, confidence score, and evidence notes.
