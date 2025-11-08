"""NCSD container reader.

This module provides functionality to read and parse NCSD (Nintendo Content Storage Device)
container structures from CCI files (.3ds/.cci).
"""


from dsconv.io.binary_reader import BinaryReader
from dsconv.models.ncsd import NCSDContainer, NCSDPartition


class NCSDReader:
    """Reads NCSD container structure from CCI files.

    The NCSD reader parses the container header and partition table from
    3DS game card image (CCI) files. It validates the magic bytes and
    extracts partition information.

    The NCSD header structure (starting at offset 0x100):
    - 0x100-0x104: Magic bytes "NCSD"
    - 0x108-0x110: Title ID (8 bytes, stored in reverse order)
    - 0x120-0x160: Partition table (8 partitions, 8 bytes each)

    Example:
        >>> with open('game.3ds', 'rb') as f:
        ...     reader = BinaryReader(f)
        ...     ncsd_reader = NCSDReader(reader)
        ...     container = ncsd_reader.read_container()
        ...     print(f"Title ID: {container.title_id.hex()}")
    """

    def __init__(self, binary_reader: BinaryReader):
        """Initialize NCSDReader with a binary reader.

        Args:
            binary_reader: BinaryReader instance for reading from the CCI file
        """
        self.reader = binary_reader

    def read_container(self) -> NCSDContainer:
        """Parse NCSD container header and partitions.

        Reads the NCSD magic bytes, title ID, and partition table from the
        CCI file. Validates the magic bytes to ensure this is a valid NCSD
        container.

        Returns:
            NCSDContainer object with parsed header and partition information

        Raises:
            ValueError: If NCSD magic bytes are invalid
        """
        # Read magic at 0x100
        magic = self.reader.read_at(0x100, 4)
        if magic != b"NCSD":
            raise ValueError(f"Invalid NCSD magic: expected b'NCSD', got {magic!r}")

        # Read title ID at 0x108 (stored in reverse byte order)
        title_id = self.reader.read_at(0x108, 8)[::-1]

        # Parse partitions from partition table
        partitions = self._read_partitions()

        return NCSDContainer(magic=magic, title_id=title_id, partitions=partitions)

    def _read_partitions(self) -> list[NCSDPartition]:
        """Parse partition table from NCSD header.

        Reads the partition table at offset 0x120, which contains up to 8 partition
        entries. Each entry has an offset and size in media units (0x200 bytes).
        Only partitions with non-zero size are included in the result.

        Partition types are assigned based on position:
        - Partition 0: Game Executable CXI
        - Partition 1: Manual CFA
        - Partition 2: Download Play child CFA
        - Partitions 3-7: Unknown/reserved

        Returns:
            List of NCSDPartition objects for all non-empty partitions

        The partition table structure:
        - Location: 0x120-0x160 (64 bytes total)
        - 8 partitions × 8 bytes each
        - Each partition entry:
          - Offset 0x00-0x04: Partition offset in media units (little-endian uint32)
          - Offset 0x04-0x08: Partition size in media units (little-endian uint32)
        """
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

        # Read all 8 partition entries from the partition table
        for i in range(8):
            base_offset = 0x120 + (i * 8)

            # Parse offset and size (both little-endian uint32)
            (offset, size) = self.reader.read_struct(base_offset, "<II")

            # Only add partition if it has non-zero size
            if size > 0:
                partitions.append(
                    NCSDPartition(offset=offset, size=size, partition_type=partition_types[i])
                )

        return partitions
