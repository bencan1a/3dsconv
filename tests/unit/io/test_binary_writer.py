"""Tests for BinaryWriter class."""

import struct
from io import BytesIO

import pytest

from dsconv.io.binary_writer import BinaryWriter


class TestBinaryWriter:
    """Tests for BinaryWriter utility class."""

    def test_init_with_file_handle(self):
        """Test creating BinaryWriter with a file handle."""
        # Arrange
        data = BytesIO()

        # Act
        writer = BinaryWriter(data)

        # Assert
        assert writer.file is data

    def test_write_at_basic(self):
        """Test writing bytes at specific offset."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_at(offset=0, data=b"TEST")

        # Assert
        data.seek(0)
        assert data.read() == b"TEST"

    def test_write_at_with_offset(self):
        """Test writing at non-zero offset."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_at(offset=5, data=b"HELLO")

        # Assert
        data.seek(0)
        result = data.read()
        # Should have 5 null bytes, then "HELLO"
        assert result == b"\x00" * 5 + b"HELLO"

    def test_write_at_updates_position(self):
        """Test that write_at updates file position."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_at(offset=3, data=b"TEST")

        # Assert
        assert writer.tell() == 7  # 3 + 4

    def test_write_at_multiple_sequential_writes(self):
        """Test multiple sequential write_at operations."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_at(offset=0, data=b"ABC")
        writer.write_at(offset=5, data=b"DEF")
        writer.write_at(offset=10, data=b"GHI")

        # Assert
        data.seek(0)
        result = data.read()
        assert result == b"ABC\x00\x00DEF\x00\x00GHI"

    def test_write_at_with_negative_offset_raises_error(self):
        """Test that negative offset raises ValueError."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act & Assert
        with pytest.raises(ValueError, match="offset must be non-negative"):
            writer.write_at(offset=-1, data=b"TEST")

    def test_write_at_overwrites_existing_data(self):
        """Test that write_at overwrites existing data."""
        # Arrange
        data = BytesIO(b"0123456789")
        writer = BinaryWriter(data)

        # Act
        writer.write_at(offset=3, data=b"XXX")

        # Assert
        data.seek(0)
        assert data.read() == b"012XXX6789"

    def test_write_at_empty_data(self):
        """Test writing empty bytes."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_at(offset=0, data=b"")

        # Assert
        data.seek(0)
        assert data.read() == b""

    def test_write_struct_single_value(self):
        """Test writing a single packed value."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_struct(0, "<I", 0x12345678)

        # Assert
        data.seek(0)
        result = data.read()
        assert result == struct.pack("<I", 0x12345678)

    def test_write_struct_multiple_values(self):
        """Test writing multiple packed values."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_struct(0, "<IHH", 0x1000, 0x20, 0x30)

        # Assert
        data.seek(0)
        result = data.read()
        assert result == struct.pack("<IHH", 0x1000, 0x20, 0x30)

    def test_write_struct_with_offset(self):
        """Test writing struct at non-zero offset."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_struct(10, "<I", 0xDEADBEEF)

        # Assert
        data.seek(0)
        result = data.read()
        assert result == b"\x00" * 10 + struct.pack("<I", 0xDEADBEEF)

    def test_write_struct_bytes_and_int(self):
        """Test writing struct with mixed types."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_struct(0, "<4sI", b"NCCH", 0x1000)

        # Assert
        data.seek(0)
        result = data.read()
        assert result == b"NCCH" + struct.pack("<I", 0x1000)

    def test_write_struct_big_endian(self):
        """Test writing struct with big-endian format."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_struct(0, ">Q", 0x0011223344556677)

        # Assert
        data.seek(0)
        result = data.read()
        assert result == struct.pack(">Q", 0x0011223344556677)

    def test_write_struct_with_negative_offset_raises_error(self):
        """Test that negative offset raises ValueError."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act & Assert
        with pytest.raises(ValueError, match="offset must be non-negative"):
            writer.write_struct(-1, "<I", 0x1000)

    def test_write_struct_with_invalid_format_raises_error(self):
        """Test that invalid format string raises struct.error."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act & Assert
        with pytest.raises(struct.error):
            writer.write_struct(0, "<INVALID", 0)

    def test_write_struct_wrong_number_of_values_raises_error(self):
        """Test that wrong number of values raises struct.error."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act & Assert
        with pytest.raises(struct.error):
            writer.write_struct(0, "<II", 0x1000)  # Missing second value

    def test_append_to_empty_file(self):
        """Test appending to an empty file."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.append(b"FIRST")

        # Assert
        data.seek(0)
        assert data.read() == b"FIRST"

    def test_append_multiple_times(self):
        """Test appending multiple times."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.append(b"FIRST")
        writer.append(b"SECOND")
        writer.append(b"THIRD")

        # Assert
        data.seek(0)
        assert data.read() == b"FIRSTSECONDTHIRD"

    def test_append_after_write_at(self):
        """Test that append works correctly after write_at."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_at(0, b"START")
        writer.append(b"END")

        # Assert
        data.seek(0)
        assert data.read() == b"STARTEND"

    def test_append_with_existing_data(self):
        """Test appending to file with existing data."""
        # Arrange
        data = BytesIO(b"EXISTING")
        writer = BinaryWriter(data)

        # Act
        writer.append(b"NEW")

        # Assert
        data.seek(0)
        assert data.read() == b"EXISTINGNEW"

    def test_append_empty_data(self):
        """Test appending empty bytes."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.append(b"")

        # Assert
        data.seek(0)
        assert data.read() == b""

    def test_tell_returns_current_position(self):
        """Test that tell returns current file position."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_at(offset=5, data=b"TEST")
        position = writer.tell()

        # Assert
        assert position == 9  # 5 + 4

    def test_tell_initial_position(self):
        """Test that initial position is 0."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        position = writer.tell()

        # Assert
        assert position == 0

    def test_seek_absolute_positioning(self):
        """Test seeking with absolute positioning (whence=0)."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        new_pos = writer.seek(5, 0)

        # Assert
        assert new_pos == 5
        assert writer.tell() == 5

    def test_seek_relative_to_current(self):
        """Test seeking relative to current position (whence=1)."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)
        writer.seek(3)

        # Act
        new_pos = writer.seek(2, 1)

        # Assert
        assert new_pos == 5
        assert writer.tell() == 5

    def test_seek_relative_to_end(self):
        """Test seeking relative to end of file (whence=2)."""
        # Arrange
        data = BytesIO(b"0123456789")
        writer = BinaryWriter(data)

        # Act
        new_pos = writer.seek(-3, 2)

        # Assert
        assert new_pos == 7
        assert writer.tell() == 7

    def test_seek_default_whence_is_absolute(self):
        """Test that default whence is 0 (absolute)."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        new_pos = writer.seek(5)

        # Assert
        assert new_pos == 5

    def test_write_at_current_position(self):
        """Test writing at current position using write()."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)
        writer.seek(5)

        # Act
        bytes_written = writer.write(b"TEST")

        # Assert
        assert bytes_written == 4
        data.seek(0)
        assert data.read() == b"\x00" * 5 + b"TEST"

    def test_write_updates_position(self):
        """Test that write updates file position."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write(b"12345")

        # Assert
        assert writer.tell() == 5

    def test_write_empty_bytes(self):
        """Test writing empty bytes."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        bytes_written = writer.write(b"")

        # Assert
        assert bytes_written == 0
        assert writer.tell() == 0

    @pytest.mark.parametrize(
        "offset,write_data,expected",
        [
            (0, b"ABCD", b"ABCD"),
            (2, b"XY", b"\x00\x00XY"),
            (5, b"TEST", b"\x00" * 5 + b"TEST"),
            (0, b"A", b"A"),
            (10, b"END", b"\x00" * 10 + b"END"),
        ],
    )
    def test_write_at_various_offsets(self, offset, write_data, expected):
        """Test write_at with various offset and data combinations."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_at(offset, write_data)

        # Assert
        data.seek(0)
        assert data.read() == expected

    @pytest.mark.parametrize(
        "format_str,values,expected",
        [
            ("<B", (0xFF,), struct.pack("<B", 0xFF)),
            ("<H", (0xABCD,), struct.pack("<H", 0xABCD)),
            ("<I", (0x12345678,), struct.pack("<I", 0x12345678)),
            ("<Q", (0x0011223344556677,), struct.pack("<Q", 0x0011223344556677)),
            (">I", (0x12345678,), struct.pack(">I", 0x12345678)),
        ],
    )
    def test_write_struct_various_formats(self, format_str, values, expected):
        """Test write_struct with various format strings."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.write_struct(0, format_str, *values)

        # Assert
        data.seek(0)
        assert data.read() == expected

    def test_integration_writing_ncch_like_structure(self):
        """Test writing a structure similar to NCCH header."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act - write NCCH-like structure
        writer.write_at(0x000, b"\x00" * 0x100)  # Signature placeholder
        writer.write_at(0x100, b"NCCH")  # Magic at 0x100
        writer.write_struct(0x104, "<I", 0x1000)  # Content size at 0x104
        writer.write_at(0x108, b"\x00" * 8)  # Partition ID at 0x108

        # Assert
        data.seek(0x100)
        assert data.read(4) == b"NCCH"
        data.seek(0x104)
        assert struct.unpack("<I", data.read(4))[0] == 0x1000
        data.seek(0x108)
        assert data.read(8) == b"\x00" * 8

    def test_integration_writing_ncsd_like_structure(self):
        """Test writing a structure similar to NCSD header."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act - write NCSD-like structure
        writer.write_at(0x000, b"\x00" * 0x100)  # Skip to magic
        writer.write_at(0x100, b"NCSD")  # Magic at 0x100
        writer.write_struct(0x104, "<I", 0x2000)  # Size at 0x104
        writer.write_at(0x108, bytes(8))  # Title ID at 0x108

        # Assert
        data.seek(0x100)
        assert data.read(4) == b"NCSD"
        data.seek(0x104)
        assert struct.unpack("<I", data.read(4))[0] == 0x2000
        data.seek(0x108)
        assert data.read(8) == bytes(8)

    def test_chained_operations(self):
        """Test that multiple operations can be chained correctly."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act - perform various operations
        writer.write_at(0, b"0123")
        writer.seek(10)
        writer.write(b"ABCD")
        pos = writer.tell()
        writer.write_struct(2, "<H", 0x5858)
        writer.append(b"END")

        # Assert
        assert pos == 14
        data.seek(0)
        result = data.read()
        # After write_struct at offset 2, bytes 0-1 are "01", bytes 2-3 are struct
        assert result[:2] == b"01"
        assert result[2:4] == struct.pack("<H", 0x5858)
        assert result[10:14] == b"ABCD"
        assert result.endswith(b"END")

    def test_with_real_file_like_object(self, tmp_path):
        """Test BinaryWriter with actual file on disk."""
        # Arrange
        test_file = tmp_path / "test.bin"

        # Act
        with open(test_file, "wb") as f:
            writer = BinaryWriter(f)
            writer.write_at(0, b"TEST")
            writer.write_struct(4, "<I", 0x12345678)
            writer.append(b"END")

        # Assert
        result = test_file.read_bytes()
        assert result[:4] == b"TEST"
        assert struct.unpack("<I", result[4:8])[0] == 0x12345678
        assert result[8:11] == b"END"

    def test_overwrite_with_write_at(self):
        """Test that write_at can overwrite existing data."""
        # Arrange
        data = BytesIO(b"AAAAAAAAAA")
        writer = BinaryWriter(data)

        # Act
        writer.write_at(2, b"XXX")
        writer.write_at(6, b"YY")

        # Assert
        data.seek(0)
        # "AAAAAAAAAA" -> write "XXX" at 2 -> "AAXXXAAAAA" -> write "YY" at 6 -> "AAXXXAYYAA"
        assert data.read() == b"AAXXXAYYAA"

    def test_mixed_write_operations(self):
        """Test mixing different write operations."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        writer.append(b"START")
        writer.write_struct(5, "<I", 0x1234)
        writer.write_at(0, b"S")
        writer.append(b"END")

        # Assert
        data.seek(0)
        result = data.read()
        assert result[0:1] == b"S"  # Overwrote first byte
        assert result[1:5] == b"TART"
        assert struct.unpack("<I", result[5:9])[0] == 0x1234
        assert result.endswith(b"END")

    def test_write_large_data(self):
        """Test writing large amount of data."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)
        large_data = b"X" * 100000

        # Act
        writer.append(large_data)

        # Assert
        data.seek(0)
        assert data.read() == large_data
        assert len(data.getvalue()) == 100000

    def test_sequential_appends(self):
        """Test sequential appends build file correctly."""
        # Arrange
        data = BytesIO()
        writer = BinaryWriter(data)

        # Act
        for i in range(10):
            writer.append(bytes([i]))

        # Assert
        data.seek(0)
        result = data.read()
        assert result == bytes(range(10))
        assert len(result) == 10
