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


def get_test_cci_files() -> list[tuple[str, Path, Path]]:
    """
    Find all CCI test files in examples/test-ccis and their corresponding CIA files.

    Returns:
        List of tuples: (test_name, cci_path, canonical_cia_path)
    """
    project_root = Path(__file__).parent.parent.parent
    test_ccis_dir = project_root / "examples" / "test-ccis"

    if not test_ccis_dir.exists():
        return []

    test_cases = []
    for cci_file in sorted(test_ccis_dir.glob("*.cci")):
        # Find corresponding CIA file
        cia_file = cci_file.with_suffix(".cia")
        if cia_file.exists():
            test_name = cci_file.stem  # e.g., "test-01-nocrypt"
            test_cases.append((test_name, cci_file, cia_file))

    return test_cases


class TestPipelineValidation:
    """End-to-end validation tests for the conversion pipeline."""

    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.parametrize("test_name,input_cci,canonical_cia", get_test_cci_files())
    def test_cci_conversion_matches_canonical(self, test_name, input_cci, canonical_cia, tmp_path):
        """
        Test that converting a CCI file produces output identical to canonical CIA.

        This test validates the entire conversion pipeline by:
        1. Running a CCI file through dsconv
        2. Comparing the output with the canonical CIA using SHA256 hash
        3. Cleaning up on success, preserving output on failure for debugging

        The test is parameterized to run against all CCI files in examples/test-ccis,
        covering various encryption modes and configurations.

        Args:
            test_name: Name of the test case (e.g., "test-01-nocrypt")
            input_cci: Path to the input CCI file
            canonical_cia: Path to the canonical CIA file
            tmp_path: Pytest fixture for temporary directory
        """
        # Arrange
        project_root = Path(__file__).parent.parent.parent

        # Verify test inputs exist (should always pass due to get_test_cci_files filter)
        assert input_cci.exists(), f"Test input not found: {input_cci}"
        assert canonical_cia.exists(), f"Canonical output not found: {canonical_cia}"

        # Create test output directory
        output_dir = tmp_path / "test_outputs"
        output_dir.mkdir()
        output_cia = output_dir / canonical_cia.name

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
                f"Conversion output does not match canonical CIA for test: {test_name}\n"
                f"Input CCI:        {input_cci.name}\n"
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
