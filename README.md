
# Kasparro Agentic Facebook Performance Analyst

A sophisticated agentic system that analyzes Facebook ad performance using AI-driven agents working through a deterministic pipeline. The system identifies performance drops, explains them with data-driven evidence, validates hypotheses, and generates campaign-level creative recommendations.

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
Planner Agent → Breaks query into structured steps
    ↓
Data Agent → Loads, cleans data & identifies metric drops
    ↓
Insight Agent → Generates hypotheses based on patterns
    ↓
Evaluator Agent → Validates hypotheses & scores confidence
    ↓
Creative Agent → Produces creative recommendations
    ↓
Orchestrator → Compiles final reports & logs
```

### Agent Responsibilities

| Agent | Role | Output |
|-------|------|--------|
| **Planner** | Converts natural-language query into actionable steps | Step sequence |
| **Data Agent** | Loads/aggregates data, detects drops | Dataset summary |
| **Insight Agent** | Produces hypotheses + supporting evidence | Hypothesis list |
| **Evaluator** | Validates hypotheses numerically | Confidence-scored insights |
| **Creative Agent** | Generates ad copy & creative suggestions | Creative JSON |
| **Orchestrator** | Runs entire pipeline & generates reports | Markdown/JSON/logs |

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
