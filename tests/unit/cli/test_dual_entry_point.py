"""Tests for dual entry point system (Task 7.2).

This module tests the dual-mode routing in __main__.py that allows
running both refactored and legacy implementations.
"""

import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestDualEntryPoint:
    """Tests for dsconv/__main__.py dual-mode routing."""

    def test_main_without_legacy_flag_uses_refactored(self):
        """Test that default mode (no --legacy flag) uses refactored implementation."""
        with patch("dsconv.cli.main.main") as mock_refactored:
            # Arrange
            import dsconv.__main__ as main_module

            # Mock sys.argv to not include --legacy
            with patch.object(sys, "argv", ["dsconv"]):
                # Act
                main_module.main()

                # Assert
                mock_refactored.assert_called_once()

    def test_main_with_legacy_flag_uses_legacy(self):
        """Test that --legacy flag triggers legacy implementation."""
        # Arrange
        import dsconv.__main__ as main_module

        # We can't easily mock exec(), so we'll test that the flag is removed from argv
        original_argv = sys.argv.copy()

        try:
            # Mock sys.argv with --legacy flag
            test_argv = ["dsconv", "--legacy", "--help"]
            with patch.object(sys, "argv", test_argv):
                # Since exec() runs the legacy code which calls sys.exit(0) on --help,
                # we expect a SystemExit
                with pytest.raises(SystemExit) as exc_info:
                    main_module.main()

                # The --help should have been processed by legacy code
                assert exc_info.value.code == 0
        finally:
            sys.argv = original_argv

    def test_main_with_use_legacy_flag_uses_legacy(self):
        """Test that --use-legacy flag also triggers legacy implementation."""
        # Arrange
        import dsconv.__main__ as main_module

        original_argv = sys.argv.copy()

        try:
            # Mock sys.argv with --use-legacy flag
            test_argv = ["dsconv", "--use-legacy", "--help"]
            with patch.object(sys, "argv", test_argv):
                # Expect SystemExit from --help
                with pytest.raises(SystemExit) as exc_info:
                    main_module.main()

                assert exc_info.value.code == 0
        finally:
            sys.argv = original_argv

    def test_legacy_flag_removed_from_argv_before_execution(self):
        """Test that --legacy flag is removed before delegating to legacy code."""
        # This test verifies that the flag is stripped so legacy parse_args doesn't fail
        import dsconv.__main__ as main_module

        original_argv = sys.argv.copy()

        try:
            # Create argv with --legacy flag
            test_argv = ["dsconv", "--legacy", "--help"]

            with patch.object(sys, "argv", test_argv):
                # The legacy implementation should process --help without seeing --legacy
                with pytest.raises(SystemExit) as exc_info:
                    main_module.main()

                # Should exit cleanly from --help
                assert exc_info.value.code == 0
        finally:
            sys.argv = original_argv


class TestRefactoredMain:
    """Tests for dsconv/cli/main.py entry point."""

    def test_main_parses_args(self):
        """Test that refactored main calls parse_args."""
        from dsconv.cli.main import main

        with patch("dsconv.cli.main.parse_args") as mock_parse:
            # Arrange - mock parse_args to return minimal valid args
            mock_args = MagicMock()
            mock_args.game = []  # Empty list means no files to process
            mock_args.batch = None  # No batch mode
            mock_args.use_deprecated = False
            mock_parse.return_value = mock_args

            # Act - should exit with error because no input files
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Assert
            mock_parse.assert_called_once()
            assert exc_info.value.code == 1

    def test_main_handles_deprecated_options(self):
        """Test that refactored main handles deprecated options gracefully."""
        from dsconv.cli.main import main

        with patch("dsconv.cli.main.parse_args") as mock_parse:
            # Arrange - mock args with use_deprecated flag
            mock_args = MagicMock()
            mock_args.use_deprecated = True
            mock_parse.return_value = mock_args

            # Act
            with patch("builtins.print") as mock_print:
                main()

            # Assert
            mock_print.assert_called()
            call_args = str(mock_print.call_args)
            assert "Deprecated" in call_args or "XORpads" in call_args

    def test_main_processes_multiple_files(self):
        """Test that refactored main processes multiple game files."""
        from dsconv.cli.main import main

        with patch("dsconv.cli.main.parse_args") as mock_parse:
            with patch("dsconv.cli.main.CLIConfigMapper") as mock_mapper:
                with patch("dsconv.cli.main.ServiceFactory") as mock_factory:
                    # Arrange
                    mock_args = MagicMock()
                    mock_args.game = ["game1.cci", "game2.cci"]
                    mock_args.batch = None
                    mock_args.use_deprecated = False
                    mock_parse.return_value = mock_args

                    mock_config = MagicMock()
                    mock_config.output_file = "output.cia"
                    mock_mapper.map_to_conversion_config.return_value = mock_config

                    mock_service = MagicMock()
                    mock_factory.create_conversion_service.return_value = mock_service

                    # Act
                    with patch("builtins.print"):
                        main()

                    # Assert - should process both files
                    assert mock_mapper.map_to_conversion_config.call_count == 2
                    assert mock_factory.create_conversion_service.call_count == 2
                    assert mock_service.convert.call_count == 2

    def test_main_handles_conversion_errors_gracefully(self):
        """Test that refactored main continues after conversion errors."""
        from dsconv.cli.main import main

        with patch("dsconv.cli.main.parse_args") as mock_parse:
            with patch("dsconv.cli.main.CLIConfigMapper") as mock_mapper:
                # Arrange
                mock_args = MagicMock()
                mock_args.game = ["game1.cci", "game2.cci"]
                mock_args.batch = None
                mock_args.use_deprecated = False
                mock_parse.return_value = mock_args

                # First file raises exception, second should still be processed
                mock_mapper.map_to_conversion_config.side_effect = [
                    Exception("Test error"),
                    MagicMock(output_file="game2.cia"),
                ]

                # Act
                with patch("builtins.print") as mock_print:
                    main()

                # Assert - error should be printed, and "Done converting 0 out of 2" message
                assert mock_print.call_count >= 2  # At least error message and final summary


class TestIntegration:
    """Integration tests for the dual entry point system."""

    def test_can_run_refactored_mode_with_help(self):
        """Test that refactored mode runs with --help."""
        result = subprocess.run(
            [sys.executable, "-m", "dsconv", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Convert Nintendo 3DS CCI" in result.stdout or "usage:" in result.stdout

    def test_can_run_legacy_mode_with_help(self):
        """Test that legacy mode runs with --legacy --help."""
        result = subprocess.run(
            [sys.executable, "-m", "dsconv", "--legacy", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Convert Nintendo 3DS CCI" in result.stdout or "usage:" in result.stdout

    def test_legacy_flag_not_in_help_output(self):
        """Test that --legacy is not shown as a valid argument in help."""
        result = subprocess.run(
            [sys.executable, "-m", "dsconv", "--help"],
            capture_output=True,
            text=True,
        )

        # The --legacy flag is internal to __main__.py routing,
        # not a documented argument
        assert "--legacy" not in result.stdout
