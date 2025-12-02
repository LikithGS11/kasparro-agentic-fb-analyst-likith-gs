
# Kasparro Agentic Facebook Performance Analyst

**VERSION 2.0** - Production-Grade Enterprise System

A sophisticated agentic system that analyzes Facebook ad performance using AI-driven agents working through a deterministic pipeline. The system identifies performance drops, explains them with data-driven evidence, validates hypotheses, and generates campaign-level creative recommendations.

## 🎯 What's New in V2

V2 adds **production-grade enterprise features** while maintaining 100% backward compatibility:

| Feature | Impact |
|---------|--------|
| **Error Handling** | Safe calls with retry + exponential backoff. Pipeline never crashes on bad data. |
| **Division-by-Zero Fix** | Robust `percent_change()` with deterministic fallback behavior. |
| **Dynamic Planning** | Planner adapts depth based on dataset complexity (campaign count, missing metrics, drops). |
| **Adaptive Insights** | IQR-based outlier removal + dynamic thresholds + confidence scoring (high/moderate/low). |
| **Schema v2.0** | Versioned JSON outputs with automatic V1→V2 upgrade and validation. |
| **Drift Detection** | Compares metrics to baseline, detects anomalies, prevents silent degradation. |
| **Structured Logging** | Per-agent execution traces, 30-second debugging capability. |

**See [V2_UPGRADE_SUMMARY.md](V2_UPGRADE_SUMMARY.md) for complete details.**

## 🎯 Overview

Kasparro is a multi-agent pipeline designed for automated Facebook ads performance diagnosis. It can:

- Detect ROAS and CTR performance drops  
- Generate evidence-backed hypotheses  
- Validate insights with numerical thresholds  
- Recommend new creatives for underperforming campaigns  
- Produce complete reports in Markdown and JSON formats  

## 🧩 System Architecture

The pipeline is sequential and deterministic:

```
User Query
    ↓
Planner Agent (V2: Dynamic Complexity) → Breaks query into structured steps
    ↓
Data Agent → Loads, cleans data & identifies metric drops
    ↓
Insight Agent (V2: Adaptive Thresholds) → Generates hypotheses based on patterns
    ↓
Evaluator Agent → Validates hypotheses & scores confidence
    ↓
Creative Agent → Produces creative recommendations
    ↓
Orchestrator (V2: Safe Calls, Structured Logging) → Compiles final reports & logs
```

### Agent Responsibilities

| Agent | Role | Output | V2 Enhancement |
|-------|------|--------|-----------------|
| **Planner** | Converts natural-language query into actionable steps | Step sequence | Dynamic complexity analysis |
| **Data Agent** | Loads/aggregates data, detects drops | Dataset summary | Robust error handling |
| **Insight Agent** | Produces hypotheses + supporting evidence | Hypothesis list | IQR outliers + adaptive confidence |
| **Evaluator** | Validates hypotheses numerically | Confidence-scored insights | (Unchanged) |
| **Creative Agent** | Generates ad copy & creative suggestions | Creative JSON | Schema v2.0 compliance |
| **Orchestrator** | Runs entire pipeline & generates reports | Markdown/JSON/logs | Safe calls + structured logging |

## 🚀 Quick Start

### Prerequisites
- Python **3.10+**
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
# Standard run (with drift detection)
python -m src.orchestrator.run "Analyze ROAS drop in last 7 days"

# Fast run (skip drift detection)
python -m src.orchestrator.run "Analyze ROAS drop" --no-drift

# V2: Check detailed logs for debugging
tail -f logs/run_*.log
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
