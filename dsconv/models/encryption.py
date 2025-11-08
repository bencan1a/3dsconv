"""Encryption state models for 3dsconv.

This module provides pure data models representing encryption state
and types used during CCI to CIA conversion. These models contain no
crypto operations - they only represent data and provide computed properties.
"""

from dataclasses import dataclass
from enum import Enum


class EncryptionType(Enum):
    """Enumeration of encryption types for NCCH content.

    The encryption type determines how the content needs to be handled
    during the conversion process:

    - DECRYPTED: Content is already decrypted (no key needed)
    - ZEROKEY: Content uses zero-key encryption (special case)
    - ORIGINAL_NCCH: Content uses original NCCH encryption (requires key derivation)

    Reference: 3dbrew.org/wiki/NCCH#Encryption
    """

    DECRYPTED = "decrypted"
    ZEROKEY = "zerokey"
    ORIGINAL_NCCH = "original_ncch"


@dataclass
class EncryptionContext:
    """Encryption state and keys for conversion.

    This dataclass encapsulates all encryption-related state needed for
    the conversion process. It contains the encryption type, any derived
    keys, and the title ID used for key derivation.

    This is a pure data model - it performs no cryptographic operations.
    Key derivation and decryption should be handled by separate services.

    Attributes:
        encryption_type: The type of encryption used (enum value)
        normal_key: The derived normal key for decryption (None if not needed)
        title_id: The title ID used for key derivation (8 bytes)

    Example:
        >>> ctx = EncryptionContext(
        ...     encryption_type=EncryptionType.DECRYPTED,
        ...     normal_key=None,
        ...     title_id=b'\\x00' * 8
        ... )
        >>> ctx.needs_decryption
        False
    """

    encryption_type: EncryptionType
    normal_key: bytes | None
    title_id: bytes

    def __post_init__(self):
        """Validate encryption context fields.

        Raises:
            ValueError: If title_id is not 8 bytes
            ValueError: If normal_key is provided but not 16 bytes
            TypeError: If encryption_type is not an EncryptionType enum
        """
        if not isinstance(self.encryption_type, EncryptionType):
            raise TypeError(
                f"encryption_type must be EncryptionType enum, got {type(self.encryption_type).__name__}"
            )

        if len(self.title_id) != 8:
            raise ValueError(f"title_id must be 8 bytes, got {len(self.title_id)} bytes")

        if self.normal_key is not None and len(self.normal_key) != 16:
            raise ValueError(
                f"normal_key must be 16 bytes when provided, got {len(self.normal_key)} bytes"
            )

    @property
    def needs_decryption(self) -> bool:
        """Check if content requires decryption.

        Returns:
            True if content needs decryption, False otherwise

        Decryption is needed for all encryption types except DECRYPTED.
        Both ZEROKEY and ORIGINAL_NCCH encryption require decryption,
        though they use different keys.
        """
        return self.encryption_type != EncryptionType.DECRYPTED

    @property
    def is_decrypted(self) -> bool:
        """Check if content is already decrypted.

        Returns:
            True if content is decrypted, False otherwise
        """
        return self.encryption_type == EncryptionType.DECRYPTED

    @property
    def is_zerokey(self) -> bool:
        """Check if content uses zero-key encryption.

        Returns:
            True if content uses zero-key encryption, False otherwise
        """
        return self.encryption_type == EncryptionType.ZEROKEY

    @property
    def is_original_ncch(self) -> bool:
        """Check if content uses original NCCH encryption.

        Returns:
            True if content uses original NCCH encryption, False otherwise
        """
        return self.encryption_type == EncryptionType.ORIGINAL_NCCH
