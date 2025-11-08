"""ExeFS filesystem reader.

This module provides functionality to read and parse the ExeFS (Executable Filesystem)
structure used in Nintendo 3DS NCCH containers. ExeFS contains executable code,
system files, and resources like the application icon (SMDH).

Reference: 3dbrew.org/wiki/ExeFS
"""

import struct
from dataclasses import dataclass

from dsconv.crypto.aes_adapter import IAESCipher
from dsconv.io.binary_reader import BinaryReader


@dataclass
class ExeFSFile:
    """Represents a file entry in ExeFS.

    ExeFS can contain up to 10 files. Each file has a header entry
    containing its name, offset, and size.

    Attributes:
        name: File name (up to 8 characters, null-padded)
        offset: Offset from the start of file data section (after 0x200 header)
        size: File size in bytes
    """

    name: str
    offset: int
    size: int

    def __post_init__(self):
        """Validate ExeFSFile fields."""
        if not isinstance(self.name, str):
            raise TypeError(f"name must be str, got {type(self.name).__name__}")
        if len(self.name) > 8:
            raise ValueError(f"name must be 8 characters or less, got {len(self.name)}")
        if self.offset < 0:
            raise ValueError(f"offset must be non-negative, got {self.offset}")
        if self.size < 0:
            raise ValueError(f"size must be non-negative, got {self.size}")


class ExeFSReader:
    """Reads ExeFS filesystem structure.

    ExeFS structure:
    - 0x000-0x0A0: File headers (10 entries, 0x10 bytes each)
    - 0x0A0-0x200: Reserved/padding
    - 0x200+: File data

    Each file header (0x10 bytes):
    - 0x00-0x08: File name (null-padded ASCII)
    - 0x08-0x0C: Offset (little-endian uint32, relative to 0x200)
    - 0x0C-0x10: Size (little-endian uint32)

    Args:
        binary_reader: BinaryReader instance for reading file data
    """

    def __init__(self, binary_reader: BinaryReader):
        """Initialize ExeFSReader with a binary reader.

        Args:
            binary_reader: BinaryReader instance for reading file data
        """
        self.reader = binary_reader

    def read_file_headers(
        self, exefs_offset: int, decrypt: bool = False, cipher: IAESCipher | None = None
    ) -> list[ExeFSFile]:
        """Parse ExeFS file headers.

        Reads up to 10 file headers from the ExeFS header section.
        Empty entries (with null names) are skipped.

        Args:
            exefs_offset: Absolute offset to the start of ExeFS in the file
            decrypt: Whether to decrypt the header before parsing
            cipher: AES cipher for decrypting header (required if decrypt=True)

        Returns:
            List of ExeFSFile objects representing files in the ExeFS

        Raises:
            ValueError: If decrypt is True but cipher is None
        """
        if decrypt and cipher is None:
            raise ValueError("cipher is required when decrypt is True")

        # Read the first 0x200 bytes containing headers
        # Only the first 0xA0 bytes contain actual headers (10 * 0x10)
        # But we read 0x200 to align with media unit boundary
        header_data = self.reader.read_at(exefs_offset, 0x200)

        # Decrypt header if needed
        if decrypt and cipher:
            # Only decrypt the first 0xA0 bytes (file headers)
            # The rest is padding and doesn't need decryption
            encrypted_headers = header_data[:0xA0]
            decrypted_headers = cipher.encrypt(encrypted_headers)  # CTR mode: encrypt = decrypt
            header_data = decrypted_headers + header_data[0xA0:]

        # Parse up to 10 file headers
        files = []
        for i in range(10):
            header_offset = i * 0x10
            header_entry = header_data[header_offset : header_offset + 0x10]

            # Extract name (8 bytes, null-padded ASCII)
            name_bytes = header_entry[0:8]
            # Strip null bytes and decode
            name = name_bytes.rstrip(b"\x00").decode("ascii", errors="ignore")

            # Skip empty entries
            if not name:
                continue

            # Extract offset (4 bytes, little-endian uint32)
            (file_offset,) = struct.unpack("<I", header_entry[8:12])

            # Extract size (4 bytes, little-endian uint32)
            (file_size,) = struct.unpack("<I", header_entry[12:16])

            files.append(ExeFSFile(name=name, offset=file_offset, size=file_size))

        return files

    def read_file(
        self,
        exefs_offset: int,
        file_info: ExeFSFile,
        decrypt: bool = False,
        cipher: IAESCipher | None = None,
    ) -> bytes:
        """Read file content from ExeFS.

        Reads the actual file data from the ExeFS data section.
        File data starts at exefs_offset + 0x200 + file_info.offset.

        Args:
            exefs_offset: Absolute offset to the start of ExeFS in the file
            file_info: ExeFSFile object describing the file to read
            decrypt: Whether to decrypt the file content
            cipher: AES cipher for decrypting content (required if decrypt=True)

        Returns:
            File content as bytes (decrypted if decrypt=True)

        Raises:
            ValueError: If decrypt is True but cipher is None,
                       or if file_info has invalid offset/size
        """
        if decrypt and cipher is None:
            raise ValueError("cipher is required when decrypt is True")

        if file_info.size == 0:
            return b""

        # File data section starts at exefs_offset + 0x200
        # Individual file offset is relative to this data section start
        data_section_start = exefs_offset + 0x200
        file_absolute_offset = data_section_start + file_info.offset

        # Read the file data
        file_data = self.reader.read_at(file_absolute_offset, file_info.size)

        # Decrypt if needed
        if decrypt and cipher:
            file_data = cipher.decrypt(file_data)

        return file_data

    def find_file(
        self,
        exefs_offset: int,
        filename: str,
        decrypt_headers: bool = False,
        cipher: IAESCipher | None = None,
    ) -> ExeFSFile | None:
        """Find a file by name in ExeFS.

        Convenience method to search for a specific file in the ExeFS.

        Args:
            exefs_offset: Absolute offset to the start of ExeFS in the file
            filename: Name of the file to find (case-sensitive)
            decrypt_headers: Whether to decrypt headers before searching
            cipher: AES cipher for decrypting headers (required if decrypt_headers=True)

        Returns:
            ExeFSFile object if found, None otherwise

        Raises:
            ValueError: If decrypt_headers is True but cipher is None
        """
        files = self.read_file_headers(exefs_offset, decrypt=decrypt_headers, cipher=cipher)
        for file_info in files:
            if file_info.name == filename:
                return file_info
        return None
