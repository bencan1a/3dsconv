"""CIA (CTR Importable Archive) structure models."""

import struct
from dataclasses import dataclass


@dataclass
class CIAHeader:
    """CIA Archive header structure.

    The CIA format is used for installing content on Nintendo 3DS systems.
    This header defines the sizes and layout of the various sections that
    make up the CIA file.

    The CIA header is 0x2020 bytes (0x20 bytes header + 0x2000 bytes reserved).
    It specifies the sizes of:
    - Certificate chain (0xA00 bytes for retail, variable for dev)
    - Ticket (0x350 bytes)
    - TMD (Title Metadata) - variable size based on number of contents
    - Meta (0x3AC0 bytes)
    - Content - variable size, sum of all content chunks
    - Content index bitmap - indicates which content indices are present

    The file structure is:
    [Header][Cert Chain][Ticket][TMD][Content][Meta]

    Each section is aligned to 64 bytes.

    Reference: 3dbrew.org/wiki/CIA
    """

    header_size: int  # 0x00-0x04: Archive header size (always 0x2020)
    type_: int  # 0x04-0x06: Type (0 for standard CIA)
    version: int  # 0x06-0x08: Version (0 for standard)
    cert_chain_size: int  # 0x08-0x0C: Certificate chain size (usually 0xA00)
    ticket_size: int  # 0x0C-0x10: Ticket size (usually 0x350)
    tmd_size: int  # 0x10-0x14: TMD size (0xB34 base + 0x30 per additional content)
    meta_size: int  # 0x14-0x18: Meta size (usually 0x3AC0)
    content_size: int  # 0x18-0x20: Total content size in bytes
    content_index: bytes  # 0x20-0x2000: Content index bitmap (0x2000 bytes)

    def __post_init__(self):
        """Validate header fields."""
        if self.header_size != 0x2020:
            raise ValueError(f"header_size must be 0x2020, got 0x{self.header_size:X}")
        if self.type_ < 0 or self.type_ > 0xFFFF:
            raise ValueError(f"type_ must be uint16, got {self.type_}")
        if self.version < 0 or self.version > 0xFFFF:
            raise ValueError(f"version must be uint16, got {self.version}")
        if self.cert_chain_size < 0:
            raise ValueError(f"cert_chain_size must be non-negative, got {self.cert_chain_size}")
        if self.ticket_size < 0:
            raise ValueError(f"ticket_size must be non-negative, got {self.ticket_size}")
        if self.tmd_size < 0:
            raise ValueError(f"tmd_size must be non-negative, got {self.tmd_size}")
        if self.meta_size < 0:
            raise ValueError(f"meta_size must be non-negative, got {self.meta_size}")
        if self.content_size < 0:
            raise ValueError(f"content_size must be non-negative, got {self.content_size}")
        if len(self.content_index) != 0x2000:
            raise ValueError(
                f"content_index must be 0x2000 bytes, got {len(self.content_index)} bytes"
            )

    @property
    def num_contents(self) -> int:
        """Get the number of contents in this CIA.

        Returns:
            Number of content chunks (count of set bits in content_index[0])

        The first byte of content_index is a bitmap where each bit represents
        a content index. Bit 7 = content 0, bit 6 = content 1, etc.
        """
        # Count set bits in the first byte (content index bitmap)
        first_byte = self.content_index[0]
        return bin(first_byte).count("1")

    @property
    def has_multiple_contents(self) -> bool:
        """Check if CIA has multiple content chunks.

        Returns:
            True if more than one content chunk, False otherwise
        """
        return self.num_contents > 1

    @property
    def cert_chain_offset(self) -> int:
        """Get offset to certificate chain.

        Returns:
            Offset in bytes (always 0x2020, right after header)
        """
        return 0x2020

    @property
    def ticket_offset(self) -> int:
        """Get offset to ticket section.

        Returns:
            Offset in bytes (cert_chain_offset + aligned cert_chain_size)
        """
        return self._align_offset(self.cert_chain_offset + self.cert_chain_size)

    @property
    def tmd_offset(self) -> int:
        """Get offset to TMD section.

        Returns:
            Offset in bytes (ticket_offset + aligned ticket_size)
        """
        return self._align_offset(self.ticket_offset + self.ticket_size)

    @property
    def content_offset(self) -> int:
        """Get offset to content section.

        Returns:
            Offset in bytes (tmd_offset + aligned tmd_size)
        """
        return self._align_offset(self.tmd_offset + self.tmd_size)

    @property
    def meta_offset(self) -> int:
        """Get offset to meta section.

        Returns:
            Offset in bytes (content_offset + aligned content_size)
        """
        return self._align_offset(self.content_offset + self.content_size)

    @staticmethod
    def _align_offset(offset: int, alignment: int = 64) -> int:
        """Align offset to specified boundary.

        Args:
            offset: Offset to align
            alignment: Alignment boundary (default: 64 bytes)

        Returns:
            Aligned offset
        """
        return (offset + alignment - 1) // alignment * alignment

    @classmethod
    def from_bytes(cls, data: bytes) -> "CIAHeader":
        """Create CIAHeader from binary data.

        Args:
            data: Binary data containing CIA header (at least 0x2020 bytes)

        Returns:
            Parsed CIAHeader object

        Raises:
            ValueError: If data is too short or invalid

        The CIA header structure (0x2020 bytes):
        - 0x00-0x04: Archive header size (always 0x2020)
        - 0x04-0x06: Type (uint16, usually 0)
        - 0x06-0x08: Version (uint16, usually 0)
        - 0x08-0x0C: Certificate chain size (uint32)
        - 0x0C-0x10: Ticket size (uint32)
        - 0x10-0x14: TMD size (uint32)
        - 0x14-0x18: Meta size (uint32)
        - 0x18-0x20: Content size (uint64)
        - 0x20-0x2020: Content index (0x2000 bytes)
        """
        if len(data) < 0x2020:
            raise ValueError(
                f"Data too short for CIA header (need at least 0x2020 bytes, got {len(data)} bytes)"
            )

        # Parse header size (0x00-0x04, little-endian uint32)
        (header_size,) = struct.unpack("<I", data[0x00:0x04])

        # Parse type (0x04-0x06, little-endian uint16)
        (type_,) = struct.unpack("<H", data[0x04:0x06])

        # Parse version (0x06-0x08, little-endian uint16)
        (version,) = struct.unpack("<H", data[0x06:0x08])

        # Parse certificate chain size (0x08-0x0C, little-endian uint32)
        (cert_chain_size,) = struct.unpack("<I", data[0x08:0x0C])

        # Parse ticket size (0x0C-0x10, little-endian uint32)
        (ticket_size,) = struct.unpack("<I", data[0x0C:0x10])

        # Parse TMD size (0x10-0x14, little-endian uint32)
        (tmd_size,) = struct.unpack("<I", data[0x10:0x14])

        # Parse meta size (0x14-0x18, little-endian uint32)
        (meta_size,) = struct.unpack("<I", data[0x14:0x18])

        # Parse content size (0x18-0x20, little-endian uint64)
        (content_size,) = struct.unpack("<Q", data[0x18:0x20])

        # Parse content index (0x20-0x2020)
        content_index = data[0x20:0x2020]

        return cls(
            header_size=header_size,
            type_=type_,
            version=version,
            cert_chain_size=cert_chain_size,
            ticket_size=ticket_size,
            tmd_size=tmd_size,
            meta_size=meta_size,
            content_size=content_size,
            content_index=content_index,
        )


@dataclass
class CIAContent:
    """Individual content record in CIA TMD (Title Metadata).

    Each CIA can contain multiple content chunks (e.g., game executable,
    manual, download play child). Each content is described by a record
    in the TMD that specifies its ID, index, size, and SHA-256 hash.

    Content records are stored in the TMD section of the CIA file.
    The TMD contains a content info record array, followed by content
    chunk records. Each chunk record is 0x30 bytes.

    Reference: 3dbrew.org/wiki/Title_metadata
    """

    content_id: int  # Content ID (4 bytes, big-endian)
    index: int  # Content index (2 bytes, big-endian)
    content_type: int  # Content type flags (2 bytes, big-endian)
    size: int  # Content size in bytes (8 bytes, big-endian)
    hash: bytes  # SHA-256 hash of content (32 bytes)

    def __post_init__(self):
        """Validate content fields."""
        if self.content_id < 0 or self.content_id > 0xFFFFFFFF:
            raise ValueError(f"content_id must be uint32, got {self.content_id}")
        if self.index < 0 or self.index > 0xFFFF:
            raise ValueError(f"index must be uint16, got {self.index}")
        if self.content_type < 0 or self.content_type > 0xFFFF:
            raise ValueError(f"content_type must be uint16, got {self.content_type}")
        if self.size < 0:
            raise ValueError(f"size must be non-negative, got {self.size}")
        if len(self.hash) != 32:
            raise ValueError(f"hash must be 32 bytes, got {len(self.hash)} bytes")

    @property
    def is_encrypted(self) -> bool:
        """Check if content is encrypted.

        Returns:
            True if content is encrypted (bit 0 of content_type is set)
        """
        return bool(self.content_type & 0x0001)

    @property
    def is_optional(self) -> bool:
        """Check if content is optional.

        Returns:
            True if content is optional (bit 14 of content_type is set)
        """
        return bool(self.content_type & 0x4000)

    @property
    def is_shared(self) -> bool:
        """Check if content is shared.

        Returns:
            True if content is shared (bit 15 of content_type is set)
        """
        return bool(self.content_type & 0x8000)

    @classmethod
    def from_bytes(cls, data: bytes) -> "CIAContent":
        """Create CIAContent from binary data.

        Args:
            data: Binary data containing content record (at least 0x30 bytes)

        Returns:
            Parsed CIAContent object

        Raises:
            ValueError: If data is too short

        The content chunk record structure (0x30 bytes):
        - 0x00-0x04: Content ID (big-endian uint32)
        - 0x04-0x06: Content index (big-endian uint16)
        - 0x06-0x08: Content type (big-endian uint16)
        - 0x08-0x10: Content size (big-endian uint64)
        - 0x10-0x30: SHA-256 hash (32 bytes)
        """
        if len(data) < 0x30:
            raise ValueError(
                f"Data too short for content record (need at least 0x30 bytes, got {len(data)} bytes)"
            )

        # Parse content ID (0x00-0x04, big-endian uint32)
        (content_id,) = struct.unpack(">I", data[0x00:0x04])

        # Parse content index (0x04-0x06, big-endian uint16)
        (index,) = struct.unpack(">H", data[0x04:0x06])

        # Parse content type (0x06-0x08, big-endian uint16)
        (content_type,) = struct.unpack(">H", data[0x06:0x08])

        # Parse content size (0x08-0x10, big-endian uint64)
        (size,) = struct.unpack(">Q", data[0x08:0x10])

        # Parse hash (0x10-0x30)
        hash_value = data[0x10:0x30]

        return cls(
            content_id=content_id,
            index=index,
            content_type=content_type,
            size=size,
            hash=hash_value,
        )
