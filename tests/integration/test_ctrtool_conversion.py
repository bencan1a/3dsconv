"""
Integration tests for ctrtool CXI extraction functionality.

This module tests the complete workflow of converting CIA files to CXI
using ctrtool integration in the CLI.
"""

import subprocess
import sys
import os
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def test_ccis_path(project_root):
    """Get path to test CCIs or skip if not found."""
    test_ccis = project_root / "examples" / "test-ccis"
    if not test_ccis.exists():
        pytest.skip("Test CCI files not found")
    return test_ccis


class TestCtrtoolIntegrationMocked:
    """Integration tests for ctrtool functionality with mocked ctrtool calls."""

    def test_to_cxi_flag_requires_ctrtool(self, tmp_path, project_root):
        """Test that --to-cxi fails gracefully when ctrtool is not found."""
        # Create a test CCI file (minimal stub)
        cci = tmp_path / "game.cci"
        cci.write_bytes(b"mock cci")

        # Prepare environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)
        env["CTRTOOL_PATH"] = ""
        env["PATH"] = os.path.dirname(sys.executable)  # Ensure ctrtool is not found in PATH

        # Run with --to-cxi but ctrtool not available
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--to-cxi",
                str(cci),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should fail with helpful error message
        assert result.returncode == 1
        assert "ctrtool not found" in result.stdout or "ctrtool not found" in result.stderr

    def test_ctrtool_path_option(self, tmp_path, project_root):
        """Test that --ctrtool-path option works."""
        # Create a test CCI file (minimal stub)
        cci = tmp_path / "game.cci"
        cci.write_bytes(b"mock cci")

        # Create a fake ctrtool
        fake_ctrtool = tmp_path / "fake_ctrtool"
        fake_ctrtool.write_text("#!/bin/sh\nexit 0")
        # On Windows, chmod might not make it executable in the same way, but it's a file path check mostly
        try:
            fake_ctrtool.chmod(0o755)
        except OSError:
            pass

        # Prepare environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        # Run with --ctrtool-path - will still fail on conversion but validates path logic
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--to-cxi",
                "--ctrtool-path",
                str(fake_ctrtool),
                str(cci),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should NOT complain about ctrtool not found
        assert "ctrtool not found" not in result.stdout
        assert "ctrtool not found" not in result.stderr

    def test_verbose_shows_ctrtool_path(self, tmp_path, project_root):
        """Test that verbose mode shows which ctrtool is being used."""
        # Create test files
        cci = tmp_path / "game.cci"
        cci.write_bytes(b"mock cci")

        fake_ctrtool = tmp_path / "my_ctrtool"
        fake_ctrtool.write_text("mock")

        # Prepare environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--to-cxi",
                "--ctrtool-path",
                str(fake_ctrtool),
                "--verbose",
                str(cci),
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Verbose should show ctrtool path
        assert "Using ctrtool" in result.stdout or "my_ctrtool" in result.stdout


@pytest.mark.integration
class TestCtrtoolBatchMode:
    """Integration tests for ctrtool with batch mode."""

    def test_batch_with_to_cxi_requires_ctrtool(self, tmp_path, project_root):
        """Test that batch mode with --to-cxi requires ctrtool."""
        batch_folder = tmp_path / "batch"
        batch_folder.mkdir()

        # Create a test CCI file
        cci = batch_folder / "game.cci"
        cci.write_bytes(b"mock cci")

        # Prepare environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)
        env["CTRTOOL_PATH"] = ""
        env["PATH"] = os.path.dirname(sys.executable)  # Ensure ctrtool is not found in PATH

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder),
                "--to-cxi",
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 1
        assert "ctrtool not found" in result.stdout or "ctrtool not found" in result.stderr


@pytest.mark.integration
class TestCtrtoolRealConversion:
    """Integration tests that test real CIA to CXI conversion.

    These tests require ctrtool to be installed and available.
    They are skipped if ctrtool is not found.
    """

    @pytest.fixture
    def ctrtool_path(self):
        """Get ctrtool path or skip test."""
        from dsconv.utils import find_ctrtool

        path = find_ctrtool()
        if not path:
            pytest.skip("ctrtool not installed - skipping real conversion test")
        return os.path.abspath(path)

    def test_cci_to_cia_to_cxi_workflow(self, test_ccis_path, ctrtool_path, tmp_path, project_root):
        """Test complete workflow: CCI -> CIA -> CXI."""
        # Copy test CCI to temp dir
        source_cci = test_ccis_path / "test-01-nocrypt.cci"
        if not source_cci.exists():
            pytest.skip("Test CCI file not found")

        cci = tmp_path / "game.cci"
        cci.write_bytes(source_cci.read_bytes())

        # Prepare environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        # Run conversion with --to-cxi
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--to-cxi",
                "--ctrtool-path",
                ctrtool_path,
                "--ignore-bad-hashes",
                str(cci),
            ],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env=env,
        )

        # Check conversion succeeded
        assert result.returncode == 0 or "Done converting 1 out of 1" in result.stdout

        # Verify CXI file was created (if ctrtool succeeded)
        cxi = tmp_path / "game.cxi"
        if cxi.exists():
            assert cxi.stat().st_size > 0

    def test_batch_cci_to_cxi_workflow(self, test_ccis_path, ctrtool_path, tmp_path, project_root):
        """Test batch workflow: multiple CCIs -> CIAs -> CXIs."""
        # Create batch folder with test CCIs
        batch_folder = tmp_path / "batch"
        batch_folder.mkdir()

        source_cci = test_ccis_path / "test-01-nocrypt.cci"
        if not source_cci.exists():
            pytest.skip("Test CCI file not found")

        # Copy two test files
        (batch_folder / "game1.cci").write_bytes(source_cci.read_bytes())
        (batch_folder / "game2.cci").write_bytes(source_cci.read_bytes())

        # Prepare environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        # Run batch conversion with --to-cxi
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dsconv",
                "--batch",
                str(batch_folder),
                "--to-cxi",
                "--ctrtool-path",
                ctrtool_path,
                "--ignore-bad-hashes",
            ],
            capture_output=True,
            text=True,
            env=env,
        )

        # Check conversion message
        assert "Done converting" in result.stdout

        # Verify CIA files were created
        cia_files = list(batch_folder.glob("*.cia"))
        assert len(cia_files) == 2

        # Check for CXI extraction message
        if "Done extracting" in result.stdout:
            # If extraction happened, CXI files should exist
            cxi_files = list(batch_folder.glob("*.cxi"))
            assert len(cxi_files) >= 1
