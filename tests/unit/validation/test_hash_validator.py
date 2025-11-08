"""Tests for HashValidator service."""

import hashlib

import pytest

from dsconv.validation.hash_validator import HashValidator


class TestHashValidator:
    """Tests for HashValidator class."""

    def test_init_with_default_ignore_flag(self):
        """Test creating validator with default ignore_bad_hashes flag."""
        # Arrange & Act
        validator = HashValidator()

        # Assert
        assert validator.ignore_bad_hashes is False

    def test_init_with_ignore_bad_hashes_true(self):
        """Test creating validator with ignore_bad_hashes=True."""
        # Arrange & Act
        validator = HashValidator(ignore_bad_hashes=True)

        # Assert
        assert validator.ignore_bad_hashes is True

    def test_init_with_ignore_bad_hashes_false(self):
        """Test creating validator with ignore_bad_hashes=False."""
        # Arrange & Act
        validator = HashValidator(ignore_bad_hashes=False)

        # Assert
        assert validator.ignore_bad_hashes is False


class TestValidateExtheaderHash:
    """Tests for validate_extheader_hash method."""

    def test_validate_with_matching_hash_returns_true(self):
        """Test validation with matching hash returns True."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        extheader = b"test extended header data"
        expected_hash = hashlib.sha256(extheader).digest()

        # Act
        result = validator.validate_extheader_hash(extheader, expected_hash)

        # Assert
        assert result is True

    def test_validate_with_mismatched_hash_and_ignore_false_returns_false(self):
        """Test validation with mismatched hash and ignore=False returns False."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        extheader = b"test extended header data"
        wrong_hash = hashlib.sha256(b"different data").digest()

        # Act
        result = validator.validate_extheader_hash(extheader, wrong_hash)

        # Assert
        assert result is False

    def test_validate_with_mismatched_hash_and_ignore_true_returns_true(self):
        """Test validation with mismatched hash and ignore=True returns True."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=True)
        extheader = b"test extended header data"
        wrong_hash = hashlib.sha256(b"different data").digest()

        # Act
        result = validator.validate_extheader_hash(extheader, wrong_hash)

        # Assert
        assert result is True

    def test_validate_with_empty_extheader(self):
        """Test validation with empty extheader data."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        extheader = b""
        expected_hash = hashlib.sha256(extheader).digest()

        # Act
        result = validator.validate_extheader_hash(extheader, expected_hash)

        # Assert
        assert result is True

    def test_validate_with_known_sha256_test_vector(self):
        """Test validation with known SHA-256 test vector."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        # Test vector: "abc" -> known SHA-256 hash
        extheader = b"abc"
        expected_hash = bytes.fromhex(
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )

        # Act
        result = validator.validate_extheader_hash(extheader, expected_hash)

        # Assert
        assert result is True

    def test_validate_with_wrong_hash_for_known_test_vector(self):
        """Test validation with wrong hash for known test vector."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        extheader = b"abc"
        wrong_hash = bytes.fromhex(
            "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        )

        # Act
        result = validator.validate_extheader_hash(extheader, wrong_hash)

        # Assert
        assert result is False

    @pytest.mark.parametrize(
        "data,expected_hash_hex",
        [
            # Empty string
            (b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            # Single character
            (b"a", "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"),
            # "abc"
            (b"abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
            # Longer string
            (
                b"The quick brown fox jumps over the lazy dog",
                "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592",
            ),
        ],
    )
    def test_validate_with_various_known_sha256_vectors(self, data, expected_hash_hex):
        """Test validation with various known SHA-256 test vectors."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        expected_hash = bytes.fromhex(expected_hash_hex)

        # Act
        result = validator.validate_extheader_hash(data, expected_hash)

        # Assert
        assert result is True

    def test_validate_with_large_extheader(self):
        """Test validation with large extended header data."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        # Create 1MB of data
        extheader = b"A" * (1024 * 1024)
        expected_hash = hashlib.sha256(extheader).digest()

        # Act
        result = validator.validate_extheader_hash(extheader, expected_hash)

        # Assert
        assert result is True

    def test_validate_preserves_original_data(self):
        """Test that validation doesn't modify the input data."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        original_data = b"test data"
        extheader = original_data
        expected_hash = hashlib.sha256(extheader).digest()

        # Act
        validator.validate_extheader_hash(extheader, expected_hash)

        # Assert
        assert extheader == original_data


class TestComputeContentHash:
    """Tests for compute_content_hash method."""

    def test_compute_hash_returns_32_bytes(self):
        """Test that computed hash is 32 bytes (SHA-256 output size)."""
        # Arrange
        validator = HashValidator()
        content = b"test content"

        # Act
        hash_result = validator.compute_content_hash(content)

        # Assert
        assert len(hash_result) == 32

    def test_compute_hash_returns_bytes(self):
        """Test that computed hash returns bytes type."""
        # Arrange
        validator = HashValidator()
        content = b"test content"

        # Act
        hash_result = validator.compute_content_hash(content)

        # Assert
        assert isinstance(hash_result, bytes)

    def test_compute_hash_with_empty_content(self):
        """Test computing hash of empty content."""
        # Arrange
        validator = HashValidator()
        content = b""
        expected_hash = bytes.fromhex(
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        )

        # Act
        hash_result = validator.compute_content_hash(content)

        # Assert
        assert hash_result == expected_hash

    def test_compute_hash_with_known_test_vector(self):
        """Test computing hash with known SHA-256 test vector."""
        # Arrange
        validator = HashValidator()
        content = b"abc"
        expected_hash = bytes.fromhex(
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        )

        # Act
        hash_result = validator.compute_content_hash(content)

        # Assert
        assert hash_result == expected_hash

    @pytest.mark.parametrize(
        "content,expected_hash_hex",
        [
            (b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            (b"a", "ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb"),
            (b"abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
            (b"message digest", "f7846f55cf23e14eebeab5b4e1550cad5b509e3348fbc4efa3a1413d393cb650"),
            (
                b"The quick brown fox jumps over the lazy dog",
                "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592",
            ),
        ],
    )
    def test_compute_hash_with_various_known_vectors(self, content, expected_hash_hex):
        """Test computing hash with various known SHA-256 test vectors."""
        # Arrange
        validator = HashValidator()
        expected_hash = bytes.fromhex(expected_hash_hex)

        # Act
        hash_result = validator.compute_content_hash(content)

        # Assert
        assert hash_result == expected_hash

    def test_compute_hash_deterministic(self):
        """Test that computing hash multiple times gives same result."""
        # Arrange
        validator = HashValidator()
        content = b"test content"

        # Act
        hash1 = validator.compute_content_hash(content)
        hash2 = validator.compute_content_hash(content)
        hash3 = validator.compute_content_hash(content)

        # Assert
        assert hash1 == hash2 == hash3

    def test_compute_hash_different_content_different_hash(self):
        """Test that different content produces different hashes."""
        # Arrange
        validator = HashValidator()
        content1 = b"content one"
        content2 = b"content two"

        # Act
        hash1 = validator.compute_content_hash(content1)
        hash2 = validator.compute_content_hash(content2)

        # Assert
        assert hash1 != hash2

    def test_compute_hash_with_large_content(self):
        """Test computing hash of large content."""
        # Arrange
        validator = HashValidator()
        # Create 10MB of data
        content = b"X" * (10 * 1024 * 1024)

        # Act
        hash_result = validator.compute_content_hash(content)

        # Assert
        assert len(hash_result) == 32
        # Verify it matches hashlib directly
        expected = hashlib.sha256(content).digest()
        assert hash_result == expected

    def test_compute_hash_preserves_original_data(self):
        """Test that computing hash doesn't modify the input data."""
        # Arrange
        validator = HashValidator()
        original_data = b"test data"
        content = original_data

        # Act
        validator.compute_content_hash(content)

        # Assert
        assert content == original_data

    def test_compute_hash_with_binary_data(self):
        """Test computing hash with binary data containing null bytes."""
        # Arrange
        validator = HashValidator()
        content = b"\x00\x01\x02\x03\xff\xfe\xfd"

        # Act
        hash_result = validator.compute_content_hash(content)

        # Assert
        assert len(hash_result) == 32
        expected = hashlib.sha256(content).digest()
        assert hash_result == expected

    @pytest.mark.parametrize("size", [1, 16, 32, 64, 128, 256, 512, 1024, 4096])
    def test_compute_hash_various_sizes(self, size):
        """Test computing hash with various data sizes."""
        # Arrange
        validator = HashValidator()
        content = b"B" * size

        # Act
        hash_result = validator.compute_content_hash(content)

        # Assert
        assert len(hash_result) == 32
        expected = hashlib.sha256(content).digest()
        assert hash_result == expected


class TestHashValidatorIntegration:
    """Integration tests for HashValidator."""

    def test_compute_and_validate_workflow(self):
        """Test complete workflow of computing and validating hash."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        content = b"Extended header content for testing"

        # Act
        computed_hash = validator.compute_content_hash(content)
        is_valid = validator.validate_extheader_hash(content, computed_hash)

        # Assert
        assert is_valid is True

    def test_ignore_flag_affects_validation_only(self):
        """Test that ignore flag only affects validation, not hash computation."""
        # Arrange
        validator_ignore = HashValidator(ignore_bad_hashes=True)
        validator_strict = HashValidator(ignore_bad_hashes=False)
        content = b"test content"

        # Act
        hash_ignore = validator_ignore.compute_content_hash(content)
        hash_strict = validator_strict.compute_content_hash(content)

        # Assert - both should compute the same hash
        assert hash_ignore == hash_strict

    def test_multiple_validations_with_same_validator(self):
        """Test performing multiple validations with the same validator instance."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        content1 = b"content one"
        content2 = b"content two"
        hash1 = hashlib.sha256(content1).digest()
        hash2 = hashlib.sha256(content2).digest()

        # Act
        result1 = validator.validate_extheader_hash(content1, hash1)
        result2 = validator.validate_extheader_hash(content2, hash2)
        result3 = validator.validate_extheader_hash(content1, hash2)  # Wrong hash

        # Assert
        assert result1 is True
        assert result2 is True
        assert result3 is False

    def test_validator_is_stateless(self):
        """Test that validator maintains no state between calls."""
        # Arrange
        validator = HashValidator(ignore_bad_hashes=False)
        content = b"stateless test"
        correct_hash = hashlib.sha256(content).digest()
        wrong_hash = hashlib.sha256(b"wrong").digest()

        # Act - alternate between correct and wrong hashes
        result1 = validator.validate_extheader_hash(content, correct_hash)
        result2 = validator.validate_extheader_hash(content, wrong_hash)
        result3 = validator.validate_extheader_hash(content, correct_hash)
        result4 = validator.validate_extheader_hash(content, wrong_hash)

        # Assert - each call is independent
        assert result1 is True
        assert result2 is False
        assert result3 is True
        assert result4 is False
