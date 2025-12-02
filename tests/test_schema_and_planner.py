"""
Unit tests for schema validation and planner agent.
Tests schema v2.0 compliance and dynamic planning logic.
"""

import pytest
import json
from src.utils.schema_validator import (
    SchemaValidator, upgrade_insights_to_v2, upgrade_creatives_to_v2
)
from src.agents.planner import PlannerAgent


class TestSchemaValidator:
    """Test suite for SchemaValidator."""

    @pytest.fixture
    def validator(self):
        """Provide validator instance."""
        return SchemaValidator()

    def test_valid_insights_v2(self, validator):
        """Test validation of valid V2 insights."""
        insights = {
            "schema_version": "2.0",
            "insights": [
                {
                    "hypothesis": "Test hypothesis",
                    "evidence": {"key": "value"},
                    "expected_impact": "High",
                    "confidence": 0.8,
                    "confidence_level": "high",
                    "schema_version": "2.0"
                }
            ]
        }
        is_valid, errors = validator.validate_insights(insights)
        assert is_valid
        assert len(errors) == 0

    def test_invalid_insights_missing_schema_version(self, validator):
        """Test validation fails without schema_version."""
        insights = {
            "insights": [
                {
                    "hypothesis": "Test",
                    "evidence": {},
                    "expected_impact": "High",
                    "confidence": 0.8,
                    "schema_version": "2.0"
                }
            ]
        }
        is_valid, errors = validator.validate_insights(insights)
        assert not is_valid
        assert any("schema_version" in str(e) for e in errors)

    def test_invalid_insights_missing_required_field(self, validator):
        """Test validation fails with missing required field."""
        insights = {
            "schema_version": "2.0",
            "insights": [
                {
                    "hypothesis": "Test",
                    # Missing 'confidence' field
                    "evidence": {},
                    "expected_impact": "High",
                    "schema_version": "2.0"
                }
            ]
        }
        is_valid, errors = validator.validate_insights(insights)
        assert not is_valid
        assert any("confidence" in str(e) for e in errors)

    def test_invalid_insights_wrong_schema_version(self, validator):
        """Test validation fails with wrong schema version."""
        insights = {
            "schema_version": "1.0",
            "insights": []
        }
        is_valid, errors = validator.validate_insights(insights)
        assert not is_valid
        assert any("2.0" in str(e) for e in errors)

    def test_invalid_insights_confidence_out_of_range(self, validator):
        """Test validation fails when confidence out of range."""
        insights = {
            "schema_version": "2.0",
            "insights": [
                {
                    "hypothesis": "Test",
                    "evidence": {},
                    "expected_impact": "High",
                    "confidence": 1.5,  # Out of range
                    "schema_version": "2.0"
                }
            ]
        }
        is_valid, errors = validator.validate_insights(insights)
        assert not is_valid
        assert any("between 0 and 1" in str(e) for e in errors)

    def test_valid_creatives_v2(self, validator):
        """Test validation of valid V2 creatives."""
        creatives = {
            "schema_version": "2.0",
            "creatives": [
                {
                    "campaign": "TestCampaign",
                    "issue": "Low CTR",
                    "recommended_headlines": ["Headline 1", "Headline 2"],
                    "recommended_messages": ["Message 1"],
                    "cta": "Shop Now",
                    "schema_version": "2.0"
                }
            ]
        }
        is_valid, errors = validator.validate_creatives(creatives)
        assert is_valid
        assert len(errors) == 0

    def test_invalid_creatives_headlines_not_array(self, validator):
        """Test validation fails when headlines not array."""
        creatives = {
            "schema_version": "2.0",
            "creatives": [
                {
                    "campaign": "Test",
                    "issue": "Low CTR",
                    "recommended_headlines": "Not an array",
                    "recommended_messages": ["Message"],
                    "cta": "Shop",
                    "schema_version": "2.0"
                }
            ]
        }
        is_valid, errors = validator.validate_creatives(creatives)
        assert not is_valid
        assert any("array" in str(e) for e in errors)


class TestSchemaUpgrade:
    """Test schema upgrade functions."""

    def test_upgrade_insights_v1_to_v2(self):
        """Test upgrading V1 insights to V2."""
        v1_insights = {
            "insights": [
                {
                    "hypothesis": "Test hypothesis",
                    "evidence": {"key": "value"},
                    "expected_impact": "High",
                    "confidence_estimate": 0.75
                }
            ]
        }
        
        v2_insights = upgrade_insights_to_v2(v1_insights)
        
        assert v2_insights["schema_version"] == "2.0"
        assert len(v2_insights["insights"]) == 1
        
        insight = v2_insights["insights"][0]
        assert insight["schema_version"] == "2.0"
        assert insight["confidence"] == 0.75
        assert insight["confidence_level"] == "high"
        assert "analysis_type" in insight

    def test_upgrade_insights_low_confidence(self):
        """Test confidence level assignment during upgrade."""
        v1_insights = {
            "insights": [
                {
                    "hypothesis": "Low conf insight",
                    "evidence": {},
                    "expected_impact": "Unknown",
                    "confidence_estimate": 0.45
                }
            ]
        }
        
        v2_insights = upgrade_insights_to_v2(v1_insights)
        assert v2_insights["insights"][0]["confidence_level"] == "low"

    def test_upgrade_insights_moderate_confidence(self):
        """Test moderate confidence level assignment."""
        v1_insights = {
            "insights": [
                {
                    "hypothesis": "Moderate conf insight",
                    "evidence": {},
                    "expected_impact": "Moderate",
                    "confidence_estimate": 0.6
                }
            ]
        }
        
        v2_insights = upgrade_insights_to_v2(v1_insights)
        assert v2_insights["insights"][0]["confidence_level"] == "moderate"

    def test_upgrade_creatives_v1_to_v2(self):
        """Test upgrading V1 creatives to V2."""
        v1_creatives = {
            "creatives": [
                {
                    "campaign": "TestCampaign",
                    "issue": "Low CTR",
                    "recommended_headlines": ["H1", "H2"],
                    "recommended_messages": ["M1"],
                    "cta": "Shop"
                }
            ]
        }
        
        v2_creatives = upgrade_creatives_to_v2(v1_creatives)
        
        assert v2_creatives["schema_version"] == "2.0"
        assert len(v2_creatives["creatives"]) == 1
        assert v2_creatives["creatives"][0]["schema_version"] == "2.0"


class TestPlannerAgent:
    """Test suite for PlannerAgent with complexity analysis."""

    def test_planner_basic_plan_without_summary(self):
        """Test basic planning without summary."""
        planner = PlannerAgent(log_reasoning=False)
        plan = planner.plan("Analyze ROAS drop")
        
        assert "steps" in plan
        assert len(plan["steps"]) > 0
        assert "roas" in " ".join(plan["steps"]).lower()

    def test_planner_keyword_priority_roas(self):
        """Test ROAS keyword prioritization."""
        planner = PlannerAgent(log_reasoning=False)
        plan = planner.plan("Analyze ROAS drop")
        
        steps = plan["steps"]
        # Should have ROAS-specific step
        assert any("roas" in step.lower() for step in steps)

    def test_planner_keyword_priority_ctr(self):
        """Test CTR keyword prioritization."""
        planner = PlannerAgent(log_reasoning=False)
        plan = planner.plan("Improve CTR performance")
        
        steps = plan["steps"]
        assert any("ctr" in step.lower() for step in steps)

    def test_planner_complexity_analysis_low(self):
        """Test complexity analysis for simple dataset."""
        planner = PlannerAgent(log_reasoning=False)
        
        simple_summary = {
            "campaigns": ["C1", "C2"],
            "overall_metrics": {
                "avg_ctr": 0.025,
                "avg_roas": 2.0,
                "total_spend": 1000,
                "total_revenue": 2000
            },
            "top_drops": {
                "roas_drop_campaigns": [],
                "ctr_drop_campaigns": []
            }
        }
        
        plan = planner.plan("Analyze performance", summary=simple_summary)
        
        assert "complexity_analysis" in plan
        complexity = plan["complexity_analysis"]["complexity_score"]
        assert 0 <= complexity <= 1

    def test_planner_complexity_analysis_high(self):
        """Test complexity analysis for complex dataset."""
        planner = PlannerAgent(complexity_threshold=0.5, log_reasoning=False)
        
        complex_summary = {
            "campaigns": [f"C{i}" for i in range(20)],
            "overall_metrics": {
                "avg_ctr": None,  # Missing metric
                "avg_roas": None,  # Missing metric
                "total_spend": 100000,
                "total_revenue": 250000
            },
            "top_drops": {
                "roas_drop_campaigns": [
                    {"campaign": f"C{i}", "change": -0.2} for i in range(5)
                ],
                "ctr_drop_campaigns": [
                    {"campaign": f"C{i}", "change": -0.15} for i in range(3)
                ]
            }
        }
        
        plan = planner.plan("Analyze performance", summary=complex_summary)
        
        assert "complexity_analysis" in plan
        complexity = plan["complexity_analysis"]["complexity_score"]
        assert complexity > 0.3  # Should be moderately complex

    def test_planner_adaptation_reasoning(self):
        """Test that adaptation reasoning is provided."""
        planner = PlannerAgent(log_reasoning=False)
        
        summary = {
            "campaigns": ["C1"],
            "overall_metrics": {
                "avg_ctr": 0.02,
                "avg_roas": 1.5,
                "total_spend": 500,
                "total_revenue": 750
            },
            "top_drops": {"roas_drop_campaigns": [], "ctr_drop_campaigns": []}
        }
        
        plan = planner.plan("Analyze", summary=summary)
        
        assert "adaptation_reasoning" in plan
        assert len(plan["adaptation_reasoning"]) > 0


if __name__ == '__main__':
    pytest.main([__file__, "-v"])
