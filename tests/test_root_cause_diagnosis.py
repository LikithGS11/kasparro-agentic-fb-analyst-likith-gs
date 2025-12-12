"""
Test cases for root cause diagnosis in InsightAgent.
"""

import pytest
from src.agents.insight_agent import InsightAgent


class TestRootCauseDiagnosis:
    """Test root cause diagnosis logic."""

    def test_creative_fatigue_diagnosis(self):
        """Test creative fatigue detection."""
        ia = InsightAgent()
        
        item = {
            "campaign": "Test Campaign",
            "relative_delta": -0.20,  # 20% CTR drop
            "impressions_change": 0.05  # Impressions stable/up
        }
        
        diagnosis = ia._diagnose_root_cause(item, 'ctr')
        
        assert "creative_fatigue" in diagnosis, f"Expected creative_fatigue in {diagnosis}"

    def test_audience_saturation_diagnosis(self):
        """Test audience saturation detection."""
        ia = InsightAgent()
        
        item = {
            "campaign": "Test Campaign",
            "relative_delta": -0.18,  # 18% CTR drop
            "impressions_change": -0.15  # Impressions also dropping
        }
        
        diagnosis = ia._diagnose_root_cause(item, 'ctr')
        
        assert "audience_saturation" in diagnosis, f"Expected audience_saturation in {diagnosis}"

    def test_engagement_decline_diagnosis(self):
        """Test general engagement decline."""
        ia = InsightAgent()
        
        item = {
            "campaign": "Test Campaign",
            "relative_delta": -0.12,  # 12% CTR drop
            "impressions_change": -0.03  # Minor impressions change
        }
        
        diagnosis = ia._diagnose_root_cause(item, 'ctr')
        
        assert "engagement_decline" in diagnosis, f"Expected engagement_decline in {diagnosis}"

    def test_roas_severe_degradation(self):
        """Test severe ROAS performance degradation."""
        ia = InsightAgent()
        
        item = {
            "campaign": "Test Campaign",
            "relative_delta": -0.50,  # 50% ROAS drop
            "spend": 12000
        }
        
        diagnosis = ia._diagnose_root_cause(item, 'roas')
        
        assert "severe_performance_degradation" in diagnosis

    def test_roas_moderate_decline(self):
        """Test moderate ROAS decline."""
        ia = InsightAgent()
        
        item = {
            "campaign": "Test Campaign",
            "relative_delta": -0.25,  # 25% ROAS drop
            "spend": 8000
        }
        
        diagnosis = ia._diagnose_root_cause(item, 'roas')
        
        assert "moderate_performance_decline" in diagnosis

    def test_roas_high_spend_inefficiency(self):
        """Test high spend inefficiency flag."""
        ia = InsightAgent()
        
        item = {
            "campaign": "Test Campaign",
            "relative_delta": -0.30,
            "spend": 15000  # High spend
        }
        
        diagnosis = ia._diagnose_root_cause(item, 'roas')
        
        assert "high_spend_inefficiency" in diagnosis

    def test_generate_insights_with_diagnosis(self):
        """Test that generated insights include diagnosis."""
        ia = InsightAgent()
        
        summary = {
            "campaigns": ["C1", "C2"],
            "top_drops": {
                "roas_drop_campaigns": [{
                    "campaign": "C1",
                    "baseline_value": 10.0,
                    "current_value": 6.0,
                    "absolute_delta": -4.0,
                    "relative_delta": -0.40,
                    "spend": 12000
                }],
                "ctr_drop_campaigns": [{
                    "campaign": "C2",
                    "baseline_value": 0.02,
                    "current_value": 0.015,
                    "absolute_delta": -0.005,
                    "relative_delta": -0.25,
                    "impressions_change": 0.02
                }]
            }
        }
        
        result = ia.generate(summary)
        
        assert 'insights' in result
        insights = result['insights']
        
        # Check ROAS insight has diagnosis
        roas_insight = [i for i in insights if 'C1' in i.get('hypothesis', '')]
        if roas_insight:
            evidence = roas_insight[0].get('evidence', {})
            assert 'diagnosis' in evidence
            assert 'baseline_value' in evidence
            assert 'current_value' in evidence
            assert 'absolute_delta' in evidence
            assert 'relative_delta' in evidence

    def test_decision_logs_generated(self):
        """Test that decision logs are generated."""
        ia = InsightAgent()
        
        summary = {
            "campaigns": ["C1"],
            "top_drops": {
                "roas_drop_campaigns": [{
                    "campaign": "C1",
                    "baseline_value": 10.0,
                    "current_value": 7.0,
                    "absolute_delta": -3.0,
                    "relative_delta": -0.30,
                    "spend": 8000
                }],
                "ctr_drop_campaigns": []
            }
        }
        
        result = ia.generate(summary)
        
        assert 'decision_logs' in result
        decision_logs = result['decision_logs']
        
        if len(decision_logs) > 0:
            log = decision_logs[0]
            assert 'campaign' in log
            assert 'trigger' in log
            assert 'diagnosis' in log


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
