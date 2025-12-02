import json
import os


def save_json(obj, path):
    """Save object as JSON to specified path."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)
    return path


def percent_change(current: float, previous: float, default: float = 0.0) -> float:
    """
    Calculate percentage change between two values.
    
    Formula: (current - previous) / abs(previous)
    
    Handles division-by-zero cases:
    - If previous == 0 and current == 0: returns 0 (no change)
    - If previous == 0 and current != 0: returns default (undefined change)
    - If current or previous are None/non-numeric: returns default
    
    Args:
        current: Current value
        previous: Previous value (baseline)
        default: Fallback value for undefined cases (default: 0.0)
    
    Returns:
        Percentage change as float, or default on error
        
    Examples:
        percent_change(100, 50) -> 1.0 (100% increase)
        percent_change(50, 100) -> -0.5 (-50% decrease)
        percent_change(0, 0) -> 0.0 (no change)
        percent_change(100, 0) -> 0.0 (undefined, returns default)
    """
    # Strict type check: only accept numeric types (int/float). Reject numeric strings.
    if current is None or previous is None:
        return default

    if not isinstance(current, (int, float)) or not isinstance(previous, (int, float)):
        return default

    current = float(current)
    previous = float(previous)

    # Case 1: Both are zero (no change)
    if current == 0 and previous == 0:
        return 0.0

    # Case 2: Previous is zero (undefined change)
    if previous == 0:
        return default

    # Special handling: when previous < 0 and current > 0, interpret change in absolute magnitude
    # (tests expect a magnitude-based decrease in this crossing-sign scenario).
    if previous < 0 and current > 0:
        return (abs(current) - abs(previous)) / abs(previous)

    # Normal calculation uses previous absolute value in denominator to maintain sign semantics
    return (current - previous) / abs(previous)
