"""Tests for NCSD container models."""

import struct

import pytest

from dsconv.models.ncsd import NCSDContainer, NCSDPartition


class TestNCSDPartition:
    """Tests for NCSDPartition model."""

    def test_create_with_valid_data(self):
        """Test creating partition with valid data."""
        # Arrange
        offset = 0x1000
        size = 0x2000
        partition_type = "game"

        # Act
        partition = NCSDPartition(offset=offset, size=size, partition_type=partition_type)

        # Assert
        assert partition.offset == offset
        assert partition.size == size
        assert partition.partition_type == partition_type

    def test_create_with_negative_offset_raises_error(self):
        """Test creating partition with negative offset raises ValueError."""
        with pytest.raises(ValueError, match="offset must be non-negative"):
            NCSDPartition(offset=-1, size=0x1000, partition_type="game")

    def test_create_with_negative_size_raises_error(self):
        """Test creating partition with negative size raises ValueError."""
        with pytest.raises(ValueError, match="size must be non-negative"):
            NCSDPartition(offset=0x1000, size=-1, partition_type="game")

    def test_create_with_invalid_type_raises_error(self):
        """Test creating partition with invalid type raises ValueError."""
        with pytest.raises(
            ValueError,
            match="partition_type must be 'game', 'manual', 'dlpchild', or 'unknown'",
        ):
            NCSDPartition(offset=0x1000, size=0x2000, partition_type="invalid")

    @pytest.mark.parametrize(
        "partition_type",
        ["game", "manual", "dlpchild", "unknown"],
    )
    def test_create_with_valid_types(self, partition_type):
        """Test creating partition with all valid types."""
        partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type=partition_type)
        assert partition.partition_type == partition_type

    def test_offset_bytes_property(self):
        """Test offset_bytes property."""
        partition = NCSDPartition(offset=0x10, size=0x20, partition_type="game")
        # 0x10 * 0x200 = 0x2000
        assert partition.offset_bytes == 0x2000

    def test_size_bytes_property(self):
        """Test size_bytes property."""
        partition = NCSDPartition(offset=0x10, size=0x20, partition_type="game")
        # 0x20 * 0x200 = 0x4000
        assert partition.size_bytes == 0x4000

    @pytest.mark.parametrize(
        "offset,expected_bytes",
        [
            (0, 0),
            (1, 0x200),
            (2, 0x400),
            (0x10, 0x2000),
            (0x100, 0x20000),
        ],
    )
    def test_offset_bytes_various_values(self, offset, expected_bytes):
        """Test offset_bytes with various offset values."""
        partition = NCSDPartition(offset=offset, size=0x1000, partition_type="game")
        assert partition.offset_bytes == expected_bytes

    @pytest.mark.parametrize(
        "size,expected_bytes",
        [
            (0, 0),
            (1, 0x200),
            (2, 0x400),
            (0x10, 0x2000),
            (0x100, 0x20000),
        ],
    )
    def test_size_bytes_various_values(self, size, expected_bytes):
        """Test size_bytes with various size values."""
        partition = NCSDPartition(offset=0x1000, size=size, partition_type="game")
        assert partition.size_bytes == expected_bytes


class TestNCSDContainer:
    """Tests for NCSDContainer model."""

    def test_create_with_valid_data(self):
        """Test creating container with valid data."""
        # Arrange
        magic = b"NCSD"
        title_id = b"\x00\x01\x02\x03\x04\x05\x06\x07"
        partitions = [
            NCSDPartition(offset=0x1000, size=0x2000, partition_type="game"),
            NCSDPartition(offset=0x3000, size=0x1000, partition_type="manual"),
        ]

        # Act
        container = NCSDContainer(magic=magic, title_id=title_id, partitions=partitions)

        # Assert
        assert container.magic == magic
        assert container.title_id == title_id
        assert container.partitions == partitions
        assert len(container.partitions) == 2

    def test_create_with_invalid_magic_raises_error(self):
        """Test creating container with invalid magic raises ValueError."""
        with pytest.raises(ValueError, match="Invalid NCSD magic"):
            NCSDContainer(
                magic=b"XXXX",
                title_id=bytes(8),
                partitions=[],
            )

    def test_create_with_wrong_magic_length_raises_error(self):
        """Test creating container with wrong magic length raises ValueError."""
        with pytest.raises(ValueError, match="magic must be 4 bytes"):
            NCSDContainer(
                magic=b"NCSDXX",
                title_id=bytes(8),
                partitions=[],
            )

    def test_create_with_wrong_title_id_length_raises_error(self):
        """Test creating container with wrong title ID length raises ValueError."""
        with pytest.raises(ValueError, match="title_id must be 8 bytes"):
            NCSDContainer(
                magic=b"NCSD",
                title_id=b"short",
                partitions=[],
            )

    def test_create_with_too_many_partitions_raises_error(self):
        """Test creating container with more than 8 partitions raises ValueError."""
        partitions = [
            NCSDPartition(offset=i * 0x1000, size=0x1000, partition_type="unknown")
            for i in range(9)
        ]
        with pytest.raises(ValueError, match="Cannot have more than 8 partitions"):
            NCSDContainer(
                magic=b"NCSD",
                title_id=bytes(8),
                partitions=partitions,
            )

    def test_create_with_empty_partitions(self):
        """Test creating container with no partitions."""
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[],
        )
        assert len(container.partitions) == 0

    def test_get_game_partition_success(self):
        """Test get_game_partition returns game partition."""
        # Arrange
        game_partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="game")
        manual_partition = NCSDPartition(offset=0x3000, size=0x1000, partition_type="manual")
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[game_partition, manual_partition],
        )

        # Act
        result = container.get_game_partition()

        # Assert
        assert result == game_partition

    def test_get_game_partition_when_missing(self):
        """Test get_game_partition returns None when no game partition."""
        # Arrange
        manual_partition = NCSDPartition(offset=0x3000, size=0x1000, partition_type="manual")
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[manual_partition],
        )

        # Act
        result = container.get_game_partition()

        # Assert
        assert result is None

    def test_get_partition_by_type_game(self):
        """Test get_partition_by_type for game partition."""
        # Arrange
        game_partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="game")
        manual_partition = NCSDPartition(offset=0x3000, size=0x1000, partition_type="manual")
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[game_partition, manual_partition],
        )

        # Act
        result = container.get_partition_by_type("game")

        # Assert
        assert result == game_partition

    def test_get_partition_by_type_manual(self):
        """Test get_partition_by_type for manual partition."""
        # Arrange
        game_partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="game")
        manual_partition = NCSDPartition(offset=0x3000, size=0x1000, partition_type="manual")
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[game_partition, manual_partition],
        )

        # Act
        result = container.get_partition_by_type("manual")

        # Assert
        assert result == manual_partition

    def test_get_partition_by_type_dlpchild(self):
        """Test get_partition_by_type for dlpchild partition."""
        # Arrange
        dlp_partition = NCSDPartition(offset=0x5000, size=0x500, partition_type="dlpchild")
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[dlp_partition],
        )

        # Act
        result = container.get_partition_by_type("dlpchild")

        # Assert
        assert result == dlp_partition

    def test_get_partition_by_type_when_missing(self):
        """Test get_partition_by_type returns None when type not found."""
        # Arrange
        game_partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="game")
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[game_partition],
        )

        # Act
        result = container.get_partition_by_type("manual")

        # Assert
        assert result is None

    def test_get_all_partitions_by_type_single(self):
        """Test get_all_partitions_by_type with single matching partition."""
        # Arrange
        game_partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="game")
        manual_partition = NCSDPartition(offset=0x3000, size=0x1000, partition_type="manual")
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[game_partition, manual_partition],
        )

        # Act
        result = container.get_all_partitions_by_type("game")

        # Assert
        assert result == [game_partition]

    def test_get_all_partitions_by_type_multiple(self):
        """Test get_all_partitions_by_type with multiple matching partitions."""
        # Arrange
        unknown1 = NCSDPartition(offset=0x1000, size=0x1000, partition_type="unknown")
        unknown2 = NCSDPartition(offset=0x2000, size=0x1000, partition_type="unknown")
        game_partition = NCSDPartition(offset=0x3000, size=0x2000, partition_type="game")
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[unknown1, unknown2, game_partition],
        )

        # Act
        result = container.get_all_partitions_by_type("unknown")

        # Assert
        assert result == [unknown1, unknown2]

    def test_get_all_partitions_by_type_none(self):
        """Test get_all_partitions_by_type returns empty list when none found."""
        # Arrange
        game_partition = NCSDPartition(offset=0x1000, size=0x2000, partition_type="game")
        container = NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[game_partition],
        )

        # Act
        result = container.get_all_partitions_by_type("manual")

        # Assert
        assert result == []

    def test_from_bytes_with_valid_data(self):
        """Test creating container from binary data."""
        # Arrange - create minimal valid NCSD header
        data = bytearray(0x160)

        # Magic at 0x100
        data[0x100:0x104] = b"NCSD"

        # Title ID at 0x108 (reversed in file)
        title_id_reversed = b"\x07\x06\x05\x04\x03\x02\x01\x00"
        data[0x108:0x110] = title_id_reversed

        # Partition table at 0x120
        # Partition 0 (game): offset=0x1000, size=0x2000
        data[0x120:0x124] = struct.pack("<I", 0x1000)
        data[0x124:0x128] = struct.pack("<I", 0x2000)

        # Partition 1 (manual): offset=0x3000, size=0x1000
        data[0x128:0x12C] = struct.pack("<I", 0x3000)
        data[0x12C:0x130] = struct.pack("<I", 0x1000)

        # Partition 2 (dlpchild): offset=0x4000, size=0x500
        data[0x130:0x134] = struct.pack("<I", 0x4000)
        data[0x134:0x138] = struct.pack("<I", 0x500)

        # Act
        container = NCSDContainer.from_bytes(bytes(data))

        # Assert
        assert container.magic == b"NCSD"
        # Title ID should be reversed
        assert container.title_id == b"\x00\x01\x02\x03\x04\x05\x06\x07"
        assert len(container.partitions) == 3

        # Check game partition
        game = container.partitions[0]
        assert game.offset == 0x1000
        assert game.size == 0x2000
        assert game.partition_type == "game"

        # Check manual partition
        manual = container.partitions[1]
        assert manual.offset == 0x3000
        assert manual.size == 0x1000
        assert manual.partition_type == "manual"

        # Check dlpchild partition
        dlp = container.partitions[2]
        assert dlp.offset == 0x4000
        assert dlp.size == 0x500
        assert dlp.partition_type == "dlpchild"

    def test_from_bytes_skips_zero_size_partitions(self):
        """Test from_bytes skips partitions with zero size."""
        # Arrange - create NCSD header with some empty partitions
        data = bytearray(0x160)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # Only partition 0 has non-zero size
        data[0x120:0x124] = struct.pack("<I", 0x1000)
        data[0x124:0x128] = struct.pack("<I", 0x2000)

        # Partitions 1-7 have zero size (already zero-filled)

        # Act
        container = NCSDContainer.from_bytes(bytes(data))

        # Assert
        assert len(container.partitions) == 1
        assert container.partitions[0].partition_type == "game"

    def test_from_bytes_with_all_eight_partitions(self):
        """Test from_bytes with all 8 partitions populated."""
        # Arrange
        data = bytearray(0x160)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes(8)

        # Add all 8 partitions
        for i in range(8):
            offset_pos = 0x120 + (i * 8)
            data[offset_pos : offset_pos + 4] = struct.pack("<I", (i + 1) * 0x1000)
            data[offset_pos + 4 : offset_pos + 8] = struct.pack("<I", 0x100)

        # Act
        container = NCSDContainer.from_bytes(bytes(data))

        # Assert
        assert len(container.partitions) == 8
        assert container.partitions[0].partition_type == "game"
        assert container.partitions[1].partition_type == "manual"
        assert container.partitions[2].partition_type == "dlpchild"
        for i in range(3, 8):
            assert container.partitions[i].partition_type == "unknown"

    def test_from_bytes_with_short_data_raises_error(self):
        """Test from_bytes with insufficient data raises ValueError."""
        data = bytes(0x100)  # Too short
        with pytest.raises(ValueError, match="Data too short for NCSD header"):
            NCSDContainer.from_bytes(data)

    def test_from_bytes_roundtrip(self):
        """Test from_bytes can parse data that represents a valid structure."""
        # Arrange - create valid NCSD data
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = b"\xff\xee\xdd\xcc\xbb\xaa\x99\x88"
        data[0x120:0x124] = struct.pack("<I", 0x8000)
        data[0x124:0x128] = struct.pack("<I", 0x10000)

        # Act
        container = NCSDContainer.from_bytes(bytes(data))

        # Assert - verify parsed correctly
        assert container.magic == b"NCSD"
        assert container.title_id == b"\x88\x99\xaa\xbb\xcc\xdd\xee\xff"
        assert len(container.partitions) == 1
        assert container.partitions[0].offset == 0x8000
        assert container.partitions[0].size == 0x10000
        assert container.partitions[0].partition_type == "game"

        # Verify we can use the container methods
        game = container.get_game_partition()
        assert game is not None
        assert game.offset == 0x8000
