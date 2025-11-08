"""
End-to-end validation tests for the 3dsconv conversion pipeline.

This module contains tests that verify the complete conversion pipeline by
running real CCI files through dsconv and validating the output matches
canonical reference files.
"""

import hashlib
import shutil
import subprocess
from pathlib import Path

import pytest


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file using streaming to handle large files efficiently.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string representation of the SHA256 hash
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


class TestPipelineValidation:
    """End-to-end validation tests for the conversion pipeline."""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_hello_cci_conversion_matches_canonical(self, tmp_path):
        """
        Test that converting hello.cci produces output identical to canonical hello.cia.

        This test validates the entire conversion pipeline by:
        1. Running hello.cci through dsconv
        2. Comparing the output byte-by-byte with the canonical hello.cia
        3. Cleaning up on success, preserving output on failure for debugging

        The hello.cci/hello.cia files serve as a canonical test case to ensure
        the conversion pipeline produces deterministic, correct output.
        """
        # Arrange
        project_root = Path(__file__).parent.parent.parent
        input_cci = project_root / "examples" / "hello.cci"
        canonical_cia = project_root / "examples" / "hello.cia"

        # Verify test inputs exist
        assert input_cci.exists(), f"Test input not found: {input_cci}"
        assert canonical_cia.exists(), f"Canonical output not found: {canonical_cia}"

        # Create test output directory
        output_dir = tmp_path / "test_outputs"
        output_dir.mkdir()
        output_cia = output_dir / "hello.cia"

        # Act
        # Run dsconv via subprocess to convert the CCI file
        result = subprocess.run(
            ["python", "-m", "dsconv", "-o", str(output_dir), str(input_cci)],
            cwd=str(project_root),
            capture_output=True,
            text=True,
        )

        # Assert - Check conversion succeeded
        assert result.returncode == 0, (
            f"Conversion failed with exit code {result.returncode}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Assert - Output file was created
        assert output_cia.exists(), (
            f"Output CIA file not created: {output_cia}\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

        # Assert - Compare output with canonical file using SHA256 hash
        output_hash = compute_sha256(output_cia)
        canonical_hash = compute_sha256(canonical_cia)

        # Provide detailed error message if hashes don't match
        if output_hash != canonical_hash:
            output_size = output_cia.stat().st_size
            canonical_size = canonical_cia.stat().st_size

            error_msg = (
                f"Output CIA does not match canonical CIA\n"
                f"Output SHA256:    {output_hash}\n"
                f"Canonical SHA256: {canonical_hash}\n"
                f"Output size:      {output_size:,} bytes\n"
                f"Canonical size:   {canonical_size:,} bytes\n"
                f"\nOutput preserved for debugging at: {output_cia}"
            )

            pytest.fail(error_msg)

        # Clean up on success
        # Note: On failure, pytest will preserve tmp_path automatically,
        # but we explicitly keep the file by not removing it above on failure
        shutil.rmtree(output_dir)

        # Success - files match exactly
        assert output_hash == canonical_hash
