"""Tests for NCSDReader."""

import struct
from io import BytesIO

import pytest

from dsconv.io.binary_reader import BinaryReader
from dsconv.io.ncsd_reader import NCSDReader
from dsconv.models.ncsd import NCSDContainer


class TestNCSDReader:
    """Tests for NCSDReader class."""

    def test_create_with_binary_reader(self):
        """Test creating NCSDReader with a BinaryReader."""
        # Arrange
        file_handle = BytesIO(b"\x00" * 0x200)
        binary_reader = BinaryReader(file_handle)

        # Act
        reader = NCSDReader(binary_reader)

        # Assert
        assert reader.reader is binary_reader

    def test_read_container_with_valid_ncsd(self):
        """Test reading a valid NCSD container."""
        # Arrange
        data = self._create_minimal_ncsd()
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert isinstance(container, NCSDContainer)
        assert container.magic == b"NCSD"

    def test_read_container_with_invalid_magic_raises_error(self):
        """Test reading container with invalid magic raises ValueError."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"XXXX"  # Invalid magic
        file_handle = BytesIO(bytes(data))
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCSD magic"):
            reader.read_container()

    def test_read_container_parses_title_id_correctly(self):
        """Test that title ID is parsed and reversed correctly."""
        # Arrange
        title_id = bytes.fromhex("0123456789ABCDEF")
        data = self._create_ncsd_with_title_id(title_id)
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        # Title ID should be reversed
        assert container.title_id == title_id[::-1]

    def test_read_container_with_no_partitions(self):
        """Test reading container with no partitions (all zero)."""
        # Arrange
        data = self._create_ncsd_with_partitions([])
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 0

    def test_read_container_with_game_partition_only(self):
        """Test reading container with only game partition."""
        # Arrange
        partitions = [(0x1000, 0x2000, "game")]
        data = self._create_ncsd_with_partitions(partitions)
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 1
        game = container.partitions[0]
        assert game.offset == 0x1000
        assert game.size == 0x2000
        assert game.partition_type == "game"

    def test_read_container_with_all_three_common_partitions(self):
        """Test reading container with game, manual, and dlpchild partitions."""
        # Arrange
        partitions = [
            (0x1000, 0x2000, "game"),
            (0x3000, 0x400, "manual"),
            (0x3400, 0x200, "dlpchild"),
        ]
        data = self._create_ncsd_with_partitions(partitions)
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 3

        game = container.partitions[0]
        assert game.offset == 0x1000
        assert game.size == 0x2000
        assert game.partition_type == "game"

        manual = container.partitions[1]
        assert manual.offset == 0x3000
        assert manual.size == 0x400
        assert manual.partition_type == "manual"

        dlpchild = container.partitions[2]
        assert dlpchild.offset == 0x3400
        assert dlpchild.size == 0x200
        assert dlpchild.partition_type == "dlpchild"

    def test_read_container_skips_zero_size_partitions(self):
        """Test that partitions with zero size are skipped."""
        # Arrange
        # Create data with game partition, but manual and dlpchild are zero
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # Game partition (non-zero)
        struct.pack_into("<I", data, 0x120, 0x1000)  # offset
        struct.pack_into("<I", data, 0x124, 0x2000)  # size

        # Manual partition (zero size - should be skipped)
        struct.pack_into("<I", data, 0x128, 0x3000)  # offset
        struct.pack_into("<I", data, 0x12C, 0)  # size = 0

        # DLP partition (zero size - should be skipped)
        struct.pack_into("<I", data, 0x130, 0x4000)  # offset
        struct.pack_into("<I", data, 0x134, 0)  # size = 0

        file_handle = BytesIO(bytes(data))
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        # Only game partition should be present
        assert len(container.partitions) == 1
        assert container.partitions[0].partition_type == "game"

    def test_read_container_with_unknown_partition_types(self):
        """Test reading partitions beyond the first 3 (marked as unknown)."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # Skip first 3 partitions, add partition at index 3
        struct.pack_into("<I", data, 0x138, 0x1000)  # offset at partition 3
        struct.pack_into("<I", data, 0x13C, 0x500)  # size at partition 3

        file_handle = BytesIO(bytes(data))
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 1
        assert container.partitions[0].partition_type == "unknown"

    def test_read_container_with_all_eight_partitions(self):
        """Test reading all 8 possible partitions."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # Add all 8 partitions
        for i in range(8):
            base_offset = 0x120 + (i * 8)
            struct.pack_into("<I", data, base_offset, 0x1000 + (i * 0x100))  # offset
            struct.pack_into("<I", data, base_offset + 4, 0x100 + i)  # size

        file_handle = BytesIO(bytes(data))
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 8

        # Check partition types
        expected_types = [
            "game",
            "manual",
            "dlpchild",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
            "unknown",
        ]
        for i, partition in enumerate(container.partitions):
            assert partition.partition_type == expected_types[i]
            assert partition.offset == 0x1000 + (i * 0x100)
            assert partition.size == 0x100 + i

    def test_read_partitions_parses_correct_offsets(self):
        """Test that partition offsets are read correctly."""
        # Arrange
        partitions = [
            (0x1000, 0x2000, "game"),
            (0x8000, 0x400, "manual"),
        ]
        data = self._create_ncsd_with_partitions(partitions)
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert container.partitions[0].offset == 0x1000
        assert container.partitions[1].offset == 0x8000

    def test_read_partitions_parses_correct_sizes(self):
        """Test that partition sizes are read correctly."""
        # Arrange
        partitions = [
            (0x1000, 0x2000, "game"),
            (0x8000, 0x400, "manual"),
        ]
        data = self._create_ncsd_with_partitions(partitions)
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert container.partitions[0].size == 0x2000
        assert container.partitions[1].size == 0x400

    @pytest.mark.parametrize(
        "partition_data,expected_count",
        [
            ([], 0),
            ([(0x1000, 0x2000, "game")], 1),
            ([(0x1000, 0x2000, "game"), (0x3000, 0x400, "manual")], 2),
            (
                [
                    (0x1000, 0x2000, "game"),
                    (0x3000, 0x400, "manual"),
                    (0x3400, 0x200, "dlpchild"),
                ],
                3,
            ),
        ],
    )
    def test_read_container_with_various_partition_counts(self, partition_data, expected_count):
        """Test reading containers with different numbers of partitions."""
        # Arrange
        data = self._create_ncsd_with_partitions(partition_data)
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == expected_count

    def test_read_container_with_realistic_cci_structure(self):
        """Test reading a realistic CCI file structure."""
        # Arrange - simulate actual CCI file structure
        data = bytearray(0x8000)

        # NCSD header at 0x100
        data[0x100:0x104] = b"NCSD"
        title_id = bytes.fromhex("0004000000055D00")  # Example title ID
        data[0x108:0x110] = title_id

        # Typical game partition: starts at offset 0x4000 media units
        struct.pack_into("<I", data, 0x120, 0x4000)
        struct.pack_into("<I", data, 0x124, 0x2000)

        # Manual partition
        struct.pack_into("<I", data, 0x128, 0x6000)
        struct.pack_into("<I", data, 0x12C, 0x200)

        # DLP partition
        struct.pack_into("<I", data, 0x130, 0x6200)
        struct.pack_into("<I", data, 0x134, 0x100)

        file_handle = BytesIO(bytes(data))
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert container.magic == b"NCSD"
        assert container.title_id == title_id[::-1]
        assert len(container.partitions) == 3

        game = container.get_game_partition()
        assert game is not None
        assert game.offset == 0x4000
        assert game.size == 0x2000

    def test_read_container_integration_with_get_game_partition(self):
        """Test that read_container integrates with NCSDContainer methods."""
        # Arrange
        partitions = [(0x1000, 0x2000, "game"), (0x3000, 0x400, "manual")]
        data = self._create_ncsd_with_partitions(partitions)
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()
        game_partition = container.get_game_partition()

        # Assert
        assert game_partition is not None
        assert game_partition.offset == 0x1000
        assert game_partition.size == 0x2000

    def test_read_container_handles_large_partition_offsets(self):
        """Test reading partitions with large offset values."""
        # Arrange
        partitions = [(0xFFFF0000, 0x1000, "game")]
        data = self._create_ncsd_with_partitions(partitions)
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert container.partitions[0].offset == 0xFFFF0000

    def test_read_container_handles_large_partition_sizes(self):
        """Test reading partitions with large size values."""
        # Arrange
        partitions = [(0x1000, 0xFFFF0000, "game")]
        data = self._create_ncsd_with_partitions(partitions)
        file_handle = BytesIO(data)
        binary_reader = BinaryReader(file_handle)
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert container.partitions[0].size == 0xFFFF0000

    # Helper methods

    def _create_minimal_ncsd(self) -> bytes:
        """Create minimal valid NCSD data."""
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)  # Zero title ID
        return bytes(data)

    def _create_ncsd_with_title_id(self, title_id: bytes) -> bytes:
        """Create NCSD data with specific title ID."""
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = title_id
        return bytes(data)

    def _create_ncsd_with_partitions(self, partitions: list[tuple[int, int, str]]) -> bytes:
        """Create NCSD data with specific partitions.

        Args:
            partitions: List of (offset, size, type) tuples

        Returns:
            NCSD binary data
        """
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        partition_type_map = {"game": 0, "manual": 1, "dlpchild": 2, "unknown": 3}

        for offset, size, ptype in partitions:
            # Determine partition index from type
            if ptype in partition_type_map:
                idx = partition_type_map[ptype]
            else:
                idx = 3  # Default to unknown

            base_offset = 0x120 + (idx * 8)
            struct.pack_into("<I", data, base_offset, offset)
            struct.pack_into("<I", data, base_offset + 4, size)

        return bytes(data)
