"""NCCH (Nintendo Content Container Header) models."""

import struct
from dataclasses import dataclass


@dataclass
class NCCHHeader:
    """NCCH Header structure.

    Represents the header of a Nintendo Content Container (NCCH).
    This structure appears at the beginning of each NCCH partition
    in a CCI file or as standalone CIA content.

    The NCCH header is 0x200 bytes and contains metadata about the
    content, including size, encryption flags, partition ID, and hashes.

    Fields Included:
        This dataclass includes only the fields required for CCI to CIA
        conversion. The full NCCH header contains additional fields for
        RomFS, plain region, and logo region that are not needed for the
        conversion process and are therefore omitted.

    Fields Omitted:
        - Verification hash (0x114-0x118): Not used in conversion
        - Reserved regions (0x120-0x160, 0x184-0x188)
        - Plain region offset/length (0x190-0x1A0)
        - Logo region offset/length (not used)
        - ExeFS hash region size (0x1A8-0x1AC)
        - RomFS offset/size/hash (0x1AC-0x200)

    Reference: 3dbrew.org/wiki/NCCH
    """

    signature: bytes  # 0x000-0x100: RSA-2048 signature
    magic: bytes  # 0x100-0x104: 'NCCH'
    content_size: int  # 0x104-0x108: Size in media units (0x200 bytes)
    partition_id: bytes  # 0x108-0x110: Partition ID (8 bytes)
    maker_code: bytes  # 0x110-0x112: Maker code (2 bytes)
    version: int  # 0x112-0x114: Version (2 bytes)
    program_id: bytes  # 0x118-0x120: Program ID / Title ID (8 bytes)
    extheader_hash: bytes  # 0x160-0x180: Extended header SHA-256 hash
    extheader_size: int  # 0x180-0x184: Extended header size (4 bytes)
    flags: bytes  # 0x188-0x190: Flags (8 bytes)
    exefs_offset: int  # 0x1A0-0x1A4: ExeFS offset in media units
    exefs_size: int  # 0x1A4-0x1A8: ExeFS size in media units

    def __post_init__(self):
        """Validate header fields."""
        if len(self.magic) != 4:
            raise ValueError("magic must be 4 bytes")
        if self.magic != b"NCCH":
            raise ValueError(f"Invalid NCCH magic: {self.magic}")
        if len(self.signature) != 0x100:
            raise ValueError("signature must be 0x100 bytes")
        if len(self.partition_id) != 8:
            raise ValueError("partition_id must be 8 bytes")
        if len(self.maker_code) != 2:
            raise ValueError("maker_code must be 2 bytes")
        if len(self.program_id) != 8:
            raise ValueError("program_id must be 8 bytes")
        if len(self.extheader_hash) != 0x20:
            raise ValueError("extheader_hash must be 0x20 bytes")
        if len(self.flags) != 8:
            raise ValueError("flags must be 8 bytes")

    @property
    def is_encrypted(self) -> bool:
        """Check if content is encrypted.

        Returns:
            True if content is encrypted, False if decrypted

        The encryption flag is at offset 0x7 (bit 2) within the flags field.
        When bit 2 is set (0x04), the content is decrypted.
        When bit 2 is clear (0x00), the content is encrypted.
        """
        # Flags are at offset 0x188-0x190 (8 bytes)
        # Encryption flags are at offset 0x18F (byte 7 of flags)
        encryption_byte = self.flags[7]
        # Bit 2 of encryption flags: 0 = encrypted, 1 = decrypted
        return not bool(encryption_byte & 0x04)

    @property
    def uses_zerokey(self) -> bool:
        """Check if content uses zero-key encryption.

        Returns:
            True if zero-key encrypted, False otherwise

        The zero-key flag is at bit 0 of the encryption flags byte.
        """
        encryption_byte = self.flags[7]
        # Bit 0 of encryption flags
        return bool(encryption_byte & 0x01)

    @property
    def size_bytes(self) -> int:
        """Get content size in bytes.

        Returns:
            Size in bytes (content_size * media_unit_size)

        Media unit size is 0x200 bytes (512 bytes).
        """
        return self.content_size * 0x200

    @property
    def title_id(self) -> bytes:
        """Get title ID (alias for program_id).

        Returns:
            Title ID as bytes (8 bytes)

        The program ID and title ID are the same field.
        """
        return self.program_id

    @classmethod
    def from_bytes(cls, data: bytes) -> "NCCHHeader":
        """Create NCCHHeader from binary data.

        Args:
            data: Binary data containing NCCH header (at least 0x200 bytes)

        Returns:
            Parsed NCCHHeader object

        Raises:
            ValueError: If data is too short or invalid

        The NCCH header structure (0x200 bytes):
        - 0x000-0x100: RSA-2048 signature
        - 0x100-0x104: Magic "NCCH"
        - 0x104-0x108: Content size (media units)
        - 0x108-0x110: Partition ID
        - 0x110-0x112: Maker code
        - 0x112-0x114: Version
        - 0x118-0x120: Program ID
        - 0x160-0x180: Extended header hash
        - 0x180-0x184: Extended header size
        - 0x188-0x190: Flags (including encryption at 0x18F)
        - 0x1A0-0x1A4: ExeFS offset
        - 0x1A4-0x1A8: ExeFS size
        """
        if len(data) < 0x200:
            raise ValueError("Data too short for NCCH header")

        # Parse signature (0x000-0x100)
        signature = data[0x000:0x100]

        # Parse magic (0x100-0x104)
        magic = data[0x100:0x104]

        # Parse content size (0x104-0x108, little-endian uint32)
        (content_size,) = struct.unpack("<I", data[0x104:0x108])

        # Parse partition ID (0x108-0x110)
        partition_id = data[0x108:0x110]

        # Parse maker code (0x110-0x112)
        maker_code = data[0x110:0x112]

        # Parse version (0x112-0x114, little-endian uint16)
        (version,) = struct.unpack("<H", data[0x112:0x114])

        # Parse program ID (0x118-0x120)
        program_id = data[0x118:0x120]

        # Parse extended header hash (0x160-0x180)
        extheader_hash = data[0x160:0x180]

        # Parse extended header size (0x180-0x184, little-endian uint32)
        (extheader_size,) = struct.unpack("<I", data[0x180:0x184])

        # Parse flags (0x188-0x190)
        flags = data[0x188:0x190]

        # Parse ExeFS offset (0x1A0-0x1A4, little-endian uint32)
        (exefs_offset,) = struct.unpack("<I", data[0x1A0:0x1A4])

        # Parse ExeFS size (0x1A4-0x1A8, little-endian uint32)
        (exefs_size,) = struct.unpack("<I", data[0x1A4:0x1A8])

        return cls(
            signature=signature,
            magic=magic,
            content_size=content_size,
            partition_id=partition_id,
            maker_code=maker_code,
            version=version,
            program_id=program_id,
            extheader_hash=extheader_hash,
            extheader_size=extheader_size,
            flags=flags,
            exefs_offset=exefs_offset,
            exefs_size=exefs_size,
        )
