"""Tests for progress reporter interfaces and implementations."""

import io
from unittest.mock import patch

import pytest

from dsconv.services.progress_reporter import (
    ConsoleProgressReporter,
    IProgressReporter,
    MockProgressReporter,
)


class TestIProgressReporter:
    """Tests for IProgressReporter interface."""

    def test_is_abstract_base_class(self):
        """Test that IProgressReporter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IProgressReporter()  # type: ignore[abstract]

    def test_has_report_stage_abstract_method(self):
        """Test that report_stage method is abstract."""
        assert hasattr(IProgressReporter, "report_stage")
        assert getattr(IProgressReporter.report_stage, "__isabstractmethod__", False)

    def test_has_report_progress_abstract_method(self):
        """Test that report_progress method is abstract."""
        assert hasattr(IProgressReporter, "report_progress")
        assert getattr(IProgressReporter.report_progress, "__isabstractmethod__", False)


class TestConsoleProgressReporter:
    """Tests for ConsoleProgressReporter implementation."""

    def test_create_with_default_verbose(self):
        """Test creating reporter with default verbose=False."""
        reporter = ConsoleProgressReporter()
        assert reporter.verbose is False

    def test_create_with_verbose_true(self):
        """Test creating reporter with verbose=True."""
        reporter = ConsoleProgressReporter(verbose=True)
        assert reporter.verbose is True

    def test_create_with_verbose_false(self):
        """Test creating reporter with explicit verbose=False."""
        reporter = ConsoleProgressReporter(verbose=False)
        assert reporter.verbose is False

    def test_implements_iprogress_reporter_interface(self):
        """Test that ConsoleProgressReporter implements IProgressReporter."""
        reporter = ConsoleProgressReporter()
        assert isinstance(reporter, IProgressReporter)

    def test_has_report_stage_method(self):
        """Test that reporter has report_stage method."""
        reporter = ConsoleProgressReporter()
        assert hasattr(reporter, "report_stage")
        assert callable(reporter.report_stage)

    def test_has_report_progress_method(self):
        """Test that reporter has report_progress method."""
        reporter = ConsoleProgressReporter()
        assert hasattr(reporter, "report_progress")
        assert callable(reporter.report_progress)

    def test_report_stage_with_verbose_true_prints_message(self):
        """Test report_stage prints message when verbose=True."""
        reporter = ConsoleProgressReporter(verbose=True)
        captured_output = io.StringIO()

        with patch("sys.stdout", captured_output):
            reporter.report_stage("Test Stage")

        output = captured_output.getvalue()
        assert "Test Stage..." in output

    def test_report_stage_with_verbose_false_does_not_print(self):
        """Test report_stage does not print when verbose=False."""
        reporter = ConsoleProgressReporter(verbose=False)
        captured_output = io.StringIO()

        with patch("sys.stdout", captured_output):
            reporter.report_stage("Test Stage")

        output = captured_output.getvalue()
        assert output == ""

    def test_report_stage_with_empty_string(self):
        """Test report_stage with empty string."""
        reporter = ConsoleProgressReporter(verbose=True)
        captured_output = io.StringIO()

        with patch("sys.stdout", captured_output):
            reporter.report_stage("")

        output = captured_output.getvalue()
        assert "..." in output

    def test_report_stage_with_multiline_string(self):
        """Test report_stage with multiline string."""
        reporter = ConsoleProgressReporter(verbose=True)
        captured_output = io.StringIO()

        with patch("sys.stdout", captured_output):
            reporter.report_stage("Line 1\nLine 2")

        output = captured_output.getvalue()
        assert "Line 1\nLine 2..." in output

    def test_report_stage_starts_with_newline_when_verbose(self):
        """Test report_stage output starts with newline when verbose=True."""
        reporter = ConsoleProgressReporter(verbose=True)
        captured_output = io.StringIO()

        with patch("sys.stdout", captured_output):
            reporter.report_stage("Test")

        output = captured_output.getvalue()
        assert output.startswith("\n")

    @patch("dsconv.utils.show_progress")
    def test_report_progress_calls_show_progress(self, mock_show_progress):
        """Test report_progress calls show_progress utility."""
        reporter = ConsoleProgressReporter()
        reporter.report_progress(50, 100)

        mock_show_progress.assert_called_once_with(50, 100)

    @patch("dsconv.utils.show_progress")
    def test_report_progress_with_zero_current(self, mock_show_progress):
        """Test report_progress with current=0."""
        reporter = ConsoleProgressReporter()
        reporter.report_progress(0, 100)

        mock_show_progress.assert_called_once_with(0, 100)

    @patch("dsconv.utils.show_progress")
    def test_report_progress_with_equal_current_and_total(self, mock_show_progress):
        """Test report_progress when current equals total."""
        reporter = ConsoleProgressReporter()
        reporter.report_progress(100, 100)

        mock_show_progress.assert_called_once_with(100, 100)

    @patch("dsconv.utils.show_progress")
    def test_report_progress_with_large_values(self, mock_show_progress):
        """Test report_progress with large values."""
        reporter = ConsoleProgressReporter()
        reporter.report_progress(1000000, 5000000)

        mock_show_progress.assert_called_once_with(1000000, 5000000)

    @patch("dsconv.utils.show_progress")
    def test_report_progress_multiple_calls(self, mock_show_progress):
        """Test multiple calls to report_progress."""
        reporter = ConsoleProgressReporter()
        reporter.report_progress(10, 100)
        reporter.report_progress(50, 100)
        reporter.report_progress(100, 100)

        assert mock_show_progress.call_count == 3
        calls = mock_show_progress.call_args_list
        assert calls[0][0] == (10, 100)
        assert calls[1][0] == (50, 100)
        assert calls[2][0] == (100, 100)

    @patch("dsconv.utils.show_progress")
    def test_report_progress_verbose_does_not_affect_behavior(self, mock_show_progress):
        """Test report_progress works same with verbose True or False."""
        reporter_verbose = ConsoleProgressReporter(verbose=True)
        reporter_quiet = ConsoleProgressReporter(verbose=False)

        reporter_verbose.report_progress(50, 100)
        reporter_quiet.report_progress(50, 100)

        assert mock_show_progress.call_count == 2

    def test_multiple_stage_reports_with_verbose_true(self):
        """Test multiple stage reports when verbose=True."""
        reporter = ConsoleProgressReporter(verbose=True)
        captured_output = io.StringIO()

        with patch("sys.stdout", captured_output):
            reporter.report_stage("Stage 1")
            reporter.report_stage("Stage 2")
            reporter.report_stage("Stage 3")

        output = captured_output.getvalue()
        assert "Stage 1..." in output
        assert "Stage 2..." in output
        assert "Stage 3..." in output


class TestMockProgressReporter:
    """Tests for MockProgressReporter implementation."""

    def test_create_mock_reporter(self):
        """Test creating MockProgressReporter."""
        reporter = MockProgressReporter()
        assert isinstance(reporter, MockProgressReporter)

    def test_implements_iprogress_reporter_interface(self):
        """Test that MockProgressReporter implements IProgressReporter."""
        reporter = MockProgressReporter()
        assert isinstance(reporter, IProgressReporter)

    def test_initial_state_empty_stages(self):
        """Test initial state has empty stages list."""
        reporter = MockProgressReporter()
        assert reporter.stages == []

    def test_initial_state_empty_progress_calls(self):
        """Test initial state has empty progress_calls list."""
        reporter = MockProgressReporter()
        assert reporter.progress_calls == []

    def test_initial_state_zero_stage_call_count(self):
        """Test initial state has zero stage_call_count."""
        reporter = MockProgressReporter()
        assert reporter.stage_call_count == 0

    def test_initial_state_zero_progress_call_count(self):
        """Test initial state has zero progress_call_count."""
        reporter = MockProgressReporter()
        assert reporter.progress_call_count == 0

    def test_report_stage_records_stage(self):
        """Test report_stage records the stage."""
        reporter = MockProgressReporter()
        reporter.report_stage("Test Stage")

        assert "Test Stage" in reporter.stages
        assert len(reporter.stages) == 1

    def test_report_stage_increments_call_count(self):
        """Test report_stage increments stage_call_count."""
        reporter = MockProgressReporter()
        reporter.report_stage("Test Stage")

        assert reporter.stage_call_count == 1

    def test_report_stage_multiple_calls(self):
        """Test multiple calls to report_stage."""
        reporter = MockProgressReporter()
        reporter.report_stage("Stage 1")
        reporter.report_stage("Stage 2")
        reporter.report_stage("Stage 3")

        assert reporter.stages == ["Stage 1", "Stage 2", "Stage 3"]
        assert reporter.stage_call_count == 3

    def test_report_stage_with_empty_string(self):
        """Test report_stage with empty string."""
        reporter = MockProgressReporter()
        reporter.report_stage("")

        assert "" in reporter.stages
        assert reporter.stage_call_count == 1

    def test_report_stage_preserves_order(self):
        """Test report_stage preserves order of stages."""
        reporter = MockProgressReporter()
        stages = ["First", "Second", "Third", "Fourth"]

        for stage in stages:
            reporter.report_stage(stage)

        assert reporter.stages == stages

    def test_report_progress_records_call(self):
        """Test report_progress records the call."""
        reporter = MockProgressReporter()
        reporter.report_progress(50, 100)

        assert (50, 100) in reporter.progress_calls
        assert len(reporter.progress_calls) == 1

    def test_report_progress_increments_call_count(self):
        """Test report_progress increments progress_call_count."""
        reporter = MockProgressReporter()
        reporter.report_progress(50, 100)

        assert reporter.progress_call_count == 1

    def test_report_progress_multiple_calls(self):
        """Test multiple calls to report_progress."""
        reporter = MockProgressReporter()
        reporter.report_progress(10, 100)
        reporter.report_progress(50, 100)
        reporter.report_progress(100, 100)

        assert reporter.progress_calls == [(10, 100), (50, 100), (100, 100)]
        assert reporter.progress_call_count == 3

    def test_report_progress_with_zero_values(self):
        """Test report_progress with zero values."""
        reporter = MockProgressReporter()
        reporter.report_progress(0, 0)

        assert (0, 0) in reporter.progress_calls
        assert reporter.progress_call_count == 1

    def test_report_progress_with_large_values(self):
        """Test report_progress with large values."""
        reporter = MockProgressReporter()
        reporter.report_progress(1000000, 5000000)

        assert (1000000, 5000000) in reporter.progress_calls

    def test_report_progress_preserves_order(self):
        """Test report_progress preserves order of calls."""
        reporter = MockProgressReporter()
        calls = [(10, 100), (20, 100), (30, 100), (40, 100)]

        for current, total in calls:
            reporter.report_progress(current, total)

        assert reporter.progress_calls == calls

    def test_mixed_stage_and_progress_calls(self):
        """Test mixed calls to report_stage and report_progress."""
        reporter = MockProgressReporter()

        reporter.report_stage("Stage 1")
        reporter.report_progress(10, 100)
        reporter.report_stage("Stage 2")
        reporter.report_progress(50, 100)
        reporter.report_progress(100, 100)

        assert reporter.stages == ["Stage 1", "Stage 2"]
        assert reporter.progress_calls == [(10, 100), (50, 100), (100, 100)]
        assert reporter.stage_call_count == 2
        assert reporter.progress_call_count == 3

    def test_reset_clears_stages(self):
        """Test reset() clears stages list."""
        reporter = MockProgressReporter()
        reporter.report_stage("Test")
        reporter.reset()

        assert reporter.stages == []

    def test_reset_clears_progress_calls(self):
        """Test reset() clears progress_calls list."""
        reporter = MockProgressReporter()
        reporter.report_progress(50, 100)
        reporter.reset()

        assert reporter.progress_calls == []

    def test_reset_clears_stage_call_count(self):
        """Test reset() resets stage_call_count to 0."""
        reporter = MockProgressReporter()
        reporter.report_stage("Test")
        reporter.reset()

        assert reporter.stage_call_count == 0

    def test_reset_clears_progress_call_count(self):
        """Test reset() resets progress_call_count to 0."""
        reporter = MockProgressReporter()
        reporter.report_progress(50, 100)
        reporter.reset()

        assert reporter.progress_call_count == 0

    def test_reset_after_mixed_calls(self):
        """Test reset() clears all data after mixed calls."""
        reporter = MockProgressReporter()

        reporter.report_stage("Stage 1")
        reporter.report_progress(10, 100)
        reporter.report_stage("Stage 2")
        reporter.report_progress(50, 100)

        reporter.reset()

        assert reporter.stages == []
        assert reporter.progress_calls == []
        assert reporter.stage_call_count == 0
        assert reporter.progress_call_count == 0

    def test_use_after_reset(self):
        """Test reporter can be used normally after reset."""
        reporter = MockProgressReporter()

        # First use
        reporter.report_stage("Stage 1")
        reporter.report_progress(50, 100)

        # Reset
        reporter.reset()

        # Second use
        reporter.report_stage("Stage 2")
        reporter.report_progress(75, 100)

        assert reporter.stages == ["Stage 2"]
        assert reporter.progress_calls == [(75, 100)]
        assert reporter.stage_call_count == 1
        assert reporter.progress_call_count == 1

    def test_multiple_resets(self):
        """Test multiple reset calls."""
        reporter = MockProgressReporter()

        reporter.report_stage("Test")
        reporter.reset()
        reporter.reset()  # Second reset on empty state

        assert reporter.stages == []
        assert reporter.stage_call_count == 0

    def test_has_reset_method(self):
        """Test that MockProgressReporter has reset method."""
        reporter = MockProgressReporter()
        assert hasattr(reporter, "reset")
        assert callable(reporter.reset)

    def test_does_not_produce_output_on_report_stage(self):
        """Test that report_stage does not produce console output."""
        reporter = MockProgressReporter()
        captured_output = io.StringIO()

        with patch("sys.stdout", captured_output):
            reporter.report_stage("Test Stage")

        output = captured_output.getvalue()
        assert output == ""

    def test_does_not_produce_output_on_report_progress(self):
        """Test that report_progress does not produce console output."""
        reporter = MockProgressReporter()
        captured_output = io.StringIO()

        with patch("sys.stdout", captured_output):
            reporter.report_progress(50, 100)

        output = captured_output.getvalue()
        assert output == ""

    @pytest.mark.parametrize(
        "stage",
        [
            "Reading CCI structure",
            "Analyzing encryption",
            "Verifying ExtHeader",
            "Getting SMDH",
            "Writing CIA",
        ],
    )
    def test_report_stage_with_various_stages(self, stage):
        """Test report_stage with various stage descriptions."""
        reporter = MockProgressReporter()
        reporter.report_stage(stage)

        assert stage in reporter.stages
        assert reporter.stage_call_count == 1

    @pytest.mark.parametrize(
        "current,total",
        [
            (0, 100),
            (50, 100),
            (100, 100),
            (0, 1000000),
            (500000, 1000000),
            (1000000, 1000000),
        ],
    )
    def test_report_progress_with_various_values(self, current, total):
        """Test report_progress with various progress values."""
        reporter = MockProgressReporter()
        reporter.report_progress(current, total)

        assert (current, total) in reporter.progress_calls
        assert reporter.progress_call_count == 1
