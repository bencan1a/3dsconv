"""Integration tests for CCI to CIA conversion edge cases and error handling.

This module contains integration tests that complement the E2E tests in
tests/e2e/test_pipeline_validation.py. While the E2E tests validate complete
conversion workflows for all test CCI files using subprocess calls, these
integration tests focus on:

1. Error handling (missing files, invalid formats, empty files)
2. Edge cases (verbose mode, directory creation, sequential conversions)
3. Configuration validation
4. Programmatic API usage via ServiceFactory

For comprehensive conversion validation across all 6 test CCI files
(test-01 through test-06) covering various encryption types, see
tests/e2e/test_pipeline_validation.py which provides byte-for-byte
validation against canonical CIA files.
"""

import struct
from pathlib import Path

import pytest

from dsconv.services.conversion_config import ConversionConfig
from dsconv.services.service_factory import ServiceFactory


class TestConversionEdgeCases:
    """Integration tests for conversion edge cases and programmatic API usage.

    These tests complement the E2E tests by focusing on edge cases and
    error handling rather than duplicating full conversion validation.
    """

    @pytest.fixture
    def test_ccis_dir(self):
        """Get path to test CCI files directory."""
        repo_root = Path(__file__).parent.parent.parent
        test_ccis = repo_root / "examples" / "test-ccis"
        if not test_ccis.exists():
            pytest.skip("Test CCI files not found")
        return test_ccis

    @pytest.fixture
    def nocrypt_cci(self, test_ccis_dir):
        """Get path to unencrypted test CCI file."""
        cci_file = test_ccis_dir / "test-01-nocrypt.cci"
        if not cci_file.exists():
            pytest.skip("test-01-nocrypt.cci not found")
        return cci_file

    @pytest.fixture
    def compressed_cci(self, test_ccis_dir):
        """Get path to compressed test CCI file."""
        cci_file = test_ccis_dir / "test-05-compressed.cci"
        if not cci_file.exists():
            pytest.skip("test-05-compressed.cci not found")
        return cci_file

    def test_convert_with_verbose_output(self, tmp_path, nocrypt_cci, capsys):
        """Test conversion with verbose output enabled.

        Validates that verbose mode produces output without affecting
        the conversion result. This tests the programmatic API's
        verbose handling which is not covered by E2E tests.
        """
        # Arrange
        output_file = tmp_path / "output.cia"
        config = ConversionConfig(
            input_file=str(nocrypt_cci),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=True,
            verbose=True,  # Enable verbose output
        )

        # Act
        service = ServiceFactory.create_conversion_service(
            str(nocrypt_cci), str(output_file), config
        )
        service.convert(config)

        # Assert
        _ = capsys.readouterr()  # Capture output (not validated in this test)
        assert output_file.exists(), "CIA file should be created even with verbose"

    def test_convert_creates_output_directory_if_missing(self, tmp_path, nocrypt_cci):
        """Test that conversion creates output directory if it doesn't exist.

        This tests the ServiceFactory's directory creation functionality
        which is important for programmatic API usage.
        """
        # Arrange
        nested_dir = tmp_path / "nested" / "output" / "dir"
        output_file = nested_dir / "output.cia"

        config = ConversionConfig(
            input_file=str(nocrypt_cci),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=True,
            verbose=False,
        )

        # Act
        service = ServiceFactory.create_conversion_service(
            str(nocrypt_cci), str(output_file), config
        )
        service.convert(config)

        # Assert
        assert nested_dir.exists(), "Output directory should be created"
        assert output_file.exists(), "CIA file should be created in nested directory"

    def test_convert_multiple_files_sequentially(self, tmp_path, nocrypt_cci, compressed_cci):
        """Test converting multiple CCI files sequentially.

        This validates that the service can handle multiple conversions
        without state pollution between conversions when using the
        programmatic API.
        """
        # Arrange
        output1 = tmp_path / "output1.cia"
        output2 = tmp_path / "output2.cia"

        config1 = ConversionConfig(
            input_file=str(nocrypt_cci),
            output_file=str(output1),
            key_provider=None,
            ignore_bad_hashes=True,
            verbose=False,
        )

        config2 = ConversionConfig(
            input_file=str(compressed_cci),
            output_file=str(output2),
            key_provider=None,
            ignore_bad_hashes=True,
            verbose=False,
        )

        # Act - Convert first file
        service1 = ServiceFactory.create_conversion_service(str(nocrypt_cci), str(output1), config1)
        service1.convert(config1)

        # Act - Convert second file
        service2 = ServiceFactory.create_conversion_service(
            str(compressed_cci), str(output2), config2
        )
        service2.convert(config2)

        # Assert - Both files should exist
        assert output1.exists(), "First CIA file should be created"
        assert output2.exists(), "Second CIA file should be created"
        assert output1.stat().st_size > 0, "First CIA should not be empty"
        assert output2.stat().st_size > 0, "Second CIA should not be empty"


class TestConversionErrors:
    """Integration tests for error handling during conversion."""

    def test_convert_with_missing_input_file_raises_error(self, tmp_path):
        """Test that conversion with missing input file raises FileNotFoundError."""
        # Arrange
        missing_file = tmp_path / "missing.cci"
        output_file = tmp_path / "output.cia"

        config = ConversionConfig(
            input_file=str(missing_file),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=True,
            verbose=False,
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Input file not found"):
            ServiceFactory.create_conversion_service(str(missing_file), str(output_file), config)

    def test_convert_with_invalid_cci_format(self, tmp_path):
        """Test conversion with invalid CCI format handles errors gracefully.

        This creates a file that isn't a valid CCI to test error handling
        in the programmatic API.
        """
        # Arrange - Create invalid CCI file
        invalid_cci = tmp_path / "invalid.cci"
        invalid_cci.write_bytes(b"NOT A VALID CCI FILE" * 100)

        output_file = tmp_path / "output.cia"
        config = ConversionConfig(
            input_file=str(invalid_cci),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=True,
            verbose=False,
        )

        # Act & Assert - Should raise an error during conversion
        service = ServiceFactory.create_conversion_service(
            str(invalid_cci), str(output_file), config
        )

        with pytest.raises((ValueError, struct.error, KeyError, IndexError)):
            # Various exceptions might be raised depending on where validation fails
            service.convert(config)

    def test_convert_with_empty_file(self, tmp_path):
        """Test conversion with empty file handles errors gracefully."""
        # Arrange - Create empty file
        empty_cci = tmp_path / "empty.cci"
        empty_cci.write_bytes(b"")

        output_file = tmp_path / "output.cia"
        config = ConversionConfig(
            input_file=str(empty_cci),
            output_file=str(output_file),
            key_provider=None,
            ignore_bad_hashes=True,
            verbose=False,
        )

        # Act & Assert
        service = ServiceFactory.create_conversion_service(str(empty_cci), str(output_file), config)

        with pytest.raises((ValueError, struct.error, KeyError, IndexError)):
            service.convert(config)


class TestConversionValidation:
    """Integration tests for validation during conversion."""

    @pytest.fixture
    def test_ccis_dir(self):
        """Get path to test CCI files directory."""
        repo_root = Path(__file__).parent.parent.parent
        test_ccis = repo_root / "examples" / "test-ccis"
        if not test_ccis.exists():
            pytest.skip("Test CCI files not found")
        return test_ccis

    @pytest.fixture
    def nocrypt_cci(self, test_ccis_dir):
        """Get path to unencrypted test CCI file."""
        cci_file = test_ccis_dir / "test-01-nocrypt.cci"
        if not cci_file.exists():
            pytest.skip("test-01-nocrypt.cci not found")
        return cci_file

    def test_conversion_validates_input_file_exists(self, tmp_path):
        """Test that ConversionConfig validates input file exists."""
        # Arrange
        missing_file = tmp_path / "missing.cci"
        output_file = tmp_path / "output.cia"

        config = ConversionConfig(
            input_file=str(missing_file),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            config.validate()

    def test_conversion_config_validation_passes_for_existing_file(self, nocrypt_cci, tmp_path):
        """Test that ConversionConfig validation passes for existing file."""
        # Arrange
        output_file = tmp_path / "output.cia"
        config = ConversionConfig(
            input_file=str(nocrypt_cci),
            output_file=str(output_file),
            key_provider=None,
        )

        # Act & Assert - Should not raise
        config.validate()
