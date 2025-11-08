"""
Key provider service for 3dsconv.

This module implements the Repository pattern for loading encryption keys
from various sources (prod.keys files, boot9 dumps). It abstracts the key
loading logic into testable, dependency-injected services.
"""

import hashlib
import os
from abc import ABC, abstractmethod


class KeyProviderError(Exception):
    """Base exception for key provider errors."""

    pass


class KeyNotFoundError(KeyProviderError):
    """Raised when a required key is not found in the key source."""

    pass


class InvalidKeyFileError(KeyProviderError):
    """Raised when a key file is invalid or corrupted."""

    pass


class IKeyProvider(ABC):
    """Interface for encryption key providers.

    This interface defines the contract for classes that provide encryption keys
    from various sources (e.g., prod.keys files, boot9 dumps).
    """

    @abstractmethod
    def get_original_ncch_key(self) -> int:
        """Get the original NCCH key (slot 0x2C key X).

        Returns:
            The original NCCH key as an integer

        Raises:
            KeyNotFoundError: If the key cannot be found
            InvalidKeyFileError: If the key file is invalid or corrupted
        """
        pass


class ProdKeysKeyProvider(IKeyProvider):
    """Loads keys from prod.keys file.

    This provider reads the prod.keys file format commonly used by 3DS tools
    to store encryption keys. The file format is:
    - Lines starting with # are comments
    - Empty lines are ignored
    - Key-value pairs: key=value (hexadecimal values)
    """

    def __init__(self, prod_keys_path: str):
        """Initialize the prod.keys key provider.

        Args:
            prod_keys_path: Path to the prod.keys file

        Raises:
            FileNotFoundError: If the prod.keys file doesn't exist
        """
        self.prod_keys_path = prod_keys_path
        if not os.path.isfile(prod_keys_path):
            raise FileNotFoundError(f"prod.keys file not found: {prod_keys_path}")

    def get_original_ncch_key(self) -> int:
        """Get the original NCCH key from prod.keys file.

        Returns:
            The slot 0x2C key as an integer

        Raises:
            KeyNotFoundError: If slot0x2CKey is not found in the file
            InvalidKeyFileError: If the file is invalid
        """
        from dsconv.utils import get_slot0x2c_key_from_prod_keys

        try:
            return get_slot0x2c_key_from_prod_keys(self.prod_keys_path)
        except KeyError as e:
            raise KeyNotFoundError(
                f"slot0x2CKey not found in prod.keys file: {self.prod_keys_path}"
            ) from e
        except (OSError, ValueError) as e:
            raise InvalidKeyFileError(f"Invalid prod.keys file: {self.prod_keys_path}") from e


class Boot9KeyProvider(IKeyProvider):
    """Loads keys from boot9.bin (ARM9 bootROM dump).

    This provider extracts encryption keys from a dump of the ARM9 bootROM.
    It supports both full (0x10000 bytes) and protected (0x8000 bytes) dumps,
    and can load either retail or development keys.
    """

    # MD5 hashes for key validation
    RETAIL_KEY_HASH = "e35bf88330f4f1b2bb6fd5b870a679ca"
    DEV_KEY_HASH = "49aa32c775608af6298ddc0fc6d18a7e"

    # Key location offsets
    KEY_OFFSET_BASE = 0x59D0
    FULL_DUMP_OFFSET = 0x8000
    DEV_KEYS_OFFSET = 0x400

    def __init__(self, boot9_path: str, dev_keys: bool = False):
        """Initialize the boot9 key provider.

        Args:
            boot9_path: Path to boot9.bin file (full or protected dump)
            dev_keys: If True, load development keys; if False, load retail keys

        Raises:
            FileNotFoundError: If the boot9 file doesn't exist
        """
        self.boot9_path = boot9_path
        self.dev_keys = dev_keys

        if not os.path.isfile(boot9_path):
            raise FileNotFoundError(f"boot9 file not found: {boot9_path}")

    def get_original_ncch_key(self) -> int:
        """Extract the original NCCH key from boot9.

        Returns:
            The slot 0x2C key X as an integer

        Raises:
            InvalidKeyFileError: If the boot9 file is invalid or corrupted
        """
        try:
            file_size = os.path.getsize(self.boot9_path)
        except OSError as e:
            raise InvalidKeyFileError(f"Cannot read boot9 file: {self.boot9_path}") from e

        # Calculate key offset based on dump type and key type
        keys_offset = self.KEY_OFFSET_BASE

        # Full dump (0x10000) has additional offset
        if file_size == 0x10000:
            keys_offset += self.FULL_DUMP_OFFSET

        # Development keys have additional offset
        if self.dev_keys:
            keys_offset += self.DEV_KEYS_OFFSET

        try:
            with open(self.boot9_path, "rb") as f:
                # Read the key (16 bytes)
                f.seek(keys_offset)
                key_bytes = f.read(0x10)

                if len(key_bytes) != 0x10:
                    raise InvalidKeyFileError(
                        f"boot9 file too short: expected at least {keys_offset + 0x10} bytes, "
                        f"got {file_size} bytes"
                    )

                # Validate key hash
                # MD5 is used here for integrity verification of a known encryption key
                # from the Nintendo 3DS boot9 ROM, not for cryptographic security.
                # The hash is compared against a hardcoded known-good value.
                key_hash = hashlib.md5(key_bytes).hexdigest()  # codeql[py/weak-cryptographic-algorithm]
                expected_hash = self.DEV_KEY_HASH if self.dev_keys else self.RETAIL_KEY_HASH

                if key_hash != expected_hash:
                    key_type = "development" if self.dev_keys else "retail"
                    raise InvalidKeyFileError(
                        f"Invalid {key_type} key in boot9 file: {self.boot9_path} "
                        f"(expected hash: {expected_hash}, got: {key_hash})"
                    )

                # Convert to integer (big-endian)
                return int.from_bytes(key_bytes, byteorder="big")

        except OSError as e:
            raise InvalidKeyFileError(f"Failed to read boot9 file: {self.boot9_path}") from e


class MockKeyProvider(IKeyProvider):
    """Mock key provider for testing.

    This provider allows tests to inject specific key values without
    requiring actual key files.
    """

    def __init__(self, key_value: int = 0x1234567890ABCDEF1234567890ABCDEF):
        """Initialize the mock key provider.

        Args:
            key_value: The key value to return (default: test value)
        """
        self.key_value = key_value

    def get_original_ncch_key(self) -> int:
        """Get the mock key value.

        Returns:
            The configured key value
        """
        return self.key_value
