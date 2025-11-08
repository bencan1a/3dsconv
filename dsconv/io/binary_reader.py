"""Binary file reading utilities."""

import struct
from typing import BinaryIO


class BinaryReader:
    """Utility for reading binary data with seeking.

    This class wraps a file handle and provides convenience methods for
    reading binary data at specific offsets. It abstracts common operations
    like seeking and unpacking struct data.

    Example:
        >>> with open('file.bin', 'rb') as f:
        ...     reader = BinaryReader(f)
        ...     magic = reader.read_at(0x100, 4)
        ...     value = reader.read_struct(0x104, '<I')[0]
    """

    def __init__(self, file_handle: BinaryIO):
        """Initialize BinaryReader with a file handle.

        Args:
            file_handle: An open file handle in binary read mode
        """
        self.file = file_handle

    def read_at(self, offset: int, length: int) -> bytes:
        """Read bytes at a specific offset.

        Args:
            offset: Offset in the file to start reading from
            length: Number of bytes to read

        Returns:
            The bytes read from the file

        Raises:
            OSError: If the file cannot be read
        """
        self.file.seek(offset)
        return self.file.read(length)

    def read_struct(self, offset: int, format_str: str) -> tuple:
        """Read and unpack struct at a specific offset.

        This method reads the appropriate number of bytes for the given
        struct format string, then unpacks them according to the format.

        Args:
            offset: Offset in the file to start reading from
            format_str: Python struct format string (e.g., '<I', '>Q', '4s')

        Returns:
            Tuple of unpacked values according to the format string

        Raises:
            struct.error: If the format string is invalid or data doesn't match
            OSError: If the file cannot be read

        Example:
            >>> # Read a little-endian unsigned int at offset 0x100
            >>> value = reader.read_struct(0x100, '<I')[0]
        """
        size = struct.calcsize(format_str)
        data = self.read_at(offset, size)
        return struct.unpack(format_str, data)
