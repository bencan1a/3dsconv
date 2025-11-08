"""Tests for BinaryReader class."""

import struct
from io import BytesIO

import pytest

from dsconv.io.binary_reader import BinaryReader


class TestBinaryReader:
    """Tests for BinaryReader utility class."""

    def test_init_with_file_handle(self):
        """Test creating BinaryReader with a file handle."""
        # Arrange
        data = BytesIO(b"test data")

        # Act
        reader = BinaryReader(data)

        # Assert
        assert reader.file is data

    def test_read_at_basic(self):
        """Test reading bytes at specific offset."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(offset=5, length=3)

        # Assert
        assert result == b"567"

    def test_read_at_from_beginning(self):
        """Test reading from offset 0."""
        # Arrange
        data = BytesIO(b"HELLO WORLD")
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(offset=0, length=5)

        # Assert
        assert result == b"HELLO"

    def test_read_at_updates_position(self):
        """Test that read_at updates file position."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)

        # Act
        reader.read_at(offset=3, length=4)

        # Assert
        assert reader.tell() == 7  # 3 + 4

    def test_read_at_multiple_sequential_reads(self):
        """Test multiple sequential read_at operations."""
        # Arrange
        data = BytesIO(b"ABCDEFGHIJ")
        reader = BinaryReader(data)

        # Act
        first = reader.read_at(offset=0, length=3)
        second = reader.read_at(offset=5, length=3)
        third = reader.read_at(offset=8, length=2)

        # Assert
        assert first == b"ABC"
        assert second == b"FGH"
        assert third == b"IJ"

    def test_read_at_with_negative_offset_raises_error(self):
        """Test that negative offset raises ValueError."""
        # Arrange
        data = BytesIO(b"test")
        reader = BinaryReader(data)

        # Act & Assert
        with pytest.raises(ValueError, match="offset must be non-negative"):
            reader.read_at(offset=-1, length=4)

    def test_read_at_with_negative_length_raises_error(self):
        """Test that negative length raises ValueError."""
        # Arrange
        data = BytesIO(b"test")
        reader = BinaryReader(data)

        # Act & Assert
        with pytest.raises(ValueError, match="length must be non-negative"):
            reader.read_at(offset=0, length=-1)

    def test_read_at_beyond_end_of_file(self):
        """Test reading beyond end of file returns partial data."""
        # Arrange
        data = BytesIO(b"short")
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(offset=3, length=10)

        # Assert
        assert result == b"rt"  # Only 2 bytes available

    def test_read_at_at_end_of_file(self):
        """Test reading at exact end of file returns empty bytes."""
        # Arrange
        data = BytesIO(b"test")
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(offset=4, length=5)

        # Assert
        assert result == b""

    def test_read_struct_single_value(self):
        """Test reading and unpacking a single value."""
        # Arrange
        data = BytesIO(struct.pack("<I", 0x12345678))
        reader = BinaryReader(data)

        # Act
        result = reader.read_struct(offset=0, format_str="<I")

        # Assert
        assert result == (0x12345678,)

    def test_read_struct_multiple_values(self):
        """Test reading and unpacking multiple values."""
        # Arrange
        data = BytesIO(struct.pack("<IHH", 0x1000, 0x20, 0x30))
        reader = BinaryReader(data)

        # Act
        result = reader.read_struct(offset=0, format_str="<IHH")

        # Assert
        assert result == (0x1000, 0x20, 0x30)

    def test_read_struct_with_offset(self):
        """Test reading struct at non-zero offset."""
        # Arrange
        data = BytesIO(b"\x00" * 10 + struct.pack("<I", 0xDEADBEEF))
        reader = BinaryReader(data)

        # Act
        result = reader.read_struct(offset=10, format_str="<I")

        # Assert
        assert result == (0xDEADBEEF,)

    def test_read_struct_bytes_and_int(self):
        """Test reading struct with mixed types."""
        # Arrange
        data = BytesIO(b"NCCH" + struct.pack("<I", 0x1000))
        reader = BinaryReader(data)

        # Act
        result = reader.read_struct(offset=0, format_str="<4sI")

        # Assert
        assert result == (b"NCCH", 0x1000)

    def test_read_struct_big_endian(self):
        """Test reading struct with big-endian format."""
        # Arrange
        data = BytesIO(struct.pack(">Q", 0x0011223344556677))
        reader = BinaryReader(data)

        # Act
        result = reader.read_struct(offset=0, format_str=">Q")

        # Assert
        assert result == (0x0011223344556677,)

    def test_read_struct_with_negative_offset_raises_error(self):
        """Test that negative offset raises ValueError."""
        # Arrange
        data = BytesIO(b"\x00" * 10)
        reader = BinaryReader(data)

        # Act & Assert
        with pytest.raises(ValueError, match="offset must be non-negative"):
            reader.read_struct(offset=-1, format_str="<I")

    def test_read_struct_with_invalid_format_raises_error(self):
        """Test that invalid format string raises struct.error."""
        # Arrange
        data = BytesIO(b"\x00" * 10)
        reader = BinaryReader(data)

        # Act & Assert
        with pytest.raises(struct.error):
            reader.read_struct(offset=0, format_str="<INVALID")

    def test_read_struct_insufficient_data_raises_error(self):
        """Test that insufficient data raises struct.error."""
        # Arrange
        data = BytesIO(b"\x00\x01")  # Only 2 bytes
        reader = BinaryReader(data)

        # Act & Assert
        with pytest.raises(struct.error):
            reader.read_struct(offset=0, format_str="<I")  # Needs 4 bytes

    def test_tell_returns_current_position(self):
        """Test that tell returns current file position."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)

        # Act
        reader.read_at(offset=5, length=3)
        position = reader.tell()

        # Assert
        assert position == 8

    def test_tell_initial_position(self):
        """Test that initial position is 0."""
        # Arrange
        data = BytesIO(b"test")
        reader = BinaryReader(data)

        # Act
        position = reader.tell()

        # Assert
        assert position == 0

    def test_seek_absolute_positioning(self):
        """Test seeking with absolute positioning (whence=0)."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)

        # Act
        new_pos = reader.seek(5, 0)

        # Assert
        assert new_pos == 5
        assert reader.tell() == 5

    def test_seek_relative_to_current(self):
        """Test seeking relative to current position (whence=1)."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)
        reader.seek(3)

        # Act
        new_pos = reader.seek(2, 1)

        # Assert
        assert new_pos == 5
        assert reader.tell() == 5

    def test_seek_relative_to_end(self):
        """Test seeking relative to end of file (whence=2)."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)

        # Act
        new_pos = reader.seek(-3, 2)

        # Assert
        assert new_pos == 7
        assert reader.tell() == 7

    def test_seek_default_whence_is_absolute(self):
        """Test that default whence is 0 (absolute)."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)

        # Act
        new_pos = reader.seek(5)

        # Assert
        assert new_pos == 5

    def test_read_without_size_reads_all(self):
        """Test that read without size reads to end of file."""
        # Arrange
        data = BytesIO(b"Hello World")
        reader = BinaryReader(data)
        reader.seek(6)

        # Act
        result = reader.read()

        # Assert
        assert result == b"World"

    def test_read_with_size(self):
        """Test reading specific number of bytes from current position."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)
        reader.seek(3)

        # Act
        result = reader.read(4)

        # Assert
        assert result == b"3456"

    def test_read_updates_position(self):
        """Test that read updates file position."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)

        # Act
        reader.read(5)

        # Assert
        assert reader.tell() == 5

    def test_read_zero_bytes(self):
        """Test reading zero bytes."""
        # Arrange
        data = BytesIO(b"test")
        reader = BinaryReader(data)

        # Act
        result = reader.read(0)

        # Assert
        assert result == b""

    @pytest.mark.parametrize(
        "test_data,offset,length,expected",
        [
            (b"ABCDEFGH", 0, 4, b"ABCD"),
            (b"ABCDEFGH", 2, 3, b"CDE"),
            (b"ABCDEFGH", 4, 4, b"EFGH"),
            (b"ABCDEFGH", 7, 1, b"H"),
            (b"ABCDEFGH", 0, 8, b"ABCDEFGH"),
        ],
    )
    def test_read_at_various_offsets_and_lengths(self, test_data, offset, length, expected):
        """Test read_at with various offset and length combinations."""
        # Arrange
        data = BytesIO(test_data)
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(offset, length)

        # Assert
        assert result == expected

    @pytest.mark.parametrize(
        "format_str,packed_value,expected",
        [
            ("<B", struct.pack("<B", 0xFF), (0xFF,)),
            ("<H", struct.pack("<H", 0xABCD), (0xABCD,)),
            ("<I", struct.pack("<I", 0x12345678), (0x12345678,)),
            ("<Q", struct.pack("<Q", 0x0011223344556677), (0x0011223344556677,)),
            (">I", struct.pack(">I", 0x12345678), (0x12345678,)),
        ],
    )
    def test_read_struct_various_formats(self, format_str, packed_value, expected):
        """Test read_struct with various format strings."""
        # Arrange
        data = BytesIO(packed_value)
        reader = BinaryReader(data)

        # Act
        result = reader.read_struct(0, format_str)

        # Assert
        assert result == expected

    def test_integration_reading_ncch_like_structure(self):
        """Test reading a structure similar to NCCH header."""
        # Arrange - simulate minimal NCCH structure
        ncch_data = BytesIO()
        ncch_data.write(b"\x00" * 0x100)  # Signature
        ncch_data.write(b"NCCH")  # Magic at 0x100
        ncch_data.write(struct.pack("<I", 0x1000))  # Content size at 0x104
        ncch_data.write(b"\x00" * 8)  # Partition ID at 0x108
        ncch_data.seek(0)

        reader = BinaryReader(ncch_data)

        # Act - read magic and content size
        magic = reader.read_at(0x100, 4)
        (content_size,) = reader.read_struct(0x104, "<I")
        partition_id = reader.read_at(0x108, 8)

        # Assert
        assert magic == b"NCCH"
        assert content_size == 0x1000
        assert partition_id == b"\x00" * 8

    def test_integration_reading_ncsd_like_structure(self):
        """Test reading a structure similar to NCSD header."""
        # Arrange - simulate minimal NCSD structure
        ncsd_data = BytesIO()
        ncsd_data.write(b"\x00" * 0x100)  # Skip to magic
        ncsd_data.write(b"NCSD")  # Magic at 0x100
        ncsd_data.write(struct.pack("<I", 0x2000))  # Size at 0x104
        ncsd_data.write(bytes(8))  # Title ID at 0x108
        ncsd_data.seek(0)

        reader = BinaryReader(ncsd_data)

        # Act
        magic = reader.read_at(0x100, 4)
        (size,) = reader.read_struct(0x104, "<I")
        title_id = reader.read_at(0x108, 8)

        # Assert
        assert magic == b"NCSD"
        assert size == 0x2000
        assert title_id == bytes(8)

    def test_chained_operations(self):
        """Test that multiple operations can be chained correctly."""
        # Arrange
        data = BytesIO(b"0123456789ABCDEF")
        reader = BinaryReader(data)

        # Act - perform various operations
        first = reader.read_at(0, 4)
        reader.seek(10)
        second = reader.read(4)
        pos = reader.tell()
        # read_struct reads at offset 2, which is "23"
        (third,) = reader.read_struct(2, "<H")

        # Assert
        assert first == b"0123"
        assert second == b"ABCD"
        assert pos == 14
        # At offset 2, we have "23" which unpacks as little-endian short
        assert third == struct.unpack("<H", b"23")[0]

    def test_with_real_file_like_object(self, tmp_path):
        """Test BinaryReader with actual file on disk."""
        # Arrange
        test_file = tmp_path / "test.bin"
        test_data = b"TEST" + struct.pack("<I", 0x12345678) + b"END"
        test_file.write_bytes(test_data)

        # Act
        with open(test_file, "rb") as f:
            reader = BinaryReader(f)
            magic = reader.read_at(0, 4)
            (value,) = reader.read_struct(4, "<I")
            end = reader.read_at(8, 3)

        # Assert
        assert magic == b"TEST"
        assert value == 0x12345678
        assert end == b"END"
