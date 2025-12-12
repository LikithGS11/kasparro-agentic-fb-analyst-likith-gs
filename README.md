
# Kasparro Agentic Facebook Performance Analyst (V2)

Production-grade, deterministic pipeline that diagnoses Facebook ad performance drops, validates hypotheses, and ships diagnosis-aware creatives.

## Quickstart (3 commands)
1) `python -m venv venv && .\venv\Scripts\activate`
2) `pip install -r requirements.txt`
3) `python -m src.orchestrator.run "Analyze ROAS drop"`

## Architecture (5-7 bullets)
- PlannerAgent: expands user query into ordered steps with complexity-aware depth.
- DataAgent: loads CSV, validates schema, computes baseline/current deltas, flags drops.
- InsightAgent: generates hypotheses with diagnoses, adaptive thresholds, and decision logs.
- EvaluatorAgent: percentile-based validation, severity scoring, confidence normalization.
- CreativeAgent: diagnosis-specific creatives aligned to detected drivers.
- Orchestrator: safe-call retries, schema validation, report generation, structured logs.

## How to modify agents
- Planner: tune step expansion in `src/agents/planner.py` (complexity thresholds, templates).
- Data: adjust required columns or delta thresholds in `src/agents/data_agent.py`.
- Insight: extend diagnosis rules in `_diagnose_root_cause` within `src/agents/insight_agent.py`.
- Evaluator: tweak percentile and severity logic in `src/agents/evaluator_agent.py`.
- Creative: update diagnosis templates in `src/agents/creative_agent.py`.

## Troubleshooting
- Tests: `python -m pytest -q` (ensure venv active).
- Missing columns: check input CSV matches required schema in `data_agent.py`.
- Schema errors: run `SchemaValidator.validate_insights/validate_creatives` in `src/utils/schema_validator.py`.
- Empty output: confirm `data/` has rows and date ranges; rerun with `--no-drift` to skip drift detector.
- Logs: inspect `logs/*_decision_logs.json` and agent tracers in `logs/` for step-by-step reasoning.
```

Windows batch helper:

```bat
run.bat run "Analyze ROAS drop"
```

## 📊 Data Format

CSV columns:

```
campaign_name, adset_name, date, spend, impressions, clicks, ctr,
purchases, revenue, roas, creative_type, creative_message,
audience_type, platform, country
```

## ⚙️ Configuration

```
low_ctr_threshold: 0.01
low_roas_threshold: 1.5
min_impressions: 1000
random_seed: 42
```

## 📤 Outputs

- **report.md** - Markdown analysis report
- **insights.json** - V2.0 schema compliant insights with confidence levels
- **creatives.json** - V2.0 schema compliant creative recommendations
- **baseline_stats.json** - Baseline metrics for drift detection (V2 NEW)
- **logs/run_*.log** - Structured per-agent execution traces (V2 NEW)
- **logs/run_*_trace.json** - Execution timing and I/O per agent (V2 NEW)

## 📁 Project Structure

```
src/
  agents/
    planner.py (V2: Complexity-based planning)
    data_agent.py
    insight_agent.py (V2: Adaptive thresholds)
    evaluator_agent.py
    creative_agent.py
  orchestrator/
    run.py (V2: Safe calls + structured logging)
  utils/
    helpers.py (V2: Fixed percent_change)
    safety.py (V2 NEW: Error handling wrapper)
    logger_config.py (V2 NEW: Structured logging)
    schema_validator.py (V2 NEW: Schema governance)
    drift_detector.py (V2 NEW: Baseline comparison)
    memory.py
prompts/
data/
config/
reports/
logs/ (V2 NEW: Structured logs)
tests/
  test_percent_change.py (V2 NEW)
  test_schema_and_planner.py (V2 NEW)
```

## 🔍 Validation Logic

V2 Confidence Scoring (Robust):

- Outliers removed using IQR (configurable)
- Dynamic thresholds based on data variance
- Base confidence: How far beyond threshold
- +5% boost: If outliers detected (robust signal)
- +2% per data point: Multiple supporting evidence
- Range: [min_confidence, max_confidence]

V1 Legacy (Still Supported):
- +0.2 if metric drop > 20%
- +0.1 if drop 10–20%
- –0.1 if evidence weak
- Confidence ∈ [0.0, 1.0]

## 🧪 Testing

```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_percent_change.py -v
python -m pytest tests/test_schema_and_planner.py -v
```

**Test Coverage**:
- `test_percent_change.py`: 20+ edge cases (division-by-zero, None, real-world scenarios)
- `test_schema_and_planner.py`: 15+ schema validation cases + 7+ planner complexity cases

## 🐛 Troubleshooting

- Activate venv → `pip install -r requirements.txt`
- Ensure CSV is inside `data/`
- If batch fails → use Python command directly
- **V2 NEW**: Check `logs/run_*.log` for detailed per-agent traces
- **V2 NEW**: Enable `--debug` flag for maximum logging

## 📚 Documentation

- **[V2_UPGRADE_SUMMARY.md](V2_UPGRADE_SUMMARY.md)** - Complete V2 feature documentation
- **README.md** (this file) - Project overview and quick start
- **[README.md](README.md)** - Detailed documentation

## 🔄 Backward Compatibility

✓ **All V1 code works unchanged**
✓ **All V1 tests pass**
✓ **V1 command-line usage supported**
✓ **V1 outputs auto-upgraded to V2**
✓ **No breaking changes**

**Migration from V1 to V2**: None required! V2 is fully backward compatible and auto-upgrades V1 outputs on first run.

---

**Version**: 2.0
**Status**: Production-Ready
**Last Updated**: December 2, 2025
- Virtual environment recommended  
- Facebook Ads CSV dataset in `data/`

### Installation

```bash
# Clone or extract the project
cd kasparro-agentic-fb-analyst-likith-gs

# Create & activate venv
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## ▶️ Usage

Run the pipeline with a natural-language query:

```bash
python src/orchestrator/run.py "Analyze ROAS drop in last 7 days"
```

Windows batch helper:

```bat
run.bat run "Analyze ROAS drop"
```

## 📊 Data Format

CSV columns:

```
campaign_name, adset_name, date, spend, impressions, clicks, ctr,
purchases, revenue, roas, creative_type, creative_message,
audience_type, platform, country
```

## ⚙️ Configuration

```
low_ctr_threshold: 0.01
low_roas_threshold: 1.5
min_impressions: 1000
random_seed: 42
```

## 📤 Outputs

- report.md  
- insights.json  
- creatives.json  
- logs/ (all agent traces)

## 📁 Project Structure

```
src/
  agents/
  orchestrator/
  utils/
prompts/
data/
config/
reports/
logs/
tests/
```

## 🔍 Validation Logic

- +0.2 if metric drop > 20%  
- +0.1 if drop 10–20%  
- –0.1 if evidence weak  
- Confidence ∈ [0.0, 1.0]

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

## 🐛 Troubleshooting

- Activate venv → `pip install -r requirements.txt`
- Ensure CSV is inside `data/`
- If batch fails → use Python command directly
