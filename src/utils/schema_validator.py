"""
Schema validation and governance for V2 outputs.
Ensures insights.json and creatives.json conform to versioned schemas.
"""

import json
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# SCHEMA DEFINITIONS - VERSION 2.0
# ============================================================================

INSIGHTS_SCHEMA_V2 = {
    "type": "object",
    "required": ["insights", "schema_version"],
    "properties": {
        "insights": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["hypothesis", "evidence", "expected_impact", "confidence", "schema_version"],
                "properties": {
                    "hypothesis": {"type": "string"},
                    "evidence": {
                        "type": "object",
                        "required": ["baseline_value", "current_value", "absolute_delta", "relative_delta", "diagnosis"],
                        "properties": {
                            "baseline_value": {"type": "number"},
                            "current_value": {"type": "number"},
                            "absolute_delta": {"type": "number"},
                            "relative_delta": {"type": "number"},
                            "diagnosis": {"type": "string"}
                        }
                    },
                    "expected_impact": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "confidence_level": {"type": "string", "enum": ["low", "moderate", "high"]},
                    "analysis_type": {"type": "string"},
                    "schema_version": {"type": "string", "const": "2.0"}
                }
            }
        },
        "schema_version": {"type": "string", "const": "2.0"}
    }
}

CREATIVES_SCHEMA_V2 = {
    "type": "object",
    "required": ["creatives", "schema_version"],
    "properties": {
        "creatives": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["campaign", "issue", "diagnosis", "recommended_headlines", "recommended_messages", "cta", "rationale", "schema_version"],
                "properties": {
                    "campaign": {"type": ["string", "null"]},
                    "issue": {"type": "string"},
                    "diagnosis": {"type": "string"},
                    "recommended_headlines": {"type": "array", "items": {"type": "string"}},
                    "recommended_messages": {"type": "array", "items": {"type": "string"}},
                    "cta": {"type": ["string", "null"]},
                    "rationale": {"type": "string"},
                    "schema_version": {"type": "string", "const": "2.0"}
                }
            }
        },
        "schema_version": {"type": "string", "const": "2.0"}
    }
}


# ============================================================================
# SCHEMA VALIDATOR
# ============================================================================

class SchemaValidator:
    """Validates output JSON against versioned schemas."""

    def validate_insights(self, insights_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate insights dict against schema v2.0.
        
        Args:
            insights_dict: Insights JSON object
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Top-level validation
        if not isinstance(insights_dict, dict):
            errors.append("Root must be a dictionary")
            return False, errors
        
        if "insights" not in insights_dict:
            errors.append("Missing required field: 'insights'")
        
        if "schema_version" not in insights_dict:
            errors.append("Missing required field: 'schema_version'")
        elif insights_dict["schema_version"] != "2.0":
            errors.append(f"Invalid schema_version: {insights_dict['schema_version']}. Expected '2.0'")
        
        # Validate insights array
        if "insights" in insights_dict:
            insights = insights_dict["insights"]
            if not isinstance(insights, list):
                errors.append("'insights' must be an array")
                return False, errors
            
            for idx, insight in enumerate(insights):
                if not isinstance(insight, dict):
                    errors.append(f"Insight[{idx}] must be a dictionary")
                    continue
                
                # Required fields
                required_fields = ["hypothesis", "evidence", "expected_impact", "confidence", "schema_version"]
                for field in required_fields:
                    if field not in insight:
                        errors.append(f"Insight[{idx}] missing required field: '{field}'")
                
                # Type validation
                if "hypothesis" in insight and not isinstance(insight["hypothesis"], str):
                    errors.append(f"Insight[{idx}].hypothesis must be a string")
                
                if "evidence" in insight and not isinstance(insight["evidence"], dict):
                    errors.append(f"Insight[{idx}].evidence must be a dictionary")
                
                if "confidence" in insight:
                    conf = insight["confidence"]
                    if not isinstance(conf, (int, float)):
                        errors.append(f"Insight[{idx}].confidence must be a number")
                    elif not (0 <= conf <= 1):
                        errors.append(f"Insight[{idx}].confidence must be between 0 and 1, got {conf}")
                
                if "schema_version" in insight and insight["schema_version"] != "2.0":
                    errors.append(f"Insight[{idx}].schema_version must be '2.0'")
        
        return len(errors) == 0, errors

    def validate_creatives(self, creatives_dict: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate creatives dict against schema v2.0.
        
        Args:
            creatives_dict: Creatives JSON object
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Top-level validation
        if not isinstance(creatives_dict, dict):
            errors.append("Root must be a dictionary")
            return False, errors
        
        if "creatives" not in creatives_dict:
            errors.append("Missing required field: 'creatives'")
        
        if "schema_version" not in creatives_dict:
            errors.append("Missing required field: 'schema_version'")
        elif creatives_dict["schema_version"] != "2.0":
            errors.append(f"Invalid schema_version: {creatives_dict['schema_version']}. Expected '2.0'")
        
        # Validate creatives array
        if "creatives" in creatives_dict:
            creatives = creatives_dict["creatives"]
            if not isinstance(creatives, list):
                errors.append("'creatives' must be an array")
                return False, errors
            
            for idx, creative in enumerate(creatives):
                if not isinstance(creative, dict):
                    errors.append(f"Creative[{idx}] must be a dictionary")
                    continue
                
                # Required fields
                required_fields = ["campaign", "issue", "recommended_headlines", "recommended_messages", "cta", "schema_version"]
                for field in required_fields:
                    if field not in creative:
                        errors.append(f"Creative[{idx}] missing required field: '{field}'")
                
                # Type validation
                if "recommended_headlines" in creative:
                    if not isinstance(creative["recommended_headlines"], list):
                        errors.append(f"Creative[{idx}].recommended_headlines must be an array")
                    else:
                        for jdx, h in enumerate(creative["recommended_headlines"]):
                            if not isinstance(h, str):
                                errors.append(f"Creative[{idx}].recommended_headlines[{jdx}] must be a string")
                
                if "recommended_messages" in creative:
                    if not isinstance(creative["recommended_messages"], list):
                        errors.append(f"Creative[{idx}].recommended_messages must be an array")
                    else:
                        for jdx, m in enumerate(creative["recommended_messages"]):
                            if not isinstance(m, str):
                                errors.append(f"Creative[{idx}].recommended_messages[{jdx}] must be a string")
                
                if "schema_version" in creative and creative["schema_version"] != "2.0":
                    errors.append(f"Creative[{idx}].schema_version must be '2.0'")
        
        return len(errors) == 0, errors


# ============================================================================
# SCHEMA UPGRADE UTILITY
# ============================================================================

def upgrade_insights_to_v2(old_insights: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upgrade insights from V1 to V2 schema.
    
    Args:
        old_insights: V1 format insights dict
    
    Returns:
        V2 format insights dict
    """
    upgraded = {
        "insights": [],
        "schema_version": "2.0"
    }
    
    for insight in old_insights.get("insights", []):
        upgraded_insight = {
            "hypothesis": insight.get("hypothesis", ""),
            "evidence": insight.get("evidence", {}),
            "expected_impact": insight.get("expected_impact", "Unknown"),
            "confidence": insight.get("confidence_estimate", 0.5),  # V1 used confidence_estimate
            "confidence_level": (
                "high" if insight.get("confidence_estimate", 0.5) > 0.7 else
                "moderate" if insight.get("confidence_estimate", 0.5) > 0.5 else
                "low"
            ),
            "analysis_type": "legacy_v1_conversion",
            "schema_version": "2.0"
        }
        upgraded["insights"].append(upgraded_insight)
    
    return upgraded


def upgrade_creatives_to_v2(old_creatives: Dict[str, Any]) -> Dict[str, Any]:
    """
    Upgrade creatives from V1 to V2 schema.
    
    Args:
        old_creatives: V1 format creatives dict
    
    Returns:
        V2 format creatives dict
    """
    upgraded = {
        "creatives": [],
        "schema_version": "2.0"
    }
    
    for creative in old_creatives.get("creatives", []):
        upgraded_creative = {
            "campaign": creative.get("campaign"),
            "issue": creative.get("issue", "Unknown"),
            "recommended_headlines": creative.get("recommended_headlines", []),
            "recommended_messages": creative.get("recommended_messages", []),
            "cta": creative.get("cta"),
            "schema_version": "2.0"
        }
        upgraded["creatives"].append(upgraded_creative)
    
    return upgraded


if __name__ == '__main__':
    # Test validator
    validator = SchemaValidator()
    
    # Test valid insights
    test_insights = {
        "insights": [
            {
                "hypothesis": "Test hypothesis",
                "evidence": {"key": "value"},
                "expected_impact": "High",
                "confidence": 0.8,
                "confidence_level": "high",
                "schema_version": "2.0"
            }
        ],
        "schema_version": "2.0"
    }
    
    is_valid, errors = validator.validate_insights(test_insights)
    print(f"Valid: {is_valid}, Errors: {errors}")
    
    # Test schema upgrade
    v1_insights = {
        "insights": [
            {
                "hypothesis": "Old insight",
                "evidence": {},
                "expected_impact": "High",
                "confidence_estimate": 0.7
            }
        ]
    }
    
    v2_insights = upgrade_insights_to_v2(v1_insights)
    is_valid, errors = validator.validate_insights(v2_insights)
    print(f"Upgraded - Valid: {is_valid}, Errors: {errors}")
