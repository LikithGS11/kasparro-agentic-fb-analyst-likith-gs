# Agentic FB Ads Analyst - V2 Upgrade Summary

## Overview

V2 is a **production-grade enhancement** of the V1 Agentic FB Ads Analyst. It adds enterprise-level error handling, observability, dynamic adaptivity, and schema governance while maintaining 100% backward compatibility with existing code.

**Key Achievement**: System can now run end-to-end without crashing on bad data, with full audit trails and automatic recovery.

---

## V2 Enhancements

### 1. **Production-Grade Error Handling**

**File**: `src/utils/safety.py` (NEW)

- **5 Categorized Error Types**: DataError, InsightError, PlannerError, CreativeError, EvaluatorError
- **safe_call Decorator**: Wraps all agent calls with:
  - Automatic retry with exponential backoff (default: 3 retries, 0.5s base delay)
  - Configurable fallback values for graceful degradation
  - Structured logging of all retry attempts
- **Helper Functions**:
  - `validate_data()`: Check DataFrame structure and required columns
  - `safe_numeric_division()`: Handle division-by-zero safely
  - `safe_json_load()`: Load JSON files with fallback
- **Pre-defined Fallback Objects**: For all major outputs (FALLBACK_INSIGHTS, FALLBACK_CREATIVES, etc.)

**Impact**: Pipeline now survives data corruption, missing columns, and transient failures. No more crashes.

---

### 2. **Division-by-Zero Bug Fixed**

**File**: `src/utils/helpers.py` (UPDATED)

- **Enhanced `percent_change()` function**:
  - ✓ Handles `previous == 0` (returns configurable default)
  - ✓ Handles `current == 0, previous == 0` (returns 0, no change)
  - ✓ Type-safe (None values return default)
  - ✓ Deterministic fallback behavior

- **Unit Tests**: `tests/test_percent_change.py` (20+ test cases)
  - Edge cases: division-by-zero, negative values, None inputs, very small/large values
  - Real-world scenarios: ROAS drops, CTR changes, spend increases
  - All tests pass with expected fallback behavior

**Impact**: No more crashes in DataAgent when comparing metrics. Robust calculation pipeline.

---

### 3. **Dynamic Planner Agent**

**File**: `src/agents/planner.py` (UPDATED)

- **Complexity Analysis**:
  - Computes complexity score (0-1) based on:
    - Campaign count (normalized to 0-0.3)
    - Missing metrics in overall_metrics (0-0.4)
    - Performance drops detected (0-0.3)
  
- **Adaptive Planning**:
  - High complexity (>0.5): Adds anomaly detection, audience overlap analysis
  - Low complexity (<0.2): Uses streamlined pipeline
  - Moderate: Standard pipeline
  
- **Logged Reasoning**: Every decision is logged for 30-second debugging
  
- **Backward Compatible**: Retains V1 keyword-based prioritization (ROAS, CTR, creative mentions)

**Example Plan Output** (V2):
```json
{
  "steps": [...],
  "complexity_analysis": {
    "complexity_score": 0.65,
    "campaign_count": 12,
    "missing_metrics": 1,
    "performance_drops": 8,
    "reasoning": [...]
  },
  "adaptation_reasoning": "High complexity dataset (0.65). Added anomaly detection..."
}
```

**Impact**: Deep analysis for complex campaigns, fast processing for simple ones. 100% backward compatible.

---

### 4. **Dataset-Aware Adaptive Insights**

**File**: `src/agents/insight_agent.py` (UPDATED)

- **Outlier Detection**:
  - IQR method (classic) or 90th percentile method (more robust)
  - Configurable IQR multiplier (default: 1.5)
  - Removes statistical outliers before threshold calculation

- **Dynamic Thresholds**:
  - Based on coefficient of variation (CV) of data
  - Low variance (CV < 0.1): Strict threshold (0.08)
  - Moderate variance: Standard threshold (0.10)
  - High variance: Relaxed threshold (0.15)
  
- **Adaptive Confidence Scoring**:
  - Base confidence: How far change exceeds threshold
  - Boost for outlier removal (more robust +5%)
  - Boost for multiple data points (+2% per point)
  - Bounded [min_confidence, max_confidence]
  
- **Generalized Hypotheses**: No longer dataset-specific (removed "undergarments" language)
  
- **Schema v2.0**: All insights include:
  - `confidence`: Numeric score (0-1)
  - `confidence_level`: "high", "moderate", "low"
  - `analysis_type`: Classification of insight type

**Example Insight** (V2):
```json
{
  "hypothesis": "Campaign 'X' shows declining click-through rate...",
  "confidence": 0.82,
  "confidence_level": "high",
  "analysis_type": "ctr_performance",
  "schema_version": "2.0"
}
```

**Impact**: More robust signal detection, less overfitting to synthetic data, transparent confidence scoring.

---

### 5. **Schema Governance v2.0**

**File**: `src/utils/schema_validator.py` (NEW)

- **Schema Definitions**: Formal V2 schemas for insights.json and creatives.json
  - Required fields: hypothesis, evidence, confidence, schema_version
  - Type validation: String, number, array, object constraints
  - Range validation: confidence ∈ [0, 1]
  
- **Full Validation**:
  - `validate_insights()`: Returns (is_valid, errors_list)
  - `validate_creatives()`: Returns (is_valid, errors_list)
  - Detailed error messages with field path and line numbers
  
- **V1→V2 Auto-Upgrade**:
  - `upgrade_insights_to_v2()`: Converts V1 confidence_estimate to V2 confidence
  - `upgrade_creatives_to_v2()`: Adds schema_version field
  - Automatic on pipeline run

**Impact**: Schema compliance enforced, outputs are audit-able, easy migration from V1.

---

### 6. **Drift Detection & Baseline Comparison**

**File**: `src/utils/drift_detector.py` (NEW)

- **Statistical Baseline Computation**:
  - Mean, median, std, quantiles (10th, 25th, 75th, 90th)
  - Campaign count and performance drop counts
  - Saved to `reports/baseline_stats.json`
  
- **Drift Detection**:
  - Compares current run metrics to baseline
  - Configurable threshold (default: 15% drift = significant)
  - Classifies severity: high, medium, low
  
- **Detects**:
  - Campaign count changes (new/removed campaigns)
  - ROAS drop count changes
  - Performance drop count changes
  - Mean metric drift
  
- **Human-Readable Reports**:
  ```
  ========================================
  DRIFT DETECTION REPORT
  ========================================
  ⚠️  DRIFT DETECTED (Severity: HIGH)
  
  • CAMPAIGN_COUNT
    Baseline: 20
    Current:  25
    Drift:    25% [HIGH]
  ```

**Impact**: Monitor system health across runs, detect anomalous changes, prevent silent data degradation.

---

### 7. **Structured Logging System**

**File**: `src/utils/logger_config.py` (NEW)

- **Console Logging**:
  - Emoji-prefixed: 🔍 DEBUG, ℹ️ INFO, ⚠️ WARNING, ✗ ERROR, 🔴 CRITICAL
  - Readable format: `[TIMESTAMP] EMOJI LEVEL | LOGGER | MESSAGE`
  - Configured per run
  
- **File Logging**:
  - Location: `logs/run_<timestamp>.log`
  - Always DEBUG level (maximum detail)
  - Includes function name and line numbers
  
- **Execution Traces**:
  - `AgentExecutionTracer` class for per-agent tracing
  - Logs: method name, input/output keys, execution time
  - Saved to `logs/run_<timestamp>_<agent>_trace.json`
  
- **Per-Agent Loggers**:
  - DataAgent, InsightAgent, EvaluatorAgent, CreativeAgent, PlannerAgent, Orchestrator
  - Easy filtering and debugging
  
**Log Level Control**:
```bash
python -m src.orchestrator.run "Query" --log-level DEBUG  # Maximum verbosity
python -m src.orchestrator.run "Query" --log-level INFO   # Standard
```

**Impact**: 30-second debugging capability, full audit trail, execution timing visibility.

---

### 8. **Updated Orchestrator Pipeline**

**File**: `src/orchestrator/run.py` (UPDATED)

- **Safe Agent Calls**: All 5 agents wrapped with `@safe_call` decorator
  - automatic retry, fallback, error categorization
  
- **Structured Logging**: 6-step pipeline with per-step logging
  - Step 1: Planning (with complexity analysis)
  - Step 2: Data Loading (with drift detection)
  - Step 3: Insight Generation
  - Step 4: Insight Validation
  - Step 5: Creative Generation
  - Step 6: Output Persistence & Validation
  
- **Schema Validation**: Automatic upgrade and validation
  - Converts V1→V2 if needed
  - Validates against schema
  - Detailed error reporting
  
- **Drift Detection**: Optional baseline comparison
  - Enabled by default
  - `--no-drift` flag to disable (for speed)
  
- **Memory Integration**: Loads and updates short-term memory with validated insights

- **Command-Line Interface**:
  ```bash
  python -m src.orchestrator.run "Analyze ROAS drop"
  python -m src.orchestrator.run "Analyze ROAS drop" --no-drift
  ```

**Output**:
```
============ 
✅ PIPELINE COMPLETE - ALL STEPS SUCCESSFUL
=====================

📁 outputs saved:
   • reports/insights.json (schema v2.0)
   • reports/creatives.json (schema v2.0)
   • reports/report.md (enhanced with confidence)
   
📊 Logs: logs/run_20251202_143027.log
```

**Impact**: Production-ready pipeline with full error recovery, 100% observability, automated schema compliance.

---

## Unit Tests

### `tests/test_percent_change.py`
- 20 test cases for percent_change function
- Edge cases: division-by-zero, None values, negative, very small/large numbers
- Real-world advertising scenarios

### `tests/test_schema_and_planner.py`
- 15+ test cases for SchemaValidator
- Schema validation (both positive and negative cases)
- V1→V2 auto-upgrade tests
- 7+ test cases for PlannerAgent
- Complexity analysis and adaptive planning

**Run Tests**:
```bash
pytest tests/test_percent_change.py -v
pytest tests/test_schema_and_planner.py -v
pytest tests/ -v  # Run all
```

---

## JSON Output Examples

### V2 Insights Schema
```json
{
  "insights": [
    {
      "hypothesis": "Campaign 'X' shows decreased return on ad spend...",
      "evidence": {
        "campaign": "X",
        "roas_change": -0.25,
        "change_percentile": "25.0%"
      },
      "expected_impact": "Moderate to High",
      "confidence": 0.82,
      "confidence_level": "high",
      "analysis_type": "roas_performance",
      "schema_version": "2.0"
    }
  ],
  "schema_version": "2.0"
}
```

### V2 Creatives Schema
```json
{
  "creatives": [
    {
      "campaign": "Campaign_X",
      "issue": "Low Click-Through Rate",
      "issue_type": "low_ctr",
      "change_metric": 25.0,
      "recommended_headlines": [
        "📢 Campaign_X: Fresh Content Inside",
        "✨ New Look for Campaign_X",
        "🎯 Updated Campaign_X"
      ],
      "recommended_messages": [
        "We've refreshed Campaign_X...",
        "Customer favorites..."
      ],
      "cta": "Shop Now",
      "priority": "high",
      "schema_version": "2.0"
    }
  ],
  "schema_version": "2.0"
}
```

### Baseline Statistics (`reports/baseline_stats.json`)
```json
{
  "run_timestamp": "2025-12-02T14:30:27.123456",
  "campaigns": {
    "count": 15,
    "list": ["Campaign_1", "Campaign_2", ...]
  },
  "performance_drops": {
    "roas_count": 3,
    "ctr_count": 2
  },
  "metrics": {
    "roas_changes": {
      "mean": -0.18,
      "median": -0.15,
      "std": 0.05,
      "q10": -0.25,
      "q90": -0.05,
      "count": 3
    }
  }
}
```

---

## System Architecture

```
┌─ src/orchestrator/run.py (MAIN PIPELINE)
│   ├─ Safe calls to all agents
│   ├─ Structured logging per step
│   ├─ Schema validation
│   ├─ Drift detection
│   └─ Memory integration
│
├─ src/agents/
│   ├─ planner.py (DYNAMIC COMPLEXITY)
│   ├─ data_agent.py (ROBUST LOADING)
│   ├─ insight_agent.py (ADAPTIVE ANALYSIS)
│   ├─ evaluator_agent.py (VALIDATION)
│   └─ creative_agent.py (RECOMMENDATIONS)
│
└─ src/utils/
    ├─ safety.py (ERROR HANDLING)
    ├─ helpers.py (PERCENT_CHANGE FIX)
    ├─ schema_validator.py (V2.0 GOVERNANCE)
    ├─ drift_detector.py (BASELINE COMPARISON)
    ├─ logger_config.py (STRUCTURED LOGS)
    └─ memory.py (CONTEXT PERSISTENCE)
```

---

## Backward Compatibility

✓ **All V1 code remains unchanged** (except enhancements)
✓ **All V1 tests still pass**
✓ **V1 API preserved** (agents accept same parameters)
✓ **V1 outputs auto-upgraded to V2** (transparent)
✓ **V1 command-line usage works** (`python -m src.orchestrator.run "query"`)

---

## What's New for V2 Users

| Feature | V1 | V2 |
|---------|----|----|
| Error Handling | Basic try/catch | Production-grade with retry + fallback |
| Division-by-Zero | Crashes | Safe with deterministic fallback |
| Planning | Keyword-based | Dynamic complexity-based adaptation |
| Insights | Simple heuristics | IQR outliers + adaptive thresholds |
| Confidence | Single estimate | Robust scoring with high/mod/low levels |
| Schema | Informal | Versioned (v2.0) with validation |
| Drift Detection | None | Baseline comparison with severity |
| Logging | Ad-hoc | Structured per-agent with traces |
| Observability | Limited | 30-second debugging capability |
| Guardrails | Minimal | Full pipeline protection |

---

## Deployment Checklist

- [x] Error handling wrapper (`safety.py`)
- [x] Division-by-zero fix with tests
- [x] Dynamic planner with complexity analysis
- [x] Adaptive insights with outlier detection
- [x] Schema v2.0 validation and upgrade
- [x] Drift detection with baseline persistence
- [x] Structured logging with per-agent traces
- [x] Updated orchestrator with safe calls
- [x] Comprehensive unit tests (30+ cases)
- [x] Documentation and examples
- [x] Backward compatibility verified

---

## Quick Start (V2)

```bash
# Basic run (with drift detection)
python -m src.orchestrator.run "Analyze ROAS drop"

# Fast run (skip drift detection)
python -m src.orchestrator.run "Analyze ROAS drop" --no-drift

# Debug mode (maximum logging)
python -m src.orchestrator.run "Analyze performance" --debug

# Run tests
pytest tests/ -v

# Check logs
tail -f logs/run_*.log
```

---

## Summary

**V2 transforms the system from prototype to production**:

1. ✓ **Never crashes**: Safe calls with retry + fallback on all failures
2. ✓ **Robust math**: Division-by-zero fixed with deterministic behavior  
3. ✓ **Smart planning**: Adapts depth based on dataset complexity
4. ✓ **Better insights**: Outlier detection + adaptive thresholds + confidence scoring
5. ✓ **Schema compliance**: Versioned outputs with automatic upgrade  
6. ✓ **Observability**: 30-second debugging through structured logs
7. ✓ **Quality monitoring**: Drift detection prevents silent degradation
8. ✓ **Fully backward compatible**: Zero breaking changes

**All code is production-ready, fully tested, and integrated into the existing pipeline.**

