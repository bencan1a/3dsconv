"""Tests for BinaryReader utility class."""

import struct
from io import BytesIO

import pytest

from dsconv.io.binary_reader import BinaryReader


class TestBinaryReader:
    """Tests for BinaryReader class."""

    def test_read_at_basic(self):
        """Test reading bytes at a specific offset."""
        # Arrange
        data = BytesIO(b"ABCD" + b"EFGH" + b"IJKL")
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(4, 4)

        # Assert
        assert result == b"EFGH"

    def test_read_at_from_start(self):
        """Test reading from the start of the file."""
        # Arrange
        data = BytesIO(b"TEST" + b"DATA")
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(0, 4)

        # Assert
        assert result == b"TEST"

    def test_read_at_multiple_calls(self):
        """Test multiple read_at calls with different offsets."""
        # Arrange
        data = BytesIO(b"0123456789ABCDEF")
        reader = BinaryReader(data)

        # Act & Assert
        assert reader.read_at(0, 4) == b"0123"
        assert reader.read_at(8, 4) == b"89AB"
        assert reader.read_at(4, 4) == b"4567"

    def test_read_at_zero_length(self):
        """Test reading zero bytes."""
        # Arrange
        data = BytesIO(b"DATA")
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(0, 0)

        # Assert
        assert result == b""

    def test_read_at_negative_length_raises_error(self):
        """Test that negative length raises ValueError."""
        # Arrange
        data = BytesIO(b"DATA")
        reader = BinaryReader(data)

        # Act & Assert
        with pytest.raises(ValueError, match="length must be non-negative"):
            reader.read_at(0, -1)

    def test_read_at_beyond_end_of_file(self):
        """Test reading beyond end of file returns partial data."""
        # Arrange
        data = BytesIO(b"SHORT")
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(0, 100)

        # Assert - read only returns what's available
        assert result == b"SHORT"

    def test_read_struct_little_endian_uint32(self):
        """Test reading a little-endian uint32."""
        # Arrange
        data = BytesIO(b"\x00" * 4 + b"\x01\x02\x03\x04" + b"\x00" * 4)
        reader = BinaryReader(data)

        # Act
        (result,) = reader.read_struct(4, "<I")

        # Assert
        assert result == 0x04030201

    def test_read_struct_big_endian_uint32(self):
        """Test reading a big-endian uint32."""
        # Arrange
        data = BytesIO(b"\x00" * 4 + b"\x01\x02\x03\x04" + b"\x00" * 4)
        reader = BinaryReader(data)

        # Act
        (result,) = reader.read_struct(4, ">I")

        # Assert
        assert result == 0x01020304

    def test_read_struct_multiple_values(self):
        """Test reading multiple values with one struct call."""
        # Arrange
        # Pack two uint32 values: 0x12345678 and 0xABCDEF00
        packed = struct.pack("<II", 0x12345678, 0xABCDEF00)
        data = BytesIO(packed)
        reader = BinaryReader(data)

        # Act
        val1, val2 = reader.read_struct(0, "<II")

        # Assert
        assert val1 == 0x12345678
        assert val2 == 0xABCDEF00

    def test_read_struct_at_offset(self):
        """Test reading struct at non-zero offset."""
        # Arrange
        packed = b"\x00" * 8 + struct.pack("<H", 0x1234)
        data = BytesIO(packed)
        reader = BinaryReader(data)

        # Act
        (result,) = reader.read_struct(8, "<H")

        # Assert
        assert result == 0x1234

    def test_read_struct_complex_format(self):
        """Test reading complex struct format."""
        # Arrange
        # Format: byte, short, int
        packed = struct.pack("<BHI", 0x12, 0x3456, 0x789ABCDE)
        data = BytesIO(packed)
        reader = BinaryReader(data)

        # Act
        byte_val, short_val, int_val = reader.read_struct(0, "<BHI")

        # Assert
        assert byte_val == 0x12
        assert short_val == 0x3456
        assert int_val == 0x789ABCDE

    def test_read_struct_invalid_format_raises_error(self):
        """Test that invalid format string raises struct.error."""
        # Arrange
        data = BytesIO(b"\x00" * 10)
        reader = BinaryReader(data)

        # Act & Assert
        with pytest.raises(struct.error):
            reader.read_struct(0, "<INVALID")

    def test_tell_returns_current_position(self):
        """Test that tell returns the current file position."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)

        # Act - read at offset 5
        reader.read_at(5, 3)
        pos = reader.tell()

        # Assert - position should be after the read (5 + 3 = 8)
        assert pos == 8

    def test_seek_absolute(self):
        """Test seeking to an absolute position."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)

        # Act
        new_pos = reader.seek(5)

        # Assert
        assert new_pos == 5
        assert reader.tell() == 5

    def test_seek_relative(self):
        """Test seeking relative to current position."""
        # Arrange
        data = BytesIO(b"0123456789")
        reader = BinaryReader(data)
        reader.seek(3)

        # Act - seek 2 bytes forward from current position
        new_pos = reader.seek(2, 1)

        # Assert
        assert new_pos == 5
        assert reader.tell() == 5

    def test_seek_from_end(self):
        """Test seeking from end of file."""
        # Arrange
        data = BytesIO(b"0123456789")  # 10 bytes
        reader = BinaryReader(data)

        # Act - seek to 3 bytes before end
        new_pos = reader.seek(-3, 2)

        # Assert
        assert new_pos == 7
        assert reader.tell() == 7

    def test_integration_read_ncch_like_structure(self):
        """Test reading a structure similar to NCCH header."""
        # Arrange - create minimal NCCH-like structure
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCCH"  # Magic at 0x100
        data[0x104:0x108] = struct.pack("<I", 0x1000)  # Content size at 0x104

        reader = BinaryReader(BytesIO(bytes(data)))

        # Act
        magic = reader.read_at(0x100, 4)
        (content_size,) = reader.read_struct(0x104, "<I")

        # Assert
        assert magic == b"NCCH"
        assert content_size == 0x1000

    def test_file_handle_not_owned(self):
        """Test that BinaryReader doesn't close the file handle."""
        # Arrange
        data = BytesIO(b"DATA")
        reader = BinaryReader(data)

        # Act
        reader.read_at(0, 4)
        del reader  # Delete the reader

        # Assert - file should still be open
        assert not data.closed
        assert data.read() == b""  # Can still read (at end of file)

    @pytest.mark.parametrize(
        "offset,length,expected",
        [
            (0, 4, b"ABCD"),
            (4, 4, b"EFGH"),
            (8, 4, b"IJKL"),
            (0, 12, b"ABCDEFGHIJKL"),
            (2, 4, b"CDEF"),
        ],
    )
    def test_read_at_parametrized(self, offset, length, expected):
        """Test read_at with various offset/length combinations."""
        # Arrange
        data = BytesIO(b"ABCDEFGHIJKL")
        reader = BinaryReader(data)

        # Act
        result = reader.read_at(offset, length)

        # Assert
        assert result == expected
