"""Tests for ConversionService cleanup and file handle management."""

from unittest.mock import MagicMock, Mock

from dsconv.services.conversion_service import ConversionService


class TestConversionServiceCleanup:
    """Test file handle cleanup in ConversionService."""

    def test_close_closes_input_file_handle(self):
        """Test that close() closes the input file handle."""
        # Arrange - create mocked dependencies
        mock_ncsd_reader = Mock()
        mock_ncch_reader = Mock()
        mock_exefs_reader = Mock()
        mock_cia_writer = Mock()
        mock_hash_validator = Mock()
        mock_progress_reporter = Mock()

        # Create mock file handles
        mock_input_file = MagicMock()
        mock_output_file = MagicMock()

        # Set up reader/writer with file handles
        mock_binary_reader = Mock()
        mock_binary_reader.file = mock_input_file
        mock_ncch_reader.reader = mock_binary_reader

        mock_binary_writer = Mock()
        mock_binary_writer.file = mock_output_file
        mock_cia_writer.writer = mock_binary_writer

        service = ConversionService(
            ncsd_reader=mock_ncsd_reader,
            ncch_reader=mock_ncch_reader,
            exefs_reader=mock_exefs_reader,
            cia_writer=mock_cia_writer,
            decryption_service=None,
            hash_validator=mock_hash_validator,
            progress_reporter=mock_progress_reporter,
        )

        # Act - call close
        service.close()

        # Assert - verify both files were closed
        mock_input_file.close.assert_called_once()
        mock_output_file.close.assert_called_once()

    def test_close_closes_output_file_handle(self):
        """Test that close() closes the output file handle."""
        # Arrange
        mock_ncsd_reader = Mock()
        mock_ncch_reader = Mock()
        mock_exefs_reader = Mock()
        mock_cia_writer = Mock()
        mock_hash_validator = Mock()
        mock_progress_reporter = Mock()

        # Create mock file handle
        mock_output_file = MagicMock()

        # Set up writer with file handle
        mock_binary_writer = Mock()
        mock_binary_writer.file = mock_output_file
        mock_cia_writer.writer = mock_binary_writer

        # Reader without proper structure (to test resilience)
        mock_ncch_reader.reader = None

        service = ConversionService(
            ncsd_reader=mock_ncsd_reader,
            ncch_reader=mock_ncch_reader,
            exefs_reader=mock_exefs_reader,
            cia_writer=mock_cia_writer,
            decryption_service=None,
            hash_validator=mock_hash_validator,
            progress_reporter=mock_progress_reporter,
        )

        # Act
        service.close()

        # Assert
        mock_output_file.close.assert_called_once()

    def test_close_handles_missing_file_handles_gracefully(self):
        """Test that close() doesn't crash if file handles are missing."""
        # Arrange
        mock_ncsd_reader = Mock()
        mock_ncch_reader = Mock()
        mock_exefs_reader = Mock()
        mock_cia_writer = Mock()
        mock_hash_validator = Mock()
        mock_progress_reporter = Mock()

        # Readers/writers without file attribute
        mock_ncch_reader.reader = Mock(spec=[])  # No 'file' attribute
        mock_cia_writer.writer = Mock(spec=[])  # No 'file' attribute

        service = ConversionService(
            ncsd_reader=mock_ncsd_reader,
            ncch_reader=mock_ncch_reader,
            exefs_reader=mock_exefs_reader,
            cia_writer=mock_cia_writer,
            decryption_service=None,
            hash_validator=mock_hash_validator,
            progress_reporter=mock_progress_reporter,
        )

        # Act & Assert - should not raise
        service.close()

    def test_close_handles_exceptions_during_close(self):
        """Test that close() handles exceptions during file close."""
        # Arrange
        mock_ncsd_reader = Mock()
        mock_ncch_reader = Mock()
        mock_exefs_reader = Mock()
        mock_cia_writer = Mock()
        mock_hash_validator = Mock()
        mock_progress_reporter = Mock()

        # Create mock file that raises exception on close
        mock_input_file = MagicMock()
        mock_input_file.close.side_effect = OSError("File already closed")

        mock_binary_reader = Mock()
        mock_binary_reader.file = mock_input_file
        mock_ncch_reader.reader = mock_binary_reader

        mock_binary_writer = Mock()
        mock_binary_writer.file = MagicMock()
        mock_cia_writer.writer = mock_binary_writer

        service = ConversionService(
            ncsd_reader=mock_ncsd_reader,
            ncch_reader=mock_ncch_reader,
            exefs_reader=mock_exefs_reader,
            cia_writer=mock_cia_writer,
            decryption_service=None,
            hash_validator=mock_hash_validator,
            progress_reporter=mock_progress_reporter,
        )

        # Act & Assert - should not raise even if close() raises
        service.close()

    def test_close_called_multiple_times_is_safe(self):
        """Test that calling close() multiple times is safe."""
        # Arrange
        mock_ncsd_reader = Mock()
        mock_ncch_reader = Mock()
        mock_exefs_reader = Mock()
        mock_cia_writer = Mock()
        mock_hash_validator = Mock()
        mock_progress_reporter = Mock()

        mock_input_file = MagicMock()
        mock_output_file = MagicMock()

        mock_binary_reader = Mock()
        mock_binary_reader.file = mock_input_file
        mock_ncch_reader.reader = mock_binary_reader

        mock_binary_writer = Mock()
        mock_binary_writer.file = mock_output_file
        mock_cia_writer.writer = mock_binary_writer

        service = ConversionService(
            ncsd_reader=mock_ncsd_reader,
            ncch_reader=mock_ncch_reader,
            exefs_reader=mock_exefs_reader,
            cia_writer=mock_cia_writer,
            decryption_service=None,
            hash_validator=mock_hash_validator,
            progress_reporter=mock_progress_reporter,
        )

        # Act - call close multiple times
        service.close()
        service.close()
        service.close()

        # Assert - should handle multiple calls gracefully
        assert mock_input_file.close.call_count >= 1
        assert mock_output_file.close.call_count >= 1
