"""Tests for CIA writer."""

import hashlib
import struct
from io import BytesIO

import pytest

from dsconv.io.binary_writer import BinaryWriter
from dsconv.io.cia_writer import CIAWriter
from dsconv.models.cia import CIAHeader


class TestCIAWriterInit:
    """Tests for CIAWriter initialization."""

    def test_init_with_valid_params(self):
        """Test creating CIAWriter with valid parameters."""
        # Arrange
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = bytes(0xA00)

        # Act
        cia_writer = CIAWriter(writer, cert_chain)

        # Assert
        assert cia_writer.writer is writer
        assert cia_writer.cert_chain == cert_chain
        assert cia_writer.dev_mode is False

    def test_init_with_dev_mode(self):
        """Test creating CIAWriter with dev_mode enabled."""
        # Arrange
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = bytes(0xA00)

        # Act
        cia_writer = CIAWriter(writer, cert_chain, dev_mode=True)

        # Assert
        assert cia_writer.dev_mode is True


class TestWriteHeader:
    """Tests for write_header method."""

    @pytest.fixture
    def cia_writer(self):
        """Create CIAWriter with BytesIO backend."""
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = bytes(0xA00)
        return CIAWriter(writer, cert_chain), file_obj

    def test_write_header_success(self, cia_writer):
        """Test writing CIA header successfully."""
        # Arrange
        writer, file_obj = cia_writer
        header = CIAHeader(
            header_size=0x2020,
            type_=0,
            version=0,
            cert_chain_size=0xA00,
            ticket_size=0x350,
            tmd_size=0xB34,
            meta_size=0x3AC0,
            content_size=0x100000,
            content_index=bytes(0x2000),
        )

        # Act
        writer.write_header(header)

        # Assert
        file_obj.seek(0)
        written_data = file_obj.read(0x2020)
        assert len(written_data) == 0x2020

        # Verify header size
        (header_size,) = struct.unpack("<I", written_data[0x00:0x04])
        assert header_size == 0x2020

        # Verify type and version
        (type_,) = struct.unpack("<H", written_data[0x04:0x06])
        assert type_ == 0

        (version,) = struct.unpack("<H", written_data[0x06:0x08])
        assert version == 0

        # Verify sizes
        (cert_chain_size,) = struct.unpack("<I", written_data[0x08:0x0C])
        assert cert_chain_size == 0xA00

        (ticket_size,) = struct.unpack("<I", written_data[0x0C:0x10])
        assert ticket_size == 0x350

        (tmd_size,) = struct.unpack("<I", written_data[0x10:0x14])
        assert tmd_size == 0xB34

        (meta_size,) = struct.unpack("<I", written_data[0x14:0x18])
        assert meta_size == 0x3AC0

        (content_size,) = struct.unpack("<Q", written_data[0x18:0x20])
        assert content_size == 0x100000

        # Verify content index
        content_index = written_data[0x20:0x2020]
        assert len(content_index) == 0x2000

    def test_write_header_with_content_index(self, cia_writer):
        """Test writing header with specific content index."""
        # Arrange
        writer, file_obj = cia_writer
        content_index = struct.pack("<I", 0x80) + bytes(0x2000 - 4)
        header = CIAHeader(
            header_size=0x2020,
            type_=0,
            version=0,
            cert_chain_size=0xA00,
            ticket_size=0x350,
            tmd_size=0xB34,
            meta_size=0x3AC0,
            content_size=0x100000,
            content_index=content_index,
        )

        # Act
        writer.write_header(header)

        # Assert
        file_obj.seek(0x20)
        written_index = file_obj.read(0x2000)
        assert written_index == content_index


class TestWriteCertChain:
    """Tests for write_cert_chain method."""

    @pytest.fixture
    def cia_writer(self):
        """Create CIAWriter with BytesIO backend."""
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = b"CERT" + bytes(0xA00 - 4)
        return CIAWriter(writer, cert_chain), file_obj

    def test_write_cert_chain_appends_at_current_position(self, cia_writer):
        """Test that cert chain is appended at current position."""
        # Arrange
        writer, file_obj = cia_writer

        # Write some data first to move position
        file_obj.write(bytes(0x2020))

        # Act
        writer.write_cert_chain()

        # Assert
        file_obj.seek(0x2020)
        written_cert = file_obj.read(0xA00)
        assert written_cert == writer.cert_chain


class TestWriteTicket:
    """Tests for write_ticket method."""

    @pytest.fixture
    def cia_writer(self):
        """Create CIAWriter with BytesIO backend."""
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = bytes(0xA00)
        return CIAWriter(writer, cert_chain), file_obj

    def test_write_ticket_aligns_to_64_bytes(self, cia_writer):
        """Test that ticket is aligned to 64 byte boundary."""
        # Arrange
        writer, file_obj = cia_writer
        ticket_data = b"TICKET" + bytes(0x350 - 6)

        # Write header and cert chain to position file
        file_obj.write(bytes(0x2020))  # Header
        file_obj.write(bytes(0xA00))  # Cert chain
        # Position is now 0x2A20, which needs alignment

        # Act
        writer.write_ticket(ticket_data)

        # Assert
        # Expected aligned position: (0x2A20 + 63) // 64 * 64 = 0x2A40
        file_obj.seek(0x2A40)
        written_ticket = file_obj.read(0x350)
        assert written_ticket == ticket_data

    def test_write_ticket_no_padding_when_aligned(self, cia_writer):
        """Test that no padding is added when already aligned."""
        # Arrange
        writer, file_obj = cia_writer
        ticket_data = b"TICKET" + bytes(0x350 - 6)

        # Write exactly aligned amount
        file_obj.write(bytes(0x2000))  # Already aligned to 64

        # Act
        writer.write_ticket(ticket_data)

        # Assert
        file_obj.seek(0x2000)
        written_ticket = file_obj.read(0x350)
        assert written_ticket == ticket_data


class TestWriteTMD:
    """Tests for write_tmd method."""

    @pytest.fixture
    def cia_writer(self):
        """Create CIAWriter with BytesIO backend."""
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = bytes(0xA00)
        return CIAWriter(writer, cert_chain), file_obj

    def test_write_tmd_aligns_to_64_bytes(self, cia_writer):
        """Test that TMD is aligned to 64 byte boundary."""
        # Arrange
        writer, file_obj = cia_writer
        tmd_data = b"TMD" + bytes(0xB34 - 3)

        # Write unaligned amount
        file_obj.write(bytes(0x1234))

        # Act
        writer.write_tmd(tmd_data)

        # Assert
        # Expected aligned position: (0x1234 + 63) // 64 * 64 = 0x1240
        file_obj.seek(0x1240)
        written_tmd = file_obj.read(0xB34)
        assert written_tmd == tmd_data


class TestWriteContent:
    """Tests for write_content method."""

    @pytest.fixture
    def cia_writer(self):
        """Create CIAWriter with BytesIO backend."""
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = bytes(0xA00)
        return CIAWriter(writer, cert_chain), file_obj

    def test_write_content_computes_hash(self, cia_writer):
        """Test that write_content computes SHA-256 hash."""
        # Arrange
        writer, file_obj = cia_writer
        content_data = b"TEST CONTENT" * 1000

        # Act
        content_hash = writer.write_content(content_data)

        # Assert
        expected_hash = hashlib.sha256(content_data).digest()
        assert content_hash == expected_hash
        assert len(content_hash) == 32

    def test_write_content_writes_data(self, cia_writer):
        """Test that write_content writes the data correctly."""
        # Arrange
        writer, file_obj = cia_writer
        content_data = b"TEST CONTENT" * 100

        # Act
        writer.write_content(content_data)

        # Assert
        file_obj.seek(0)
        written_data = file_obj.read()
        assert content_data in written_data

    def test_write_content_without_hash(self, cia_writer):
        """Test writing content without computing hash."""
        # Arrange
        writer, file_obj = cia_writer
        content_data = b"TEST CONTENT"

        # Act
        content_hash = writer.write_content(content_data, compute_hash=False)

        # Assert
        assert content_hash == b""

    def test_write_content_with_custom_chunk_size(self, cia_writer):
        """Test writing content with custom chunk size."""
        # Arrange
        writer, file_obj = cia_writer
        content_data = b"A" * 1000
        chunk_size = 100

        # Act
        content_hash = writer.write_content(content_data, chunk_size=chunk_size)

        # Assert
        expected_hash = hashlib.sha256(content_data).digest()
        assert content_hash == expected_hash

    def test_write_content_aligns_to_64_bytes(self, cia_writer):
        """Test that content is aligned to 64 byte boundary."""
        # Arrange
        writer, file_obj = cia_writer
        content_data = b"TEST"

        # Write unaligned amount
        file_obj.write(bytes(0x123))

        # Act
        writer.write_content(content_data)

        # Assert
        # Expected aligned position: (0x123 + 63) // 64 * 64 = 0x140
        file_obj.seek(0x140)
        written_content = file_obj.read(len(content_data))
        assert written_content == content_data

    def test_write_content_handles_large_data(self, cia_writer):
        """Test writing large content with chunking."""
        # Arrange
        writer, file_obj = cia_writer
        # Create content larger than default chunk size
        content_data = b"X" * (0x800000 + 100)

        # Act
        content_hash = writer.write_content(content_data)

        # Assert
        expected_hash = hashlib.sha256(content_data).digest()
        assert content_hash == expected_hash

    def test_write_content_invalid_chunk_size_raises_error(self, cia_writer):
        """Test that invalid chunk size raises ValueError."""
        # Arrange
        writer, file_obj = cia_writer
        content_data = b"TEST"

        # Act & Assert
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            writer.write_content(content_data, chunk_size=0)

        with pytest.raises(ValueError, match="chunk_size must be positive"):
            writer.write_content(content_data, chunk_size=-1)


class TestWriteContentFromSource:
    """Tests for write_content_from_source method."""

    @pytest.fixture
    def cia_writer(self):
        """Create CIAWriter with BytesIO backend."""
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = bytes(0xA00)
        return CIAWriter(writer, cert_chain), file_obj

    def test_write_content_from_source_computes_hash(self, cia_writer):
        """Test that write_content_from_source computes SHA-256 hash."""
        # Arrange
        writer, file_obj = cia_writer
        source_data = b"SOURCE CONTENT" * 1000
        source = BytesIO(source_data)

        # Act
        content_hash = writer.write_content_from_source(source, len(source_data))

        # Assert
        expected_hash = hashlib.sha256(source_data).digest()
        assert content_hash == expected_hash

    def test_write_content_from_source_writes_data(self, cia_writer):
        """Test that write_content_from_source writes data correctly."""
        # Arrange
        writer, file_obj = cia_writer
        source_data = b"SOURCE CONTENT" * 100
        source = BytesIO(source_data)

        # Act
        writer.write_content_from_source(source, len(source_data))

        # Assert
        file_obj.seek(0)
        written_data = file_obj.read()
        assert source_data in written_data

    def test_write_content_from_source_without_hash(self, cia_writer):
        """Test writing from source without computing hash."""
        # Arrange
        writer, file_obj = cia_writer
        source_data = b"SOURCE CONTENT"
        source = BytesIO(source_data)

        # Act
        content_hash = writer.write_content_from_source(
            source, len(source_data), compute_hash=False
        )

        # Assert
        assert content_hash == b""

    def test_write_content_from_source_with_custom_chunk_size(self, cia_writer):
        """Test writing from source with custom chunk size."""
        # Arrange
        writer, file_obj = cia_writer
        source_data = b"A" * 1000
        source = BytesIO(source_data)
        chunk_size = 100

        # Act
        content_hash = writer.write_content_from_source(
            source, len(source_data), chunk_size=chunk_size
        )

        # Assert
        expected_hash = hashlib.sha256(source_data).digest()
        assert content_hash == expected_hash

    def test_write_content_from_source_handles_large_data(self, cia_writer):
        """Test writing large content from source with chunking."""
        # Arrange
        writer, file_obj = cia_writer
        # Create content larger than default chunk size
        source_data = b"Y" * (0x800000 + 100)
        source = BytesIO(source_data)

        # Act
        content_hash = writer.write_content_from_source(source, len(source_data))

        # Assert
        expected_hash = hashlib.sha256(source_data).digest()
        assert content_hash == expected_hash

    def test_write_content_from_source_handles_partial_read(self, cia_writer):
        """Test writing from source that returns less data than requested."""
        # Arrange
        writer, file_obj = cia_writer
        source_data = b"SHORT"
        source = BytesIO(source_data)

        # Act - request more data than available
        content_hash = writer.write_content_from_source(source, 1000)

        # Assert - should only write what's available
        expected_hash = hashlib.sha256(source_data).digest()
        assert content_hash == expected_hash

    def test_write_content_from_source_invalid_size_raises_error(self, cia_writer):
        """Test that invalid size raises ValueError."""
        # Arrange
        writer, file_obj = cia_writer
        source = BytesIO(b"TEST")

        # Act & Assert
        with pytest.raises(ValueError, match="size must be non-negative"):
            writer.write_content_from_source(source, -1)

    def test_write_content_from_source_invalid_chunk_size_raises_error(self, cia_writer):
        """Test that invalid chunk size raises ValueError."""
        # Arrange
        writer, file_obj = cia_writer
        source = BytesIO(b"TEST")

        # Act & Assert
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            writer.write_content_from_source(source, 4, chunk_size=0)

    def test_write_content_from_source_aligns_to_64_bytes(self, cia_writer):
        """Test that content from source is aligned to 64 byte boundary."""
        # Arrange
        writer, file_obj = cia_writer
        source_data = b"TEST"
        source = BytesIO(source_data)

        # Write unaligned amount
        file_obj.write(bytes(0x123))

        # Act
        writer.write_content_from_source(source, len(source_data))

        # Assert
        # Expected aligned position: (0x123 + 63) // 64 * 64 = 0x140
        file_obj.seek(0x140)
        written_content = file_obj.read(len(source_data))
        assert written_content == source_data


class TestWriteMeta:
    """Tests for write_meta method."""

    @pytest.fixture
    def cia_writer(self):
        """Create CIAWriter with BytesIO backend."""
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = bytes(0xA00)
        return CIAWriter(writer, cert_chain), file_obj

    def test_write_meta_writes_data(self, cia_writer):
        """Test that write_meta writes meta data."""
        # Arrange
        writer, file_obj = cia_writer
        meta_data = b"META" + bytes(0x3AC0 - 4)

        # Act
        writer.write_meta(meta_data)

        # Assert
        file_obj.seek(0)
        written_data = file_obj.read()
        assert meta_data in written_data

    def test_write_meta_aligns_to_64_bytes(self, cia_writer):
        """Test that meta is aligned to 64 byte boundary."""
        # Arrange
        writer, file_obj = cia_writer
        meta_data = b"META" + bytes(0x3AC0 - 4)

        # Write unaligned amount
        file_obj.write(bytes(0x567))

        # Act
        writer.write_meta(meta_data)

        # Assert
        # Expected aligned position: (0x567 + 63) // 64 * 64 = 0x580
        file_obj.seek(0x580)
        written_meta = file_obj.read(0x3AC0)
        assert written_meta == meta_data


class TestUpdateTMDHash:
    """Tests for update_tmd_hash method."""

    @pytest.fixture
    def cia_writer(self):
        """Create CIAWriter with BytesIO backend."""
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = bytes(0xA00)
        return CIAWriter(writer, cert_chain), file_obj

    def test_update_tmd_hash_writes_hash_at_correct_offset(self, cia_writer):
        """Test that hash is written at correct offset in TMD."""
        # Arrange
        writer, file_obj = cia_writer
        tmd_offset = 0x3000
        content_hash = b"H" * 32

        # Write some dummy data at TMD location
        file_obj.write(bytes(0x4000))

        # Act
        writer.update_tmd_hash(tmd_offset, content_hash, content_index=0)

        # Assert
        # Hash should be at tmd_offset + 0xB04 + 0x10
        expected_offset = tmd_offset + 0xB04 + 0x10
        file_obj.seek(expected_offset)
        written_hash = file_obj.read(32)
        assert written_hash == content_hash

    def test_update_tmd_hash_for_second_content(self, cia_writer):
        """Test updating hash for second content."""
        # Arrange
        writer, file_obj = cia_writer
        tmd_offset = 0x3000
        content_hash = b"G" * 32

        # Write some dummy data
        file_obj.write(bytes(0x5000))

        # Act
        writer.update_tmd_hash(tmd_offset, content_hash, content_index=1)

        # Assert
        # Hash should be at tmd_offset + 0xB04 + 0x30 + 0x10
        expected_offset = tmd_offset + 0xB04 + 0x30 + 0x10
        file_obj.seek(expected_offset)
        written_hash = file_obj.read(32)
        assert written_hash == content_hash

    def test_update_tmd_hash_invalid_hash_raises_error(self, cia_writer):
        """Test that invalid hash length raises ValueError."""
        # Arrange
        writer, file_obj = cia_writer
        tmd_offset = 0x3000

        # Act & Assert
        with pytest.raises(ValueError, match="content_hash must be 32 bytes"):
            writer.update_tmd_hash(tmd_offset, b"SHORT")

        with pytest.raises(ValueError, match="content_hash must be 32 bytes"):
            writer.update_tmd_hash(tmd_offset, b"X" * 64)


class TestAlignOffset:
    """Tests for _align_offset static method."""

    def test_align_offset_already_aligned(self):
        """Test aligning offset that is already aligned."""
        # Arrange
        offset = 0x1000  # Already aligned to 64

        # Act
        aligned = CIAWriter._align_offset(offset)

        # Assert
        assert aligned == 0x1000

    def test_align_offset_needs_alignment(self):
        """Test aligning offset that needs alignment."""
        # Arrange
        offset = 0x1001  # Not aligned

        # Act
        aligned = CIAWriter._align_offset(offset)

        # Assert
        assert aligned == 0x1040  # Next 64-byte boundary

    @pytest.mark.parametrize(
        "offset,expected",
        [
            (0, 0),
            (1, 64),
            (63, 64),
            (64, 64),
            (65, 128),
            (127, 128),
            (128, 128),
            (0x2A20, 0x2A40),
            (0x2A40, 0x2A40),
        ],
    )
    def test_align_offset_various_offsets(self, offset, expected):
        """Test alignment for various offsets."""
        assert CIAWriter._align_offset(offset) == expected

    def test_align_offset_custom_alignment(self):
        """Test alignment with custom alignment value."""
        # Arrange
        offset = 100
        alignment = 128

        # Act
        aligned = CIAWriter._align_offset(offset, alignment)

        # Assert
        assert aligned == 128


class TestCIAWriterIntegration:
    """Integration tests for CIAWriter."""

    def test_write_complete_cia_structure(self):
        """Test writing a complete CIA file structure."""
        # Arrange
        file_obj = BytesIO()
        writer = BinaryWriter(file_obj)
        cert_chain = b"CERT" + bytes(0xA00 - 4)
        cia_writer = CIAWriter(writer, cert_chain)

        header = CIAHeader(
            header_size=0x2020,
            type_=0,
            version=0,
            cert_chain_size=0xA00,
            ticket_size=0x350,
            tmd_size=0xB34,
            meta_size=0x3AC0,
            content_size=0x1000,
            content_index=struct.pack("<I", 0x80) + bytes(0x2000 - 4),
        )

        ticket_data = b"TICKET" + bytes(0x350 - 6)
        tmd_data = b"TMD" + bytes(0xB34 - 3)
        content_data = b"CONTENT" * 100
        meta_data = b"META" + bytes(0x3AC0 - 4)

        # Act
        cia_writer.write_header(header)
        cia_writer.write_cert_chain()
        cia_writer.write_ticket(ticket_data)
        cia_writer.write_tmd(tmd_data)
        content_hash = cia_writer.write_content(content_data)
        cia_writer.write_meta(meta_data)

        # Assert
        file_obj.seek(0)
        all_data = file_obj.read()
        assert len(all_data) > 0

        # Verify header
        (header_size,) = struct.unpack("<I", all_data[0x00:0x04])
        assert header_size == 0x2020

        # Verify cert chain is present
        assert all_data[0x2020 : 0x2020 + 4] == b"CERT"

        # Verify content hash was computed
        assert len(content_hash) == 32
        expected_hash = hashlib.sha256(content_data).digest()
        assert content_hash == expected_hash
