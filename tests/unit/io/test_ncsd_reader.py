"""Tests for NCSDReader class."""

import struct
from io import BytesIO

import pytest

from dsconv.io.binary_reader import BinaryReader
from dsconv.io.ncsd_reader import NCSDReader
from dsconv.models.ncsd import NCSDContainer


class TestNCSDReader:
    """Tests for NCSDReader."""

    @pytest.fixture
    def minimal_ncsd_data(self):
        """Create minimal valid NCSD data for testing.

        Creates a BytesIO object containing a minimal but valid NCSD header with:
        - Magic bytes at 0x100
        - Title ID at 0x108
        - Partition table at 0x120
        """
        data = bytearray(0x1000)  # Large enough buffer

        # NCSD magic at 0x100
        data[0x100:0x104] = b"NCSD"

        # Title ID at 0x108 (8 bytes, will be reversed when read)
        data[0x108:0x110] = bytes([0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77])

        # Partition table at 0x120
        # Partition 0 (game): offset=0x1000, size=0x2000
        struct.pack_into("<II", data, 0x120, 0x1000, 0x2000)

        # Partition 1 (manual): offset=0x3000, size=0x400
        struct.pack_into("<II", data, 0x128, 0x3000, 0x400)

        # Partition 2 (dlpchild): offset=0x3400, size=0x200
        struct.pack_into("<II", data, 0x130, 0x3400, 0x200)

        # Remaining partitions are empty (size=0)
        for i in range(3, 8):
            struct.pack_into("<II", data, 0x120 + (i * 8), 0, 0)

        return BytesIO(bytes(data))

    @pytest.fixture
    def ncsd_reader(self, minimal_ncsd_data):
        """Create NCSDReader with minimal NCSD data."""
        binary_reader = BinaryReader(minimal_ncsd_data)
        return NCSDReader(binary_reader)

    def test_init_with_binary_reader(self):
        """Test creating NCSDReader with a BinaryReader."""
        # Arrange
        data = BytesIO(b"test data")
        binary_reader = BinaryReader(data)

        # Act
        reader = NCSDReader(binary_reader)

        # Assert
        assert reader.reader is binary_reader

    def test_read_container_returns_ncsd_container(self, ncsd_reader):
        """Test read_container returns NCSDContainer object."""
        # Act
        container = ncsd_reader.read_container()

        # Assert
        assert isinstance(container, NCSDContainer)

    def test_read_container_parses_magic_bytes(self, ncsd_reader):
        """Test read_container correctly reads NCSD magic bytes."""
        # Act
        container = ncsd_reader.read_container()

        # Assert
        assert container.magic == b"NCSD"

    def test_read_container_parses_title_id(self, ncsd_reader):
        """Test read_container correctly reads and reverses title ID."""
        # Act
        container = ncsd_reader.read_container()

        # Assert
        # Title ID should be reversed from what was written
        expected_title_id = bytes([0x77, 0x66, 0x55, 0x44, 0x33, 0x22, 0x11, 0x00])
        assert container.title_id == expected_title_id

    def test_read_container_parses_partitions(self, ncsd_reader):
        """Test read_container correctly reads partition table."""
        # Act
        container = ncsd_reader.read_container()

        # Assert
        assert len(container.partitions) == 3  # Only non-zero size partitions

    def test_read_container_partition_types(self, ncsd_reader):
        """Test read_container assigns correct partition types."""
        # Act
        container = ncsd_reader.read_container()

        # Assert
        assert container.partitions[0].partition_type == "game"
        assert container.partitions[1].partition_type == "manual"
        assert container.partitions[2].partition_type == "dlpchild"

    def test_read_container_partition_offsets(self, ncsd_reader):
        """Test read_container reads correct partition offsets."""
        # Act
        container = ncsd_reader.read_container()

        # Assert
        assert container.partitions[0].offset == 0x1000
        assert container.partitions[1].offset == 0x3000
        assert container.partitions[2].offset == 0x3400

    def test_read_container_partition_sizes(self, ncsd_reader):
        """Test read_container reads correct partition sizes."""
        # Act
        container = ncsd_reader.read_container()

        # Assert
        assert container.partitions[0].size == 0x2000
        assert container.partitions[1].size == 0x400
        assert container.partitions[2].size == 0x200

    def test_read_container_with_invalid_magic_raises_error(self):
        """Test read_container raises ValueError for invalid NCSD magic."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"XXXX"  # Invalid magic
        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCSD magic"):
            reader.read_container()

    def test_read_container_with_all_empty_partitions(self):
        """Test read_container with all partitions having zero size."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)  # Title ID

        # All partitions have size 0
        for i in range(8):
            struct.pack_into("<II", data, 0x120 + (i * 8), 0, 0)

        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 0

    def test_read_container_with_only_game_partition(self):
        """Test read_container with only the game partition present."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # Only partition 0 (game) has non-zero size
        struct.pack_into("<II", data, 0x120, 0x1000, 0x5000)

        # Rest are empty
        for i in range(1, 8):
            struct.pack_into("<II", data, 0x120 + (i * 8), 0, 0)

        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 1
        assert container.partitions[0].partition_type == "game"
        assert container.partitions[0].offset == 0x1000
        assert container.partitions[0].size == 0x5000

    def test_read_container_with_all_8_partitions(self):
        """Test read_container with all 8 partitions having non-zero size."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # All 8 partitions have non-zero size
        for i in range(8):
            offset = 0x1000 + (i * 0x100)
            size = 0x100
            struct.pack_into("<II", data, 0x120 + (i * 8), offset, size)

        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 8
        # Check partition types
        assert container.partitions[0].partition_type == "game"
        assert container.partitions[1].partition_type == "manual"
        assert container.partitions[2].partition_type == "dlpchild"
        for i in range(3, 8):
            assert container.partitions[i].partition_type == "unknown"

    def test_read_partitions_skips_zero_size_partitions(self):
        """Test _read_partitions skips partitions with zero size."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # Partition 0: non-zero size
        struct.pack_into("<II", data, 0x120, 0x1000, 0x2000)
        # Partition 1: zero size
        struct.pack_into("<II", data, 0x128, 0x3000, 0)
        # Partition 2: non-zero size
        struct.pack_into("<II", data, 0x130, 0x3400, 0x200)
        # Rest: zero size
        for i in range(3, 8):
            struct.pack_into("<II", data, 0x120 + (i * 8), 0, 0)

        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 2
        assert container.partitions[0].partition_type == "game"
        assert container.partitions[1].partition_type == "dlpchild"

    @pytest.mark.parametrize(
        "magic,expected_error",
        [
            (b"XXXX", "Invalid NCSD magic"),
            (b"ncsd", "Invalid NCSD magic"),
            (b"NCS", "Invalid NCSD magic"),
            (b"NCCH", "Invalid NCSD magic"),
            (b"\x00\x00\x00\x00", "Invalid NCSD magic"),
        ],
    )
    def test_read_container_with_various_invalid_magic(self, magic, expected_error):
        """Test read_container with various invalid magic bytes."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = magic
        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act & Assert
        with pytest.raises(ValueError, match=expected_error):
            reader.read_container()

    def test_read_container_preserves_title_id_byte_order(self):
        """Test that title ID is correctly reversed from file format."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"

        # Write title ID in file format (will be reversed)
        file_title_id = bytes([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
        data[0x108:0x110] = file_title_id

        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        # Should be reversed
        expected = bytes([0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01])
        assert container.title_id == expected

    def test_read_container_with_large_partition_values(self):
        """Test read_container with maximum valid partition values."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # Use large values (but within uint32 range)
        struct.pack_into("<II", data, 0x120, 0xFFFF0000, 0xFFFF0000)

        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 1
        assert container.partitions[0].offset == 0xFFFF0000
        assert container.partitions[0].size == 0xFFFF0000

    def test_read_container_can_be_called_multiple_times(self, minimal_ncsd_data):
        """Test that read_container can be called multiple times."""
        # Arrange
        binary_reader = BinaryReader(minimal_ncsd_data)
        reader = NCSDReader(binary_reader)

        # Act
        container1 = reader.read_container()
        # Reset file position
        minimal_ncsd_data.seek(0)
        container2 = reader.read_container()

        # Assert
        assert container1.magic == container2.magic
        assert container1.title_id == container2.title_id
        assert len(container1.partitions) == len(container2.partitions)

    def test_read_container_integration_with_ncsd_container_model(self, ncsd_reader):
        """Test that read_container returns a valid NCSDContainer that can use its methods."""
        # Act
        container = ncsd_reader.read_container()

        # Assert - Test NCSDContainer methods work
        game_partition = container.get_game_partition()
        assert game_partition is not None
        assert game_partition.partition_type == "game"
        assert game_partition.offset == 0x1000
        assert game_partition.size == 0x2000

    def test_read_container_with_minimal_file_size(self):
        """Test read_container with exactly the minimum required data."""
        # Arrange - exactly 0x160 bytes (minimum for NCSD header)
        data = bytearray(0x160)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)
        struct.pack_into("<II", data, 0x120, 0x100, 0x200)

        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert container.magic == b"NCSD"
        assert len(container.partitions) == 1

    def test_read_container_partition_order_preserved(self):
        """Test that partitions are returned in the correct order."""
        # Arrange
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # Add partitions in specific order
        struct.pack_into("<II", data, 0x120, 0x1000, 0x100)  # Partition 0: game
        struct.pack_into("<II", data, 0x128, 0x2000, 0x200)  # Partition 1: manual
        struct.pack_into("<II", data, 0x130, 0x3000, 0x300)  # Partition 2: dlpchild
        struct.pack_into("<II", data, 0x138, 0x4000, 0x400)  # Partition 3: unknown

        binary_reader = BinaryReader(BytesIO(bytes(data)))
        reader = NCSDReader(binary_reader)

        # Act
        container = reader.read_container()

        # Assert
        assert len(container.partitions) == 4
        assert container.partitions[0].offset == 0x1000
        assert container.partitions[1].offset == 0x2000
        assert container.partitions[2].offset == 0x3000
        assert container.partitions[3].offset == 0x4000
