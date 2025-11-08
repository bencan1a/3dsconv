"""NCSD container reader for CCI files."""

from dsconv.io.binary_reader import BinaryReader
from dsconv.models.ncsd import NCSDContainer, NCSDPartition


class NCSDReader:
    """Reads NCSD container structure from CCI files.

    The NCSD (Nintendo Content Storage Device) format is used for 3DS game
    cards (CCI files with .3ds/.cci extensions). This reader parses the
    NCSD header and partition table to create an NCSDContainer domain model.

    The reader expects a BinaryReader instance that is positioned at the
    start of a valid CCI file. It will read the NCSD header starting at
    offset 0x100 and parse up to 8 partitions from the partition table.

    Example:
        >>> with open('game.cci', 'rb') as f:
        ...     reader = NCSDReader(BinaryReader(f))
        ...     container = reader.read_container()
        ...     game_partition = container.get_game_partition()

    Reference: 3dbrew.org/wiki/NCSD
    """

    def __init__(self, binary_reader: BinaryReader):
        """Initialize NCSDReader with a BinaryReader.

        Args:
            binary_reader: BinaryReader instance for reading file data
        """
        self.reader = binary_reader

    def read_container(self) -> NCSDContainer:
        """Parse NCSD container header and partitions.

        Reads the NCSD header at offset 0x100 and parses the partition table
        to create a complete NCSDContainer model.

        Returns:
            NCSDContainer object with parsed header and partition data

        Raises:
            ValueError: If NCSD magic is invalid or data is malformed

        The NCSD header structure (all offsets relative to file start):
        - 0x100-0x104: Magic bytes "NCSD"
        - 0x108-0x110: Title ID (8 bytes, stored in reverse order)
        - 0x120-0x160: Partition table (8 partitions, 8 bytes each)
        """
        # Read and validate magic at 0x100
        magic = self.reader.read_at(0x100, 4)
        if magic != b"NCSD":
            raise ValueError(f"Invalid NCSD magic: {magic!r} (expected b'NCSD')")

        # Read title ID at 0x108 (stored in reverse byte order)
        title_id = self.reader.read_at(0x108, 8)[::-1]

        # Parse partition table
        partitions = self._read_partitions()

        return NCSDContainer(magic=magic, title_id=title_id, partitions=partitions)

    def _read_partitions(self) -> list[NCSDPartition]:
        """Parse partition table from NCSD header.

        Reads the 8-entry partition table starting at offset 0x120.
        Each partition entry is 8 bytes:
        - Bytes 0-3: Offset in media units (little-endian uint32)
        - Bytes 4-7: Size in media units (little-endian uint32)

        Only partitions with non-zero size are included in the result.

        Partition types are assigned based on position:
        - Partition 0: Game Executable CXI
        - Partition 1: Manual CFA
        - Partition 2: Download Play child CFA
        - Partitions 3-7: Unknown/reserved

        Returns:
            List of NCSDPartition objects (may be empty if no partitions)
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

        for i in range(8):
            # Calculate offset for this partition entry
            base_offset = 0x120 + (i * 8)

            # Read offset and size (both uint32, little-endian)
            (offset,) = self.reader.read_struct(base_offset, "<I")
            (size,) = self.reader.read_struct(base_offset + 4, "<I")

            # Only add partition if it has non-zero size
            if size > 0:
                partitions.append(
                    NCSDPartition(offset=offset, size=size, partition_type=partition_types[i])
                )

        return partitions
