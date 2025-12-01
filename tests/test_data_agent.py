import pytest
import pandas as pd
from src.agents.data_agent import DataAgent

def test_data_agent_load():
    da = DataAgent("data/synthetic_fb_ads_undergarments.csv")
    df = da.load()
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "roas" in df.columns

def test_data_agent_summarize():
    da = DataAgent("data/synthetic_fb_ads_undergarments.csv")
    da.load()
    summary = da.summarize()
    assert "overall_metrics" in summary
    assert "avg_roas" in summary["overall_metrics"]
