"""
Unit tests for ctrtool integration utilities.

This module tests the ctrtool-related functions in dsconv.utils,
including finding the ctrtool executable, running it, and renaming
output files.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from dsconv.utils import (
    convert_cia_to_cxi,
    find_ctrtool,
    parse_args,
    rename_contents_to_cxi,
    run_ctrtool_extract_contents,
)


class TestParseArgsCtrTool:
    """Test suite for ctrtool-related argument parsing."""

    def test_parse_args_to_cxi_flag(self, monkeypatch):
        """Test parsing with --to-cxi flag."""
        test_args = ["3dsconv.py", "--to-cxi", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        args = parse_args()

        assert args.to_cxi is True
        assert args.game == ["game.cci"]

    def test_parse_args_to_cxi_default_false(self, monkeypatch):
        """Test that --to-cxi defaults to False."""
        test_args = ["3dsconv.py", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        args = parse_args()

        assert args.to_cxi is False

    def test_parse_args_ctrtool_path(self, monkeypatch):
        """Test parsing with --ctrtool-path option."""
        test_args = ["3dsconv.py", "--ctrtool-path", "/path/to/ctrtool", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        args = parse_args()

        assert args.ctrtool_path == "/path/to/ctrtool"
        assert args.game == ["game.cci"]

    def test_parse_args_ctrtool_path_env_var(self, monkeypatch):
        """Test that CTRTOOL_PATH environment variable is used as default."""
        test_args = ["3dsconv.py", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        with patch.dict(os.environ, {"CTRTOOL_PATH": "/env/path/ctrtool"}):
            args = parse_args()

        assert args.ctrtool_path == "/env/path/ctrtool"

    def test_parse_args_ctrtool_path_flag_overrides_env(self, monkeypatch):
        """Test that --ctrtool-path flag overrides CTRTOOL_PATH environment variable."""
        test_args = ["3dsconv.py", "--ctrtool-path", "/flag/path/ctrtool", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        with patch.dict(os.environ, {"CTRTOOL_PATH": "/env/path/ctrtool"}):
            args = parse_args()

        assert args.ctrtool_path == "/flag/path/ctrtool"

    def test_parse_args_to_cxi_with_batch_mode(self, monkeypatch):
        """Test combining --to-cxi with batch mode."""
        test_args = ["3dsconv.py", "--batch", "/input/folder", "--to-cxi"]
        monkeypatch.setattr(sys, "argv", test_args)

        args = parse_args()

        assert args.batch == "/input/folder"
        assert args.to_cxi is True
        assert args.game == []


class TestFindCtrtool:
    """Test suite for find_ctrtool function."""

    def test_find_ctrtool_custom_path_file(self, tmp_path):
        """Test finding ctrtool with custom path pointing to a file."""
        # Create a mock ctrtool executable
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")

        result = find_ctrtool(str(ctrtool))

        assert result == str(ctrtool)

    def test_find_ctrtool_custom_path_directory(self, tmp_path):
        """Test finding ctrtool with custom path pointing to a directory."""
        # Create a mock ctrtool executable in the directory
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")

        result = find_ctrtool(str(tmp_path))

        assert result == str(ctrtool)

    def test_find_ctrtool_custom_path_directory_exe(self, tmp_path):
        """Test finding ctrtool.exe in a custom directory."""
        # Create a mock ctrtool.exe in the directory
        ctrtool = tmp_path / "ctrtool.exe"
        ctrtool.write_text("mock")

        result = find_ctrtool(str(tmp_path))

        assert result == str(ctrtool)

    def test_find_ctrtool_custom_path_not_found(self, tmp_path):
        """Test that find_ctrtool returns None for invalid custom path."""
        result = find_ctrtool(str(tmp_path / "nonexistent"))

        assert result is None

    def test_find_ctrtool_env_var_file(self, tmp_path, monkeypatch):
        """Test finding ctrtool via CTRTOOL_PATH environment variable (file)."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        monkeypatch.setenv("CTRTOOL_PATH", str(ctrtool))

        result = find_ctrtool()

        assert result == str(ctrtool)

    def test_find_ctrtool_env_var_directory(self, tmp_path, monkeypatch):
        """Test finding ctrtool via CTRTOOL_PATH environment variable (directory)."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        monkeypatch.setenv("CTRTOOL_PATH", str(tmp_path))

        result = find_ctrtool()

        assert result == str(ctrtool)

    def test_find_ctrtool_in_path(self, tmp_path, monkeypatch):
        """Test finding ctrtool in system PATH."""
        # Clear CTRTOOL_PATH and mock shutil.which
        monkeypatch.delenv("CTRTOOL_PATH", raising=False)

        with patch("dsconv.utils.shutil.which") as mock_which:
            mock_which.side_effect = lambda x: str(tmp_path / x) if x == "ctrtool" else None

            result = find_ctrtool()

            assert result == str(tmp_path / "ctrtool")

    def test_find_ctrtool_not_found(self, monkeypatch):
        """Test that find_ctrtool returns None when ctrtool is not found."""
        monkeypatch.delenv("CTRTOOL_PATH", raising=False)

        with patch("dsconv.utils.shutil.which") as mock_which:
            mock_which.return_value = None

            result = find_ctrtool()

            assert result is None


class TestRunCtrtoolExtractContents:
    """Test suite for run_ctrtool_extract_contents function."""

    def test_run_ctrtool_cia_not_found(self, tmp_path):
        """Test error when CIA file doesn't exist."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")

        success, msg = run_ctrtool_extract_contents(str(ctrtool), "/nonexistent/game.cia")

        assert success is False
        assert "CIA file not found" in msg

    def test_run_ctrtool_ctrtool_not_found(self, tmp_path):
        """Test error when ctrtool doesn't exist."""
        cia = tmp_path / "game.cia"
        cia.write_bytes(b"mock cia")

        success, msg = run_ctrtool_extract_contents("/nonexistent/ctrtool", str(cia))

        assert success is False
        assert "ctrtool not found" in msg

    def test_run_ctrtool_success(self, tmp_path):
        """Test successful ctrtool execution."""
        # Create mock files
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        cia = tmp_path / "game.cia"
        cia.write_bytes(b"mock cia")

        with patch("dsconv.utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            success, msg = run_ctrtool_extract_contents(str(ctrtool), str(cia))

            assert success is True
            assert "Contents extracted" in msg
            # Verify correct command was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert str(ctrtool) in call_args
            assert "--intype=cia" in call_args
            assert str(cia) in call_args
            assert any("--contents=" in arg for arg in call_args)

    def test_run_ctrtool_failure(self, tmp_path):
        """Test ctrtool execution failure."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        cia = tmp_path / "game.cia"
        cia.write_bytes(b"mock cia")

        with patch("dsconv.utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Invalid CIA")

            success, msg = run_ctrtool_extract_contents(str(ctrtool), str(cia))

            assert success is False
            assert "ctrtool failed" in msg
            assert "Invalid CIA" in msg

    def test_run_ctrtool_timeout(self, tmp_path):
        """Test ctrtool timeout."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        cia = tmp_path / "game.cia"
        cia.write_bytes(b"mock cia")

        with patch("dsconv.utils.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="ctrtool", timeout=120)

            success, msg = run_ctrtool_extract_contents(str(ctrtool), str(cia))

            assert success is False
            assert "timed out" in msg

    def test_run_ctrtool_custom_output_dir(self, tmp_path):
        """Test ctrtool with custom output directory."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        cia = tmp_path / "game.cia"
        cia.write_bytes(b"mock cia")
        output_dir = tmp_path / "output"

        with patch("dsconv.utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            success, msg = run_ctrtool_extract_contents(str(ctrtool), str(cia), str(output_dir))

            assert success is True
            assert output_dir.exists()
            # Verify output dir is used in command
            call_args = mock_run.call_args[0][0]
            assert any(str(output_dir) in arg for arg in call_args)


class TestRenameContentsToCxi:
    """Test suite for rename_contents_to_cxi function."""

    def test_rename_contents_no_file(self, tmp_path):
        """Test error when no contents file exists."""
        cia = tmp_path / "game.cia"

        success, msg = rename_contents_to_cxi(str(cia), str(tmp_path))

        assert success is False
        assert "No contents.0000" in msg

    def test_rename_contents_success(self, tmp_path):
        """Test successful rename of contents file."""
        # Create mock contents file
        contents = tmp_path / "contents.0000.ncch"
        contents.write_bytes(b"mock content")
        cia = tmp_path / "game.cia"

        success, cxi_path = rename_contents_to_cxi(str(cia), str(tmp_path))

        assert success is True
        assert cxi_path == str(tmp_path / "game.cxi")
        assert Path(cxi_path).exists()
        assert not contents.exists()  # Original should be renamed

    def test_rename_contents_overwrites_existing(self, tmp_path):
        """Test that existing CXI file is overwritten."""
        # Create mock contents file
        contents = tmp_path / "contents.0000.ncch"
        contents.write_bytes(b"new content")

        # Create existing CXI file
        existing_cxi = tmp_path / "game.cxi"
        existing_cxi.write_bytes(b"old content")

        cia = tmp_path / "game.cia"

        success, cxi_path = rename_contents_to_cxi(str(cia), str(tmp_path))

        assert success is True
        assert Path(cxi_path).read_bytes() == b"new content"

    def test_rename_contents_default_output_dir(self, tmp_path):
        """Test rename using CIA's directory as default."""
        # Create mock contents file in same dir as CIA
        contents = tmp_path / "contents.0000.ncch"
        contents.write_bytes(b"mock content")
        cia = tmp_path / "game.cia"

        success, cxi_path = rename_contents_to_cxi(str(cia))

        assert success is True
        assert cxi_path == str(tmp_path / "game.cxi")


class TestConvertCiaToCxi:
    """Test suite for convert_cia_to_cxi function."""

    def test_convert_success(self, tmp_path):
        """Test successful CIA to CXI conversion."""
        # Create mock files
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        cia = tmp_path / "game.cia"
        cia.write_bytes(b"mock cia")

        with patch("dsconv.utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            # Create the contents file that ctrtool would create
            contents = tmp_path / "contents.0000.ncch"
            contents.write_bytes(b"mock content")

            success, cxi_path = convert_cia_to_cxi(str(ctrtool), str(cia))

            assert success is True
            assert cxi_path == str(tmp_path / "game.cxi")

    def test_convert_ctrtool_fails(self, tmp_path):
        """Test conversion when ctrtool fails."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        cia = tmp_path / "game.cia"
        cia.write_bytes(b"mock cia")

        with patch("dsconv.utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")

            success, msg = convert_cia_to_cxi(str(ctrtool), str(cia))

            assert success is False
            assert "ctrtool failed" in msg

    def test_convert_rename_fails(self, tmp_path):
        """Test conversion when rename fails (no contents file created)."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        cia = tmp_path / "game.cia"
        cia.write_bytes(b"mock cia")

        with patch("dsconv.utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            # Don't create contents file, so rename will fail

            success, msg = convert_cia_to_cxi(str(ctrtool), str(cia))

            assert success is False
            assert "No contents.0000" in msg

    def test_convert_verbose_output(self, tmp_path, capsys):
        """Test verbose output during conversion."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        cia = tmp_path / "game.cia"
        cia.write_bytes(b"mock cia")

        with patch("dsconv.utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            contents = tmp_path / "contents.0000.ncch"
            contents.write_bytes(b"mock content")

            success, _ = convert_cia_to_cxi(str(ctrtool), str(cia), verbose=True)

            assert success is True
            captured = capsys.readouterr()
            assert "Extracting CXI" in captured.out
            assert "Created CXI" in captured.out

    def test_convert_with_custom_output_dir(self, tmp_path):
        """Test conversion with custom output directory."""
        ctrtool = tmp_path / "ctrtool"
        ctrtool.write_text("mock")
        cia = tmp_path / "input" / "game.cia"
        cia.parent.mkdir()
        cia.write_bytes(b"mock cia")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with patch("dsconv.utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            contents = output_dir / "contents.0000.ncch"
            contents.write_bytes(b"mock content")

            success, cxi_path = convert_cia_to_cxi(str(ctrtool), str(cia), str(output_dir))

            assert success is True
            assert cxi_path == str(output_dir / "game.cxi")
