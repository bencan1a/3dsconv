"""Tests for NCCHReader class."""

import struct
from io import BytesIO
from unittest.mock import Mock

import pytest

from dsconv.io.binary_reader import BinaryReader
from dsconv.io.ncch_reader import NCCHReader
from dsconv.models.ncch import NCCHHeader


class TestNCCHReader:
    """Tests for NCCHReader class."""

    @pytest.fixture
    def minimal_ncch_data(self):
        """Create minimal valid NCCH header data."""
        data = bytearray(0x1000)  # Enough space for header + extended header

        # Signature (0x000-0x100)
        data[0x000:0x100] = bytes(0x100)

        # Magic "NCCH" at 0x100
        data[0x100:0x104] = b"NCCH"

        # Content size at 0x104 (little-endian uint32) - 0x1000 media units
        data[0x104:0x108] = struct.pack("<I", 0x1000)

        # Partition ID at 0x108
        data[0x108:0x110] = b"\x01\x02\x03\x04\x05\x06\x07\x08"

        # Maker code at 0x110
        data[0x110:0x112] = b"01"

        # Version at 0x112
        data[0x112:0x114] = struct.pack("<H", 0x0000)

        # Program ID at 0x118
        data[0x118:0x120] = b"\x11\x22\x33\x44\x55\x66\x77\x88"

        # Extended header hash at 0x160
        data[0x160:0x180] = bytes(0x20)

        # Extended header size at 0x180
        data[0x180:0x184] = struct.pack("<I", 0x400)

        # Flags at 0x188 (8 bytes) - decrypted (0x04 in byte 7)
        data[0x188:0x190] = b"\x00\x00\x00\x00\x00\x00\x00\x04"

        # ExeFS offset at 0x1A0 (in media units)
        data[0x1A0:0x1A4] = struct.pack("<I", 0x10)

        # ExeFS size at 0x1A4 (in media units)
        data[0x1A4:0x1A8] = struct.pack("<I", 0x20)

        # Extended header at 0x200
        data[0x200:0x600] = b"EXT" + bytes(0x3FD)

        return bytes(data)

    @pytest.fixture
    def ncch_reader(self, minimal_ncch_data):
        """Create NCCHReader with minimal NCCH data."""
        data = BytesIO(minimal_ncch_data)
        binary_reader = BinaryReader(data)
        return NCCHReader(binary_reader)

    def test_initialization(self):
        """Test NCCHReader initialization."""
        # Arrange
        data = BytesIO(b"\x00" * 0x200)
        binary_reader = BinaryReader(data)

        # Act
        reader = NCCHReader(binary_reader)

        # Assert
        assert reader.reader is binary_reader

    def test_read_header_success(self, ncch_reader):
        """Test reading valid NCCH header."""
        # Act
        header = ncch_reader.read_header(offset=0)

        # Assert
        assert isinstance(header, NCCHHeader)
        assert header.magic == b"NCCH"
        assert header.content_size == 0x1000
        assert header.partition_id == b"\x01\x02\x03\x04\x05\x06\x07\x08"
        assert header.maker_code == b"01"
        assert header.version == 0x0000
        assert header.program_id == b"\x11\x22\x33\x44\x55\x66\x77\x88"
        assert header.extheader_size == 0x400
        assert header.flags == b"\x00\x00\x00\x00\x00\x00\x00\x04"
        assert header.exefs_offset == 0x10
        assert header.exefs_size == 0x20

    def test_read_header_at_offset(self):
        """Test reading NCCH header at non-zero offset."""
        # Arrange - create data with NCCH at offset 0x1000
        full_data = bytearray(0x1000 + 0x200)  # Padding + header
        full_data[0x1100:0x1104] = b"NCCH"  # Magic at offset 0x1000 + 0x100
        full_data[0x1104:0x1108] = struct.pack("<I", 0x100)
        full_data[0x1108:0x1110] = bytes(8)
        full_data[0x1110:0x1112] = b"01"
        full_data[0x1112:0x1114] = struct.pack("<H", 0)
        full_data[0x1118:0x1120] = bytes(8)
        full_data[0x1160:0x1180] = bytes(0x20)
        full_data[0x1180:0x1184] = struct.pack("<I", 0)
        full_data[0x1188:0x1190] = bytes(8)
        full_data[0x11A0:0x11A4] = struct.pack("<I", 0)
        full_data[0x11A4:0x11A8] = struct.pack("<I", 0)

        data = BytesIO(bytes(full_data))
        binary_reader = BinaryReader(data)
        reader = NCCHReader(binary_reader)

        # Act
        header = reader.read_header(offset=0x1000)

        # Assert
        assert header.magic == b"NCCH"
        assert header.content_size == 0x100

    def test_read_header_invalid_magic_raises_error(self):
        """Test that invalid magic bytes raise ValueError."""
        # Arrange
        data = BytesIO(b"\x00" * 0x200)
        data.seek(0x100)
        data.write(b"XXXX")  # Invalid magic
        data.seek(0)

        binary_reader = BinaryReader(data)
        reader = NCCHReader(binary_reader)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid NCCH magic"):
            reader.read_header(offset=0)

    def test_read_header_invalid_magic_with_offset_raises_error(self):
        """Test error message includes offset for invalid magic."""
        # Arrange
        full_data = bytearray(0x1000 + 0x200)
        full_data[0x1100:0x1104] = b"BAAD"  # Invalid magic at 0x1000 + 0x100

        data = BytesIO(bytes(full_data))
        binary_reader = BinaryReader(data)
        reader = NCCHReader(binary_reader)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            reader.read_header(offset=0x1000)

        assert "0x1100" in str(exc_info.value)  # offset + 0x100
        assert "b'BAAD'" in str(exc_info.value)

    def test_read_extheader_without_decryption(self, ncch_reader):
        """Test reading extended header without decryption."""
        # Act
        extheader = ncch_reader.read_extheader(offset=0, decrypt=False)

        # Assert
        assert len(extheader) == 0x400
        assert extheader[:3] == b"EXT"

    def test_read_extheader_at_offset(self):
        """Test reading extended header at non-zero offset."""
        # Arrange
        full_data = bytearray(0x1000 + 0x200 + 0x400)
        # Extended header is at offset + 0x200 = 0x1000 + 0x200 = 0x1200
        full_data[0x1200 : 0x1200 + 14] = b"EXTHEADER_DATA"

        data = BytesIO(bytes(full_data))
        binary_reader = BinaryReader(data)
        reader = NCCHReader(binary_reader)

        # Act
        extheader = reader.read_extheader(offset=0x1000, decrypt=False)

        # Assert
        assert len(extheader) == 0x400
        assert extheader[:14] == b"EXTHEADER_DATA"

    def test_read_extheader_with_decryption(self, ncch_reader):
        """Test reading and decrypting extended header."""
        # Arrange
        mock_decryption_service = Mock()
        mock_decryption_service.decrypt_extheader.return_value = b"DECRYPTED" + b"\x00" * (
            0x400 - 9
        )

        key_y = bytes(0x10)
        title_id = bytes(8)

        # Act
        extheader = ncch_reader.read_extheader(
            offset=0,
            decrypt=True,
            decryption_service=mock_decryption_service,
            key_y=key_y,
            title_id=title_id,
        )

        # Assert
        assert extheader[:9] == b"DECRYPTED"
        mock_decryption_service.decrypt_extheader.assert_called_once()

        # Verify call arguments
        call_args = mock_decryption_service.decrypt_extheader.call_args
        encrypted_data, called_key_y, called_title_id = call_args[0]
        assert called_key_y == key_y
        assert called_title_id == title_id
        assert len(encrypted_data) == 0x400

    def test_read_extheader_decrypt_true_without_service_raises_error(self, ncch_reader):
        """Test that decrypt=True without service raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="decryption_service is required"):
            ncch_reader.read_extheader(offset=0, decrypt=True)

    def test_read_extheader_decrypt_true_without_key_y_raises_error(self, ncch_reader):
        """Test that decrypt=True without key_y raises ValueError."""
        # Arrange
        mock_service = Mock()

        # Act & Assert
        with pytest.raises(ValueError, match="key_y is required"):
            ncch_reader.read_extheader(offset=0, decrypt=True, decryption_service=mock_service)

    def test_read_extheader_decrypt_true_without_title_id_raises_error(self, ncch_reader):
        """Test that decrypt=True without title_id raises ValueError."""
        # Arrange
        mock_service = Mock()
        key_y = bytes(0x10)

        # Act & Assert
        with pytest.raises(ValueError, match="title_id is required"):
            ncch_reader.read_extheader(
                offset=0, decrypt=True, decryption_service=mock_service, key_y=key_y
            )

    def test_read_key_y(self, ncch_reader):
        """Test reading KeyY from NCCH header."""
        # Act
        key_y = ncch_reader.read_key_y(offset=0)

        # Assert
        assert len(key_y) == 0x10
        assert isinstance(key_y, bytes)

    def test_read_key_y_at_offset(self):
        """Test reading KeyY at non-zero offset."""
        # Arrange
        full_data = bytearray(0x1000 + 0x10)
        full_data[0x1000:0x1010] = (
            b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"
        )

        data = BytesIO(bytes(full_data))
        binary_reader = BinaryReader(data)
        reader = NCCHReader(binary_reader)

        # Act
        key_y = reader.read_key_y(offset=0x1000)

        # Assert
        assert key_y == b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"

    def test_read_exefs_offset(self, ncch_reader):
        """Test reading ExeFS offset."""
        # Act
        exefs_offset = ncch_reader.read_exefs_offset(offset=0)

        # Assert
        # Stored as 0x10 media units, which is 0x10 * 0x200 = 0x2000 bytes
        # Absolute offset is 0 + 0x2000 = 0x2000
        assert exefs_offset == 0x2000

    def test_read_exefs_offset_at_ncch_offset(self):
        """Test reading ExeFS offset when NCCH is at non-zero offset."""
        # Arrange
        full_data = bytearray(0x5000 + 0x200)
        full_data[0x5000 + 0x1A0 : 0x5000 + 0x1A4] = struct.pack("<I", 0x20)  # 0x20 media units

        data = BytesIO(bytes(full_data))
        binary_reader = BinaryReader(data)
        reader = NCCHReader(binary_reader)

        # Act
        exefs_offset = reader.read_exefs_offset(offset=0x5000)

        # Assert
        # 0x20 media units = 0x20 * 0x200 = 0x4000 bytes
        # Absolute offset: 0x5000 + 0x4000 = 0x9000
        assert exefs_offset == 0x9000

    def test_read_exefs_size(self, ncch_reader):
        """Test reading ExeFS size."""
        # Act
        exefs_size = ncch_reader.read_exefs_size(offset=0)

        # Assert
        # Stored as 0x20 media units, which is 0x20 * 0x200 = 0x4000 bytes
        assert exefs_size == 0x4000

    def test_read_exefs_size_at_offset(self):
        """Test reading ExeFS size when NCCH is at non-zero offset."""
        # Arrange
        full_data = bytearray(0x3000 + 0x200)
        full_data[0x3000 + 0x1A4 : 0x3000 + 0x1A8] = struct.pack("<I", 0x100)  # 0x100 media units

        data = BytesIO(bytes(full_data))
        binary_reader = BinaryReader(data)
        reader = NCCHReader(binary_reader)

        # Act
        exefs_size = reader.read_exefs_size(offset=0x3000)

        # Assert
        # 0x100 media units = 0x100 * 0x200 = 0x20000 bytes
        assert exefs_size == 0x20000

    def test_integration_read_complete_ncch(self, minimal_ncch_data):
        """Test reading all parts of an NCCH header."""
        # Arrange
        data = BytesIO(minimal_ncch_data)
        binary_reader = BinaryReader(data)
        reader = NCCHReader(binary_reader)

        # Act
        header = reader.read_header(offset=0)
        extheader = reader.read_extheader(offset=0, decrypt=False)
        key_y = reader.read_key_y(offset=0)
        exefs_offset = reader.read_exefs_offset(offset=0)
        exefs_size = reader.read_exefs_size(offset=0)

        # Assert
        assert header.magic == b"NCCH"
        assert len(extheader) == 0x400
        assert len(key_y) == 0x10
        assert exefs_offset == 0x2000  # 0x10 * 0x200
        assert exefs_size == 0x4000  # 0x20 * 0x200

    def test_integration_read_with_decryption_service(self, minimal_ncch_data):
        """Test complete workflow with decryption service."""
        # Arrange
        data = BytesIO(minimal_ncch_data)
        binary_reader = BinaryReader(data)
        reader = NCCHReader(binary_reader)

        mock_service = Mock()
        mock_service.decrypt_extheader.return_value = b"DECRYPTED_EXTHEADER" + b"\x00" * (
            0x400 - 19
        )

        # Act
        header = reader.read_header(offset=0)
        key_y = reader.read_key_y(offset=0)
        extheader = reader.read_extheader(
            offset=0,
            decrypt=True,
            decryption_service=mock_service,
            key_y=key_y,
            title_id=header.title_id,
        )

        # Assert
        assert header.magic == b"NCCH"
        assert extheader[:19] == b"DECRYPTED_EXTHEADER"
        # Verify the call was made with correct parameters
        assert mock_service.decrypt_extheader.call_count == 1
        call_args = mock_service.decrypt_extheader.call_args[0]
        assert call_args[1] == key_y
        assert call_args[2] == header.title_id
