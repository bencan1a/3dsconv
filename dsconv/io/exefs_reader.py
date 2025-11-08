"""ExeFS filesystem reader for Nintendo 3DS.

This module provides functionality to read the ExeFS (Executable Filesystem)
structure from 3DS content. ExeFS contains executable code and game metadata
including the SMDH (icon) file.

The ExeFS structure consists of:
- File headers (up to 10, each 0x10 bytes)
- Hash table (0x20 bytes per file, in reverse order)
- File data (aligned to 0x200 bytes)

Reference: 3dbrew.org/wiki/ExeFS
"""

import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dsconv.io.binary_reader import BinaryReader

if TYPE_CHECKING:
    from dsconv.crypto.aes_adapter import IAESCipher


@dataclass
class ExeFSFile:
    """Represents a file entry in ExeFS filesystem.

    Each file entry contains metadata about a file stored in the ExeFS,
    including its name, offset within the ExeFS, and size.

    Args:
        name: File name (max 8 characters, null-terminated)
        offset: Offset of file data from start of ExeFS data section (after headers)
        size: Size of file data in bytes

    Example:
        >>> file_entry = ExeFSFile(name="icon", offset=0, size=0x36C0)
        >>> print(f"{file_entry.name}: {file_entry.size} bytes at offset {file_entry.offset}")
    """

    name: str
    offset: int
    size: int

    def __post_init__(self):
        """Validate file entry fields."""
        if len(self.name) > 8:
            raise ValueError(f"File name too long: {self.name} (max 8 chars)")
        if self.offset < 0:
            raise ValueError(f"Invalid offset: {self.offset}")
        if self.size < 0:
            raise ValueError(f"Invalid size: {self.size}")


class ExeFSReader:
    """Reads ExeFS filesystem structure.

    ExeFS contains up to 10 files. The structure starts with file headers
    (0x10 bytes each), followed by hashes, then the actual file data.

    File header format (0x10 bytes):
    - 0x00-0x07: File name (null-terminated string)
    - 0x08-0x0B: Offset (from start of file data section)
    - 0x0C-0x0F: Size in bytes

    Args:
        binary_reader: BinaryReader instance for reading file data

    Example:
        >>> with open('game.cci', 'rb') as f:
        ...     reader = BinaryReader(f)
        ...     exefs_reader = ExeFSReader(reader)
        ...     files = exefs_reader.read_file_headers(exefs_offset)
        ...     icon = exefs_reader.read_file(exefs_offset, files[0])
    """

    # ExeFS constants
    MAX_FILES = 10  # Maximum number of files in ExeFS
    HEADER_SIZE = 0x10  # Size of each file header
    HEADERS_REGION_SIZE = 0xA0  # Total size of headers (10 * 0x10)
    HASH_REGION_SIZE = 0x140  # Size of hash region (10 * 0x20)
    HEADER_TOTAL_SIZE = 0x200  # Headers + hashes (0xA0 + 0x140 + padding)

    def __init__(self, binary_reader: BinaryReader):
        """Initialize ExeFS reader with binary reader dependency.

        Args:
            binary_reader: BinaryReader for reading file data
        """
        self.reader = binary_reader

    def read_file_headers(self, exefs_offset: int) -> list[ExeFSFile]:
        """Parse ExeFS file headers.

        Reads up to 10 file headers from the ExeFS structure. Empty entries
        (with null names) are skipped.

        Args:
            exefs_offset: Absolute offset of ExeFS in the file

        Returns:
            List of ExeFSFile objects for non-empty entries

        Raises:
            IOError: If reading fails

        Example:
            >>> files = reader.read_file_headers(0x4000)
            >>> icon_file = next(f for f in files if f.name == "icon")
        """
        files = []

        # Read all file headers (up to 10)
        for header_num in range(self.MAX_FILES):
            header_offset = exefs_offset + (header_num * self.HEADER_SIZE)
            header_data = self.reader.read_at(header_offset, self.HEADER_SIZE)

            # Parse header fields
            name_bytes = header_data[0:8]
            offset, size = struct.unpack("<II", header_data[8:16])

            # Strip null bytes and decode name
            name = name_bytes.rstrip(b"\x00").decode("ascii", errors="ignore")

            # Skip empty entries
            if not name:
                continue

            files.append(ExeFSFile(name=name, offset=offset, size=size))

        return files

    def read_file(
        self,
        exefs_offset: int,
        file_info: ExeFSFile,
        decrypt: bool = False,
        cipher: "IAESCipher | None" = None,
    ) -> bytes:
        """Read file content from ExeFS.

        Reads the data for a specific file from the ExeFS. Optionally
        decrypts the data using the provided cipher.

        The file data starts after the header region (0x200 bytes).
        The file's offset is relative to the start of the data region.

        Args:
            exefs_offset: Absolute offset of ExeFS in the file
            file_info: ExeFSFile object describing the file to read
            decrypt: Whether to decrypt the file data (default: False)
            cipher: AES cipher for decryption (required if decrypt=True)

        Returns:
            File data bytes (decrypted if requested)

        Raises:
            ValueError: If decrypt=True but cipher is None
            IOError: If reading fails

        Example:
            >>> file_info = ExeFSFile(name="icon", offset=0, size=0x36C0)
            >>> data = reader.read_file(exefs_offset, file_info)
            >>> # Or with decryption:
            >>> from dsconv.crypto.aes_adapter import PyAESAdapter
            >>> cipher = PyAESAdapter(key, counter_value)
            >>> data = reader.read_file(exefs_offset, file_info, decrypt=True, cipher=cipher)
        """
        if decrypt and cipher is None:
            raise ValueError("Cipher required when decrypt=True")

        # Calculate absolute offset of file data
        # File data starts after the header region (0x200 bytes)
        file_data_offset = exefs_offset + self.HEADER_TOTAL_SIZE + file_info.offset

        # Read the file data
        data = self.reader.read_at(file_data_offset, file_info.size)

        # Decrypt if requested
        if decrypt and cipher is not None:
            data = cipher.decrypt(data)

        return data

    def find_file(self, exefs_offset: int, filename: str) -> ExeFSFile | None:
        """Find a file by name in the ExeFS.

        This is a convenience method that reads the file headers and
        searches for a file with the given name.

        Args:
            exefs_offset: Absolute offset of ExeFS in the file
            filename: Name of the file to find (case-sensitive)

        Returns:
            ExeFSFile object if found, None otherwise

        Example:
            >>> icon_file = reader.find_file(exefs_offset, "icon")
            >>> if icon_file:
            ...     icon_data = reader.read_file(exefs_offset, icon_file)
        """
        files = self.read_file_headers(exefs_offset)
        for file_entry in files:
            if file_entry.name == filename:
                return file_entry
        return None
