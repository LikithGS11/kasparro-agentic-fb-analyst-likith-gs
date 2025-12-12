import pandas as pd
import numpy as np
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class DataAgent:
    """
    Loads CSV data and returns compact aggregations/summaries with V2 enhancements.
    
    V2 Features:
    - Pre-load dataset schema validation
    - Baseline vs current with absolute/relative deltas
    - Root cause diagnosis signals (creative fatigue, audience saturation, etc.)
    """

    REQUIRED_COLUMNS = [
        'campaign_name', 'date', 'spend', 'impressions', 'clicks', 
        'ctr', 'purchases', 'revenue', 'roas'
    ]

    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.df = None

    def validate_schema(self, df):
        """
        Validate that dataframe contains all required columns.
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            Tuple (is_valid, missing_columns)
        """
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        return (len(missing) == 0, missing)

    def load(self):
        """Load and validate CSV data."""
        self.df = pd.read_csv(self.csv_path, parse_dates=['date'])
        # normalize column names
        self.df.columns = [c.strip() for c in self.df.columns]
        
        # Validate schema
        is_valid, missing = self.validate_schema(self.df)
        if not is_valid:
            raise ValueError(f"Dataset missing required columns: {missing}")
        
        logger.info(f"✓ Dataset schema validated. Loaded {len(self.df)} rows.")
        return self.df

    def summarize(self, recent_days=14):
        if self.df is None:
            self.load()
        df = self.df.copy()
        df = df.sort_values('date')
        date_range = f"{df['date'].min().date()} to {df['date'].max().date()}"

        # Overall metrics
        overall = {
            "avg_ctr": float(df['ctr'].mean()) if 'ctr' in df else None,
            "avg_roas": float(df['roas'].mean()) if 'roas' in df else None,
            "total_spend": float(df['spend'].sum()) if 'spend' in df else None,
            "total_revenue": float(df['revenue'].sum()) if 'revenue' in df else None
        }

        # campaigns list
        campaigns = df['campaign_name'].dropna().unique().tolist()

        # Detect recent drops by comparing last N days vs previous period
        last_date = df['date'].max()
        recent_mask = df['date'] > (last_date - pd.Timedelta(days=recent_days))
        prev_mask = (df['date'] <= (last_date - pd.Timedelta(days=recent_days))) & (df['date'] > (last_date - pd.Timedelta(days=recent_days*2)))

        recent = df[recent_mask]
        prev = df[prev_mask]
        roas_drop_campaigns = []
        ctr_drop_campaigns = []

        if (not recent.empty) and (not prev.empty):
            def percent_change(a, b):
                try:
                    return float((a - b) / abs(b))
                except Exception:
                    return None

            for camp in campaigns:
                r = recent[recent['campaign_name'] == camp]
                p = prev[prev['campaign_name'] == camp]
                if r.empty or p.empty:
                    continue
                # Compute metrics
                r_roas = r['roas'].mean()
                p_roas = p['roas'].mean()
                r_ctr = r['ctr'].mean()
                p_ctr = p['ctr'].mean()
                r_impressions = r['impressions'].mean()
                p_impressions = p['impressions'].mean()
                r_spend = r['spend'].sum()
                p_spend = p['spend'].sum()
                
                # Calculate deltas
                roas_pct = percent_change(r_roas, p_roas) if p_roas != 0 else None
                ctr_pct = percent_change(r_ctr, p_ctr) if p_ctr != 0 else None
                impressions_pct = percent_change(r_impressions, p_impressions) if p_impressions != 0 else None
                
                # ROAS drops with full evidence
                if roas_pct is not None and roas_pct < -0.1:
                    roas_drop_campaigns.append({
                        "campaign": camp,
                        "baseline_value": float(p_roas),
                        "current_value": float(r_roas),
                        "absolute_delta": float(r_roas - p_roas),
                        "relative_delta": roas_pct,
                        "spend": float(r_spend),
                        "baseline_spend": float(p_spend)
                    })
                
                # CTR drops with diagnosis signals
                if ctr_pct is not None and ctr_pct < -0.1:
                    ctr_drop_campaigns.append({
                        "campaign": camp,
                        "baseline_value": float(p_ctr),
                        "current_value": float(r_ctr),
                        "absolute_delta": float(r_ctr - p_ctr),
                        "relative_delta": ctr_pct,
                        "impressions_change": impressions_pct,
                        "current_impressions": float(r_impressions),
                        "baseline_impressions": float(p_impressions)
                    })

        summary = {
            "date_range": date_range,
            "campaigns": campaigns,
            "overall_metrics": overall,
            "top_drops": {
                "roas_drop_campaigns": roas_drop_campaigns,
                "ctr_drop_campaigns": ctr_drop_campaigns
            }
        }
        return summary

    def save_summary(self, out_path):
        summary = self.summarize()
        with open(out_path, 'w') as f:
            json.dump(summary, f, indent=2)
        return summary

if __name__ == '__main__':
    da = DataAgent('/mnt/data/sample.csv')
    print(da.summarize())
