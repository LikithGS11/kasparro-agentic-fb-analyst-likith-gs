import json
import os
from pathlib import Path

MEMORY_FILE = "memory.json"

def load_memory():
    """Load short-term memory from file."""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"previous_insights": [], "learned_patterns": []}

def save_memory(memory):
    """Save short-term memory to file."""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def update_memory(new_insights, memory):
    """Update memory with new insights for iterative learning."""
    memory["previous_insights"].extend(new_insights)
    # Keep only last 5 runs to avoid bloat
    memory["previous_insights"] = memory["previous_insights"][-5:]
    # Simple pattern learning: track common hypotheses
    patterns = {}
    for insight in memory["previous_insights"]:
        hyp = insight.get("hypothesis", "")
        patterns[hyp] = patterns.get(hyp, 0) + 1
    memory["learned_patterns"] = [{"hypothesis": k, "frequency": v} for k, v in patterns.items() if v > 1]
    save_memory(memory)
