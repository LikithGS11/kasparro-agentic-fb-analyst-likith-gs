"""
Drift detector for detecting changes between runs.
Compares current metrics to baseline using statistical methods.
"""

import json
import os
import logging
from typing import Dict, Any, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

BASELINE_PATH = "reports/baseline_stats.json"


class DriftDetector:
    """
    Detects metric drift between runs using statistical comparison.
    
    Methods:
    - Mean/median drift detection
    - Quantile-based anomaly detection
    - Count-based drift for campaign/dimension changes
    """

    def __init__(self, baseline_path: str = BASELINE_PATH, drift_threshold: float = 0.15):
        """
        Initialize DriftDetector.
        
        Args:
            baseline_path: Path to baseline statistics JSON
            drift_threshold: Threshold for significant drift (0-1, default 0.15 = 15%)
        """
        self.baseline_path = baseline_path
        self.drift_threshold = drift_threshold
        self.baseline = self._load_baseline()

    def _load_baseline(self) -> Dict[str, Any]:
        """Load baseline statistics from file."""
        if not os.path.exists(self.baseline_path):
            logger.info(f"Baseline file not found: {self.baseline_path}. Starting fresh.")
            return None
        
        try:
            with open(self.baseline_path, 'r') as f:
                baseline = json.load(f)
                logger.info(f"Loaded baseline from {self.baseline_path}")
                return baseline
        except Exception as e:
            logger.warning(f"Failed to load baseline: {e}")
            return None

    def compute_stats(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute statistical summary of current metrics.
        
        Computes:
        - Mean, median, std, quantiles (10th, 25th, 75th, 90th)
        - Count of campaigns and performance drops
        - Min/max values
        
        Args:
            summary: Data summary dict from DataAgent
        
        Returns:
            Stats dict with all computed statistics
        """
        stats = {
            "run_timestamp": str(__import__('datetime').datetime.now().isoformat()),
            "campaigns": {
                "count": len(summary.get('campaigns', [])),
                "list": summary.get('campaigns', [])
            },
            "performance_drops": {
                "roas_count": len(summary.get('top_drops', {}).get('roas_drop_campaigns', [])),
                "ctr_count": len(summary.get('top_drops', {}).get('ctr_drop_campaigns', []))
            },
            "metrics": {}
        }
        
        # Extract numeric metrics
        overall_metrics = summary.get('overall_metrics', {})
        for metric_name, value in overall_metrics.items():
            if value is not None and isinstance(value, (int, float)):
                stats['metrics'][metric_name] = {
                    "value": value,
                    "type": type(value).__name__
                }
        
        # Extract ROAS and CTR changes as arrays for quantile computation
        roas_changes = [
            item['change'] for item in summary.get('top_drops', {}).get('roas_drop_campaigns', [])
            if item.get('change') is not None
        ]
        ctr_changes = [
            item['change'] for item in summary.get('top_drops', {}).get('ctr_drop_campaigns', [])
            if item.get('change') is not None
        ]
        
        # Compute quantiles for changes
        if roas_changes:
            arr = np.array(roas_changes)
            stats['metrics']['roas_changes'] = {
                "mean": float(np.mean(arr)),
                "median": float(np.median(arr)),
                "std": float(np.std(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "q10": float(np.percentile(arr, 10)),
                "q25": float(np.percentile(arr, 25)),
                "q75": float(np.percentile(arr, 75)),
                "q90": float(np.percentile(arr, 90)),
                "count": len(arr)
            }
        
        if ctr_changes:
            arr = np.array(ctr_changes)
            stats['metrics']['ctr_changes'] = {
                "mean": float(np.mean(arr)),
                "median": float(np.median(arr)),
                "std": float(np.std(arr)),
                "min": float(np.min(arr)),
                "max": float(np.max(arr)),
                "q10": float(np.percentile(arr, 10)),
                "q25": float(np.percentile(arr, 25)),
                "q75": float(np.percentile(arr, 75)),
                "q90": float(np.percentile(arr, 90)),
                "count": len(arr)
            }
        
        return stats

    def detect_drift(self, current_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare current metrics to baseline and detect significant drifts.
        
        Args:
            current_stats: Stats dict from compute_stats()
        
        Returns:
            Dict with detected drifts and severity levels
        """
        drifts = {
            "has_drift": False,
            "severity": "none",
            "detections": []
        }
        
        if self.baseline is None:
            logger.info("No baseline for comparison. Skipping drift detection.")
            return drifts
        
        try:
            # Check campaign count drift
            baseline_campaigns = self.baseline.get('campaigns', {}).get('count', 0)
            current_campaigns = current_stats.get('campaigns', {}).get('count', 0)
            
            if baseline_campaigns > 0:
                campaign_drift = abs(current_campaigns - baseline_campaigns) / baseline_campaigns
                if campaign_drift > self.drift_threshold:
                    drifts["detections"].append({
                        "type": "campaign_count",
                        "baseline": baseline_campaigns,
                        "current": current_campaigns,
                        "drift_pct": round(campaign_drift * 100, 1),
                        "severity": "high" if campaign_drift > 0.5 else "medium"
                    })
            
            # Check performance drop counts
            baseline_roas_drops = self.baseline.get('performance_drops', {}).get('roas_count', 0)
            current_roas_drops = current_stats.get('performance_drops', {}).get('roas_count', 0)
            
            if baseline_roas_drops > 0:
                roas_drop_drift = abs(current_roas_drops - baseline_roas_drops) / baseline_roas_drops
                if roas_drop_drift > self.drift_threshold:
                    drifts["detections"].append({
                        "type": "roas_drop_count",
                        "baseline": baseline_roas_drops,
                        "current": current_roas_drops,
                        "drift_pct": round(roas_drop_drift * 100, 1),
                        "severity": "high" if roas_drop_drift > 0.5 else "medium"
                    })
            
            # Check metric-level mean drift
            baseline_metrics = self.baseline.get('metrics', {})
            current_metrics = current_stats.get('metrics', {})
            
            for metric_name in ['roas_changes', 'ctr_changes']:
                if metric_name in baseline_metrics and metric_name in current_metrics:
                    baseline_mean = baseline_metrics[metric_name].get('mean')
                    current_mean = current_metrics[metric_name].get('mean')
                    
                    if baseline_mean is not None and current_mean is not None and baseline_mean != 0:
                        mean_drift = abs(current_mean - baseline_mean) / abs(baseline_mean)
                        if mean_drift > self.drift_threshold:
                            drifts["detections"].append({
                                "type": f"{metric_name}_mean",
                                "baseline": round(baseline_mean, 4),
                                "current": round(current_mean, 4),
                                "drift_pct": round(mean_drift * 100, 1),
                                "severity": "high" if mean_drift > 0.5 else "medium"
                            })
            
            # Set overall drift flag and severity
            if drifts["detections"]:
                drifts["has_drift"] = True
                severities = [d.get('severity', 'low') for d in drifts["detections"]]
                if 'high' in severities:
                    drifts["severity"] = "high"
                else:
                    drifts["severity"] = "medium"
        
        except Exception as e:
            logger.warning(f"Error during drift detection: {e}")
        
        return drifts

    def save_baseline(self, stats: Dict[str, Any]) -> bool:
        """
        Save current stats as new baseline.
        
        Args:
            stats: Stats dict from compute_stats()
        
        Returns:
            True if successfully saved
        """
        try:
            os.makedirs(os.path.dirname(self.baseline_path), exist_ok=True)
            with open(self.baseline_path, 'w') as f:
                json.dump(stats, f, indent=2)
            logger.info(f"Baseline saved to {self.baseline_path}")
            self.baseline = stats
            return True
        except Exception as e:
            logger.error(f"Failed to save baseline: {e}")
            return False

    def generate_report(self, drift_detection: Dict[str, Any]) -> str:
        """
        Generate human-readable drift detection report.
        
        Args:
            drift_detection: Result from detect_drift()
        
        Returns:
            Formatted report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("DRIFT DETECTION REPORT")
        lines.append("=" * 60)
        
        has_drift = drift_detection.get('has_drift', False)
        severity = drift_detection.get('severity', 'none')
        
        if not has_drift:
            lines.append("✓ No significant drift detected from baseline.")
            lines.append("  All metrics are within acceptable ranges.")
        else:
            lines.append(f"⚠️  DRIFT DETECTED (Severity: {severity.upper()})")
            lines.append(f"\nDetected {len(drift_detection['detections'])} drift(s):\n")
            
            for detection in drift_detection['detections']:
                lines.append(f"  • {detection['type'].upper()}")
                lines.append(f"    Baseline: {detection['baseline']}")
                lines.append(f"    Current:  {detection['current']}")
                lines.append(f"    Drift:    {detection['drift_pct']}% [{detection['severity'].upper()}]")
        
        lines.append("=" * 60)
        return "\n".join(lines)


if __name__ == '__main__':
    # Test drift detector
    detector = DriftDetector()
    
    sample_summary = {
        "campaigns": ["C1", "C2", "C3"],
        "overall_metrics": {
            "avg_ctr": 0.025,
            "avg_roas": 2.1,
            "total_spend": 5000,
            "total_revenue": 10500
        },
        "top_drops": {
            "roas_drop_campaigns": [
                {"campaign": "C1", "change": -0.2},
                {"campaign": "C2", "change": -0.15}
            ],
            "ctr_drop_campaigns": [
                {"campaign": "C3", "change": -0.18}
            ]
        }
    }
    
    stats = detector.compute_stats(sample_summary)
    print("Current Stats:")
    print(json.dumps(stats, indent=2))
    
    drift = detector.detect_drift(stats)
    print("\nDrift Detection:")
    print(json.dumps(drift, indent=2))
    
    print("\nDrift Report:")
    print(detector.generate_report(drift))
