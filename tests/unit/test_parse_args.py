"""
Unit tests for CLI argument parsing in 3dsconv.

This module tests the parse_args() function which handles command-line argument
parsing using argparse.
"""

import os
import sys
from unittest.mock import patch

import pytest

from dsconv.utils import parse_args


class TestParseArgs:
    """Test suite for the parse_args() function."""

    def test_parse_args_minimal_required(self, monkeypatch):
        """Test parsing with minimal required arguments (just the game file)."""
        # Arrange
        test_args = ["3dsconv.py", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert args.game == ["game.cci"]
        assert args.output == ""
        assert args.boot9 is None
        assert args.overwrite is False
        assert args.ignore_bad_hashes is False
        assert args.ignore_encryption is False
        assert args.verbose is False
        assert args.dev_keys is False

    def test_parse_args_all_options(self, monkeypatch):
        """Test parsing with all options enabled."""
        # Arrange
        test_args = [
            "3dsconv.py",
            "-o",
            "output_dir",
            "-b",
            "/path/to/boot9.bin",
            "--overwrite",
            "--ignore-bad-hashes",
            "--ignore-encryption",
            "-v",
            "--dev-keys",
            "game1.cci",
            "game2.cci",
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert args.game == ["game1.cci", "game2.cci"]
        assert args.output == "output_dir"
        assert args.boot9 == "/path/to/boot9.bin"
        assert args.overwrite is True
        assert args.ignore_bad_hashes is True
        assert args.ignore_encryption is True
        assert args.verbose is True
        assert args.dev_keys is True

    def test_parse_args_short_flags(self, monkeypatch):
        """Test parsing with short flag versions."""
        # Arrange
        test_args = ["3dsconv.py", "-o", "out", "-b", "boot9", "-v", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert args.output == "out"
        assert args.boot9 == "boot9"
        assert args.verbose is True
        assert args.game == ["game.cci"]

    def test_parse_args_long_flags(self, monkeypatch):
        """Test parsing with long flag versions."""
        # Arrange
        test_args = ["3dsconv.py", "--output", "out", "--boot9", "boot9", "--verbose", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert args.output == "out"
        assert args.boot9 == "boot9"
        assert args.verbose is True
        assert args.game == ["game.cci"]

    def test_parse_args_no_args_exits(self, monkeypatch, capsys):
        """Test that calling with no arguments exits with code 1."""
        # Arrange
        test_args = ["3dsconv.py"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act & Assert
        with pytest.raises(SystemExit) as exc_info:
            parse_args()

        assert exc_info.value.code == 1
        # Verify help message was printed to stderr
        captured = capsys.readouterr()
        assert "usage:" in captured.err or "usage:" in captured.out

    def test_parse_args_boot9_env_var(self, monkeypatch):
        """Test that BOOT9_PATH environment variable is used as default."""
        # Arrange
        test_args = ["3dsconv.py", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)
        monkeypatch.setenv("BOOT9_PATH", "/env/path/to/boot9.bin")

        # Act
        # Need to reimport or call the function with fresh environment
        # Since parse_args reads os.environ.get at definition time, we need to patch it
        with patch.dict(os.environ, {"BOOT9_PATH": "/env/path/to/boot9.bin"}):
            # We need to reload the module or mock the environment before parse_args is called
            # For simplicity, we'll just verify the default value is set correctly
            args = parse_args()

        # Assert
        assert args.boot9 == "/env/path/to/boot9.bin"

    def test_parse_args_boot9_flag_overrides_env(self, monkeypatch):
        """Test that --boot9 flag overrides BOOT9_PATH environment variable."""
        # Arrange
        test_args = ["3dsconv.py", "-b", "/flag/path/boot9.bin", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)
        monkeypatch.setenv("BOOT9_PATH", "/env/path/to/boot9.bin")

        # Act
        with patch.dict(os.environ, {"BOOT9_PATH": "/env/path/to/boot9.bin"}):
            args = parse_args()

        # Assert
        assert args.boot9 == "/flag/path/boot9.bin"

    def test_parse_args_deprecated_gen_ncchinfo(self, monkeypatch):
        """Test that deprecated --gen-ncchinfo option is recognized."""
        # Arrange
        test_args = ["3dsconv.py", "--gen-ncchinfo", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert args.use_deprecated is True
        assert args.game == ["game.cci"]

    def test_parse_args_deprecated_gen_ncch_all(self, monkeypatch):
        """Test that deprecated --gen-ncch-all option is recognized."""
        # Arrange
        test_args = ["3dsconv.py", "--gen-ncch-all", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert args.use_deprecated is True
        assert args.game == ["game.cci"]

    def test_parse_args_deprecated_xorpads(self, monkeypatch):
        """Test that deprecated --xorpads option is recognized."""
        # Arrange
        test_args = ["3dsconv.py", "--xorpads", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert args.use_deprecated is True
        assert args.game == ["game.cci"]

    def test_parse_args_multiple_games(self, monkeypatch):
        """Test parsing multiple game files."""
        # Arrange
        test_args = ["3dsconv.py", "game1.cci", "game2.3ds", "game3.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert len(args.game) == 3
        assert args.game == ["game1.cci", "game2.3ds", "game3.cci"]

    @pytest.mark.parametrize(
        "flag,attr,expected",
        [
            ("-v", "verbose", True),
            ("--verbose", "verbose", True),
            ("--overwrite", "overwrite", True),
            ("--ignore-bad-hashes", "ignore_bad_hashes", True),
            ("--ignore-encryption", "ignore_encryption", True),
            ("--dev-keys", "dev_keys", True),
        ],
    )
    def test_parse_args_boolean_flags(self, monkeypatch, flag, attr, expected):
        """Test various boolean flags using parametrize."""
        # Arrange
        test_args = ["3dsconv.py", flag, "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert getattr(args, attr) == expected

    @pytest.mark.parametrize(
        "flag,value,attr,expected",
        [
            ("-o", "output_dir", "output", "output_dir"),
            ("--output", "output_dir", "output", "output_dir"),
            ("-b", "/path/boot9", "boot9", "/path/boot9"),
            ("--boot9", "/path/boot9", "boot9", "/path/boot9"),
        ],
    )
    def test_parse_args_value_flags(self, monkeypatch, flag, value, attr, expected):
        """Test flags that take values using parametrize."""
        # Arrange
        test_args = ["3dsconv.py", flag, value, "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert getattr(args, attr) == expected

    def test_parse_args_prod_keys_short_flag(self, monkeypatch):
        """Test parsing with -p flag for prod.keys."""
        # Arrange
        test_args = ["3dsconv.py", "-p", "/path/to/prod.keys", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert args.prod_keys == "/path/to/prod.keys"
        assert args.game == ["game.cci"]

    def test_parse_args_prod_keys_long_flag(self, monkeypatch):
        """Test parsing with --prod-keys flag."""
        # Arrange
        test_args = ["3dsconv.py", "--prod-keys", "/path/to/prod.keys", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        assert args.prod_keys == "/path/to/prod.keys"
        assert args.game == ["game.cci"]

    def test_parse_args_prod_keys_env_var(self, monkeypatch):
        """Test that PROD_KEYS_PATH environment variable is used as default."""
        # Arrange
        test_args = ["3dsconv.py", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        with patch.dict(os.environ, {"PROD_KEYS_PATH": "/env/path/to/prod.keys"}):
            args = parse_args()

        # Assert
        assert args.prod_keys == "/env/path/to/prod.keys"

    def test_parse_args_prod_keys_flag_overrides_env(self, monkeypatch):
        """Test that --prod-keys flag overrides PROD_KEYS_PATH environment variable."""
        # Arrange
        test_args = ["3dsconv.py", "-p", "/flag/path/prod.keys", "game.cci"]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        with patch.dict(os.environ, {"PROD_KEYS_PATH": "/env/path/to/prod.keys"}):
            args = parse_args()

        # Assert
        assert args.prod_keys == "/flag/path/prod.keys"

    def test_parse_args_both_boot9_and_prod_keys(self, monkeypatch):
        """Test that both --boot9 and --prod-keys can be parsed (validation happens at runtime)."""
        # Arrange
        test_args = [
            "3dsconv.py",
            "-b",
            "/path/to/boot9.bin",
            "-p",
            "/path/to/prod.keys",
            "game.cci",
        ]
        monkeypatch.setattr(sys, "argv", test_args)

        # Act
        args = parse_args()

        # Assert
        # Both can be parsed; the mutual exclusivity check happens in the main script
        assert args.boot9 == "/path/to/boot9.bin"
        assert args.prod_keys == "/path/to/prod.keys"
        assert args.game == ["game.cci"]
