"""Binary file reading utilities."""

import struct
from typing import BinaryIO


class BinaryReader:
    """Utility for reading binary data with seeking.

    This class wraps a file handle and provides convenience methods
    for reading binary data at specific offsets without managing
    seek operations manually. It's designed to simplify reading
    structured binary formats like NCSD, NCCH, and CIA files.

    Example:
        >>> with open('file.bin', 'rb') as f:
        ...     reader = BinaryReader(f)
        ...     magic = reader.read_at(0x100, 4)
        ...     size, = reader.read_struct(0x104, '<I')
    """

    def __init__(self, file_handle: BinaryIO):
        """Initialize BinaryReader with a file handle.

        Args:
            file_handle: A file-like object opened in binary read mode.
                        Must support seek() and read() operations.
        """
        self.file = file_handle

    def read_at(self, offset: int, length: int) -> bytes:
        """Read bytes at specific offset.

        Seeks to the specified offset and reads the requested number
        of bytes. The file position after this call will be at
        offset + length.

        Args:
            offset: Byte offset from the beginning of the file.
            length: Number of bytes to read.

        Returns:
            Bytes read from the file. May be shorter than length
            if end of file is reached.

        Raises:
            ValueError: If offset or length is negative.
        """
        if offset < 0:
            raise ValueError(f"offset must be non-negative, got {offset}")
        if length < 0:
            raise ValueError(f"length must be non-negative, got {length}")

        self.file.seek(offset)
        return self.file.read(length)

    def read_struct(self, offset: int, format_str: str) -> tuple:
        """Read and unpack struct at offset.

        Seeks to the specified offset, reads the appropriate number
        of bytes for the struct format, and unpacks the data according
        to the format string.

        Args:
            offset: Byte offset from the beginning of the file.
            format_str: Format string for struct.unpack().
                       See Python's struct module for format specification.
                       Example: '<I' for little-endian unsigned int.

        Returns:
            Tuple of unpacked values according to the format string.

        Raises:
            ValueError: If offset is negative or format_str is invalid.
            struct.error: If format string is malformed.

        Example:
            >>> reader.read_struct(0x100, '<4sI')
            (b'NCCH', 4096)
        """
        if offset < 0:
            raise ValueError(f"offset must be non-negative, got {offset}")

        size = struct.calcsize(format_str)
        data = self.read_at(offset, size)
        return struct.unpack(format_str, data)

    def tell(self) -> int:
        """Get current file position.

        Returns:
            Current byte offset in the file.
        """
        return self.file.tell()

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to a position in the file.

        Args:
            offset: Offset to seek to.
            whence: How to interpret offset:
                   0 (default): absolute file positioning
                   1: seek relative to current position
                   2: seek relative to file's end

        Returns:
            The new absolute position.
        """
        return self.file.seek(offset, whence)

    def read(self, size: int = -1) -> bytes:
        """Read and return up to size bytes from current position.

        Args:
            size: Number of bytes to read. If -1 (default),
                 read until end of file.

        Returns:
            Bytes read from the file.
        """
        return self.file.read(size)
