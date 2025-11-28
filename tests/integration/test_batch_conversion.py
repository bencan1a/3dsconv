"""Integration tests for batch conversion functionality.

This module tests the complete batch conversion workflow, including
file discovery, output directory handling, and conversion of multiple files.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def test_ccis_path():
    """Get path to test CCIs or skip if not found.

    This fixture provides the path to the examples/test-ccis directory
    and skips the test if the directory doesn't exist.
    """
    test_ccis = Path(__file__).parent.parent.parent / "examples" / "test-ccis"
    if not test_ccis.exists():
        pytest.skip("Test CCI files not found")
    return test_ccis


class TestBatchConversionIntegration:
    """Integration tests for batch mode conversion."""

    @pytest.fixture
    def test_ccis_dir(self, test_ccis_path):
        """Get path to test CCI files directory."""
        return test_ccis_path

    def test_batch_mode_discovers_all_cci_files(self, test_ccis_dir, tmp_path):
        """Test that batch mode finds and converts all CCI files in a folder."""
        # Arrange
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Act
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(test_ccis_dir),
                "-o",
                str(output_dir),
                "--ignore-bad-hashes",
            ],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        assert "Done converting 6 out of 6 files" in result.stdout

        # Verify output files were created
        output_files = list(output_dir.glob("*.cia"))
        assert len(output_files) == 6

    def test_batch_mode_outputs_to_input_folder_by_default(self, test_ccis_path, tmp_path):
        """Test that batch mode outputs to input folder when --output is not specified."""
        # Arrange - Create test folder with CCI files
        batch_folder = tmp_path / "batch_input"
        batch_folder.mkdir()

        # Copy a test CCI file
        source_cci = test_ccis_path / "test-01-nocrypt.cci"
        dest_cci = batch_folder / "test-01-nocrypt.cci"
        dest_cci.write_bytes(source_cci.read_bytes())

        # Act
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder),
                "--ignore-bad-hashes",
            ],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        assert "Done converting 1 out of 1 files" in result.stdout

        # Verify output was created in input folder
        output_cia = batch_folder / "test-01-nocrypt.cia"
        assert output_cia.exists()

    def test_batch_mode_with_custom_output_directory(self, test_ccis_path, tmp_path):
        """Test batch mode with explicit --output directory."""
        # Arrange
        batch_folder = tmp_path / "batch_input"
        batch_folder.mkdir()
        output_folder = tmp_path / "custom_output"
        output_folder.mkdir()

        # Copy test CCI
        source_cci = test_ccis_path / "test-01-nocrypt.cci"
        dest_cci = batch_folder / "game.cci"
        dest_cci.write_bytes(source_cci.read_bytes())

        # Act
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder),
                "-o",
                str(output_folder),
                "--ignore-bad-hashes",
            ],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        output_cia = output_folder / "game.cia"
        assert output_cia.exists()

    def test_batch_mode_with_nonexistent_folder(self, tmp_path):
        """Test batch mode error handling for nonexistent folder."""
        # Arrange
        nonexistent = tmp_path / "nonexistent"

        # Act
        result = subprocess.run(
            [sys.executable, "-m", "dsconv", "--batch", str(nonexistent)],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 1
        assert "Batch folder not found" in result.stdout

    def test_batch_mode_with_file_not_directory(self, tmp_path):
        """Test batch mode error handling when path is a file not directory."""
        # Arrange
        file_path = tmp_path / "not_a_folder.txt"
        file_path.write_text("test")

        # Act
        result = subprocess.run(
            [sys.executable, "-m", "dsconv", "--batch", str(file_path)],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 1
        assert "Batch path is not a directory" in result.stdout

    def test_batch_mode_with_empty_folder(self, tmp_path):
        """Test batch mode with folder containing no CCI files."""
        # Arrange
        empty_folder = tmp_path / "empty"
        empty_folder.mkdir()

        # Act
        result = subprocess.run(
            [sys.executable, "-m", "dsconv", "--batch", str(empty_folder)],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        assert "No CCI files found" in result.stdout
        assert "Done converting 0 out of 0 files" in result.stdout

    def test_batch_mode_ignores_non_cci_files(self, test_ccis_path, tmp_path):
        """Test that batch mode ignores non-CCI files."""
        # Arrange
        batch_folder = tmp_path / "mixed"
        batch_folder.mkdir()

        # Create non-CCI files
        (batch_folder / "readme.txt").write_text("test")
        (batch_folder / "data.bin").write_bytes(b"test")
        (batch_folder / "output.cia").write_bytes(b"test")

        # Copy a test CCI
        source_cci = test_ccis_path / "test-01-nocrypt.cci"
        dest_cci = batch_folder / "game.cci"
        dest_cci.write_bytes(source_cci.read_bytes())

        # Act
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder),
                "--ignore-bad-hashes",
            ],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        assert "Done converting 1 out of 1 files" in result.stdout

    def test_batch_mode_handles_3ds_extension(self, test_ccis_path, tmp_path):
        """Test that batch mode handles .3ds files."""
        # Arrange
        batch_folder = tmp_path / "batch_3ds"
        batch_folder.mkdir()

        # Copy test CCI as .3ds
        source_cci = test_ccis_path / "test-01-nocrypt.cci"
        dest_3ds = batch_folder / "game.3ds"
        dest_3ds.write_bytes(source_cci.read_bytes())

        # Act
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder),
                "--ignore-bad-hashes",
            ],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        assert "Done converting 1 out of 1 files" in result.stdout

    def test_batch_mode_continues_on_conversion_error(self, test_ccis_path, tmp_path):
        """Test that batch mode continues processing after a failed conversion."""
        # Arrange
        batch_folder = tmp_path / "batch_with_errors"
        batch_folder.mkdir()

        # Create an invalid CCI file
        invalid_cci = batch_folder / "invalid.cci"
        invalid_cci.write_bytes(b"NOT A VALID CCI FILE")

        # Copy a valid test CCI
        source_cci = test_ccis_path / "test-01-nocrypt.cci"
        valid_cci = batch_folder / "valid.cci"
        valid_cci.write_bytes(source_cci.read_bytes())

        # Act
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder),
                "--ignore-bad-hashes",
            ],
            capture_output=True,
            text=True,
        )

        # Assert - Should continue and convert the valid file
        assert result.returncode == 0
        assert "[FAILED]" in result.stdout or "Error:" in result.stdout
        # At least the valid file should be converted
        output_files = list(batch_folder.glob("*.cia"))
        assert len(output_files) >= 1


@pytest.mark.integration
class TestBatchModeWithOptions:
    """Integration tests for batch mode combined with other CLI options."""

    @pytest.fixture
    def batch_folder_with_cci(self, test_ccis_path, tmp_path):
        """Create a batch folder with a test CCI file."""
        batch_folder = tmp_path / "batch"
        batch_folder.mkdir()

        source_cci = test_ccis_path / "test-01-nocrypt.cci"
        dest_cci = batch_folder / "test.cci"
        dest_cci.write_bytes(source_cci.read_bytes())

        return batch_folder

    def test_batch_mode_with_verbose_flag(self, batch_folder_with_cci):
        """Test batch mode with verbose output."""
        # Act
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder_with_cci),
                "--verbose",
                "--ignore-bad-hashes",
            ],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        assert "Done converting 1 out of 1 files" in result.stdout

    def test_batch_mode_with_overwrite_flag(self, batch_folder_with_cci):
        """Test batch mode with overwrite flag."""
        # Arrange - First run to create output
        subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder_with_cci),
                "--ignore-bad-hashes",
            ],
            capture_output=True,
        )

        # Act - Second run with overwrite
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder_with_cci),
                "--overwrite",
                "--ignore-bad-hashes",
            ],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 0
        assert "Done converting 1 out of 1 files" in result.stdout


class TestBatchLegacyIncompatibility:
    """Tests for --batch and --legacy incompatibility."""

    def test_batch_with_legacy_flag_shows_error(self, tmp_path):
        """Test that combining --batch with --legacy shows a clear error."""
        # Arrange
        batch_folder = tmp_path / "batch"
        batch_folder.mkdir()

        # Act
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder),
                "--legacy",
            ],
            capture_output=True,
            text=True,
        )

        # Assert
        assert result.returncode == 1
        assert "--batch is not supported with --legacy" in result.stdout
