"""Tests for ServiceFactory (Task 6.4 / Task 7.2 prerequisite).

This module tests the ServiceFactory class which creates fully configured
ConversionService instances with all dependencies wired together.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from dsconv.services.service_factory import ServiceFactory


class TestServiceFactory:
    """Tests for ServiceFactory.create_conversion_service."""

    def test_create_service_with_valid_files(self, tmp_path):
        """Test creating service with valid input/output files."""
        # Arrange
        input_file = tmp_path / "game.cci"
        input_file.write_bytes(b"test content")
        output_file = tmp_path / "output.cia"

        config = Mock()
        config.dev_keys = False
        config.key_provider = None
        config.ignore_bad_hashes = False
        config.verbose = False

        # Act
        service = ServiceFactory.create_conversion_service(
            str(input_file), str(output_file), config
        )

        # Assert
        assert service is not None
        assert service.ncsd_reader is not None
        assert service.ncch_reader is not None
        assert service.exefs_reader is not None
        assert service.cia_writer is not None
        assert service.hash_validator is not None
        assert service.progress_reporter is not None

    def test_create_service_raises_error_for_missing_input(self):
        """Test that creating service with missing input file raises error."""
        # Arrange
        input_file = "/nonexistent/file.cci"
        output_file = "/tmp/output.cia"
        config = Mock()

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            ServiceFactory.create_conversion_service(input_file, output_file, config)

    def test_create_service_creates_output_directory(self, tmp_path):
        """Test that service factory creates output directory if needed."""
        # Arrange
        input_file = tmp_path / "game.cci"
        input_file.write_bytes(b"test content")

        output_dir = tmp_path / "nested" / "output" / "dir"
        output_file = output_dir / "game.cia"

        config = Mock()
        config.dev_keys = False
        config.key_provider = None
        config.ignore_bad_hashes = False
        config.verbose = False

        # Ensure output directory doesn't exist yet
        assert not output_dir.exists()

        # Act
        ServiceFactory.create_conversion_service(
            str(input_file), str(output_file), config
        )

        # Assert
        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_create_service_with_key_provider(self, tmp_path):
        """Test creating service with key provider configures decryption."""
        # Arrange
        input_file = tmp_path / "game.cci"
        input_file.write_bytes(b"test content")
        output_file = tmp_path / "output.cia"

        mock_key_provider = Mock()
        mock_key_provider.get_original_ncch_key.return_value = 0x12345678

        config = Mock()
        config.dev_keys = False
        config.key_provider = mock_key_provider
        config.ignore_bad_hashes = False
        config.verbose = False

        # Act
        service = ServiceFactory.create_conversion_service(
            str(input_file), str(output_file), config
        )

        # Assert
        assert service.decryption_service is not None
        mock_key_provider.get_original_ncch_key.assert_called_once()

    def test_create_service_without_key_provider(self, tmp_path):
        """Test creating service without key provider has no decryption service."""
        # Arrange
        input_file = tmp_path / "game.cci"
        input_file.write_bytes(b"test content")
        output_file = tmp_path / "output.cia"

        config = Mock()
        config.dev_keys = False
        config.key_provider = None
        config.ignore_bad_hashes = False
        config.verbose = False

        # Act
        service = ServiceFactory.create_conversion_service(
            str(input_file), str(output_file), config
        )

        # Assert
        assert service.decryption_service is None

    def test_create_service_handles_key_loading_failure(self, tmp_path, capsys):
        """Test that service gracefully handles key loading failures."""
        # Arrange
        input_file = tmp_path / "game.cci"
        input_file.write_bytes(b"test content")
        output_file = tmp_path / "output.cia"

        mock_key_provider = Mock()
        mock_key_provider.get_original_ncch_key.side_effect = Exception("Key loading error")

        config = Mock()
        config.dev_keys = False
        config.key_provider = mock_key_provider
        config.ignore_bad_hashes = False
        config.verbose = True  # Enable verbose to see warning

        # Act
        service = ServiceFactory.create_conversion_service(
            str(input_file), str(output_file), config
        )

        # Assert
        assert service.decryption_service is None
        captured = capsys.readouterr()
        assert "Warning: Could not load encryption keys" in captured.out

    def test_create_service_with_ignore_bad_hashes(self, tmp_path):
        """Test that ignore_bad_hashes flag is passed to hash validator."""
        # Arrange
        input_file = tmp_path / "game.cci"
        input_file.write_bytes(b"test content")
        output_file = tmp_path / "output.cia"

        config = Mock()
        config.dev_keys = False
        config.key_provider = None
        config.ignore_bad_hashes = True
        config.verbose = False

        # Act
        service = ServiceFactory.create_conversion_service(
            str(input_file), str(output_file), config
        )

        # Assert
        assert service.hash_validator.ignore_bad_hashes is True

    def test_create_service_with_verbose_mode(self, tmp_path):
        """Test that verbose flag is passed to progress reporter."""
        # Arrange
        input_file = tmp_path / "game.cci"
        input_file.write_bytes(b"test content")
        output_file = tmp_path / "output.cia"

        config = Mock()
        config.dev_keys = False
        config.key_provider = None
        config.ignore_bad_hashes = False
        config.verbose = True

        # Act
        service = ServiceFactory.create_conversion_service(
            str(input_file), str(output_file), config
        )

        # Assert
        assert service.progress_reporter.verbose is True  # type: ignore[attr-defined]


class TestServiceFactoryIntegration:
    """Integration tests for ServiceFactory."""

    def test_factory_creates_working_service_components(self, tmp_path):
        """Test that factory creates all components in working state."""
        # Arrange
        input_file = tmp_path / "game.cci"
        input_file.write_bytes(b"\x00" * 1024)  # Dummy content
        output_file = tmp_path / "output.cia"

        config = Mock()
        config.dev_keys = False
        config.key_provider = None
        config.ignore_bad_hashes = False
        config.verbose = False

        # Act
        service = ServiceFactory.create_conversion_service(
            str(input_file), str(output_file), config
        )

        # Assert - all components are initialized
        assert service.ncsd_reader.reader.file.readable()
        assert service.ncch_reader.reader.file.readable()
        assert service.exefs_reader.reader.file.readable()
        assert service.cia_writer.writer.file.writable()

    def test_factory_with_all_options_enabled(self, tmp_path):
        """Test factory with all configuration options enabled."""
        # Arrange
        input_file = tmp_path / "game.cci"
        input_file.write_bytes(b"\x00" * 1024)
        output_file = tmp_path / "nested" / "output.cia"

        mock_key_provider = Mock()
        mock_key_provider.get_original_ncch_key.return_value = 0x12345678

        config = Mock()
        config.dev_keys = False  # Can't test True without actual dev certchain
        config.key_provider = mock_key_provider
        config.ignore_bad_hashes = True
        config.verbose = True

        # Act
        service = ServiceFactory.create_conversion_service(
            str(input_file), str(output_file), config
        )

        # Assert
        assert service.decryption_service is not None
        assert service.hash_validator.ignore_bad_hashes is True
        assert service.progress_reporter.verbose is True  # type: ignore[attr-defined]
        assert Path(output_file).parent.exists()
