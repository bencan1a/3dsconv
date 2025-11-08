"""Tests for NCCH reader."""

import struct
from io import BytesIO
from unittest.mock import Mock

import pytest

from dsconv.crypto.decryption_service import DecryptionService
from dsconv.io.binary_reader import BinaryReader
from dsconv.io.ncch_reader import NCCHReader
from dsconv.models.ncch import NCCHHeader


class TestNCCHReader:
    """Tests for NCCHReader class."""

    @pytest.fixture
    def minimal_ncch_data(self):
        """Create minimal valid NCCH header data."""
        data = bytearray(0x200)

        # Signature (0x000-0x100)
        data[0x000:0x010] = b"KeyY_16_bytes___"  # KeyY for testing
        data[0x010:0x100] = bytes(0xF0)  # Rest of signature

        # Magic (0x100-0x104)
        data[0x100:0x104] = b"NCCH"

        # Content size (0x104-0x108) - 0x1000 media units
        data[0x104:0x108] = struct.pack("<I", 0x1000)

        # Partition ID (0x108-0x110)
        data[0x108:0x110] = b"PARTID__"

        # Maker code (0x110-0x112)
        data[0x110:0x112] = b"01"

        # Version (0x112-0x114)
        data[0x112:0x114] = struct.pack("<H", 0x0002)

        # Program ID / Title ID (0x118-0x120)
        data[0x118:0x120] = b"\x01\x02\x03\x04\x05\x06\x07\x08"

        # Extended header hash (0x160-0x180)
        data[0x160:0x180] = b"ExtheaderHash_32bytes____123\x00\x00\x00\x00"

        # Extended header size (0x180-0x184)
        data[0x180:0x184] = struct.pack("<I", 0x400)

        # Flags (0x188-0x190)
        # Byte 7 (0x18F) is encryption flags: 0x04 = decrypted
        data[0x188:0x190] = bytes([0, 0, 0, 0, 0, 0, 0, 0x04])

        # ExeFS offset (0x1A0-0x1A4)
        data[0x1A0:0x1A4] = struct.pack("<I", 0x800)

        # ExeFS size (0x1A4-0x1A8)
        data[0x1A4:0x1A8] = struct.pack("<I", 0x400)

        return bytes(data)

    @pytest.fixture
    def binary_reader_with_ncch(self, minimal_ncch_data):
        """Create BinaryReader with minimal NCCH data."""
        # Just use the minimal NCCH data without extra padding
        # Individual tests can add their own data as needed
        file_handle = BytesIO(minimal_ncch_data)
        return BinaryReader(file_handle)

    @pytest.fixture
    def ncch_reader(self, binary_reader_with_ncch):
        """Create NCCHReader instance."""
        return NCCHReader(binary_reader_with_ncch)

    # Test initialization
    def test_init_stores_binary_reader(self, binary_reader_with_ncch):
        """Test that initialization stores the binary reader."""
        reader = NCCHReader(binary_reader_with_ncch)
        assert reader.reader is binary_reader_with_ncch

    # Test read_header method
    def test_read_header_at_offset_zero(self, ncch_reader):
        """Test reading NCCH header at offset 0."""
        header = ncch_reader.read_header(offset=0)

        assert isinstance(header, NCCHHeader)
        assert header.magic == b"NCCH"
        assert header.content_size == 0x1000
        assert header.partition_id == b"PARTID__"
        assert header.maker_code == b"01"
        assert header.version == 0x0002
        assert header.program_id == b"\x01\x02\x03\x04\x05\x06\x07\x08"
        assert header.extheader_size == 0x400
        assert header.exefs_offset == 0x800
        assert header.exefs_size == 0x400

    def test_read_header_at_nonzero_offset(self, minimal_ncch_data):
        """Test reading NCCH header at non-zero offset."""
        # Create data with NCCH at offset 0x1000
        offset = 0x1000
        data = bytes(offset) + minimal_ncch_data + bytes(0x100)  # Add padding
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        header = reader.read_header(offset=offset)

        assert isinstance(header, NCCHHeader)
        assert header.magic == b"NCCH"
        assert header.content_size == 0x1000

    def test_read_header_validates_magic_bytes(self, minimal_ncch_data):
        """Test that read_header validates magic bytes."""
        # Create data with invalid magic
        data = bytearray(minimal_ncch_data)
        data[0x100:0x104] = b"XXXX"  # Invalid magic

        # Add padding so we have enough bytes for the read
        file_handle = BytesIO(bytes(data) + bytes(0x100))
        reader = NCCHReader(BinaryReader(file_handle))

        with pytest.raises(ValueError, match="Invalid NCCH magic.*b'XXXX'"):
            reader.read_header(offset=0)

    def test_read_header_with_insufficient_data(self):
        """Test read_header with insufficient data raises error."""
        # Only 0x100 bytes, need 0x200
        data = bytes(0x100)
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        with pytest.raises(ValueError, match="Insufficient data for NCCH header"):
            reader.read_header(offset=0)

    def test_read_header_error_message_includes_offset(self):
        """Test that error messages include the offset for debugging."""
        data = bytes(0x100)
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        with pytest.raises(ValueError, match="offset 0x0"):
            reader.read_header(offset=0)

    def test_read_header_parses_all_fields_correctly(self, ncch_reader):
        """Test that all header fields are parsed correctly."""
        header = ncch_reader.read_header(offset=0)

        # Verify signature (first 16 bytes should be KeyY)
        assert header.signature[:16] == b"KeyY_16_bytes___"

        # Verify extended header hash (just check it was read, it will have null padding)
        assert header.extheader_hash[:28] == b"ExtheaderHash_32bytes____123"

        # Verify flags
        assert header.flags == bytes([0, 0, 0, 0, 0, 0, 0, 0x04])

    # Test read_extheader method
    def test_read_extheader_without_decryption(self, minimal_ncch_data):
        """Test reading extended header without decryption."""
        # Create data with extended header at offset 0x200
        extheader_data = b"ExtendedHeader" + bytes(0x400 - 14)
        data = minimal_ncch_data + extheader_data + bytes(0x100)  # Add padding
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        result = reader.read_extheader(offset=0x200, decrypt=False)

        assert result.startswith(b"ExtendedHeader")
        assert len(result) == 0x400

    def test_read_extheader_with_custom_size(self, minimal_ncch_data):
        """Test reading extended header with custom size."""
        extheader_data = b"ExtendedHeader" + bytes(0x800 - 14)
        data = minimal_ncch_data + extheader_data + bytes(0x100)  # Add padding
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        result = reader.read_extheader(offset=0x200, size=0x800, decrypt=False)

        assert len(result) == 0x800

    def test_read_extheader_with_decryption(self, minimal_ncch_data):
        """Test reading extended header with decryption."""
        # Create mock decryption service
        mock_service = Mock(spec=DecryptionService)
        encrypted_data = b"Encrypted" + bytes(0x400 - 9)
        decrypted_data = b"Decrypted" + bytes(0x400 - 9)
        mock_service.decrypt_extheader.return_value = decrypted_data

        data = minimal_ncch_data + encrypted_data + bytes(0x100)  # Add padding
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        key_y = b"KeyY_16_bytes___"
        title_id = b"\x01\x02\x03\x04\x05\x06\x07\x08"

        result = reader.read_extheader(
            offset=0x200,
            decrypt=True,
            decryption_service=mock_service,
            key_y=key_y,
            title_id=title_id,
        )

        # Verify the decryption service was called correctly
        # Get the actual encrypted data that was passed
        call_args = mock_service.decrypt_extheader.call_args
        assert call_args[0][0].startswith(b"Encrypted")
        assert call_args[0][1] == key_y
        assert call_args[0][2] == title_id
        assert result == decrypted_data

    def test_read_extheader_decrypt_requires_service(self, ncch_reader):
        """Test that decrypt=True requires decryption_service."""
        with pytest.raises(ValueError, match="decryption_service is required"):
            ncch_reader.read_extheader(offset=0x200, decrypt=True)

    def test_read_extheader_decrypt_requires_key_y(self, ncch_reader):
        """Test that decrypt=True requires key_y."""
        mock_service = Mock(spec=DecryptionService)

        with pytest.raises(ValueError, match="key_y is required"):
            ncch_reader.read_extheader(offset=0x200, decrypt=True, decryption_service=mock_service)

    def test_read_extheader_decrypt_requires_title_id(self, ncch_reader):
        """Test that decrypt=True requires title_id."""
        mock_service = Mock(spec=DecryptionService)
        key_y = b"KeyY_16_bytes___"

        with pytest.raises(ValueError, match="title_id is required"):
            ncch_reader.read_extheader(
                offset=0x200,
                decrypt=True,
                decryption_service=mock_service,
                key_y=key_y,
            )

    def test_read_extheader_default_size_is_0x400(self, minimal_ncch_data):
        """Test that default extended header size is 0x400 bytes."""
        extheader_data = bytes(0x400)
        data = minimal_ncch_data + extheader_data + bytes(0x100)  # Add padding
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        result = reader.read_extheader(offset=0x200, decrypt=False)

        assert len(result) == 0x400

    def test_read_extheader_at_different_offsets(self, minimal_ncch_data):
        """Test reading extended header at various offsets."""
        extheader_data = b"ExtHeader" + bytes(0x400 - 9)
        # Add padding before extended header
        padding = bytes(0x1000)
        data = padding + extheader_data + bytes(0x100)  # Add extra padding
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        result = reader.read_extheader(offset=0x1000, decrypt=False)

        assert result.startswith(b"ExtHeader")
        assert len(result) == 0x400

    # Test read_key_y method
    def test_read_key_y_at_offset_zero(self, ncch_reader):
        """Test reading KeyY at offset 0."""
        key_y = ncch_reader.read_key_y(ncch_offset=0)

        assert key_y == b"KeyY_16_bytes___"
        assert len(key_y) == 16

    def test_read_key_y_at_nonzero_offset(self, minimal_ncch_data):
        """Test reading KeyY at non-zero offset."""
        offset = 0x4000
        data = bytes(offset) + minimal_ncch_data
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        key_y = reader.read_key_y(ncch_offset=offset)

        assert key_y == b"KeyY_16_bytes___"
        assert len(key_y) == 16

    def test_read_key_y_returns_exactly_16_bytes(self, ncch_reader):
        """Test that read_key_y always returns exactly 16 bytes."""
        key_y = ncch_reader.read_key_y(ncch_offset=0)

        assert len(key_y) == 16
        assert isinstance(key_y, bytes)

    def test_read_key_y_from_different_ncch_headers(self):
        """Test reading KeyY from different NCCH headers."""
        # Create two different NCCH headers with different KeyY values
        key_y_1 = b"FirstKeyY_16____"
        key_y_2 = b"SecondKeyY16____"

        data = bytearray(0x400)
        data[0x000:0x010] = key_y_1
        data[0x100:0x104] = b"NCCH"  # First NCCH
        data[0x200:0x210] = key_y_2
        data[0x300:0x304] = b"NCCH"  # Second NCCH

        file_handle = BytesIO(bytes(data))
        reader = NCCHReader(BinaryReader(file_handle))

        # Read from first NCCH
        result_1 = reader.read_key_y(ncch_offset=0)
        assert result_1 == key_y_1

        # Read from second NCCH
        result_2 = reader.read_key_y(ncch_offset=0x200)
        assert result_2 == key_y_2

    # Integration tests combining multiple methods
    def test_workflow_read_header_then_key_y(self, ncch_reader):
        """Test typical workflow: read header, then read KeyY."""
        # Read header first
        header = ncch_reader.read_header(offset=0)
        assert header.magic == b"NCCH"

        # Then read KeyY from same offset
        key_y = ncch_reader.read_key_y(ncch_offset=0)
        assert len(key_y) == 16

    def test_workflow_read_header_then_extheader(self, minimal_ncch_data):
        """Test workflow: read header, then read extended header."""
        extheader_data = b"ExtHeader" + bytes(0x400 - 9)
        # Ensure we have enough data after the NCCH header for extended header
        data = minimal_ncch_data + extheader_data + bytes(0x100)  # Extra padding
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        # Read header to get metadata
        header = reader.read_header(offset=0)
        assert header.extheader_size == 0x400

        # Read extended header using info from header
        extheader = reader.read_extheader(offset=0x200, size=header.extheader_size)
        assert len(extheader) == header.extheader_size

    def test_workflow_full_encrypted_read(self, minimal_ncch_data):
        """Test complete workflow for reading encrypted NCCH."""
        # Setup mock decryption
        mock_service = Mock(spec=DecryptionService)
        decrypted_extheader = b"Decrypted" + bytes(0x400 - 9)
        mock_service.decrypt_extheader.return_value = decrypted_extheader

        extheader_data = b"Encrypted" + bytes(0x400 - 9)
        data = minimal_ncch_data + extheader_data + bytes(0x100)  # Add padding
        file_handle = BytesIO(data)
        reader = NCCHReader(BinaryReader(file_handle))

        # 1. Read header
        header = reader.read_header(offset=0)

        # 2. Read KeyY
        key_y = reader.read_key_y(ncch_offset=0)

        # 3. Read and decrypt extended header
        extheader = reader.read_extheader(
            offset=0x200,
            decrypt=True,
            decryption_service=mock_service,
            key_y=key_y,
            title_id=header.title_id,
        )

        assert extheader == decrypted_extheader
        assert mock_service.decrypt_extheader.called

    def test_multiple_reads_from_same_reader(self, ncch_reader):
        """Test that multiple reads work correctly from same reader."""
        # Read header multiple times
        header1 = ncch_reader.read_header(offset=0)
        header2 = ncch_reader.read_header(offset=0)

        assert header1.magic == header2.magic
        assert header1.content_size == header2.content_size

        # Read KeyY multiple times
        key_y1 = ncch_reader.read_key_y(ncch_offset=0)
        key_y2 = ncch_reader.read_key_y(ncch_offset=0)

        assert key_y1 == key_y2

    # Edge case tests
    def test_read_header_with_encrypted_flag(self):
        """Test reading header with encrypted flag set."""
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCCH"
        data[0x104:0x108] = struct.pack("<I", 0x1000)
        data[0x108:0x110] = b"PARTID__"
        data[0x110:0x112] = b"01"
        data[0x112:0x114] = struct.pack("<H", 0x0002)
        data[0x118:0x120] = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        data[0x160:0x180] = bytes(0x20)
        data[0x180:0x184] = struct.pack("<I", 0x400)
        # Encryption flag: 0x00 = encrypted
        data[0x188:0x190] = bytes([0, 0, 0, 0, 0, 0, 0, 0x00])
        data[0x1A0:0x1A4] = struct.pack("<I", 0x800)
        data[0x1A4:0x1A8] = struct.pack("<I", 0x400)

        file_handle = BytesIO(bytes(data))
        reader = NCCHReader(BinaryReader(file_handle))

        header = reader.read_header(offset=0)
        assert header.is_encrypted is True

    def test_read_header_with_zerokey_flag(self):
        """Test reading header with zerokey encryption flag."""
        data = bytearray(0x200)
        data[0x100:0x104] = b"NCCH"
        data[0x104:0x108] = struct.pack("<I", 0x1000)
        data[0x108:0x110] = b"PARTID__"
        data[0x110:0x112] = b"01"
        data[0x112:0x114] = struct.pack("<H", 0x0002)
        data[0x118:0x120] = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        data[0x160:0x180] = bytes(0x20)
        data[0x180:0x184] = struct.pack("<I", 0x400)
        # Encryption flag: 0x01 = zerokey encrypted
        data[0x188:0x190] = bytes([0, 0, 0, 0, 0, 0, 0, 0x01])
        data[0x1A0:0x1A4] = struct.pack("<I", 0x800)
        data[0x1A4:0x1A8] = struct.pack("<I", 0x400)

        file_handle = BytesIO(bytes(data))
        reader = NCCHReader(BinaryReader(file_handle))

        header = reader.read_header(offset=0)
        assert header.uses_zerokey is True

    @pytest.mark.parametrize(
        "offset,key_y_value",
        [
            (0x0000, b"KeyY_at_0x0000__"),
            (0x1000, b"KeyY_at_0x1000__"),
            (0x4000, b"KeyY_at_0x4000__"),
        ],
    )
    def test_read_key_y_at_various_offsets(self, offset, key_y_value):
        """Test reading KeyY at various offsets."""
        data = bytearray(offset + 0x200)
        data[offset : offset + 16] = key_y_value
        data[offset + 0x100 : offset + 0x104] = b"NCCH"

        file_handle = BytesIO(bytes(data))
        reader = NCCHReader(BinaryReader(file_handle))

        key_y = reader.read_key_y(ncch_offset=offset)
        assert key_y == key_y_value
