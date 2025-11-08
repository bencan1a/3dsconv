"""Tests for format validator."""

import pytest

from dsconv.models.ncsd import NCSDPartition
from dsconv.validation.format_validator import FormatValidator


class TestValidateNCSDMagic:
    """Tests for validate_ncsd_magic method."""

    def test_validate_with_valid_ncsd_magic(self):
        """Test validation succeeds with valid NCSD magic bytes."""
        # Arrange
        magic = b"NCSD"

        # Act & Assert (should not raise)
        FormatValidator.validate_ncsd_magic(magic)

    def test_validate_with_invalid_magic_raises_error(self):
        """Test validation raises ValueError with invalid magic bytes."""
        # Arrange
        magic = b"XXXX"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCSD magic, not a CCI file"):
            FormatValidator.validate_ncsd_magic(magic)

    def test_validate_with_empty_bytes_raises_error(self):
        """Test validation raises ValueError with empty bytes."""
        # Arrange
        magic = b""

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCSD magic, not a CCI file"):
            FormatValidator.validate_ncsd_magic(magic)

    def test_validate_with_ncch_magic_raises_error(self):
        """Test validation raises ValueError when NCCH magic is provided."""
        # Arrange
        magic = b"NCCH"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCSD magic, not a CCI file"):
            FormatValidator.validate_ncsd_magic(magic)

    def test_validate_with_partial_match_raises_error(self):
        """Test validation raises ValueError with partial match."""
        # Arrange
        magic = b"NCS"  # Too short

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCSD magic, not a CCI file"):
            FormatValidator.validate_ncsd_magic(magic)

    def test_validate_with_lowercase_raises_error(self):
        """Test validation raises ValueError with lowercase magic."""
        # Arrange
        magic = b"ncsd"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCSD magic, not a CCI file"):
            FormatValidator.validate_ncsd_magic(magic)

    def test_validate_with_extra_bytes_raises_error(self):
        """Test validation raises ValueError with extra bytes."""
        # Arrange
        magic = b"NCSD\x00"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCSD magic, not a CCI file"):
            FormatValidator.validate_ncsd_magic(magic)

    @pytest.mark.parametrize(
        "invalid_magic",
        [
            b"\x00\x00\x00\x00",  # Null bytes
            b"AAAA",  # Random letters
            b"1234",  # Digits
            b"\xff\xff\xff\xff",  # Invalid bytes
            b"NCCH",  # Wrong magic (NCCH instead of NCSD)
            b"ncsd",  # Lowercase
        ],
    )
    def test_validate_with_various_invalid_values(self, invalid_magic):
        """Test validation raises error for various invalid magic values."""
        with pytest.raises(ValueError, match="Invalid NCSD magic, not a CCI file"):
            FormatValidator.validate_ncsd_magic(invalid_magic)

    def test_error_message_is_descriptive(self):
        """Test that error message is clear and descriptive."""
        # Arrange
        magic = b"FAKE"

        # Act & Assert
        try:
            FormatValidator.validate_ncsd_magic(magic)
            pytest.fail("Expected ValueError to be raised")
        except ValueError as e:
            error_message = str(e)
            assert "Invalid NCSD magic" in error_message
            assert "not a CCI file" in error_message


class TestValidateNCCHMagic:
    """Tests for validate_ncch_magic method."""

    def test_validate_with_valid_ncch_magic(self):
        """Test validation succeeds with valid NCCH magic bytes."""
        # Arrange
        magic = b"NCCH"

        # Act & Assert (should not raise)
        FormatValidator.validate_ncch_magic(magic)

    def test_validate_with_invalid_magic_raises_error(self):
        """Test validation raises ValueError with invalid magic bytes."""
        # Arrange
        magic = b"XXXX"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCCH magic, not a valid partition"):
            FormatValidator.validate_ncch_magic(magic)

    def test_validate_with_empty_bytes_raises_error(self):
        """Test validation raises ValueError with empty bytes."""
        # Arrange
        magic = b""

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCCH magic, not a valid partition"):
            FormatValidator.validate_ncch_magic(magic)

    def test_validate_with_ncsd_magic_raises_error(self):
        """Test validation raises ValueError when NCSD magic is provided."""
        # Arrange
        magic = b"NCSD"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCCH magic, not a valid partition"):
            FormatValidator.validate_ncch_magic(magic)

    def test_validate_with_partial_match_raises_error(self):
        """Test validation raises ValueError with partial match."""
        # Arrange
        magic = b"NCC"  # Too short

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCCH magic, not a valid partition"):
            FormatValidator.validate_ncch_magic(magic)

    def test_validate_with_lowercase_raises_error(self):
        """Test validation raises ValueError with lowercase magic."""
        # Arrange
        magic = b"ncch"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCCH magic, not a valid partition"):
            FormatValidator.validate_ncch_magic(magic)

    def test_validate_with_extra_bytes_raises_error(self):
        """Test validation raises ValueError with extra bytes."""
        # Arrange
        magic = b"NCCH\x00"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCCH magic, not a valid partition"):
            FormatValidator.validate_ncch_magic(magic)

    @pytest.mark.parametrize(
        "invalid_magic",
        [
            b"\x00\x00\x00\x00",  # Null bytes
            b"AAAA",  # Random letters
            b"1234",  # Digits
            b"\xff\xff\xff\xff",  # Invalid bytes
            b"NCSD",  # Wrong magic (NCSD instead of NCCH)
            b"ncch",  # Lowercase
        ],
    )
    def test_validate_with_various_invalid_values(self, invalid_magic):
        """Test validation raises error for various invalid magic values."""
        with pytest.raises(ValueError, match="Invalid NCCH magic, not a valid partition"):
            FormatValidator.validate_ncch_magic(invalid_magic)

    def test_error_message_is_descriptive(self):
        """Test that error message is clear and descriptive."""
        # Arrange
        magic = b"FAKE"

        # Act & Assert
        try:
            FormatValidator.validate_ncch_magic(magic)
            pytest.fail("Expected ValueError to be raised")
        except ValueError as e:
            error_message = str(e)
            assert "Invalid NCCH magic" in error_message
            assert "not a valid partition" in error_message


class TestValidatePartitionExists:
    """Tests for validate_partition_exists method."""

    def test_validate_with_existing_game_partition(self):
        """Test validation succeeds with existing game partition."""
        # Arrange
        partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="game")

        # Act & Assert (should not raise)
        FormatValidator.validate_partition_exists(partition)

    def test_validate_with_existing_manual_partition(self):
        """Test validation succeeds with existing manual partition."""
        # Arrange
        partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="manual")

        # Act & Assert (should not raise)
        FormatValidator.validate_partition_exists(partition)

    def test_validate_with_existing_dlpchild_partition(self):
        """Test validation succeeds with existing dlpchild partition."""
        # Arrange
        partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="dlpchild")

        # Act & Assert (should not raise)
        FormatValidator.validate_partition_exists(partition)

    def test_validate_with_existing_unknown_partition(self):
        """Test validation succeeds with existing unknown partition."""
        # Arrange
        partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="unknown")

        # Act & Assert (should not raise)
        FormatValidator.validate_partition_exists(partition)

    def test_validate_with_zero_offset_partition(self):
        """Test validation succeeds with partition at offset 0."""
        # Arrange
        partition = NCSDPartition(offset=0, size=0x1000, partition_type="game")

        # Act & Assert (should not raise)
        FormatValidator.validate_partition_exists(partition)

    def test_validate_with_large_partition(self):
        """Test validation succeeds with large partition."""
        # Arrange
        partition = NCSDPartition(offset=0x1000, size=0xFFFFFFFF, partition_type="game")

        # Act & Assert (should not raise)
        FormatValidator.validate_partition_exists(partition)

    def test_validate_with_none_raises_error(self):
        """Test validation raises ValueError when partition is None."""
        # Arrange
        partition = None

        # Act & Assert
        with pytest.raises(ValueError, match="Required partition not found"):
            FormatValidator.validate_partition_exists(partition)

    def test_error_message_is_descriptive(self):
        """Test that error message is clear and descriptive."""
        # Arrange
        partition = None

        # Act & Assert
        try:
            FormatValidator.validate_partition_exists(partition)
            pytest.fail("Expected ValueError to be raised")
        except ValueError as e:
            error_message = str(e)
            assert "Required partition not found" in error_message

    @pytest.mark.parametrize(
        "partition_type",
        ["game", "manual", "dlpchild", "unknown"],
    )
    def test_validate_with_all_partition_types(self, partition_type):
        """Test validation succeeds for all valid partition types."""
        # Arrange
        partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type=partition_type)

        # Act & Assert (should not raise)
        FormatValidator.validate_partition_exists(partition)


class TestFormatValidator:
    """Tests for FormatValidator class."""

    def test_class_exists(self):
        """Test that FormatValidator class exists."""
        assert FormatValidator is not None

    def test_all_methods_are_static(self):
        """Test that all validation methods are static."""
        # All methods should be accessible without instantiation
        assert callable(FormatValidator.validate_ncsd_magic)
        assert callable(FormatValidator.validate_ncch_magic)
        assert callable(FormatValidator.validate_partition_exists)

    def test_validator_has_no_instance_state(self):
        """Test that validator doesn't maintain instance state."""
        # Should be able to call methods without creating instance
        # These calls should not affect each other
        FormatValidator.validate_ncsd_magic(b"NCSD")
        FormatValidator.validate_ncch_magic(b"NCCH")

        partition = NCSDPartition(offset=0, size=100, partition_type="game")
        FormatValidator.validate_partition_exists(partition)

        # No state should be maintained between calls
        FormatValidator.validate_ncsd_magic(b"NCSD")

    def test_methods_have_no_side_effects(self):
        """Test that validation methods have no side effects."""
        # Arrange
        magic_ncsd = b"NCSD"
        magic_ncch = b"NCCH"
        partition = NCSDPartition(offset=0, size=100, partition_type="game")

        # Act - Call methods multiple times
        FormatValidator.validate_ncsd_magic(magic_ncsd)
        FormatValidator.validate_ncsd_magic(magic_ncsd)

        FormatValidator.validate_ncch_magic(magic_ncch)
        FormatValidator.validate_ncch_magic(magic_ncch)

        FormatValidator.validate_partition_exists(partition)
        FormatValidator.validate_partition_exists(partition)

        # Assert - Objects should be unchanged
        assert magic_ncsd == b"NCSD"
        assert magic_ncch == b"NCCH"
        assert partition.offset == 0
        assert partition.size == 100

    def test_validator_can_be_used_without_instantiation(self):
        """Test that validator methods can be called without creating instance."""
        # Should not need to create FormatValidator() instance
        # All methods are static
        FormatValidator.validate_ncsd_magic(b"NCSD")
        FormatValidator.validate_ncch_magic(b"NCCH")

        partition = NCSDPartition(offset=0, size=100, partition_type="game")
        FormatValidator.validate_partition_exists(partition)

    def test_multiple_validations_in_sequence(self):
        """Test performing multiple validations in sequence."""
        # Arrange
        partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="game")

        # Act & Assert - Should all succeed
        FormatValidator.validate_ncsd_magic(b"NCSD")
        FormatValidator.validate_ncch_magic(b"NCCH")
        FormatValidator.validate_partition_exists(partition)

        # Repeat
        FormatValidator.validate_ncsd_magic(b"NCSD")
        FormatValidator.validate_ncch_magic(b"NCCH")
        FormatValidator.validate_partition_exists(partition)

    def test_error_handling_doesnt_affect_subsequent_calls(self):
        """Test that raising an error doesn't affect subsequent calls."""
        # First call raises error
        with pytest.raises(ValueError):
            FormatValidator.validate_ncsd_magic(b"XXXX")

        # Subsequent valid call should work
        FormatValidator.validate_ncsd_magic(b"NCSD")

        # Another error
        with pytest.raises(ValueError):
            FormatValidator.validate_ncch_magic(b"YYYY")

        # Subsequent valid call should work
        FormatValidator.validate_ncch_magic(b"NCCH")
