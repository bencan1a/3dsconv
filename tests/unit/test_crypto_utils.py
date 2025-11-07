"""
Unit tests for cryptographic utility functions in 3dsconv.

This module tests the pure cryptographic functions, particularly the rol() function
which is critical for key derivation operations.
"""

import pytest

from dsconv.utils import rol


class TestRol:
    """Test suite for the rol() (rotate left) function."""

    def test_rol_basic_rotation(self):
        """Test basic left rotation with 8-bit value."""
        # Arrange
        val = 0b11010010  # 210 in decimal
        r_bits = 3
        max_bits = 8

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        # 11010010 rotated left by 3 bits = 10010110 = 150
        expected = 0b10010110
        assert result == expected

    def test_rol_zero_bits(self):
        """Test rotation by zero bits returns the original value."""
        # Arrange
        val = 0b11110000
        r_bits = 0
        max_bits = 8

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        assert result == val

    def test_rol_full_rotation(self):
        """Test that rotation by max_bits returns the original value."""
        # Arrange
        val = 0b10101010
        r_bits = 8
        max_bits = 8

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        assert result == val

    def test_rol_128bit_values(self):
        """Test rotation with 128-bit values (used in key derivation)."""
        # Arrange
        # A 128-bit value (16 bytes)
        val = 0x0123456789ABCDEF0123456789ABCDEF
        r_bits = 8
        max_bits = 128

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        # Rotating left by 8 bits should move the high byte to the low position
        # Original: 01 23 45 67 89 AB CD EF 01 23 45 67 89 AB CD EF
        # Rotated:  23 45 67 89 AB CD EF 01 23 45 67 89 AB CD EF 01
        expected = 0x23456789ABCDEF0123456789ABCDEF01
        assert result == expected

    def test_rol_128bit_single_bit(self):
        """Test single bit rotation with 128-bit values."""
        # Arrange
        val = 0x80000000000000000000000000000000  # High bit set
        r_bits = 1
        max_bits = 128

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        # High bit should move to position 1, and also wrap to low bit
        expected = 0x00000000000000000000000000000001
        assert result == expected

    def test_rol_edge_case_large_rotation(self):
        """Test rotation with r_bits larger than max_bits."""
        # Arrange
        val = 0b11000011
        r_bits = 11  # More than 8 bits, should be equivalent to 11 % 8 = 3
        max_bits = 8

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        # Should be same as rotating by 3 bits
        expected = rol(val, 3, max_bits)
        assert result == expected

    def test_rol_edge_case_zero_value(self):
        """Test rotation of zero value."""
        # Arrange
        val = 0
        r_bits = 5
        max_bits = 32

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        assert result == 0

    def test_rol_edge_case_all_ones(self):
        """Test rotation of all ones (max value for given bit width)."""
        # Arrange
        max_bits = 16
        val = (2**max_bits) - 1  # All bits set
        r_bits = 5

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        # Rotating all ones should still be all ones
        assert result == val

    @pytest.mark.parametrize("max_bits", [8, 16, 32, 64, 128])
    def test_rol_multiple_full_rotations(self, max_bits):
        """Test that multiple full rotations return to original value."""
        # Arrange
        val = 0xABCD if max_bits >= 16 else 0xAB
        if max_bits > 16:
            val = val << (max_bits - 16)
        r_bits = max_bits * 3  # 3 full rotations

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        assert result == val

    @pytest.mark.parametrize(
        "r_bits,expected",
        [
            (1, 0b01010101),
            (2, 0b10101010),
            (3, 0b01010101),
            (4, 0b10101010),
            (7, 0b01010101),  # 7 bits rotation of 10101010 = 01010101
        ],
    )
    def test_rol_alternating_bits_pattern(self, r_bits, expected):
        """Test rotation of alternating bit pattern."""
        # Arrange
        val = 0b10101010
        max_bits = 8

        # Act
        result = rol(val, r_bits, max_bits)

        # Assert
        assert result == expected
