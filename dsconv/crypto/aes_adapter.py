"""AES cipher adapters for encryption/decryption operations.

This module provides abstractions for AES cipher operations, allowing
for testability and flexibility in choosing encryption implementations.
"""

from abc import ABC, abstractmethod
from typing import cast


class IAESCipher(ABC):
    """Interface for AES encryption operations.

    This abstract base class defines the contract for AES cipher implementations,
    supporting both encryption and decryption operations in CTR mode.
    """

    @abstractmethod
    def decrypt(self, data: bytes) -> bytes:
        """Decrypt data using AES-CTR mode.

        Args:
            data: Encrypted data to decrypt

        Returns:
            Decrypted data

        Raises:
            ValueError: If data is invalid or cannot be decrypted
        """
        pass

    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using AES-CTR mode.

        Args:
            data: Plain data to encrypt

        Returns:
            Encrypted data

        Raises:
            ValueError: If data is invalid or cannot be encrypted
        """
        pass


class PyAESAdapter(IAESCipher):
    """Adapter wrapping the pyaes library for AES operations.

    This adapter provides a clean interface to the pyaes library,
    using AES-CTR (Counter) mode for encryption and decryption.
    CTR mode is used for Nintendo 3DS content encryption.

    Args:
        key: 16-byte AES key
        counter_value: Initial counter value for CTR mode

    Raises:
        ValueError: If key is not 16 bytes
        ImportError: If pyaes library is not available
    """

    def __init__(self, key: bytes, counter_value: int):
        """Initialize the PyAES adapter.

        Args:
            key: 16-byte AES key
            counter_value: Initial counter value for CTR mode

        Raises:
            ValueError: If key is not 16 bytes
            ImportError: If pyaes library is not available
        """
        if len(key) != 16:
            raise ValueError("AES key must be exactly 16 bytes")

        try:
            import pyaes  # type: ignore[import-not-found]

            self._pyaes = pyaes
        except ImportError as e:
            raise ImportError("pyaes library not found. Install with: pip install pyaes") from e

        self.key = key
        self.counter_value = counter_value

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt data using AES-CTR mode.

        Args:
            data: Encrypted data to decrypt

        Returns:
            Decrypted data
        """
        if not data:
            return b""

        # Create a new counter for each operation to maintain state independence
        ctr = self._pyaes.Counter(initial_value=self.counter_value)
        cipher = self._pyaes.AESModeOfOperationCTR(self.key, counter=ctr)
        return cast(bytes, cipher.decrypt(data))

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using AES-CTR mode.

        Args:
            data: Plain data to encrypt

        Returns:
            Encrypted data
        """
        if not data:
            return b""

        # Create a new counter for each operation to maintain state independence
        ctr = self._pyaes.Counter(initial_value=self.counter_value)
        cipher = self._pyaes.AESModeOfOperationCTR(self.key, counter=ctr)
        return cast(bytes, cipher.encrypt(data))


class MockAESAdapter(IAESCipher):
    """Mock AES adapter for testing.

    This adapter provides a simple XOR-based "encryption" for testing purposes.
    It allows testing code that depends on AES operations without requiring
    the pyaes library or dealing with real cryptographic operations.

    Args:
        key: Key bytes (not used for actual encryption, only for tracking)
        counter_value: Counter value (not used for actual encryption, only for tracking)
    """

    def __init__(self, key: bytes, counter_value: int):
        """Initialize the mock adapter.

        Args:
            key: Key bytes (stored but not used for encryption)
            counter_value: Counter value (stored but not used)
        """
        self.key = key
        self.counter_value = counter_value
        self.decrypt_called = False
        self.encrypt_called = False
        self.last_decrypt_input = b""
        self.last_encrypt_input = b""

    def decrypt(self, data: bytes) -> bytes:
        """Mock decrypt operation using simple XOR.

        Args:
            data: Data to "decrypt"

        Returns:
            "Decrypted" data (XOR with 0xAA for testing)
        """
        self.decrypt_called = True
        self.last_decrypt_input = data

        if not data:
            return b""

        # Simple XOR for testing - NOT cryptographically secure
        return bytes(b ^ 0xAA for b in data)

    def encrypt(self, data: bytes) -> bytes:
        """Mock encrypt operation using simple XOR.

        Args:
            data: Data to "encrypt"

        Returns:
            "Encrypted" data (XOR with 0xAA for testing)
        """
        self.encrypt_called = True
        self.last_encrypt_input = data

        if not data:
            return b""

        # Simple XOR for testing - NOT cryptographically secure
        # Same operation as decrypt for symmetry
        return bytes(b ^ 0xAA for b in data)
