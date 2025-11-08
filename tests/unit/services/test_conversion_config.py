"""Tests for ConversionConfig dataclass."""

import os
from pathlib import Path

import pytest

from dsconv.crypto.key_provider import MockKeyProvider
from dsconv.services.conversion_config import ConversionConfig


class TestConversionConfig:
    """Tests for ConversionConfig dataclass."""

    def test_create_with_all_required_fields(self, tmp_path):
        """Test creating config with all required fields."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Assert
        assert config.input_file == str(input_file)
        assert config.output_file == str(output_file)
        assert config.key_provider is None

    def test_create_with_key_provider(self, tmp_path):
        """Test creating config with a key provider."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"
        key_provider = MockKeyProvider()

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=key_provider,
        )

        # Assert
        assert config.key_provider is key_provider

    def test_default_values_for_optional_fields(self, tmp_path):
        """Test that optional fields have correct default values."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Assert
        assert config.ignore_bad_hashes is False
        assert config.ignore_encryption is False
        assert config.dev_keys is False
        assert config.verbose is False

    def test_ignore_bad_hashes_true(self, tmp_path):
        """Test setting ignore_bad_hashes to True."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=True,
        )

        # Assert
        assert config.ignore_bad_hashes is True

    def test_ignore_encryption_true(self, tmp_path):
        """Test setting ignore_encryption to True."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
            ignore_encryption=True,
        )

        # Assert
        assert config.ignore_encryption is True

    def test_dev_keys_true(self, tmp_path):
        """Test setting dev_keys to True."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
            dev_keys=True,
        )

        # Assert
        assert config.dev_keys is True

    def test_verbose_true(self, tmp_path):
        """Test setting verbose to True."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
            verbose=True,
        )

        # Assert
        assert config.verbose is True

    def test_all_flags_true(self, tmp_path):
        """Test creating config with all boolean flags set to True."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=True,
            ignore_encryption=True,
            dev_keys=True,
            verbose=True,
        )

        # Assert
        assert config.ignore_bad_hashes is True
        assert config.ignore_encryption is True
        assert config.dev_keys is True
        assert config.verbose is True

    def test_validate_with_existing_file_succeeds(self, tmp_path):
        """Test validation succeeds when input file exists."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert (should not raise)
        config.validate()

    def test_validate_with_nonexistent_file_raises_error(self, tmp_path):
        """Test validation raises FileNotFoundError when input file does not exist."""
        # Arrange
        input_file = tmp_path / "nonexistent.cci"
        output_file = tmp_path / "output.cia"

        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            config.validate()

    def test_validate_error_message_contains_filename(self, tmp_path):
        """Test that validation error message contains the filename."""
        # Arrange
        input_file = tmp_path / "missing_file.cci"
        output_file = tmp_path / "output.cia"

        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError, match=str(input_file)):
            config.validate()

    def test_validate_with_directory_instead_of_file_raises_error(self, tmp_path):
        """Test validation fails when input_file points to a directory."""
        # Arrange
        input_dir = tmp_path / "directory"
        input_dir.mkdir()
        output_file = tmp_path / "output.cia"

        config = ConversionConfig(
            input_file=str(input_dir),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            config.validate()

    def test_output_file_can_be_nonexistent(self, tmp_path):
        """Test that validation passes even if output file does not exist."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "new_output.cia"  # Does not exist

        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert (should not raise)
        config.validate()

    def test_config_is_dataclass(self):
        """Test that ConversionConfig is a dataclass."""
        # Arrange & Act
        from dataclasses import is_dataclass

        # Assert
        assert is_dataclass(ConversionConfig)

    def test_config_fields_have_type_hints(self):
        """Test that all fields have proper type hints."""
        # Arrange
        from typing import get_type_hints

        from dsconv.crypto.key_provider import IKeyProvider

        # Act - provide globals to resolve forward references
        hints = get_type_hints(ConversionConfig, globalns={"IKeyProvider": IKeyProvider})

        # Assert
        assert "input_file" in hints
        assert "output_file" in hints
        assert "key_provider" in hints
        assert "ignore_bad_hashes" in hints
        assert "ignore_encryption" in hints
        assert "dev_keys" in hints
        assert "verbose" in hints

    def test_config_repr_contains_field_values(self, tmp_path):
        """Test that repr contains field values for debugging."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
            verbose=True,
        )

        # Act
        repr_str = repr(config)

        # Assert
        assert "ConversionConfig" in repr_str
        assert str(input_file) in repr_str
        assert str(output_file) in repr_str
        assert "verbose=True" in repr_str

    def test_config_equality_with_same_values(self, tmp_path):
        """Test that configs with same values are equal."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        config1 = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        config2 = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert
        assert config1 == config2

    def test_config_inequality_with_different_values(self, tmp_path):
        """Test that configs with different values are not equal."""
        # Arrange
        input_file1 = tmp_path / "test1.cci"
        input_file1.write_bytes(b"test data")
        input_file2 = tmp_path / "test2.cci"
        input_file2.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        config1 = ConversionConfig(
            input_file=str(input_file1),
            output_file=str(output_file),
            key_provider=None,
        )

        config2 = ConversionConfig(
            input_file=str(input_file2),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert
        assert config1 != config2

    @pytest.mark.parametrize(
        "ignore_bad_hashes,ignore_encryption,dev_keys,verbose",
        [
            (False, False, False, False),
            (True, False, False, False),
            (False, True, False, False),
            (False, False, True, False),
            (False, False, False, True),
            (True, True, False, False),
            (True, False, True, False),
            (True, False, False, True),
            (False, True, True, False),
            (False, True, False, True),
            (False, False, True, True),
            (True, True, True, False),
            (True, True, False, True),
            (True, False, True, True),
            (False, True, True, True),
            (True, True, True, True),
        ],
    )
    def test_all_boolean_combinations(
        self, tmp_path, ignore_bad_hashes, ignore_encryption, dev_keys, verbose
    ):
        """Test all combinations of boolean flags."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=ignore_bad_hashes,
            ignore_encryption=ignore_encryption,
            dev_keys=dev_keys,
            verbose=verbose,
        )

        # Assert
        assert config.ignore_bad_hashes == ignore_bad_hashes
        assert config.ignore_encryption == ignore_encryption
        assert config.dev_keys == dev_keys
        assert config.verbose == verbose

    def test_validate_multiple_times_is_idempotent(self, tmp_path):
        """Test that calling validate multiple times is safe."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert (should not raise)
        config.validate()
        config.validate()
        config.validate()

    def test_validate_after_file_deletion_raises_error(self, tmp_path):
        """Test that validation fails if file is deleted after config creation."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        config = ConversionConfig(
            input_file=str(input_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Validate once (should succeed)
        config.validate()

        # Delete the file
        input_file.unlink()

        # Act & Assert (should now raise)
        with pytest.raises(FileNotFoundError):
            config.validate()

    def test_input_and_output_can_be_same_path(self, tmp_path):
        """Test that input and output can point to the same path."""
        # Arrange
        file_path = tmp_path / "test.cci"
        file_path.write_bytes(b"test data")

        # Act
        config = ConversionConfig(
            input_file=str(file_path),
            output_file=str(file_path),
            key_provider=None,
        )

        # Assert (should not raise during creation or validation)
        config.validate()
        assert config.input_file == config.output_file

    def test_paths_can_be_relative(self, tmp_path, monkeypatch):
        """Test that relative paths work correctly."""
        # Arrange
        monkeypatch.chdir(tmp_path)
        input_file = Path("test.cci")
        input_file.write_bytes(b"test data")

        # Act
        config = ConversionConfig(
            input_file=str(input_file),
            output_file="output.cia",
            key_provider=None,
        )

        # Assert (should not raise)
        config.validate()

    def test_paths_can_be_absolute(self, tmp_path):
        """Test that absolute paths work correctly."""
        # Arrange
        input_file = tmp_path / "test.cci"
        input_file.write_bytes(b"test data")
        output_file = tmp_path / "output.cia"

        # Act
        config = ConversionConfig(
            input_file=str(input_file.absolute()),
            output_file=str(output_file.absolute()),
            key_provider=None,
        )

        # Assert (should not raise)
        config.validate()
        assert os.path.isabs(config.input_file)
        assert os.path.isabs(config.output_file)
