"""Cryptographic services for 3dsconv.

This package provides encryption and key management services
for Nintendo 3DS content conversion.
"""

from .aes_adapter import IAESCipher, MockAESAdapter, PyAESAdapter
from .decryption_service import DecryptionService
from .key_derivation import KeyDerivationService
from .key_provider import (
    Boot9KeyProvider,
    IKeyProvider,
    InvalidKeyFileError,
    KeyNotFoundError,
    KeyProviderError,
    MockKeyProvider,
    ProdKeysKeyProvider,
)

__all__ = [
    # AES Cipher adapters
    "IAESCipher",
    "PyAESAdapter",
    "MockAESAdapter",
    # Key derivation
    "KeyDerivationService",
    # Decryption service
    "DecryptionService",
    # Key providers
    "IKeyProvider",
    "ProdKeysKeyProvider",
    "Boot9KeyProvider",
    "MockKeyProvider",
    # Exceptions
    "KeyProviderError",
    "KeyNotFoundError",
    "InvalidKeyFileError",
]
