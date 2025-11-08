"""Tests for BinaryReader utility."""

import struct
from io import BytesIO

import pytest

from dsconv.io.binary_reader import BinaryReader


class TestBinaryReader:
    """Tests for BinaryReader class."""

    @pytest.fixture
    def sample_data(self):
        """Create sample binary data for testing."""
        data = BytesIO()
        # Write some test data
        data.write(b"NCSD")  # 0x00-0x03: Magic
        data.write(struct.pack("<I", 0x1000))  # 0x04-0x07: Size
        data.write(b"\x00" * 8)  # 0x08-0x0F: Padding
        data.write(b"NCCH")  # 0x10-0x13: Second magic
        data.write(struct.pack("<HH", 0x0102, 0x0304))  # 0x14-0x17: Two shorts
        data.write(b"\xff" * 100)  # 0x18-0x7B: Fill data
        data.seek(0)
        return data

    @pytest.fixture
    def reader(self, sample_data):
        """Create BinaryReader with sample data."""
        return BinaryReader(sample_data)

    def test_create_with_file_handle(self, sample_data):
        """Test creating reader with file handle succeeds."""
        reader = BinaryReader(sample_data)
        assert reader.file is sample_data

    def test_read_at_reads_correct_bytes(self, reader):
        """Test read_at reads bytes from correct offset."""
        # Read magic at offset 0
        magic = reader.read_at(0, 4)
        assert magic == b"NCSD"

        # Read second magic at offset 0x10
        magic2 = reader.read_at(0x10, 4)
        assert magic2 == b"NCCH"

    def test_read_at_with_different_lengths(self, reader):
        """Test read_at with various lengths."""
        # Read 1 byte
        byte1 = reader.read_at(0, 1)
        assert len(byte1) == 1
        assert byte1 == b"N"

        # Read 4 bytes
        bytes4 = reader.read_at(0, 4)
        assert len(bytes4) == 4
        assert bytes4 == b"NCSD"

        # Read 8 bytes
        bytes8 = reader.read_at(0x08, 8)
        assert len(bytes8) == 8
        assert bytes8 == b"\x00" * 8

    def test_read_at_updates_position(self, reader):
        """Test that read_at updates file position."""
        reader.read_at(0x10, 4)
        # Position should be at 0x14 after reading 4 bytes from 0x10
        assert reader.tell() == 0x14

    def test_read_at_can_read_from_different_offsets_sequentially(self, reader):
        """Test reading from different offsets in sequence."""
        # Read from offset 0
        data1 = reader.read_at(0, 4)
        assert data1 == b"NCSD"

        # Read from offset 0x10
        data2 = reader.read_at(0x10, 4)
        assert data2 == b"NCCH"

        # Read from offset 4
        data3 = reader.read_at(4, 4)
        assert data3 == struct.pack("<I", 0x1000)

    def test_read_struct_unpacks_single_value(self, reader):
        """Test read_struct with single value format."""
        # Read uint32 at offset 4
        result = reader.read_struct(4, "<I")
        assert isinstance(result, tuple)
        assert len(result) == 1
        assert result[0] == 0x1000

    def test_read_struct_unpacks_multiple_values(self, reader):
        """Test read_struct with multiple values."""
        # Read magic (4 bytes) and size (4 bytes)
        magic, size = reader.read_struct(0, "<4sI")
        assert magic == b"NCSD"
        assert size == 0x1000

    def test_read_struct_with_different_formats(self, reader):
        """Test read_struct with various format strings."""
        # Read two shorts at offset 0x14
        short1, short2 = reader.read_struct(0x14, "<HH")
        assert short1 == 0x0102
        assert short2 == 0x0304

        # Read as single uint32
        uint32 = reader.read_struct(0x14, "<I")[0]
        assert uint32 == 0x03040102  # Little-endian

    def test_read_struct_calculates_size_correctly(self, reader):
        """Test that read_struct calculates correct size from format."""
        # Format '<4sI' should be 8 bytes (4 + 4)
        magic, size = reader.read_struct(0, "<4sI")
        assert magic == b"NCSD"
        assert size == 0x1000

        # Format '<HH' should be 4 bytes (2 + 2)
        s1, s2 = reader.read_struct(0x14, "<HH")
        assert s1 == 0x0102
        assert s2 == 0x0304

    def test_read_struct_raises_on_invalid_format(self, reader):
        """Test read_struct raises error on invalid format string."""
        with pytest.raises(struct.error):
            reader.read_struct(0, "<INVALID")

    def test_tell_returns_current_position(self, reader):
        """Test tell() returns current file position."""
        # Initial position
        assert reader.tell() == 0

        # After reading
        reader.read_at(0x10, 4)
        assert reader.tell() == 0x14

        # After seeking
        reader.seek(0x20)
        assert reader.tell() == 0x20

    def test_seek_from_start(self, reader):
        """Test seek with whence=0 (from start)."""
        pos = reader.seek(0x10, 0)
        assert pos == 0x10
        assert reader.tell() == 0x10

    def test_seek_from_current(self, reader):
        """Test seek with whence=1 (from current)."""
        reader.seek(0x10)
        pos = reader.seek(4, 1)  # Move forward 4 bytes
        assert pos == 0x14
        assert reader.tell() == 0x14

    def test_seek_from_end(self, sample_data):
        """Test seek with whence=2 (from end)."""
        reader = BinaryReader(sample_data)
        # Seek to 10 bytes before end
        sample_data.seek(0, 2)  # Go to end to find size
        size = sample_data.tell()
        sample_data.seek(0)  # Reset

        reader.seek(-10, 2)
        assert reader.tell() == size - 10

    def test_multiple_reads_maintain_position(self, reader):
        """Test that multiple read operations maintain position correctly."""
        # Read 4 bytes from offset 0
        reader.read_at(0, 4)
        assert reader.tell() == 4

        # Read 4 more bytes (continuing from current position would be offset 4)
        # But read_at seeks first
        reader.read_at(4, 4)
        assert reader.tell() == 8

    def test_read_at_with_zero_length(self, reader):
        """Test reading zero bytes."""
        data = reader.read_at(0, 0)
        assert data == b""
        assert len(data) == 0

    def test_read_struct_big_endian(self, reader):
        """Test read_struct with big-endian format."""
        # Write big-endian data
        data = BytesIO()
        data.write(struct.pack(">I", 0x12345678))
        data.seek(0)
        reader = BinaryReader(data)

        result = reader.read_struct(0, ">I")[0]
        assert result == 0x12345678

    def test_read_at_beyond_file_size(self, reader):
        """Test reading beyond file size returns partial data."""
        # Try to read 1000 bytes from near the end
        data = reader.read_at(100, 1000)
        # Should return less than 1000 bytes
        assert len(data) < 1000

    @pytest.mark.parametrize(
        "offset,length,expected",
        [
            (0, 4, b"NCSD"),
            (0x10, 4, b"NCCH"),
            (4, 4, struct.pack("<I", 0x1000)),
            (0x08, 8, b"\x00" * 8),
        ],
    )
    def test_read_at_parametrized(self, reader, offset, length, expected):
        """Test read_at with various offset/length combinations."""
        result = reader.read_at(offset, length)
        assert result == expected

    def test_works_with_real_file_like_objects(self, tmp_path):
        """Test that reader works with actual file objects."""
        # Create a temporary file
        test_file = tmp_path / "test.bin"
        with open(test_file, "wb") as f:
            f.write(b"TEST")
            f.write(struct.pack("<I", 0xDEADBEEF))

        # Read it with BinaryReader
        with open(test_file, "rb") as f:
            reader = BinaryReader(f)
            magic = reader.read_at(0, 4)
            value = reader.read_struct(4, "<I")[0]

        assert magic == b"TEST"
        assert value == 0xDEADBEEF

    def test_reader_with_empty_file(self):
        """Test reader with empty file."""
        empty = BytesIO(b"")
        reader = BinaryReader(empty)

        # Reading from empty file should return empty bytes
        data = reader.read_at(0, 10)
        assert data == b""

    def test_sequential_reads_without_seeking(self, sample_data):
        """Test reading sequentially without explicit seeking."""
        reader = BinaryReader(sample_data)

        # Position starts at 0
        assert reader.tell() == 0

        # Read 4 bytes (read_at seeks to 0 first)
        data1 = reader.read_at(0, 4)
        assert data1 == b"NCSD"
        assert reader.tell() == 4

        # Continue from current position by using tell()
        current = reader.tell()
        data2 = reader.read_at(current, 4)
        assert data2 == struct.pack("<I", 0x1000)
        assert reader.tell() == 8
