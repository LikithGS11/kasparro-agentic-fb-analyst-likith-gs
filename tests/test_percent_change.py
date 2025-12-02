"""
Unit tests for percent_change() function and safety utilities.
Tests edge cases and division-by-zero scenarios.
"""

import pytest
from src.utils.helpers import percent_change


class TestPercentChange:
    """Test suite for percent_change function."""

    def test_normal_increase(self):
        """Test normal percentage increase."""
        result = percent_change(100, 50)
        assert result == 1.0  # 100% increase

    def test_normal_decrease(self):
        """Test normal percentage decrease."""
        result = percent_change(50, 100)
        assert result == -0.5  # 50% decrease

    def test_no_change(self):
        """Test when current equals previous."""
        result = percent_change(100, 100)
        assert result == 0.0

    def test_zero_to_zero(self):
        """Test both values are zero (edge case)."""
        result = percent_change(0, 0)
        assert result == 0.0

    def test_division_by_zero(self):
        """Test when previous is zero (division by zero)."""
        result = percent_change(100, 0)
        assert result == 0.0  # Should return default

    def test_division_by_zero_with_custom_default(self):
        """Test division by zero with custom default."""
        result = percent_change(100, 0, default=-1.0)
        assert result == -1.0

    def test_small_positive_change(self):
        """Test small positive change."""
        result = percent_change(105, 100)
        assert result == pytest.approx(0.05)  # 5% increase

    def test_small_negative_change(self):
        """Test small negative change."""
        result = percent_change(95, 100)
        assert result == pytest.approx(-0.05)  # 5% decrease

    def test_negative_to_positive(self):
        """Test change from negative to positive."""
        result = percent_change(50, -100)
        assert result == pytest.approx(-0.5)  # 50% decrease (in absolute terms)

    def test_positive_to_negative(self):
        """Test change from positive to negative."""
        result = percent_change(-50, 100)
        assert result == pytest.approx(-1.5)  # 150% decrease

    def test_none_current(self):
        """Test when current is None."""
        result = percent_change(None, 100)
        assert result == 0.0

    def test_none_previous(self):
        """Test when previous is None."""
        result = percent_change(100, None)
        assert result == 0.0

    def test_both_none(self):
        """Test when both are None."""
        result = percent_change(None, None)
        assert result == 0.0

    def test_string_inputs(self):
        """Test with string inputs (should return default)."""
        result = percent_change("100", "50")
        assert result == 0.0

    def test_mixed_types(self):
        """Test with mixed numeric types."""
        result = percent_change(100.5, 50)
        assert result == pytest.approx(1.01)  # 101% increase

    def test_very_small_values(self):
        """Test with very small decimal values."""
        result = percent_change(0.0005, 0.0001)
        assert result == pytest.approx(4.0)  # 400% increase

    def test_very_large_values(self):
        """Test with very large values."""
        result = percent_change(1_000_000, 500_000)
        assert result == pytest.approx(1.0)  # 100% increase

    def test_negative_default(self):
        """Test division by zero with negative default."""
        result = percent_change(50, 0, default=-99.0)
        assert result == -99.0

    def test_fractional_change(self):
        """Test fractional percentage change."""
        result = percent_change(100.1, 100)
        assert result == pytest.approx(0.001)  # 0.1% increase

    def test_absolute_value_used_in_denominator(self):
        """Test that absolute value is used for denominator."""
        # (current - previous) / abs(previous)
        result1 = percent_change(0, -100)
        result2 = percent_change(0, 100)
        assert result1 == pytest.approx(1.0)
        assert result2 == pytest.approx(-1.0)


class TestPercentChangeWithDefaults:
    """Test percent_change with different default values."""

    def test_default_zero(self):
        """Test with default=0."""
        result = percent_change(100, 0, default=0.0)
        assert result == 0.0

    def test_default_infinity_symbol(self):
        """Test with special marker for undefined."""
        result = percent_change(100, 0, default=-999.0)
        assert result == -999.0

    def test_default_preserves_zero_zero_case(self):
        """Test that 0/0 returns 0 regardless of default."""
        result = percent_change(0, 0, default=100.0)
        assert result == 0.0  # Should return 0, not default


class TestPercentChangeRealWorldScenarios:
    """Test real-world advertising metrics scenarios."""

    def test_roas_drop(self):
        """Test ROAS drop scenario."""
        # ROAS dropped from 2.5 to 2.1
        result = percent_change(2.1, 2.5)
        assert result == pytest.approx(-0.16)  # 16% drop

    def test_ctr_drop(self):
        """Test CTR drop scenario."""
        # CTR dropped from 3.5% to 2.8%
        result = percent_change(2.8, 3.5)
        assert result == pytest.approx(-0.2)  # 20% drop

    def test_spend_increase(self):
        """Test spend increase scenario."""
        # Spend increased from $1000 to $1500
        result = percent_change(1500, 1000)
        assert result == 0.5  # 50% increase

    def test_zero_roas_previous_period(self):
        """Test when previous ROAS was zero (new campaign)."""
        result = percent_change(1.5, 0)
        assert result == 0.0  # Undefined, returns default

    def test_campaigns_with_no_drops(self):
        """Test scenario where metrics haven't changed."""
        result = percent_change(0.02, 0.02)
        assert result == 0.0


if __name__ == '__main__':
    pytest.main([__file__, "-v"])
