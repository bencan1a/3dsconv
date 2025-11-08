"""Tests for BinaryReader utility."""

import struct
from io import BytesIO

import pytest

from dsconv.io.binary_reader import BinaryReader


class TestBinaryReader:
    """Tests for BinaryReader class."""

    def test_create_with_file_handle(self):
        """Test creating BinaryReader with a file handle."""
        # Arrange
        file_handle = BytesIO(b"test data")

        # Act
        reader = BinaryReader(file_handle)

        # Assert
        assert reader.file is file_handle

    def test_read_at_from_start_of_file(self):
        """Test reading bytes from the start of the file."""
        # Arrange
        data = b"Hello, World!"
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_at(0, 5)

        # Assert
        assert result == b"Hello"

    def test_read_at_from_middle_of_file(self):
        """Test reading bytes from the middle of the file."""
        # Arrange
        data = b"Hello, World!"
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_at(7, 5)

        # Assert
        assert result == b"World"

    def test_read_at_zero_bytes(self):
        """Test reading zero bytes returns empty bytes."""
        # Arrange
        data = b"Hello, World!"
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_at(0, 0)

        # Assert
        assert result == b""

    def test_read_at_beyond_file_end_returns_partial_data(self):
        """Test reading beyond file end returns partial data."""
        # Arrange
        data = b"Hello"
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_at(0, 100)

        # Assert
        # BytesIO returns what's available, not full requested length
        assert result == b"Hello"

    def test_read_at_updates_file_position(self):
        """Test that read_at updates the file position."""
        # Arrange
        data = b"Hello, World!"
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        reader.read_at(7, 5)

        # Assert
        # File position should be at 7 + 5 = 12
        assert file_handle.tell() == 12

    def test_multiple_read_at_operations(self):
        """Test multiple read_at operations work correctly."""
        # Arrange
        data = b"ABCDEFGHIJKLMNOP"
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result1 = reader.read_at(0, 4)
        result2 = reader.read_at(8, 4)
        result3 = reader.read_at(4, 4)

        # Assert
        assert result1 == b"ABCD"
        assert result2 == b"IJKL"
        assert result3 == b"EFGH"

    def test_read_struct_single_unsigned_int(self):
        """Test reading a single unsigned int."""
        # Arrange
        value = 0x12345678
        data = struct.pack("<I", value) + b"\x00" * 100
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_struct(0, "<I")

        # Assert
        assert result == (value,)

    def test_read_struct_multiple_values(self):
        """Test reading multiple values in one struct."""
        # Arrange
        values = (0x1234, 0x5678, 0xABCD)
        data = struct.pack("<HHH", *values) + b"\x00" * 100
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_struct(0, "<HHH")

        # Assert
        assert result == values

    def test_read_struct_at_offset(self):
        """Test reading struct at a specific offset."""
        # Arrange
        value = 0x12345678
        data = b"\x00" * 0x100 + struct.pack("<I", value) + b"\x00" * 100
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_struct(0x100, "<I")

        # Assert
        assert result == (value,)

    def test_read_struct_big_endian(self):
        """Test reading big-endian struct."""
        # Arrange
        value = 0x12345678
        data = struct.pack(">I", value) + b"\x00" * 100
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_struct(0, ">I")

        # Assert
        assert result == (value,)

    def test_read_struct_with_strings(self):
        """Test reading fixed-length string."""
        # Arrange
        data = b"NCSD" + b"\x00" * 100
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_struct(0, "4s")

        # Assert
        assert result == (b"NCSD",)

    def test_read_struct_mixed_types(self):
        """Test reading mixed data types."""
        # Arrange
        magic = b"TEST"
        value1 = 0x1234
        value2 = 0x56789ABC
        data = struct.pack("<4sHI", magic, value1, value2) + b"\x00" * 100
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_struct(0, "<4sHI")

        # Assert
        assert result == (magic, value1, value2)

    @pytest.mark.parametrize(
        "format_str,values",
        [
            ("<B", (255,)),  # Unsigned byte
            ("<H", (65535,)),  # Unsigned short
            ("<I", (0xFFFFFFFF,)),  # Unsigned int
            ("<Q", (0xFFFFFFFFFFFFFFFF,)),  # Unsigned long long
            (">I", (0x12345678,)),  # Big-endian int
            ("<II", (0x1234, 0x5678)),  # Multiple ints
        ],
    )
    def test_read_struct_various_formats(self, format_str, values):
        """Test reading various struct formats."""
        # Arrange
        data = struct.pack(format_str, *values) + b"\x00" * 100
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_struct(0, format_str)

        # Assert
        assert result == values

    def test_read_struct_calculates_size_correctly(self):
        """Test that read_struct reads the correct number of bytes."""
        # Arrange
        # Create data with a known pattern
        data = bytes(range(256))
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act - read a struct at offset 10
        reader.read_struct(10, "<I")  # Should read 4 bytes

        # Assert - file position should be at 10 + 4 = 14
        assert file_handle.tell() == 14

    def test_read_struct_with_invalid_format_raises_error(self):
        """Test that invalid format string raises struct.error."""
        # Arrange
        data = b"\x00" * 100
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act & Assert
        with pytest.raises(struct.error):
            reader.read_struct(0, "invalid_format")

    def test_read_struct_with_insufficient_data_raises_error(self):
        """Test that insufficient data raises struct.error."""
        # Arrange
        data = b"\x00\x01\x02"  # Only 3 bytes
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act & Assert
        # Trying to read 4 bytes as uint should fail
        with pytest.raises(struct.error):
            reader.read_struct(0, "<I")

    def test_sequential_operations(self):
        """Test combining read_at and read_struct operations."""
        # Arrange
        # Create a mock NCSD header structure
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCSD"  # Magic at 0x100
        data[0x108:0x110] = b"\x01\x02\x03\x04\x05\x06\x07\x08"  # Title ID
        struct.pack_into("<I", data, 0x120, 0x1000)  # Partition offset

        file_handle = BytesIO(bytes(data))
        reader = BinaryReader(file_handle)

        # Act
        magic = reader.read_at(0x100, 4)
        title_id = reader.read_at(0x108, 8)
        (partition_offset,) = reader.read_struct(0x120, "<I")

        # Assert
        assert magic == b"NCSD"
        assert title_id == b"\x01\x02\x03\x04\x05\x06\x07\x08"
        assert partition_offset == 0x1000

    def test_read_at_with_large_data(self):
        """Test reading from large files."""
        # Arrange
        # Create 1MB of data
        data = bytes(1024 * 1024)
        file_handle = BytesIO(data)
        reader = BinaryReader(file_handle)

        # Act
        result = reader.read_at(1000000, 100)

        # Assert
        assert len(result) == 100
        assert result == bytes(100)

    def test_reading_from_real_file_pattern(self):
        """Test reading pattern similar to real NCSD file."""
        # Arrange - simulate NCSD container structure
        data = bytearray(0x8000)  # 32KB file

        # NCSD header at 0x100
        data[0x100:0x104] = b"NCSD"
        data[0x108:0x110] = bytes.fromhex("0123456789ABCDEF")[::-1]

        # Partition table at 0x120
        struct.pack_into("<I", data, 0x120, 0x1000)  # Game offset
        struct.pack_into("<I", data, 0x124, 0x2000)  # Game size
        struct.pack_into("<I", data, 0x128, 0x3000)  # Manual offset
        struct.pack_into("<I", data, 0x12C, 0x400)  # Manual size

        file_handle = BytesIO(bytes(data))
        reader = BinaryReader(file_handle)

        # Act - read like NCSDReader would
        magic = reader.read_at(0x100, 4)
        title_id = reader.read_at(0x108, 8)
        (game_offset,) = reader.read_struct(0x120, "<I")
        (game_size,) = reader.read_struct(0x124, "<I")
        (manual_offset,) = reader.read_struct(0x128, "<I")
        (manual_size,) = reader.read_struct(0x12C, "<I")

        # Assert
        assert magic == b"NCSD"
        assert title_id == bytes.fromhex("0123456789ABCDEF")[::-1]
        assert game_offset == 0x1000
        assert game_size == 0x2000
        assert manual_offset == 0x3000
        assert manual_size == 0x400
