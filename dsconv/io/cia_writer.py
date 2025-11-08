"""CIA file writing utilities."""

import hashlib
import struct
from typing import BinaryIO

from dsconv.io.binary_writer import BinaryWriter
from dsconv.models.cia import CIAHeader


class CIAWriter:
    """Writes CIA (CTR Importable Archive) files.

    This writer class handles the construction of CIA files by writing
    the various sections in the correct order and format:
    1. CIA Header (0x2020 bytes)
    2. Certificate Chain (aligned to 64 bytes)
    3. Ticket (aligned to 64 bytes)
    4. TMD (Title Metadata) (aligned to 64 bytes)
    5. Content (aligned to 64 bytes)
    6. Meta (aligned to 64 bytes)

    The writer uses dependency injection for the binary writer and
    certificate chain to make it testable and flexible.

    Example:
        >>> with open('output.cia', 'wb') as f:
        ...     writer = CIAWriter(BinaryWriter(f), cert_chain)
        ...     writer.write_header(header)
        ...     writer.write_cert_chain()
        ...     # ... write other sections

    Reference: 3dbrew.org/wiki/CIA
    """

    def __init__(
        self,
        binary_writer: BinaryWriter,
        cert_chain: bytes,
        dev_mode: bool = False,
    ):
        """Initialize CIAWriter with dependencies.

        Args:
            binary_writer: BinaryWriter instance for file operations
            cert_chain: Certificate chain bytes (retail or dev)
            dev_mode: If True, use dev certificate chain (default: False)
        """
        self.writer = binary_writer
        self.cert_chain = cert_chain
        self.dev_mode = dev_mode

    def write_header(self, header: CIAHeader) -> None:
        """Write CIA header to file.

        Writes the complete 0x2020 byte CIA header at the beginning
        of the file.

        Args:
            header: CIAHeader object to write

        Raises:
            ValueError: If header is invalid
        """
        # Build header bytes from CIAHeader object
        header_bytes = struct.pack(
            "<IHHIIIIQ",
            header.header_size,  # 0x2020
            header.type_,  # Type (usually 0)
            header.version,  # Version (usually 0)
            header.cert_chain_size,  # Certificate chain size
            header.ticket_size,  # Ticket size
            header.tmd_size,  # TMD size
            header.meta_size,  # Meta size
            header.content_size,  # Content size (8 bytes)
        )

        # Add content index (0x2000 bytes)
        header_bytes += header.content_index

        # Write header at offset 0
        self.writer.write_at(0, header_bytes)

    def write_cert_chain(self) -> None:
        """Write certificate chain to file.

        Writes the certificate chain immediately after the header.
        The certificate chain is 0xA00 bytes for retail, or variable
        size for dev mode.
        """
        self.writer.append(self.cert_chain)

    def write_ticket(self, ticket_data: bytes) -> None:
        """Write ticket section to file.

        The ticket must be aligned to 64 bytes from the start of the
        certificate chain. This method writes the ticket data and
        adds padding if necessary.

        Args:
            ticket_data: Ticket data bytes (usually 0x350 bytes)
        """
        # Align to 64 bytes
        current_pos = self.writer.tell()
        aligned_pos = self._align_offset(current_pos)
        if aligned_pos > current_pos:
            self.writer.append(bytes(aligned_pos - current_pos))

        self.writer.append(ticket_data)

    def write_tmd(self, tmd_data: bytes) -> None:
        """Write TMD (Title Metadata) section to file.

        The TMD must be aligned to 64 bytes. This method writes the
        TMD data and adds padding if necessary.

        Args:
            tmd_data: TMD data bytes (variable size based on content count)
        """
        # Align to 64 bytes
        current_pos = self.writer.tell()
        aligned_pos = self._align_offset(current_pos)
        if aligned_pos > current_pos:
            self.writer.append(bytes(aligned_pos - current_pos))

        self.writer.append(tmd_data)

    def write_content(
        self,
        content_data: bytes,
        compute_hash: bool = True,
        chunk_size: int = 0x800000,
    ) -> bytes:
        """Write content and return its hash.

        This method writes content data in chunks to handle large files
        efficiently. It computes and returns the SHA-256 hash of the
        content for use in the TMD.

        Args:
            content_data: Content data to write (can be very large)
            compute_hash: If True, compute and return SHA-256 hash (default: True)
            chunk_size: Size of chunks for writing (default: 8MB = 0x800000)

        Returns:
            SHA-256 hash digest (32 bytes) if compute_hash is True,
            otherwise empty bytes

        Raises:
            ValueError: If chunk_size is not positive
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")

        # Align to 64 bytes
        current_pos = self.writer.tell()
        aligned_pos = self._align_offset(current_pos)
        if aligned_pos > current_pos:
            self.writer.append(bytes(aligned_pos - current_pos))

        hash_obj = hashlib.sha256()

        # Write in chunks to handle large files
        offset = 0
        while offset < len(content_data):
            chunk = content_data[offset : offset + chunk_size]
            self.writer.append(chunk)
            if compute_hash:
                hash_obj.update(chunk)
            offset += chunk_size

        return hash_obj.digest() if compute_hash else b""

    def write_content_from_source(
        self,
        source: BinaryIO,
        size: int,
        compute_hash: bool = True,
        chunk_size: int = 0x800000,
    ) -> bytes:
        """Write content from a source file and return its hash.

        This method reads from a source file in chunks and writes to
        the CIA, computing the hash as it goes. This is more memory
        efficient than reading the entire content into memory first.

        Args:
            source: Source file object to read from (must support read())
            size: Total number of bytes to read and write
            compute_hash: If True, compute and return SHA-256 hash (default: True)
            chunk_size: Size of chunks for reading/writing (default: 8MB = 0x800000)

        Returns:
            SHA-256 hash digest (32 bytes) if compute_hash is True,
            otherwise empty bytes

        Raises:
            ValueError: If size is negative or chunk_size is not positive
        """
        if size < 0:
            raise ValueError(f"size must be non-negative, got {size}")
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")

        # Align to 64 bytes
        current_pos = self.writer.tell()
        aligned_pos = self._align_offset(current_pos)
        if aligned_pos > current_pos:
            self.writer.append(bytes(aligned_pos - current_pos))

        hash_obj = hashlib.sha256()
        bytes_left = size

        while bytes_left > 0:
            to_read = min(chunk_size, bytes_left)
            chunk = source.read(to_read)

            if len(chunk) == 0:
                # End of file reached prematurely
                break

            self.writer.append(chunk)
            if compute_hash:
                hash_obj.update(chunk)
            bytes_left -= len(chunk)

        return hash_obj.digest() if compute_hash else b""

    def write_meta(self, meta_data: bytes) -> None:
        """Write meta section to file.

        The meta section must be aligned to 64 bytes. This method writes
        the meta data and adds padding if necessary.

        The meta section is typically 0x3AC0 bytes and contains:
        - Dependency list (0x180 bytes)
        - Reserved (0x180 bytes)
        - Core version (4 bytes)
        - Reserved (0xFC bytes)
        - Icon data (0x36C0 bytes)

        Args:
            meta_data: Meta section data (usually 0x3AC0 bytes)
        """
        # Align to 64 bytes
        current_pos = self.writer.tell()
        aligned_pos = self._align_offset(current_pos)
        if aligned_pos > current_pos:
            self.writer.append(bytes(aligned_pos - current_pos))

        self.writer.append(meta_data)

    def update_tmd_hash(
        self,
        tmd_offset: int,
        content_hash: bytes,
        content_index: int = 0,
    ) -> None:
        """Update content hash in TMD chunk records.

        After writing content, this method updates the TMD with the
        computed content hash.

        Args:
            tmd_offset: Byte offset to the TMD section in the CIA file
            content_hash: SHA-256 hash of the content (32 bytes)
            content_index: Index of the content in the TMD (default: 0)

        Raises:
            ValueError: If content_hash is not 32 bytes
        """
        if len(content_hash) != 32:
            raise ValueError(f"content_hash must be 32 bytes, got {len(content_hash)}")

        # Chunk records start at TMD offset + 0xB04
        # Each chunk record is 0x30 bytes
        # Hash is at offset 0x10 within each chunk record
        chunk_record_offset = tmd_offset + 0xB04 + (content_index * 0x30) + 0x10
        self.writer.write_at(chunk_record_offset, content_hash)

    @staticmethod
    def _align_offset(offset: int, alignment: int = 64) -> int:
        """Align offset to specified boundary.

        Args:
            offset: Offset to align
            alignment: Alignment boundary in bytes (default: 64)

        Returns:
            Aligned offset (rounded up to next alignment boundary)
        """
        return (offset + alignment - 1) // alignment * alignment
