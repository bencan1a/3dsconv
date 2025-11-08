"""Binary reader utility for reading binary data with seeking.

This module provides the BinaryReader class which wraps a file handle to provide
convenient methods for reading binary data at specific offsets and unpacking
structured data using the struct module.
"""

import struct
from typing import BinaryIO


class BinaryReader:
    """Utility for reading binary data with seeking.

    This class wraps a file handle and provides convenience methods for reading
    binary data at specific offsets and unpacking structured data. It simplifies
    the common pattern of seeking to an offset, reading bytes, and unpacking them.

    The file handle is not owned by this class and will not be closed when the
    BinaryReader is destroyed. The caller is responsible for managing the file
    handle lifecycle.

    Attributes:
        file: The file handle wrapped by this reader

    Example:
        >>> with open('data.bin', 'rb') as f:
        ...     reader = BinaryReader(f)
        ...     magic = reader.read_at(0x100, 4)
        ...     size, = reader.read_struct(0x104, '<I')
    """

    def __init__(self, file_handle: BinaryIO):
        """Initialize the binary reader with a file handle.

        Args:
            file_handle: A file object opened in binary read mode
        """
        self.file = file_handle

    def read_at(self, offset: int, length: int) -> bytes:
        """Read bytes at a specific offset.

        This method seeks to the specified offset and reads the requested number
        of bytes. The file position after this call is undefined and should not
        be relied upon.

        Args:
            offset: The byte offset in the file to start reading from
            length: The number of bytes to read

        Returns:
            The bytes read from the file

        Raises:
            OSError: If seeking or reading fails
            ValueError: If length is negative

        Example:
            >>> magic = reader.read_at(0x100, 4)
            >>> print(magic)
            b'NCCH'
        """
        if length < 0:
            raise ValueError(f"length must be non-negative, got {length}")

        self.file.seek(offset)
        return self.file.read(length)

    def read_struct(self, offset: int, format_str: str) -> tuple:
        """Read and unpack structured binary data at a specific offset.

        This method combines seeking, reading, and struct unpacking into a single
        convenient operation. It uses the Python struct module format strings.

        Args:
            offset: The byte offset in the file to start reading from
            format_str: A struct format string (e.g., '<I' for little-endian uint32)

        Returns:
            A tuple of unpacked values as specified by the format string

        Raises:
            struct.error: If the format string is invalid or data doesn't match
            OSError: If seeking or reading fails

        Example:
            >>> # Read a little-endian uint32 at offset 0x104
            >>> size, = reader.read_struct(0x104, '<I')
            >>> # Read two uint32 values
            >>> offset, length = reader.read_struct(0x120, '<II')
        """
        size = struct.calcsize(format_str)
        data = self.read_at(offset, size)
        return struct.unpack(format_str, data)

    def tell(self) -> int:
        """Get the current file position.

        Returns:
            The current byte offset in the file

        Example:
            >>> pos = reader.tell()
        """
        return self.file.tell()

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to a position in the file.

        Args:
            offset: The offset to seek to
            whence: How to interpret offset (0=absolute, 1=relative, 2=from end)

        Returns:
            The new absolute position in the file

        Example:
            >>> reader.seek(0x100)  # Seek to offset 0x100
            >>> reader.seek(0x10, 1)  # Seek 16 bytes forward
        """
        return self.file.seek(offset, whence)
