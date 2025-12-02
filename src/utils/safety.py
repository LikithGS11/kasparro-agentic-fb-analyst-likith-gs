"""
Production-grade error handling and retry logic for agentic pipeline.
Provides categorized errors and safe_call decorator with exponential backoff.
"""

import functools
import time
import logging
from typing import Callable, Any, Optional, Type, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# CATEGORIZED ERRORS
# ============================================================================

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class DataError(PipelineError):
    """Data loading, parsing, or validation error."""
    pass


class InsightError(PipelineError):
    """Insight generation or analysis error."""
    pass


class PlannerError(PipelineError):
    """Planning or task decomposition error."""
    pass


class CreativeError(PipelineError):
    """Creative recommendation generation error."""
    pass


class EvaluatorError(PipelineError):
    """Validation or evaluation error."""
    pass


class UnexpectedError(PipelineError):
    """Unexpected/unclassified runtime error."""
    pass


# ============================================================================
# SAFE CALL DECORATOR WITH RETRY & EXPONENTIAL BACKOFF
# ============================================================================

def safe_call(
    error_type: Type[PipelineError] = UnexpectedError,
    max_retries: int = 3,
    base_delay: float = 0.5,
    fallback: Optional[Any] = None,
    log_level: str = "warning"
) -> Callable:
    """
    Decorator for safe execution of agent functions with retry logic.
    
    Features:
    - Automatic retry with exponential backoff
    - Categorized error classification
    - Graceful fallback on final failure
    - Structured logging of attempts and failures
    
    Args:
        error_type: Exception class to raise on final failure (default: UnexpectedError)
        max_retries: Maximum retry attempts (default: 3)
        base_delay: Initial delay in seconds for exponential backoff (default: 0.5)
        fallback: Fallback value to return on final failure (default: None)
        log_level: Logging level for retry events ("debug", "info", "warning")
    
    Returns:
        Decorated function with retry and error handling
    
    Example:
        @safe_call(error_type=DataError, max_retries=2, fallback={"status": "error"})
        def load_data(path):
            return pd.read_csv(path)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"✓ {func.__name__} succeeded on attempt {attempt + 1}/{max_retries + 1}"
                        )
                    return result
                
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # exponential backoff
                        log_func = getattr(logger, log_level, logger.warning)
                        log_func(
                            f"⚠️  {func.__name__} attempt {attempt + 1}/{max_retries + 1} failed. "
                            f"Error: {type(e).__name__}: {str(e)}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"✗ {func.__name__} failed after {max_retries + 1} attempts. "
                            f"Final error: {type(e).__name__}: {str(e)}"
                        )
            
            # Final failure: use fallback or raise
            if fallback is not None:
                logger.warning(
                    f"→ {func.__name__} returning fallback value: {type(fallback).__name__}"
                )
                return fallback
            else:
                raise error_type(
                    f"{func.__name__} failed after {max_retries + 1} attempts: {str(last_exception)}"
                ) from last_exception
        
        return wrapper
    return decorator


# ============================================================================
# RECOVERY & VALIDATION HELPERS
# ============================================================================

def validate_data(df, min_rows: int = 1, required_cols: Optional[list] = None) -> Tuple[bool, str]:
    """
    Validate dataframe structure and content.
    
    Args:
        df: DataFrame to validate
        min_rows: Minimum required rows
        required_cols: List of required column names
    
    Returns:
        Tuple of (is_valid, message)
    """
    if df is None or df.empty:
        return False, "DataFrame is None or empty"
    
    if len(df) < min_rows:
        return False, f"DataFrame has {len(df)} rows, minimum required: {min_rows}"
    
    if required_cols:
        missing = set(required_cols) - set(df.columns)
        if missing:
            return False, f"Missing required columns: {missing}"
    
    return True, "DataFrame is valid"


def safe_numeric_division(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers with fallback for division by zero.
    
    Args:
        numerator: Dividend
        denominator: Divisor
        default: Value to return if denominator is zero
    
    Returns:
        Result of division or default value
    """
    try:
        if denominator == 0:
            return default
        return numerator / denominator
    except (TypeError, ValueError):
        return default


def safe_json_load(filepath: str, default: Optional[dict] = None) -> dict:
    """
    Safely load JSON file with fallback to default on error.
    
    Args:
        filepath: Path to JSON file
        default: Default value if file cannot be loaded
    
    Returns:
        Loaded JSON dict or default value
    """
    import json
    import os
    
    if not os.path.exists(filepath):
        logger.warning(f"JSON file not found: {filepath}")
        return default or {}
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {filepath}: {e}")
        return default or {}
    except Exception as e:
        logger.error(f"Unexpected error loading JSON from {filepath}: {e}")
        return default or {}


# ============================================================================
# FALLBACK OBJECTS
# ============================================================================

FALLBACK_SUMMARY = {
    "date_range": "N/A",
    "campaigns": [],
    "overall_metrics": {
        "avg_ctr": None,
        "avg_roas": None,
        "total_spend": None,
        "total_revenue": None
    },
    "top_drops": {
        "roas_drop_campaigns": [],
        "ctr_drop_campaigns": []
    }
}

FALLBACK_INSIGHTS = {
    "insights": [{
        "hypothesis": "Unable to generate insights due to data or processing error.",
        "evidence": {},
        "expected_impact": "Unknown",
        "confidence_estimate": 0.0,
        "schema_version": "2.0"
    }]
}

FALLBACK_CREATIVES = {
    "creatives": [{
        "campaign": None,
        "issue": "System error",
        "recommended_headlines": ["Please review data and retry"],
        "recommended_messages": ["An error occurred during creative generation"],
        "cta": None,
        "schema_version": "2.0"
    }]
}

FALLBACK_VALIDATED = {
    "validated": [{
        "hypothesis": "Unable to validate due to processing error",
        "confidence": 0.0,
        "validation_notes": "System error during validation",
        "schema_version": "2.0"
    }]
}
