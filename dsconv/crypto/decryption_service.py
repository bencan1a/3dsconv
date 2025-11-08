"""Decryption service for NCCH content.

This module provides the DecryptionService class which orchestrates the decryption
of NCCH content (Extended Header and ExeFS) using AES-CTR mode encryption.
"""

from collections.abc import Callable

from dsconv.crypto.aes_adapter import IAESCipher
from dsconv.crypto.key_derivation import KeyDerivationService


class DecryptionService:
    """Service for decrypting NCCH content.

    This service orchestrates the decryption of Nintendo 3DS NCCH content,
    including Extended Headers and ExeFS filesystems. It uses dependency injection
    for key derivation and AES cipher creation, making it fully testable without
    requiring actual cryptographic operations.

    The decryption process follows the Nintendo 3DS encryption scheme:
    1. Derive a normal key from KeyY and the original NCCH key
    2. Calculate a counter value based on the title ID and content type
    3. Create an AES-CTR cipher with the normal key and counter
    4. Decrypt the content using the cipher

    Attributes:
        key_derivation: Service for deriving normal keys from KeyY values
        aes_cipher_factory: Factory function that creates IAESCipher instances
                           given a key and counter value
    """

    def __init__(
        self,
        key_derivation: KeyDerivationService,
        aes_cipher_factory: Callable[[bytes, int], IAESCipher],
    ):
        """Initialize the decryption service.

        Args:
            key_derivation: Service for deriving normal keys from KeyY values.
                           This service contains the original NCCH key needed for
                           key derivation.
            aes_cipher_factory: Factory function that creates IAESCipher instances.
                               Takes key (bytes) and counter_value (int) as parameters
                               and returns an IAESCipher implementation.
                               Example: lambda k, c: PyAESAdapter(k, c)
        """
        self.key_derivation = key_derivation
        self.aes_cipher_factory = aes_cipher_factory

    def decrypt_extheader(self, encrypted_data: bytes, key_y: bytes, title_id: bytes) -> bytes:
        """Decrypt an NCCH Extended Header.

        The Extended Header contains important metadata about the NCCH content,
        including dependency lists and save data size. It is encrypted using
        AES-CTR mode with a counter value derived from the title ID.

        The counter value for Extended Header decryption is:
        title_id || 0x01 || 0x000000000000 (16 bytes total, big-endian)

        Args:
            encrypted_data: The encrypted Extended Header data (typically 0x400 bytes)
            key_y: The KeyY value read from the NCCH header (16 bytes)
            title_id: The title ID from the NCCH header (8 bytes, little-endian)

        Returns:
            The decrypted Extended Header data

        Raises:
            ValueError: If encrypted_data, key_y, or title_id have invalid lengths

        Example:
            >>> service = DecryptionService(key_deriv, cipher_factory)
            >>> key_y = bytes.fromhex('00112233...')  # 16 bytes
            >>> title_id = bytes.fromhex('0123456789ABCDEF')  # 8 bytes
            >>> extheader = service.decrypt_extheader(encrypted, key_y, title_id)
        """
        if len(key_y) != 16:
            raise ValueError(f"key_y must be 16 bytes, got {len(key_y)}")
        if len(title_id) != 8:
            raise ValueError(f"title_id must be 8 bytes, got {len(title_id)}")

        # Derive the normal key from KeyY
        normal_key = self.key_derivation.derive_normal_key(key_y)

        # Calculate counter value for Extended Header
        # Counter: title_id (8 bytes) || 0x01 (1 byte) || 0x00... (7 bytes)
        counter_bytes = title_id + b"\x01" + bytes(7)
        counter_value = int.from_bytes(counter_bytes, byteorder="big")

        # Create cipher and decrypt
        cipher = self.aes_cipher_factory(normal_key, counter_value)
        return cipher.decrypt(encrypted_data)

    def decrypt_exefs(
        self,
        encrypted_data: bytes,
        key_y: bytes,
        title_id: bytes,
        offset_in_blocks: int = 0,
    ) -> bytes:
        """Decrypt ExeFS content.

        The ExeFS (Executable Filesystem) contains the game executable code and
        other files like the icon. It is encrypted using AES-CTR mode with a
        counter value that depends on both the title ID and the position within
        the ExeFS.

        The counter value for ExeFS decryption is:
        title_id || 0x02 || 0x000000000000 (base counter, 16 bytes total, big-endian)
        Then add the offset in 16-byte blocks to account for position within ExeFS.

        Args:
            encrypted_data: The encrypted ExeFS data
            key_y: The KeyY value read from the NCCH header (16 bytes)
            title_id: The title ID from the NCCH header (8 bytes, little-endian)
            offset_in_blocks: Offset within the ExeFS in 16-byte blocks.
                            This is calculated as: (file_offset_in_exefs / 16) + 0x20
                            The 0x20 accounts for the ExeFS header size (0x200 bytes = 32 blocks)
                            Default is 0 for decrypting the ExeFS header itself.

        Returns:
            The decrypted ExeFS data

        Raises:
            ValueError: If encrypted_data, key_y, or title_id have invalid lengths

        Example:
            >>> service = DecryptionService(key_deriv, cipher_factory)
            >>> # Decrypt ExeFS header (first 0x200 bytes)
            >>> header = service.decrypt_exefs(encrypted_header, key_y, title_id, 0)
            >>> # Decrypt icon file at offset 0x1000 in ExeFS
            >>> # offset_in_blocks = (0x1000 / 16) + 0x20 = 0x120
            >>> icon = service.decrypt_exefs(encrypted_icon, key_y, title_id, 0x120)
        """
        if len(key_y) != 16:
            raise ValueError(f"key_y must be 16 bytes, got {len(key_y)}")
        if len(title_id) != 8:
            raise ValueError(f"title_id must be 8 bytes, got {len(title_id)}")

        # Derive the normal key from KeyY
        normal_key = self.key_derivation.derive_normal_key(key_y)

        # Calculate base counter value for ExeFS
        # Counter: title_id (8 bytes) || 0x02 (1 byte) || 0x00... (7 bytes)
        base_counter_bytes = title_id + b"\x02" + bytes(7)
        base_counter_value = int.from_bytes(base_counter_bytes, byteorder="big")

        # Add the offset in blocks to the counter
        counter_value = base_counter_value + offset_in_blocks

        # Create cipher and decrypt
        cipher = self.aes_cipher_factory(normal_key, counter_value)
        return cipher.decrypt(encrypted_data)
