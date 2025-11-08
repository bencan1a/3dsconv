"""
Key derivation service for 3dsconv.

This module provides the KeyDerivationService class which is responsible for
deriving encryption keys used in the CCI to CIA conversion process. The key
derivation follows the Nintendo 3DS encryption scheme.
"""

from typing import cast

from dsconv.utils import rol


class KeyDerivationService:
    """Service for deriving encryption keys.

    This service derives normal keys from KeyY values and the original NCCH key
    using the Nintendo 3DS key derivation algorithm. The derivation uses rotate-left
    operations and addition with a constant to transform the input keys.

    The derived keys are used for decrypting NCCH content (ExtHeader, ExeFS, RomFS)
    during the conversion process.

    Attributes:
        original_ncch_key: The original NCCH key (128-bit integer) used as the base
                          for key derivation. This is typically loaded from boot9.bin
                          or prod.keys file.
    """

    def __init__(self, original_ncch_key: int):
        """Initialize the key derivation service.

        Args:
            original_ncch_key: The original NCCH key as a 128-bit integer.
                              This key is obtained from either boot9.bin or
                              the prod.keys file (slot0x2CKeyX).
        """
        self.original_ncch_key = original_ncch_key

    def derive_normal_key(self, key_y: bytes) -> bytes:
        """Derive a normal key from KeyY and the original NCCH key.

        This method implements the Nintendo 3DS key derivation algorithm:
        1. Convert KeyY from bytes to integer (big-endian)
        2. Rotate the original NCCH key left by 2 bits (128-bit width)
        3. XOR the rotated key with KeyY
        4. Add the constant 0x1FF9E9AAC5FE0408024591DC5D52768A
        5. Rotate the result left by 87 bits (128-bit width)
        6. Convert back to bytes (big-endian)

        Args:
            key_y: The KeyY value as 16 bytes (128 bits) in big-endian format.
                  This is read from the NCCH header at offset 0x00.

        Returns:
            The derived normal key as 16 bytes (128 bits) in big-endian format.
            This key can be used directly with AES-CTR for decryption.

        Example:
            >>> service = KeyDerivationService(0x12345678...)
            >>> key_y = bytes.fromhex('00112233445566778899AABBCCDDEEFF')
            >>> normal_key = service.derive_normal_key(key_y)
            >>> len(normal_key)
            16
        """
        # Convert KeyY from bytes to integer (big-endian)
        key_y_int = int.from_bytes(key_y, byteorder="big")

        # Apply the key derivation algorithm
        # Formula: rol((rol(original_key, 2, 128) XOR key_y) + constant, 87, 128)
        key_int = rol(
            (rol(self.original_ncch_key, 2, 128) ^ key_y_int) + 0x1FF9E9AAC5FE0408024591DC5D52768A,
            87,
            128,
        )

        # Convert back to bytes (big-endian, 16 bytes)
        return cast(bytes, key_int.to_bytes(0x10, byteorder="big"))
