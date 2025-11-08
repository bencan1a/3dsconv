"""NCCH reader for parsing Nintendo Content Container Headers.

This module provides the NCCHReader class for reading and parsing NCCH
(Nintendo Content Container Header) structures from CCI files. It supports
reading NCCH headers, extended headers with optional decryption, and
encryption key extraction.
"""

from dsconv.crypto.decryption_service import DecryptionService
from dsconv.io.binary_reader import BinaryReader
from dsconv.models.ncch import NCCHHeader


class NCCHReader:
    """Reads NCCH header and content from binary data.

    This reader wraps a BinaryReader and provides methods to parse
    NCCH structures at specified offsets. It can optionally decrypt
    encrypted content using an injected DecryptionService.

    The NCCH format is used for Nintendo 3DS content containers, both
    in CCI files (as partitions) and standalone CIA files.

    Attributes:
        reader: BinaryReader instance for reading binary data
    """

    def __init__(self, binary_reader: BinaryReader):
        """Initialize NCCHReader with a binary reader.

        Args:
            binary_reader: BinaryReader instance for reading binary data.
                          Must be positioned at or before the NCCH data.
        """
        self.reader = binary_reader

    def read_header(self, offset: int = 0) -> NCCHHeader:
        """Read NCCH header at given offset.

        Reads and parses a complete NCCH header from the binary data.
        The header is 0x200 bytes and contains metadata about the content
        including size, encryption flags, and hashes.

        Args:
            offset: Byte offset to the start of the NCCH header.
                   Default is 0 (read from current position or start).

        Returns:
            Parsed NCCHHeader object containing all header fields.

        Raises:
            ValueError: If the magic bytes are not 'NCCH' or if the
                       header data is invalid.

        Example:
            >>> reader = NCCHReader(binary_reader)
            >>> header = reader.read_header(offset=0x4000)
            >>> print(f"Title ID: {header.title_id.hex()}")
        """
        # Read the full NCCH header (0x200 bytes)
        header_data = self.reader.read_at(offset, 0x200)

        # Validate that we have enough data
        if len(header_data) < 0x200:
            raise ValueError(
                f"Insufficient data for NCCH header at offset 0x{offset:X} "
                f"(need 0x200 bytes, got {len(header_data)} bytes)"
            )

        # Check magic bytes before parsing
        magic = header_data[0x100:0x104]
        if magic != b"NCCH":
            raise ValueError(
                f"Invalid NCCH magic at offset 0x{offset:X}: {magic!r} " f"(expected b'NCCH')"
            )

        # Parse the header using the model's from_bytes method
        return NCCHHeader.from_bytes(header_data)

    def read_extheader(
        self,
        offset: int,
        size: int = 0x400,
        decrypt: bool = False,
        decryption_service: DecryptionService | None = None,
        key_y: bytes | None = None,
        title_id: bytes | None = None,
    ) -> bytes:
        """Read extended header, optionally decrypting it.

        The extended header contains important metadata about the NCCH
        content, including system control info and dependency lists.
        It may be encrypted and require decryption before use.

        Args:
            offset: Byte offset to the start of the extended header.
                   This is typically at NCCH_offset + 0x200.
            size: Size of the extended header in bytes. Default is 0x400.
            decrypt: If True, decrypt the extended header using the
                    provided decryption_service. Default is False.
            decryption_service: DecryptionService instance for decryption.
                               Required if decrypt=True.
            key_y: The KeyY value for decryption (16 bytes).
                  Required if decrypt=True.
            title_id: The title ID for decryption (8 bytes).
                     Required if decrypt=True.

        Returns:
            The extended header data as bytes. Decrypted if decrypt=True,
            otherwise raw data as stored in the file.

        Raises:
            ValueError: If decrypt=True but decryption_service, key_y, or
                       title_id are not provided.

        Example:
            >>> # Read encrypted extended header
            >>> header = reader.read_header(0x4000)
            >>> key_y = reader.read_key_y(0x4000)
            >>> extheader = reader.read_extheader(
            ...     offset=0x4200,
            ...     decrypt=True,
            ...     decryption_service=decryption_svc,
            ...     key_y=key_y,
            ...     title_id=header.title_id
            ... )
        """
        # Read the extended header data
        data = self.reader.read_at(offset, size)

        # If decryption is requested, validate and decrypt
        if decrypt:
            if decryption_service is None:
                raise ValueError("decryption_service is required when decrypt=True")
            if key_y is None:
                raise ValueError("key_y is required when decrypt=True")
            if title_id is None:
                raise ValueError("title_id is required when decrypt=True")

            # Decrypt using the provided service
            data = decryption_service.decrypt_extheader(data, key_y, title_id)

        return data

    def read_key_y(self, ncch_offset: int) -> bytes:
        """Read KeyY value from NCCH header.

        The KeyY is used for deriving the normal encryption key needed
        to decrypt encrypted NCCH content. It is stored at the beginning
        of the NCCH header (first 16 bytes of the signature).

        Args:
            ncch_offset: Byte offset to the start of the NCCH header.

        Returns:
            KeyY value as 16 bytes.

        Example:
            >>> reader = NCCHReader(binary_reader)
            >>> key_y = reader.read_key_y(0x4000)
            >>> print(f"KeyY: {key_y.hex()}")
        """
        # KeyY is at the very start of the NCCH (first 16 bytes of signature)
        return self.reader.read_at(ncch_offset, 0x10)
