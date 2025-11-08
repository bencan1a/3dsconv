"""NCSD (Nintendo Content Storage Device) container models."""

import struct
from dataclasses import dataclass


@dataclass
class NCSDPartition:
    """Represents a partition in an NCSD container.

    Each NCSD container can have up to 8 partitions, though typically only
    the first three are used for:
    - Game Executable CXI (partition 0)
    - Manual CFA (partition 1)
    - Download Play child CFA (partition 2)

    Partitions are defined by their offset and size in media units (0x200 bytes).

    Reference: 3dbrew.org/wiki/NCSD
    """

    offset: int  # Offset in media units (multiply by 0x200 for bytes)
    size: int  # Size in media units (multiply by 0x200 for bytes)
    partition_type: str  # 'game', 'manual', 'dlpchild', or 'unknown'

    def __post_init__(self):
        """Validate partition fields."""
        if self.offset < 0:
            raise ValueError("offset must be non-negative")
        if self.size < 0:
            raise ValueError("size must be non-negative")
        if self.partition_type not in ("game", "manual", "dlpchild", "unknown"):
            raise ValueError(
                f"partition_type must be 'game', 'manual', 'dlpchild', or 'unknown', got '{self.partition_type}'"
            )

    @property
    def offset_bytes(self) -> int:
        """Get partition offset in bytes.

        Returns:
            Offset in bytes (offset * media_unit_size)
        """
        return self.offset * 0x200

    @property
    def size_bytes(self) -> int:
        """Get partition size in bytes.

        Returns:
            Size in bytes (size * media_unit_size)
        """
        return self.size * 0x200


@dataclass
class NCSDContainer:
    """NCSD Container (CCI file structure).

    The NCSD format is used for 3DS game cards (CCI files with .3ds/.cci extensions).
    It contains a header with metadata and up to 8 partitions.

    The NCSD header is located at offset 0x100 in the file and contains:
    - Magic bytes "NCSD"
    - Title ID (Program ID)
    - Partition table (8 partitions, offset and size for each)

    Reference: 3dbrew.org/wiki/NCSD
    """

    magic: bytes  # 0x100-0x104: Should be b'NCSD'
    title_id: bytes  # 0x108-0x110: Title ID (8 bytes, reversed)
    partitions: list[NCSDPartition]  # Partition table (up to 8 partitions)

    def __post_init__(self):
        """Validate container fields."""
        if len(self.magic) != 4:
            raise ValueError("magic must be 4 bytes")
        if self.magic != b"NCSD":
            raise ValueError(f"Invalid NCSD magic: {self.magic!r}")
        if len(self.title_id) != 8:
            raise ValueError("title_id must be 8 bytes")
        if len(self.partitions) > 8:
            raise ValueError(f"Cannot have more than 8 partitions, got {len(self.partitions)}")

    def get_game_partition(self) -> NCSDPartition | None:
        """Get the main game executable partition.

        Returns:
            The game partition (partition 0) if it exists, None otherwise
        """
        for partition in self.partitions:
            if partition.partition_type == "game":
                return partition
        return None

    def get_partition_by_type(self, partition_type: str) -> NCSDPartition | None:
        """Get partition by type.

        Args:
            partition_type: Type of partition ('game', 'manual', 'dlpchild', or 'unknown')

        Returns:
            The first partition matching the type, or None if not found
        """
        for partition in self.partitions:
            if partition.partition_type == partition_type:
                return partition
        return None

    def get_all_partitions_by_type(self, partition_type: str) -> list[NCSDPartition]:
        """Get all partitions matching a type.

        Args:
            partition_type: Type of partition ('game', 'manual', 'dlpchild', or 'unknown')

        Returns:
            List of partitions matching the type (may be empty)
        """
        return [p for p in self.partitions if p.partition_type == partition_type]

    @classmethod
    def from_bytes(cls, data: bytes) -> "NCSDContainer":
        """Create NCSDContainer from binary data.

        Args:
            data: Binary data containing NCSD header (at least 0x160 bytes)

        Returns:
            Parsed NCSDContainer object

        Raises:
            ValueError: If data is too short or invalid

        The NCSD header structure:
        - 0x100-0x104: Magic "NCSD"
        - 0x108-0x110: Title ID (8 bytes, stored in reverse order)
        - 0x120-0x160: Partition table (8 partitions, 8 bytes each)
          Each partition entry:
          - 0x00-0x04: Offset in media units (little-endian uint32)
          - 0x04-0x08: Size in media units (little-endian uint32)

        Partition types are assigned based on position:
        - Partition 0: Game Executable CXI
        - Partition 1: Manual CFA
        - Partition 2: Download Play child CFA
        - Partitions 3-7: Unknown/reserved
        """
        if len(data) < 0x160:
            raise ValueError(
                f"Data too short for NCSD header (need at least 0x160 bytes, got {len(data)} bytes)"
            )

        # Parse magic (0x100-0x104)
        magic = data[0x100:0x104]

        # Parse title ID (0x108-0x110)
        # Title ID is stored in reverse byte order
        title_id = data[0x108:0x110][::-1]

        # Parse partition table (0x120-0x160)
        # 8 partitions, each with offset and size (8 bytes total per partition)
        partitions = []
        partition_types = [
            "game",
            "manual",
            "dlpchild",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
        ]

        for i in range(8):
            base_offset = 0x120 + (i * 8)
            # Parse offset (little-endian uint32)
            (offset,) = struct.unpack("<I", data[base_offset : base_offset + 4])
            # Parse size (little-endian uint32)
            (size,) = struct.unpack("<I", data[base_offset + 4 : base_offset + 8])

            # Only add partition if it has non-zero size
            if size > 0:
                partitions.append(
                    NCSDPartition(offset=offset, size=size, partition_type=partition_types[i])
                )

        return cls(magic=magic, title_id=title_id, partitions=partitions)
