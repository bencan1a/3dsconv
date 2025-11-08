"""Hash validation service for validating SHA-256 hashes."""

import hashlib


class HashValidator:
    """Service for validating SHA-256 hashes.

    This service provides methods for validating content hashes and computing
    SHA-256 hashes. It supports an optional ignore mode for bad hashes, which
    can be useful when working with files that have incorrect hash values.

    Attributes:
        ignore_bad_hashes: If True, validation failures are ignored and True is returned.
                          If False, validation failures return False.
    """

    def __init__(self, ignore_bad_hashes: bool = False):
        """Initialize HashValidator with configuration.

        Args:
            ignore_bad_hashes: If True, validation failures are ignored.
                              Default is False.
        """
        self.ignore_bad_hashes = ignore_bad_hashes

    def validate_extheader_hash(self, extheader: bytes, expected_hash: bytes) -> bool:
        """Validate extended header hash.

        Computes the SHA-256 hash of the extended header and compares it
        to the expected hash value.

        Args:
            extheader: The extended header data to validate
            expected_hash: The expected SHA-256 hash (32 bytes)

        Returns:
            True if hash matches or if ignore_bad_hashes is True,
            False if hash doesn't match and ignore_bad_hashes is False

        Examples:
            >>> validator = HashValidator(ignore_bad_hashes=False)
            >>> data = b"test data"
            >>> expected = hashlib.sha256(data).digest()
            >>> validator.validate_extheader_hash(data, expected)
            True
        """
        actual_hash = hashlib.sha256(extheader).digest()

        if actual_hash != expected_hash:
            if self.ignore_bad_hashes:
                return True  # Ignore and continue
            return False

        return True

    def compute_content_hash(self, content: bytes) -> bytes:
        """Compute SHA-256 hash of content.

        Args:
            content: The content data to hash

        Returns:
            The SHA-256 hash as bytes (32 bytes)

        Examples:
            >>> validator = HashValidator()
            >>> data = b"test data"
            >>> hash_bytes = validator.compute_content_hash(data)
            >>> len(hash_bytes)
            32
        """
        return hashlib.sha256(content).digest()
