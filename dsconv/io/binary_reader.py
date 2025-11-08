"""Binary file reader utility for 3DS file formats.

This module provides a wrapper around file handles to simplify
reading binary data from specific offsets and unpacking structures.
"""

import struct
from typing import BinaryIO


class BinaryReader:
    """Utility for reading binary data with seeking.

    This class wraps a file handle and provides convenient methods
    for reading data at specific offsets and unpacking binary structures.

    Args:
        file_handle: A file-like object opened in binary mode

    Example:
        >>> with open('game.cci', 'rb') as f:
        ...     reader = BinaryReader(f)
        ...     magic = reader.read_at(0x100, 4)
        ...     size = reader.read_struct(0x104, '<I')[0]
    """

    def __init__(self, file_handle: BinaryIO):
        """Initialize the binary reader.

        Args:
            file_handle: A file-like object opened in binary read mode
        """
        self.file = file_handle

    def read_at(self, offset: int, length: int) -> bytes:
        """Read bytes at specific offset.

        Args:
            offset: Byte offset from start of file
            length: Number of bytes to read

        Returns:
            Bytes read from the file

        Raises:
            IOError: If seeking or reading fails
        """
        self.file.seek(offset)
        return self.file.read(length)

    def read_struct(self, offset: int, format_str: str) -> tuple:
        """Read and unpack struct at offset.

        This is a convenience method that reads the appropriate number
        of bytes for the given format string and unpacks them.

        Args:
            offset: Byte offset from start of file
            format_str: struct format string (e.g., '<I' for little-endian uint32)

        Returns:
            Tuple of unpacked values

        Raises:
            struct.error: If format string is invalid or data doesn't match format
            IOError: If seeking or reading fails

        Example:
            >>> reader.read_struct(0x100, '<4sI')  # Read 4 bytes + uint32
            (b'NCCH', 4096)
        """
        size = struct.calcsize(format_str)
        data = self.read_at(offset, size)
        return struct.unpack(format_str, data)

    def tell(self) -> int:
        """Get current file position.

        Returns:
            Current byte offset in the file
        """
        return self.file.tell()

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to a position in the file.

        Args:
            offset: Byte offset
            whence: Reference point (0=start, 1=current, 2=end)

        Returns:
            New absolute position in the file
        """
        return self.file.seek(offset, whence)
