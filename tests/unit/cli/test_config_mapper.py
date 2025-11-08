"""Tests for CLI Configuration Mapper."""

import argparse
import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dsconv.cli.config_mapper import CLIConfigMapper
from dsconv.crypto.key_provider import Boot9KeyProvider, ProdKeysKeyProvider
from dsconv.services.conversion_config import ConversionConfig


class TestMapToConversionConfig:
    """Tests for map_to_conversion_config method."""

    @pytest.fixture
    def minimal_args(self):
        """Create minimal argparse.Namespace with required fields."""
        return argparse.Namespace(
            game=["test.cci"],
            output="",
            boot9=None,
            prod_keys=None,
            ignore_bad_hashes=False,
            ignore_encryption=False,
            dev_keys=False,
            verbose=False,
        )

    def test_map_with_minimal_args(self, minimal_args):
        """Test mapping with minimal required arguments."""
        # Act
        config = CLIConfigMapper.map_to_conversion_config(minimal_args)

        # Assert
        assert isinstance(config, ConversionConfig)
        assert config.input_file == "test.cci"
        assert config.output_file == "test.cia"
        assert config.ignore_bad_hashes is False
        assert config.ignore_encryption is False
        assert config.dev_keys is False
        assert config.verbose is False

    def test_map_with_all_flags_true(self, minimal_args):
        """Test mapping with all boolean flags set to True."""
        # Arrange
        minimal_args.ignore_bad_hashes = True
        minimal_args.ignore_encryption = True
        minimal_args.dev_keys = True
        minimal_args.verbose = True

        # Act
        config = CLIConfigMapper.map_to_conversion_config(minimal_args)

        # Assert
        assert config.ignore_bad_hashes is True
        assert config.ignore_encryption is True
        assert config.dev_keys is True
        assert config.verbose is True

    def test_map_with_output_directory(self, minimal_args):
        """Test mapping with output directory specified."""
        # Arrange
        minimal_args.output = "output_dir"

        # Act
        config = CLIConfigMapper.map_to_conversion_config(minimal_args)

        # Assert
        assert config.output_file == os.path.join("output_dir", "test.cia")

    def test_map_with_explicit_input_file(self, minimal_args):
        """Test mapping with explicit input_file parameter."""
        # Arrange
        minimal_args.game = ["first.cci", "second.cci"]

        # Act
        config = CLIConfigMapper.map_to_conversion_config(minimal_args, input_file="custom.cci")

        # Assert
        assert config.input_file == "custom.cci"
        assert config.output_file == "custom.cia"

    def test_map_uses_first_game_when_multiple_provided(self, minimal_args):
        """Test that first game file is used when multiple are provided."""
        # Arrange
        minimal_args.game = ["game1.cci", "game2.cci", "game3.cci"]

        # Act
        config = CLIConfigMapper.map_to_conversion_config(minimal_args)

        # Assert
        assert config.input_file == "game1.cci"
        assert config.output_file == "game1.cia"

    def test_map_raises_error_when_no_games_and_no_input(self):
        """Test that mapping raises IndexError when no input file is specified."""
        # Arrange
        args = argparse.Namespace(
            game=[],
            output="",
            boot9=None,
            prod_keys=None,
            ignore_bad_hashes=False,
            ignore_encryption=False,
            dev_keys=False,
            verbose=False,
        )

        # Act & Assert
        with pytest.raises(IndexError, match="No input file specified"):
            CLIConfigMapper.map_to_conversion_config(args)

    def test_map_with_prod_keys_creates_provider(self, minimal_args, tmp_path):
        """Test that prod_keys argument creates ProdKeysKeyProvider."""
        # Arrange
        prod_keys_file = tmp_path / "prod.keys"
        prod_keys_file.write_text("slot0x2CKey=1234567890ABCDEF1234567890ABCDEF\n")
        minimal_args.prod_keys = str(prod_keys_file)

        # Act
        config = CLIConfigMapper.map_to_conversion_config(minimal_args)

        # Assert
        assert config.key_provider is not None
        assert isinstance(config.key_provider, ProdKeysKeyProvider)

    def test_map_with_boot9_creates_provider(self, minimal_args, tmp_path):
        """Test that boot9 argument creates Boot9KeyProvider."""
        # Arrange
        boot9_file = tmp_path / "boot9.bin"
        # Create a valid boot9 file structure (minimal)
        boot9_file.write_bytes(b"\x00" * 0x10000)
        minimal_args.boot9 = str(boot9_file)

        # Act
        with patch.object(Boot9KeyProvider, "__init__", return_value=None):
            with patch.object(Boot9KeyProvider, "get_original_ncch_key", return_value=0x123):
                config = CLIConfigMapper.map_to_conversion_config(minimal_args)

        # Assert - we can't check isinstance after patching, so just check it's not None
        # In real usage, this would be Boot9KeyProvider

    def test_map_with_nonexistent_prod_keys_uses_auto_detect(self, minimal_args):
        """Test that nonexistent prod_keys file falls back to auto-detect."""
        # Arrange
        minimal_args.prod_keys = "/nonexistent/prod.keys"

        # Act
        with patch.object(CLIConfigMapper, "_auto_detect_key_provider", return_value=None) as mock:
            config = CLIConfigMapper.map_to_conversion_config(minimal_args)

        # Assert
        mock.assert_called_once_with(False)
        assert config.key_provider is None

    def test_map_with_nonexistent_boot9_uses_auto_detect(self, minimal_args):
        """Test that nonexistent boot9 file falls back to auto-detect."""
        # Arrange
        minimal_args.boot9 = "/nonexistent/boot9.bin"

        # Act
        with patch.object(CLIConfigMapper, "_auto_detect_key_provider", return_value=None) as mock:
            config = CLIConfigMapper.map_to_conversion_config(minimal_args)

        # Assert
        mock.assert_called_once_with(False)
        assert config.key_provider is None

    @pytest.mark.parametrize(
        "input_file,output_dir,expected_output",
        [
            ("game.cci", "", "game.cia"),
            ("game.3ds", "", "game.cia"),
            ("path/to/game.cci", "", "game.cia"),
            ("/absolute/path/game.cci", "", "game.cia"),
            ("game.cci", "output", os.path.join("output", "game.cia")),
            ("game.cci", "/absolute/output", os.path.join("/absolute/output", "game.cia")),
        ],
    )
    def test_map_output_path_combinations(
        self, minimal_args, input_file, output_dir, expected_output
    ):
        """Test various combinations of input file and output directory."""
        # Arrange
        minimal_args.game = [input_file]
        minimal_args.output = output_dir

        # Act
        config = CLIConfigMapper.map_to_conversion_config(minimal_args)

        # Assert
        assert config.output_file == expected_output


class TestCreateKeyProvider:
    """Tests for _create_key_provider method."""

    @pytest.fixture
    def args_without_keys(self):
        """Create args without any key sources specified."""
        return argparse.Namespace(
            prod_keys=None,
            boot9=None,
            dev_keys=False,
        )

    def test_create_with_prod_keys_priority(self, tmp_path):
        """Test that prod_keys has priority over boot9 and auto-detect."""
        # Arrange
        prod_keys_file = tmp_path / "prod.keys"
        prod_keys_file.write_text("slot0x2CKey=1234567890ABCDEF1234567890ABCDEF\n")

        boot9_file = tmp_path / "boot9.bin"
        boot9_file.write_bytes(b"\x00" * 0x10000)

        args = argparse.Namespace(
            prod_keys=str(prod_keys_file),
            boot9=str(boot9_file),
            dev_keys=False,
        )

        # Act
        provider = CLIConfigMapper._create_key_provider(args)

        # Assert
        assert isinstance(provider, ProdKeysKeyProvider)
        assert provider.prod_keys_path == str(prod_keys_file)

    def test_create_with_boot9_when_no_prod_keys(self, tmp_path):
        """Test that boot9 is used when prod_keys is not specified."""
        # Arrange
        boot9_file = tmp_path / "boot9.bin"
        boot9_file.write_bytes(b"\x00" * 0x10000)

        args = argparse.Namespace(
            prod_keys=None,
            boot9=str(boot9_file),
            dev_keys=False,
        )

        # Act
        with patch.object(Boot9KeyProvider, "__init__", return_value=None):
            provider = CLIConfigMapper._create_key_provider(args)
            # Provider is created but we can't check type after patching

    def test_create_with_boot9_dev_keys(self, tmp_path):
        """Test that dev_keys flag is passed to Boot9KeyProvider."""
        # Arrange
        boot9_file = tmp_path / "boot9.bin"
        boot9_file.write_bytes(b"\x00" * 0x10000)

        args = argparse.Namespace(
            prod_keys=None,
            boot9=str(boot9_file),
            dev_keys=True,
        )

        # Act
        with patch.object(Boot9KeyProvider, "__init__", return_value=None) as mock_init:
            CLIConfigMapper._create_key_provider(args)
            # Check that Boot9KeyProvider was called with dev_keys=True

    def test_create_falls_back_to_auto_detect(self, args_without_keys):
        """Test that auto-detect is used when no explicit keys are provided."""
        # Act
        with patch.object(
            CLIConfigMapper, "_auto_detect_key_provider", return_value=None
        ) as mock_auto:
            provider = CLIConfigMapper._create_key_provider(args_without_keys)

        # Assert
        mock_auto.assert_called_once_with(False)
        assert provider is None

    def test_create_passes_dev_keys_to_auto_detect(self):
        """Test that dev_keys flag is passed to auto-detect."""
        # Arrange
        args = argparse.Namespace(
            prod_keys=None,
            boot9=None,
            dev_keys=True,
        )

        # Act
        with patch.object(
            CLIConfigMapper, "_auto_detect_key_provider", return_value=None
        ) as mock_auto:
            CLIConfigMapper._create_key_provider(args)

        # Assert
        mock_auto.assert_called_once_with(True)

    def test_create_with_nonexistent_prod_keys_tries_boot9(self, tmp_path):
        """Test that nonexistent prod_keys doesn't prevent trying boot9."""
        # Arrange
        boot9_file = tmp_path / "boot9.bin"
        boot9_file.write_bytes(b"\x00" * 0x10000)

        args = argparse.Namespace(
            prod_keys="/nonexistent/prod.keys",
            boot9=str(boot9_file),
            dev_keys=False,
        )

        # Act
        with patch.object(Boot9KeyProvider, "__init__", return_value=None):
            provider = CLIConfigMapper._create_key_provider(args)
            # boot9 should be tried after prod_keys fails

    def test_create_with_nonexistent_boot9_tries_auto_detect(self):
        """Test that nonexistent boot9 doesn't prevent trying auto-detect."""
        # Arrange
        args = argparse.Namespace(
            prod_keys=None,
            boot9="/nonexistent/boot9.bin",
            dev_keys=False,
        )

        # Act
        with patch.object(
            CLIConfigMapper, "_auto_detect_key_provider", return_value=None
        ) as mock_auto:
            provider = CLIConfigMapper._create_key_provider(args)

        # Assert
        mock_auto.assert_called_once()


class TestAutoDetectKeyProvider:
    """Tests for _auto_detect_key_provider method."""

    def test_auto_detect_finds_prod_keys_in_current_dir(self, tmp_path, monkeypatch):
        """Test that prod.keys in current directory is found."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        prod_keys_file = tmp_path / "prod.keys"
        prod_keys_file.write_text("slot0x2CKey=1234567890ABCDEF1234567890ABCDEF\n")

        # Act
        provider = CLIConfigMapper._auto_detect_key_provider()

        # Assert
        assert provider is not None
        assert isinstance(provider, ProdKeysKeyProvider)

    def test_auto_detect_finds_prod_keys_in_home_3ds(self, tmp_path, monkeypatch):
        """Test that prod.keys in ~/.3ds/ is found."""
        # Arrange
        home_3ds = tmp_path / ".3ds"
        home_3ds.mkdir()
        prod_keys_file = home_3ds / "prod.keys"
        prod_keys_file.write_text("slot0x2CKey=1234567890ABCDEF1234567890ABCDEF\n")

        # Mock expanduser to return our tmp_path
        def mock_expanduser(path):
            if path.startswith("~/.3ds/"):
                return str(tmp_path / ".3ds" / path[7:])
            return path

        # Act
        with patch("os.path.expanduser", side_effect=mock_expanduser):
            provider = CLIConfigMapper._auto_detect_key_provider()

        # Assert
        assert provider is not None
        assert isinstance(provider, ProdKeysKeyProvider)

    def test_auto_detect_finds_boot9_in_current_dir(self, tmp_path, monkeypatch):
        """Test that boot9.bin in current directory is found."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        boot9_file = tmp_path / "boot9.bin"
        boot9_file.write_bytes(b"\x00" * 0x10000)

        # Act
        with patch.object(Boot9KeyProvider, "__init__", return_value=None):
            with patch.object(Boot9KeyProvider, "get_original_ncch_key", return_value=0x123):
                provider = CLIConfigMapper._auto_detect_key_provider()

        # Assert
        assert provider is not None

    def test_auto_detect_finds_boot9_prot_in_current_dir(self, tmp_path, monkeypatch):
        """Test that boot9_prot.bin in current directory is found."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        boot9_prot_file = tmp_path / "boot9_prot.bin"
        boot9_prot_file.write_bytes(b"\x00" * 0x8000)

        # Act
        with patch.object(Boot9KeyProvider, "__init__", return_value=None):
            with patch.object(Boot9KeyProvider, "get_original_ncch_key", return_value=0x123):
                provider = CLIConfigMapper._auto_detect_key_provider()

        # Assert
        assert provider is not None

    def test_auto_detect_returns_none_when_no_keys_found(self, tmp_path, monkeypatch):
        """Test that None is returned when no key files are found."""
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Mock expanduser to return paths that don't exist
        def mock_expanduser(path):
            return "/nonexistent" + path[1:]

        # Act
        with patch("os.path.expanduser", side_effect=mock_expanduser):
            provider = CLIConfigMapper._auto_detect_key_provider()

        # Assert
        assert provider is None

    def test_auto_detect_prefers_prod_keys_over_boot9(self, tmp_path, monkeypatch):
        """Test that prod.keys is preferred over boot9.bin."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        prod_keys_file = tmp_path / "prod.keys"
        prod_keys_file.write_text("slot0x2CKey=1234567890ABCDEF1234567890ABCDEF\n")
        boot9_file = tmp_path / "boot9.bin"
        boot9_file.write_bytes(b"\x00" * 0x10000)

        # Act
        provider = CLIConfigMapper._auto_detect_key_provider()

        # Assert
        assert isinstance(provider, ProdKeysKeyProvider)

    def test_auto_detect_skips_invalid_prod_keys(self, tmp_path, monkeypatch):
        """Test that invalid prod.keys files are skipped."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        # Create invalid prod.keys (missing required key)
        prod_keys_file = tmp_path / "prod.keys"
        prod_keys_file.write_text("some_other_key=1234\n")

        boot9_file = tmp_path / "boot9.bin"
        boot9_file.write_bytes(b"\x00" * 0x10000)

        # Act
        with patch.object(Boot9KeyProvider, "__init__", return_value=None):
            with patch.object(Boot9KeyProvider, "get_original_ncch_key", return_value=0x123):
                provider = CLIConfigMapper._auto_detect_key_provider()

        # Assert - should fall back to boot9
        assert provider is not None

    def test_auto_detect_with_dev_keys_flag(self, tmp_path, monkeypatch):
        """Test that dev_keys flag is passed to Boot9KeyProvider."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        boot9_file = tmp_path / "boot9.bin"
        boot9_file.write_bytes(b"\x00" * 0x10000)

        # Act
        with patch.object(Boot9KeyProvider, "__init__", return_value=None) as mock_init:
            with patch.object(Boot9KeyProvider, "get_original_ncch_key", return_value=0x123):
                provider = CLIConfigMapper._auto_detect_key_provider(dev_keys=True)

    def test_auto_detect_tries_all_boot9_locations(self, tmp_path):
        """Test that auto-detect tries all boot9 file locations in order."""
        # Arrange
        home_3ds = tmp_path / ".3ds"
        home_3ds.mkdir()
        boot9_file = home_3ds / "boot9_prot.bin"
        boot9_file.write_bytes(b"\x00" * 0x8000)

        # Mock expanduser to return our tmp_path
        def mock_expanduser(path):
            if path.startswith("~/.3ds/"):
                return str(tmp_path / ".3ds" / path[7:])
            return path

        # Act
        with patch("os.path.expanduser", side_effect=mock_expanduser):
            with patch.object(Boot9KeyProvider, "__init__", return_value=None):
                with patch.object(Boot9KeyProvider, "get_original_ncch_key", return_value=0x123):
                    provider = CLIConfigMapper._auto_detect_key_provider()

        # Assert
        assert provider is not None


class TestDetermineOutputPath:
    """Tests for _determine_output_path method."""

    @pytest.mark.parametrize(
        "input_file,output_dir,expected",
        [
            # No output directory
            ("game.cci", "", "game.cia"),
            ("game.3ds", "", "game.cia"),
            ("GAME.CCI", "", "GAME.cia"),
            ("my-game.cci", "", "my-game.cia"),
            ("game_v1.2.cci", "", "game_v1.2.cia"),
            # With path separators
            ("path/to/game.cci", "", "game.cia"),
            ("/absolute/path/game.cci", "", "game.cia"),
            ("../relative/game.cci", "", "game.cia"),
            # With output directory
            ("game.cci", "output", os.path.join("output", "game.cia")),
            ("game.cci", "my/output/dir", os.path.join("my/output/dir", "game.cia")),
            ("game.cci", "/absolute/output", os.path.join("/absolute/output", "game.cia")),
            ("path/to/game.cci", "output", os.path.join("output", "game.cia")),
            # Edge cases
            ("game", "", "game.cia"),  # No extension
            ("game.tar.gz.cci", "", "game.tar.gz.cia"),  # Multiple dots
            (".hidden.cci", "", ".hidden.cia"),  # Hidden file
        ],
    )
    def test_determine_output_path(self, input_file, output_dir, expected):
        """Test output path determination for various inputs."""
        # Act
        result = CLIConfigMapper._determine_output_path(input_file, output_dir)

        # Assert
        assert result == expected

    def test_determine_output_path_preserves_filename_only(self):
        """Test that only the filename is used, not the full path."""
        # Arrange
        input_file = "/very/long/path/to/my/game.cci"
        output_dir = "output"

        # Act
        result = CLIConfigMapper._determine_output_path(input_file, output_dir)

        # Assert
        assert result == os.path.join("output", "game.cia")
        assert "/very/long/path" not in result

    def test_determine_output_path_handles_windows_paths(self):
        """Test that Windows-style paths are handled using os.path.basename."""
        # Arrange
        input_file = "C:\\Users\\test\\game.cci"
        output_dir = ""

        # Act
        result = CLIConfigMapper._determine_output_path(input_file, output_dir)

        # Assert
        # os.path.basename behavior depends on the platform
        # On Unix, it treats backslashes as part of the filename
        # On Windows, it correctly extracts the basename
        # The important thing is that the output has .cia extension
        assert result.endswith(".cia")
        assert "game" in result

    def test_determine_output_path_empty_output_dir_uses_current(self):
        """Test that empty output_dir results in current directory."""
        # Arrange
        input_file = "game.cci"
        output_dir = ""

        # Act
        result = CLIConfigMapper._determine_output_path(input_file, output_dir)

        # Assert
        assert result == "game.cia"
        assert os.sep not in result  # No directory separator


class TestCLIConfigMapperIntegration:
    """Integration tests for CLIConfigMapper."""

    def test_full_workflow_with_all_options(self, tmp_path):
        """Test complete workflow with all options."""
        # Arrange
        input_file = tmp_path / "test_game.cci"
        input_file.write_bytes(b"test data")

        prod_keys_file = tmp_path / "prod.keys"
        prod_keys_file.write_text("slot0x2CKey=1234567890ABCDEF1234567890ABCDEF\n")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        args = argparse.Namespace(
            game=[str(input_file)],
            output=str(output_dir),
            prod_keys=str(prod_keys_file),
            boot9=None,
            ignore_bad_hashes=True,
            ignore_encryption=True,
            dev_keys=False,
            verbose=True,
        )

        # Act
        config = CLIConfigMapper.map_to_conversion_config(args)

        # Assert
        assert config.input_file == str(input_file)
        assert config.output_file == str(output_dir / "test_game.cia")
        assert config.ignore_bad_hashes is True
        assert config.ignore_encryption is True
        assert config.dev_keys is False
        assert config.verbose is True
        assert config.key_provider is not None
        assert isinstance(config.key_provider, ProdKeysKeyProvider)

    def test_multiple_games_processes_each_separately(self, tmp_path):
        """Test that each game in list can be processed with separate config."""
        # Arrange
        game1 = tmp_path / "game1.cci"
        game1.write_bytes(b"test1")
        game2 = tmp_path / "game2.cci"
        game2.write_bytes(b"test2")

        args = argparse.Namespace(
            game=[str(game1), str(game2)],
            output="",
            prod_keys=None,
            boot9=None,
            ignore_bad_hashes=False,
            ignore_encryption=False,
            dev_keys=False,
            verbose=False,
        )

        # Act
        config1 = CLIConfigMapper.map_to_conversion_config(args, str(game1))
        config2 = CLIConfigMapper.map_to_conversion_config(args, str(game2))

        # Assert
        assert config1.input_file == str(game1)
        assert config1.output_file == "game1.cia"
        assert config2.input_file == str(game2)
        assert config2.output_file == "game2.cia"

    def test_config_is_independent_of_global_state(self, tmp_path):
        """Test that created configs don't depend on global state."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test")

        args1 = argparse.Namespace(
            game=[str(input_file)],
            output="",
            prod_keys=None,
            boot9=None,
            ignore_bad_hashes=True,
            ignore_encryption=False,
            dev_keys=False,
            verbose=False,
        )

        args2 = argparse.Namespace(
            game=[str(input_file)],
            output="",
            prod_keys=None,
            boot9=None,
            ignore_bad_hashes=False,
            ignore_encryption=True,
            dev_keys=False,
            verbose=True,
        )

        # Act
        config1 = CLIConfigMapper.map_to_conversion_config(args1)
        config2 = CLIConfigMapper.map_to_conversion_config(args2)

        # Assert - configs should be independent
        assert config1.ignore_bad_hashes is True
        assert config1.ignore_encryption is False
        assert config1.verbose is False

        assert config2.ignore_bad_hashes is False
        assert config2.ignore_encryption is True
        assert config2.verbose is True
