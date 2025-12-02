"""
Structured logging configuration for V2 system.
Per-agent logging with timestamps, input/output traces, and execution timing.
"""

import logging
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
import time

LOG_DIR = "logs"


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured, readable log output."""

    def format(self, record):
        """Format log record with timestamp and level prefix."""
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        
        level_emoji = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️ ',
            'WARNING': '⚠️ ',
            'ERROR': '✗',
            'CRITICAL': '🔴'
        }
        
        emoji = level_emoji.get(record.levelname, '•')
        return f"[{timestamp}] {emoji} {record.levelname:8} | {record.name:20} | {record.getMessage()}"


class FileFormatter(logging.Formatter):
    """Formatter for file output with full details."""

    def format(self, record):
        """Format log record for file storage."""
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        return (
            f"[{timestamp}] {record.levelname:8} | {record.name:30} | "
            f"{record.funcName}:{record.lineno} | {record.getMessage()}"
        )


class AgentExecutionTracer:
    """Traces agent execution with input/output logging and timing."""

    def __init__(self, agent_name: str, log_dir: str = LOG_DIR):
        """
        Initialize tracer for an agent.
        
        Args:
            agent_name: Name of the agent (e.g., "DataAgent", "InsightAgent")
            log_dir: Directory for execution traces
        """
        self.agent_name = agent_name
        self.log_dir = log_dir
        self.traces = []
        self.start_time = None

    def start(self, method_name: str, input_data: Optional[Dict[str, Any]] = None):
        """
        Start timing an agent method execution.
        
        Args:
            method_name: Name of the method being executed
            input_data: Input dictionary to log
        """
        self.start_time = time.time()
        self.current_method = method_name
        self.current_input = input_data or {}
        
        logger = logging.getLogger(f"{self.agent_name}.{method_name}")
        logger.info(f"Starting {method_name}")
        if input_data:
            logger.debug(f"Input: {json.dumps(input_data, default=str, indent=2)[:200]}")

    def end(self, output_data: Optional[Dict[str, Any]] = None, error: Optional[Exception] = None):
        """
        End timing and log results.
        
        Args:
            output_data: Output dictionary to log
            error: Exception if method failed
        """
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        logger = logging.getLogger(f"{self.agent_name}.{self.current_method}")
        
        trace = {
            "agent": self.agent_name,
            "method": self.current_method,
            "status": "error" if error else "success",
            "elapsed_ms": round(elapsed * 1000, 1),
            "timestamp": datetime.now().isoformat()
        }
        
        if error:
            logger.error(f"Failed after {elapsed:.2f}s: {str(error)}")
            trace["error"] = str(error)
        else:
            logger.info(f"Completed in {elapsed:.2f}s")
            if output_data:
                logger.debug(f"Output keys: {list(output_data.keys())}")
                trace["output_keys"] = list(output_data.keys())
        
        self.traces.append(trace)
        self.start_time = None

    def save_traces(self, run_id: str):
        """
        Save execution traces to JSON file.
        
        Args:
            run_id: Unique run identifier (e.g., timestamp)
        """
        os.makedirs(self.log_dir, exist_ok=True)
        trace_path = os.path.join(self.log_dir, f"{run_id}_{self.agent_name}_trace.json")
        
        try:
            with open(trace_path, 'w') as f:
                json.dump(self.traces, f, indent=2)
            logger = logging.getLogger(self.agent_name)
            logger.info(f"Execution trace saved to {trace_path}")
        except Exception as e:
            logger = logging.getLogger(self.agent_name)
            logger.error(f"Failed to save execution trace: {e}")


def configure_logging(run_id: str, log_level: str = "INFO") -> str:
    """
    Configure logging for the entire pipeline.
    
    Sets up:
    - Console handler (to stdout)
    - File handler (to logs/run_<timestamp>.log)
    - Per-agent loggers
    
    Args:
        run_id: Unique run identifier (typically timestamp)
        log_level: Logging level ("DEBUG", "INFO", "WARNING", "ERROR")
    
    Returns:
        Path to log file
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (structured, colored)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    # File handler (detailed, timestamped)
    log_file = os.path.join(LOG_DIR, f"run_{run_id}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel("DEBUG")  # Always log DEBUG to file
    file_handler.setFormatter(FileFormatter())
    root_logger.addHandler(file_handler)
    
    # Per-agent loggers
    agent_names = [
        "DataAgent", "InsightAgent", "EvaluatorAgent", 
        "CreativeAgent", "PlannerAgent", "Orchestrator"
    ]
    
    for agent_name in agent_names:
        agent_logger = logging.getLogger(agent_name)
        agent_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Log initialization
    root_logger.info(f"Logging initialized | Run ID: {run_id}")
    root_logger.info(f"Log file: {log_file}")
    root_logger.info(f"Log level: {log_level}")
    
    return log_file


def get_pipeline_logger() -> logging.Logger:
    """Get logger for main orchestrator pipeline."""
    return logging.getLogger("Orchestrator")


def get_agent_logger(agent_name: str) -> logging.Logger:
    """Get logger for specific agent."""
    return logging.getLogger(agent_name)


if __name__ == '__main__':
    # Test logging configuration
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = configure_logging(run_id, log_level="DEBUG")
    
    # Test pipeline logger
    pipeline = get_pipeline_logger()
    pipeline.info("Pipeline started")
    
    # Test agent logger
    data_agent = get_agent_logger("DataAgent")
    data_agent.info("DataAgent initialized")
    
    # Test execution tracer
    tracer = AgentExecutionTracer("DataAgent")
    tracer.start("load", {"path": "data/sample.csv"})
    time.sleep(0.1)
    tracer.end({"rows": 1000, "columns": 15})
    tracer.save_traces(run_id)
    
    pipeline.info("Test complete")
    print(f"\nLog file: {log_file}")
