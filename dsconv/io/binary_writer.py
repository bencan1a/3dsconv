"""Binary file writing utilities."""

import struct
from typing import BinaryIO


class BinaryWriter:
    """Utility for writing binary data.

    This class wraps a file handle and provides convenience methods
    for writing binary data at specific offsets without managing
    seek operations manually. It's designed to simplify writing
    structured binary formats like CIA files.

    Example:
        >>> with open('file.bin', 'wb') as f:
        ...     writer = BinaryWriter(f)
        ...     writer.write_at(0x100, b'NCCH')
        ...     writer.write_struct(0x104, '<I', 0x1000)
    """

    def __init__(self, file_handle: BinaryIO):
        """Initialize BinaryWriter with a file handle.

        Args:
            file_handle: A file-like object opened in binary write mode.
                        Must support seek() and write() operations.
        """
        self.file = file_handle

    def write_at(self, offset: int, data: bytes) -> None:
        """Write bytes at specific offset.

        Seeks to the specified offset and writes the provided bytes.
        The file position after this call will be at offset + len(data).

        Args:
            offset: Byte offset from the beginning of the file.
            data: Bytes to write to the file.

        Raises:
            ValueError: If offset is negative.
        """
        if offset < 0:
            raise ValueError(f"offset must be non-negative, got {offset}")

        self.file.seek(offset)
        self.file.write(data)

    def write_struct(self, offset: int, format_str: str, *values) -> None:
        """Pack and write struct at offset.

        Seeks to the specified offset, packs the values according to
        the format string, and writes the packed data.

        Args:
            offset: Byte offset from the beginning of the file.
            format_str: Format string for struct.pack().
                       See Python's struct module for format specification.
                       Example: '<I' for little-endian unsigned int.
            *values: Values to pack according to format_str.

        Raises:
            ValueError: If offset is negative.
            struct.error: If format string is malformed or values don't match.

        Example:
            >>> writer.write_struct(0x100, '<4sI', b'NCCH', 0x1000)
        """
        if offset < 0:
            raise ValueError(f"offset must be non-negative, got {offset}")

        data = struct.pack(format_str, *values)
        self.write_at(offset, data)

    def append(self, data: bytes) -> None:
        """Append data to end of file.

        Seeks to the end of the file and writes the provided bytes.
        This is useful for writing sequential content without tracking
        the current position.

        Args:
            data: Bytes to append to the file.
        """
        self.file.seek(0, 2)  # Seek to end (whence=2)
        self.file.write(data)

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

    def write(self, data: bytes) -> int:
        """Write bytes at current position.

        Args:
            data: Bytes to write to the file.

        Returns:
            Number of bytes written.
        """
        return self.file.write(data)
