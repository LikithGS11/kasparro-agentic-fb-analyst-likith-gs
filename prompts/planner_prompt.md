# Planner Agent Logic

The Planner Agent decomposes user queries into fixed deterministic steps using keyword matching.

## Decomposition Rules
- Default steps: load_and_summarize_data, analyze_roas_trend, identify_top_underperformers, generate_hypotheses, validate_hypotheses, generate_creative_recommendations, save_outputs
- If query contains "roas": Insert "focus_on_roas_time_series" after data loading
- No dynamic generation - uses predefined step sequences

## Step Categories
- Data processing: Loading, cleaning, summarization
- Analysis: Trend detection, performance comparison
- Insight generation: Hypothesis creation
- Validation: Evidence-based confidence scoring
- Creative: Template-based recommendation generation
- Output: Report compilation and saving

## Deterministic Behavior
- Same query keywords always produce same step sequence
- No randomness or dynamic planning
- Fixed workflow optimized for Facebook ads analysis

## Output Structure
Returns steps array with predefined actionable task names.
