# Agent Graph and Data Flow

## Diagram

```
User Query
    |
    v
Planner Agent -> Decomposes query into subtasks
    |
    v
Data Agent -> Loads and summarizes dataset
    |
    v
Insight Agent -> Generates hypotheses explaining patterns
    |
    v
Evaluator Agent -> Validates hypotheses quantitatively
    |
    v
Creative Agent -> Produces new creative recommendations
    |
    v
Orchestrator -> Compiles final report
```

## Explanation

- **Planner Agent**: Breaks down the user query into actionable steps for other agents.
- **Data Agent**: Handles data loading, cleaning, and aggregation to provide summaries.
- **Insight Agent**: Analyzes summaries to generate hypotheses about performance changes.
- **Evaluator Agent**: Quantitatively validates hypotheses using metrics and thresholds.
- **Creative Agent**: Generates new ad copy ideas for underperforming campaigns based on data patterns.
- **Orchestrator**: Coordinates the pipeline, logs events, and produces outputs (insights.json, creatives.json, report.md).
