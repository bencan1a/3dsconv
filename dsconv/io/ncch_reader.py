"""NCCH reader for reading Nintendo 3DS NCCH headers and content.

This module provides the NCCHReader class which reads NCCH (Nintendo Content
Container Header) structures from CCI files. It can read headers, extended
headers, and supports optional decryption via an injected decryption service.
"""

from typing import TYPE_CHECKING

from dsconv.io.binary_reader import BinaryReader
from dsconv.models.ncch import NCCHHeader

if TYPE_CHECKING:
    from dsconv.crypto.decryption_service import DecryptionService


class NCCHReader:
    """Reads NCCH header and content from binary files.

    This class provides methods to read and parse NCCH (Nintendo Content Container
    Header) structures from CCI files. It handles both the main NCCH header and
    the extended header, with support for optional decryption when content is
    encrypted.

    The reader uses dependency injection for the decryption service, allowing it
    to work with encrypted content when a service is provided, or read decrypted
    content without any cryptographic dependencies.

    NCCH Structure:
        - 0x000-0x100: RSA-2048 signature
        - 0x100-0x104: Magic "NCCH"
        - 0x104-0x200: Header fields (size, partition ID, flags, etc.)
        - 0x200-0x600: Extended header (encrypted if content is encrypted)
        - 0x600+: Additional content (ExeFS, RomFS, etc.)

    Attributes:
        reader: BinaryReader instance for reading from the file

    Example:
        >>> with open('game.cci', 'rb') as f:
        ...     reader = BinaryReader(f)
        ...     ncch_reader = NCCHReader(reader)
        ...     header = ncch_reader.read_header(offset=0x4000)
        ...     extheader = ncch_reader.read_extheader(offset=0x4000)
    """

    def __init__(self, binary_reader: BinaryReader):
        """Initialize the NCCH reader.

        Args:
            binary_reader: A BinaryReader instance for reading from the file
        """
        self.reader = binary_reader

    def read_header(self, offset: int = 0) -> NCCHHeader:
        """Read NCCH header at the given offset.

        This method reads and parses a complete NCCH header (0x200 bytes) starting
        at the specified offset. It validates the magic bytes to ensure this is a
        valid NCCH structure.

        The NCCH header contains metadata about the content including:
        - Content size and partition ID
        - Encryption flags
        - Extended header size and hash
        - ExeFS and RomFS offsets and sizes

        Args:
            offset: The byte offset in the file where the NCCH header starts.
                   The magic "NCCH" is expected at offset + 0x100.
                   Default is 0 (read from start of file).

        Returns:
            A parsed NCCHHeader object containing all header fields

        Raises:
            ValueError: If the magic bytes at offset + 0x100 are not b'NCCH'
            OSError: If reading from the file fails

        Example:
            >>> # Read NCCH header from game partition at offset 0x4000
            >>> header = ncch_reader.read_header(offset=0x4000)
            >>> print(f"Title ID: {header.title_id.hex()}")
            >>> print(f"Encrypted: {header.is_encrypted}")
        """
        # Read the full NCCH header (0x200 bytes)
        header_data = self.reader.read_at(offset, 0x200)

        # Validate NCCH magic at offset 0x100 within the header
        magic = header_data[0x100:0x104]
        if magic != b"NCCH":
            raise ValueError(
                f"Invalid NCCH magic at offset {offset + 0x100:#x}: "
                f"expected b'NCCH', got {magic!r}"
            )

        # Use the NCCHHeader.from_bytes factory method to parse the header
        return NCCHHeader.from_bytes(header_data)

    def read_extheader(
        self,
        offset: int,
        decrypt: bool = False,
        decryption_service: "DecryptionService | None" = None,
        key_y: bytes | None = None,
        title_id: bytes | None = None,
    ) -> bytes:
        """Read extended header, optionally decrypting it.

        The extended header (0x400 bytes) contains important metadata including:
        - System control info (application title, dependencies)
        - Access control info (permissions, resource limits)
        - Save data size

        If the content is encrypted and decrypt=True, the decryption service will
        be used to decrypt the extended header before returning it.

        Extended Header Location:
        The extended header is always at offset + 0x200 from the NCCH header start,
        regardless of encryption status.

        Args:
            offset: The byte offset where the NCCH header starts (not the extended
                   header itself - that's at offset + 0x200)
            decrypt: Whether to decrypt the extended header. If True, decryption_service,
                    key_y, and title_id must be provided.
            decryption_service: The decryption service to use for decryption.
                              Required if decrypt=True.
            key_y: The KeyY value from the NCCH header (16 bytes).
                  Required if decrypt=True.
            title_id: The title ID from the NCCH header (8 bytes).
                     Required if decrypt=True.

        Returns:
            The extended header data (0x400 bytes), decrypted if requested

        Raises:
            ValueError: If decrypt=True but required parameters are missing
            OSError: If reading from the file fails

        Example:
            >>> # Read decrypted extended header
            >>> header = ncch_reader.read_header(offset=0x4000)
            >>> key_y = ncch_reader.read_key_y(offset=0x4000)
            >>> extheader = ncch_reader.read_extheader(
            ...     offset=0x4000,
            ...     decrypt=header.is_encrypted,
            ...     decryption_service=decryption_service,
            ...     key_y=key_y,
            ...     title_id=header.title_id
            ... )
        """
        # Validate parameters if decryption is requested
        if decrypt:
            if decryption_service is None:
                raise ValueError("decryption_service is required when decrypt=True")
            if key_y is None:
                raise ValueError("key_y is required when decrypt=True")
            if title_id is None:
                raise ValueError("title_id is required when decrypt=True")

        # Read extended header (0x400 bytes) at offset + 0x200
        extheader_data = self.reader.read_at(offset + 0x200, 0x400)

        # Decrypt if requested
        if decrypt and decryption_service is not None:
            # Type checking knows these are not None due to validation above
            assert key_y is not None
            assert title_id is not None
            extheader_data = decryption_service.decrypt_extheader(extheader_data, key_y, title_id)

        return extheader_data

    def read_key_y(self, offset: int = 0) -> bytes:
        """Read the KeyY value from the NCCH header.

        The KeyY is located at the very beginning of the NCCH header (first 16 bytes
        of the signature field) and is used for key derivation when decrypting
        encrypted content.

        For decrypted content, this value is still present but not used.

        Args:
            offset: The byte offset where the NCCH header starts. Default is 0.

        Returns:
            The KeyY value (16 bytes)

        Raises:
            OSError: If reading from the file fails

        Example:
            >>> key_y = ncch_reader.read_key_y(offset=0x4000)
            >>> print(f"KeyY: {key_y.hex()}")
        """
        # KeyY is the first 16 bytes of the NCCH header (part of signature)
        return self.reader.read_at(offset, 0x10)

    def read_exefs_offset(self, offset: int = 0) -> int:
        """Read the ExeFS offset from the NCCH header.

        The ExeFS offset is stored in media units (0x200 bytes) at offset 0x1A0
        within the NCCH header. This method returns the absolute byte offset.

        Args:
            offset: The byte offset where the NCCH header starts. Default is 0.

        Returns:
            The absolute byte offset to the ExeFS (offset + exefs_offset * 0x200)

        Example:
            >>> exefs_offset = ncch_reader.read_exefs_offset(offset=0x4000)
        """
        # Read ExeFS offset in media units
        (exefs_offset_mu,) = self.reader.read_struct(offset + 0x1A0, "<I")
        # Convert to bytes and make it absolute from the NCCH start
        return offset + (exefs_offset_mu * 0x200)

    def read_exefs_size(self, offset: int = 0) -> int:
        """Read the ExeFS size from the NCCH header.

        The ExeFS size is stored in media units (0x200 bytes) at offset 0x1A4
        within the NCCH header.

        Args:
            offset: The byte offset where the NCCH header starts. Default is 0.

        Returns:
            The ExeFS size in bytes (exefs_size * 0x200)

        Example:
            >>> exefs_size = ncch_reader.read_exefs_size(offset=0x4000)
        """
        # Read ExeFS size in media units
        (exefs_size_mu,) = self.reader.read_struct(offset + 0x1A4, "<I")
        # Convert to bytes
        return exefs_size_mu * 0x200
