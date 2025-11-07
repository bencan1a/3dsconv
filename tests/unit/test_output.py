"""
Unit tests for output utility functions in 3dsconv.

This module tests the output and display functions, including error messages
and progress bars. Tests for verbose output functions (print_v, v) are not included
in Phase 1 as they depend on global state and will be addressed in later refactoring.
"""

import pytest

from dsconv.utils import error, show_progress


class TestError:
    """Test suite for the error() function."""

    def test_error_prints_with_prefix(self, capsys):
        """Test that error() prints messages with 'Error:' prefix."""
        # Act
        error("Something went wrong")
        
        # Assert
        captured = capsys.readouterr()
        assert "Error: Something went wrong" in captured.out

    def test_error_prints_multiple_args(self, capsys):
        """Test that error() can print multiple arguments."""
        # Act
        error("File", "not", "found")
        
        # Assert
        captured = capsys.readouterr()
        assert "Error: File not found" in captured.out

    def test_error_prints_empty_message(self, capsys):
        """Test that error() can be called with no message."""
        # Act
        error()
        
        # Assert
        captured = capsys.readouterr()
        assert "Error:" in captured.out


class TestShowProgress:
    """Test suite for the show_progress() function."""

    def test_show_progress_formatting(self, capsys):
        """Test that show_progress() formats output correctly."""
        # Act
        show_progress(500, 1000)
        
        # Assert
        captured = capsys.readouterr()
        output = captured.out
        # Should contain percentage and values
        assert "50.0%" in output
        assert "500" in output
        assert "1000" in output

    def test_show_progress_zero_percent(self, capsys):
        """Test show_progress() with 0% progress."""
        # Act
        show_progress(0, 1000)
        
        # Assert
        captured = capsys.readouterr()
        output = captured.out
        assert "0.0%" in output or "0%" in output

    def test_show_progress_hundred_percent(self, capsys):
        """Test show_progress() with 100% progress."""
        # Act
        show_progress(1000, 1000)
        
        # Assert
        captured = capsys.readouterr()
        output = captured.out
        assert "100.0%" in output

    def test_show_progress_exceeds_max(self, capsys):
        """Test show_progress() when value exceeds max (should clamp to max)."""
        # Act
        show_progress(1500, 1000)
        
        # Assert
        captured = capsys.readouterr()
        output = captured.out
        # Should use min(val, maxval) so 100%
        assert "100.0%" in output
        assert "1000" in output  # Should show maxval twice

    def test_show_progress_partial_percent(self, capsys):
        """Test show_progress() with a partial percentage."""
        # Act
        show_progress(333, 1000)
        
        # Assert
        captured = capsys.readouterr()
        output = captured.out
        assert "33.3%" in output

    @pytest.mark.parametrize("val,maxval,expected_percent", [
        (0, 100, "0.0%"),
        (25, 100, "25.0%"),
        (50, 100, "50.0%"),
        (75, 100, "75.0%"),
        (100, 100, "100.0%"),
    ])
    def test_show_progress_various_percentages(self, capsys, val, maxval, expected_percent):
        """Test show_progress() with various percentages."""
        # Act
        show_progress(val, maxval)
        
        # Assert
        captured = capsys.readouterr()
        assert expected_percent in captured.out


# Note: Tests for print_v() and v() are deferred to Phase 2 as they depend on
# global state (args.verbose) that requires more extensive refactoring to test properly.
# The Test-Automation-Plan.md acknowledges this as a known issue with the current codebase.

