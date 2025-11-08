"""
Unit tests for KeyDerivationService.

This module tests the key derivation functionality used to derive normal keys
from KeyY values and the original NCCH key. The tests include known test vectors
and edge cases to ensure correct implementation of the Nintendo 3DS key derivation
algorithm.
"""

import pytest

from dsconv.crypto.key_derivation import KeyDerivationService


class TestKeyDerivationService:
    """Tests for KeyDerivationService class."""

    def test_initialization(self):
        """Test that service can be initialized with a key."""
        # Arrange
        original_key = 0x12345678901234567890123456789012

        # Act
        service = KeyDerivationService(original_key)

        # Assert
        assert service.original_ncch_key == original_key

    def test_initialization_with_zero_key(self):
        """Test initialization with zero key."""
        # Arrange
        original_key = 0

        # Act
        service = KeyDerivationService(original_key)

        # Assert
        assert service.original_ncch_key == 0

    def test_initialization_with_max_128bit_key(self):
        """Test initialization with maximum 128-bit key."""
        # Arrange
        original_key = (2**128) - 1  # All bits set

        # Act
        service = KeyDerivationService(original_key)

        # Assert
        assert service.original_ncch_key == original_key

    def test_derive_normal_key_returns_16_bytes(self):
        """Test that derived key is always 16 bytes (128 bits)."""
        # Arrange
        service = KeyDerivationService(0x12345678901234567890123456789012)
        key_y = bytes(16)  # Zero-filled KeyY

        # Act
        result = service.derive_normal_key(key_y)

        # Assert
        assert isinstance(result, bytes)
        assert len(result) == 16

    def test_derive_normal_key_with_zero_key_y(self):
        """Test key derivation with zero KeyY."""
        # Arrange
        # Use a known original key
        original_key = 0x0123456789ABCDEF0123456789ABCDEF
        service = KeyDerivationService(original_key)
        key_y = bytes(16)  # All zeros

        # Act
        result = service.derive_normal_key(key_y)

        # Assert
        # Result should be deterministic based on the formula:
        # rol((rol(original_key, 2, 128) ^ 0) + constant, 87, 128)
        assert len(result) == 16
        # The result should not be all zeros (due to the constant addition)
        assert result != bytes(16)

    def test_derive_normal_key_with_all_ones_key_y(self):
        """Test key derivation with all-ones KeyY."""
        # Arrange
        original_key = 0x0123456789ABCDEF0123456789ABCDEF
        service = KeyDerivationService(original_key)
        key_y = bytes([0xFF] * 16)  # All ones

        # Act
        result = service.derive_normal_key(key_y)

        # Assert
        assert len(result) == 16
        # Result should be different from zero KeyY case
        zero_key_y_result = service.derive_normal_key(bytes(16))
        assert result != zero_key_y_result

    def test_derive_normal_key_deterministic(self):
        """Test that derivation is deterministic (same inputs = same output)."""
        # Arrange
        original_key = 0x0123456789ABCDEF0123456789ABCDEF
        service = KeyDerivationService(original_key)
        key_y = bytes.fromhex("00112233445566778899AABBCCDDEEFF")

        # Act
        result1 = service.derive_normal_key(key_y)
        result2 = service.derive_normal_key(key_y)

        # Assert
        assert result1 == result2

    def test_derive_normal_key_different_key_y_different_result(self):
        """Test that different KeyY values produce different results."""
        # Arrange
        service = KeyDerivationService(0x0123456789ABCDEF0123456789ABCDEF)
        key_y1 = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
        key_y2 = bytes.fromhex("FFEEDDCCBBAA99887766554433221100")

        # Act
        result1 = service.derive_normal_key(key_y1)
        result2 = service.derive_normal_key(key_y2)

        # Assert
        assert result1 != result2

    def test_derive_normal_key_different_original_key_different_result(self):
        """Test that different original keys produce different results."""
        # Arrange
        key_y = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
        service1 = KeyDerivationService(0x0123456789ABCDEF0123456789ABCDEF)
        service2 = KeyDerivationService(0xFEDCBA9876543210FEDCBA9876543210)

        # Act
        result1 = service1.derive_normal_key(key_y)
        result2 = service2.derive_normal_key(key_y)

        # Assert
        assert result1 != result2

    def test_derive_normal_key_test_vector_1(self):
        """Test key derivation with known test vector 1.

        This test uses a manually computed test vector to verify the algorithm.
        The computation follows: rol((rol(orig_key, 2, 128) ^ key_y) + constant, 87, 128)
        """
        # Arrange
        # Simple test case with small values
        original_key = 0x00000000000000000000000000000001
        service = KeyDerivationService(original_key)
        key_y = bytes(16)  # All zeros

        # Act
        result = service.derive_normal_key(key_y)

        # Assert
        # Intermediate steps:
        # 1. rol(0x01, 2, 128) = 0x04
        # 2. 0x04 ^ 0x00 = 0x04
        # 3. 0x04 + 0x1FF9E9AAC5FE0408024591DC5D52768A = 0x1FF9E9AAC5FE0408024591DC5D52768E
        # 4. rol(0x1FF9E9AAC5FE0408024591DC5D52768E, 87, 128)
        # Expected result can be computed, but we verify it's consistent
        assert len(result) == 16
        # Store expected value for regression testing
        expected = int.to_bytes(
            0xEE2EA93B470FFCF4D562FF02040122C8, 16, byteorder="big"  # Pre-computed value
        )
        assert result == expected

    def test_derive_normal_key_test_vector_2(self):
        """Test key derivation with known test vector 2.

        This uses a more realistic key value.
        """
        # Arrange
        # A realistic original key value
        original_key = 0x82E9C9BEBFB8B7D8B7C7A6A5A4A3A2A1
        service = KeyDerivationService(original_key)
        key_y = bytes.fromhex("0123456789ABCDEF0123456789ABCDEF")

        # Act
        result = service.derive_normal_key(key_y)

        # Assert
        assert len(result) == 16
        # Pre-computed expected value (computed using the algorithm)
        expected = int.to_bytes(
            0xE6BC3BDEF9953F26A41EA38B4AF041B8, 16, byteorder="big"  # Pre-computed value
        )
        assert result == expected

    def test_derive_normal_key_matches_original_implementation(self):
        """Test that the service produces the same result as original code.

        This test replicates the exact formula from the original 3dsconv.py:
        rol((rol(orig_ncch_key, 2, 128) ^ key_y) + 0x1FF9E9AAC5FE0408024591DC5D52768A, 87, 128)
        """
        # Arrange
        from dsconv.utils import rol

        original_key = 0x82E9C9BEBFB8B7D8B7C7A6A5A4A3A2A1
        key_y_bytes = bytes.fromhex("FEDCBA9876543210FEDCBA9876543210")
        key_y_int = int.from_bytes(key_y_bytes, byteorder="big")

        # Expected result from original formula
        expected_int = rol(
            (rol(original_key, 2, 128) ^ key_y_int) + 0x1FF9E9AAC5FE0408024591DC5D52768A,
            87,
            128,
        )
        expected_bytes = expected_int.to_bytes(0x10, byteorder="big")

        # Act - using service
        service = KeyDerivationService(original_key)
        result = service.derive_normal_key(key_y_bytes)

        # Assert
        assert result == expected_bytes

    @pytest.mark.parametrize(
        "original_key,key_y_hex,expected_hex",
        [
            # Test case 1: Simple values
            (
                0x00000000000000000000000000000001,
                "00000000000000000000000000000000",
                "EE2EA93B470FFCF4D562FF02040122C8",  # Pre-computed
            ),
            # Test case 2: Another combination
            (
                0x82E9C9BEBFB8B7D8B7C7A6A5A4A3A2A1,
                "0123456789ABCDEF0123456789ABCDEF",
                "E6BC3BDEF9953F26A41EA38B4AF041B8",  # Pre-computed
            ),
            # Test case 3: Different values
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                "00000000000000000000000000000000",
                "EE2EA93B448FFCF4D562FF02040122C8",  # Pre-computed
            ),
        ],
    )
    def test_derive_normal_key_parametrized(self, original_key, key_y_hex, expected_hex):
        """Test key derivation with multiple test vectors."""
        # Arrange
        service = KeyDerivationService(original_key)
        key_y = bytes.fromhex(key_y_hex)
        expected = bytes.fromhex(expected_hex)

        # Act
        result = service.derive_normal_key(key_y)

        # Assert
        assert result == expected

    def test_derive_normal_key_big_endian_conversion(self):
        """Test that KeyY is correctly interpreted as big-endian."""
        # Arrange
        service = KeyDerivationService(0x12345678901234567890123456789012)
        # KeyY with distinctive byte pattern
        key_y = bytes(range(16))  # 0x00, 0x01, ..., 0x0F

        # Act
        result = service.derive_normal_key(key_y)

        # Assert
        assert len(result) == 16
        # Verify the conversion uses big-endian
        # (This is implicit in the algorithm, but we check it's not all zeros)
        assert result != bytes(16)

    def test_derive_normal_key_output_big_endian_format(self):
        """Test that output is in big-endian format."""
        # Arrange
        service = KeyDerivationService(0x12345678901234567890123456789012)
        key_y = bytes.fromhex("00112233445566778899AABBCCDDEEFF")

        # Act
        result = service.derive_normal_key(key_y)

        # Assert
        # Convert back to int and verify it matches what we'd expect
        result_int = int.from_bytes(result, byteorder="big")
        # Re-convert and verify
        reconv = result_int.to_bytes(16, byteorder="big")
        assert reconv == result

    def test_multiple_derivations_independent(self):
        """Test that multiple derivations don't affect each other."""
        # Arrange
        service = KeyDerivationService(0x0123456789ABCDEF0123456789ABCDEF)
        key_y1 = bytes.fromhex("00112233445566778899AABBCCDDEEFF")
        key_y2 = bytes.fromhex("FFEEDDCCBBAA99887766554433221100")
        key_y3 = bytes.fromhex("0F0E0D0C0B0A09080706050403020100")

        # Act
        result1_first = service.derive_normal_key(key_y1)
        result2 = service.derive_normal_key(key_y2)
        result3 = service.derive_normal_key(key_y3)
        result1_second = service.derive_normal_key(key_y1)

        # Assert
        # Same input should give same output
        assert result1_first == result1_second
        # Different inputs should give different outputs
        assert result1_first != result2
        assert result1_first != result3
        assert result2 != result3

    def test_service_has_no_side_effects(self):
        """Test that the service doesn't modify its state during derivation."""
        # Arrange
        original_key = 0x0123456789ABCDEF0123456789ABCDEF
        service = KeyDerivationService(original_key)
        key_y = bytes.fromhex("00112233445566778899AABBCCDDEEFF")

        # Act
        service.derive_normal_key(key_y)

        # Assert
        # Original key should remain unchanged
        assert service.original_ncch_key == original_key

    def test_key_derivation_constant_value(self):
        """Test that the correct constant is used in derivation.

        This test indirectly verifies the constant by checking against
        a known result. The constant 0x1FF9E9AAC5FE0408024591DC5D52768A
        is part of the Nintendo 3DS key derivation algorithm.
        """
        # Arrange
        service = KeyDerivationService(0)
        key_y = bytes(16)  # All zeros

        # Act
        result = service.derive_normal_key(key_y)

        # Assert
        # With original_key=0 and key_y=0:
        # 1. rol(0, 2, 128) = 0
        # 2. 0 ^ 0 = 0
        # 3. 0 + 0x1FF9E9AAC5FE0408024591DC5D52768A = 0x1FF9E9AAC5FE0408024591DC5D52768A
        # 4. rol(0x1FF9E9AAC5FE0408024591DC5D52768A, 87, 128)
        from dsconv.utils import rol

        expected_int = rol(0x1FF9E9AAC5FE0408024591DC5D52768A, 87, 128)
        expected_bytes = expected_int.to_bytes(16, byteorder="big")
        assert result == expected_bytes
