"""Tests for CIA structure models."""

import struct

import pytest

from dsconv.models.cia import CIAContent, CIAHeader


class TestCIAHeader:
    """Tests for CIAHeader model."""

    def test_create_with_valid_data(self):
        """Test creating header with valid data."""
        # Arrange
        header_size = 0x2020
        type_ = 0
        version = 0
        cert_chain_size = 0xA00
        ticket_size = 0x350
        tmd_size = 0xB34
        meta_size = 0x3AC0
        content_size = 0x100000
        content_index = bytes(0x2000)

        # Act
        header = CIAHeader(
            header_size=header_size,
            type_=type_,
            version=version,
            cert_chain_size=cert_chain_size,
            ticket_size=ticket_size,
            tmd_size=tmd_size,
            meta_size=meta_size,
            content_size=content_size,
            content_index=content_index,
        )

        # Assert
        assert header.header_size == 0x2020
        assert header.type_ == 0
        assert header.version == 0
        assert header.cert_chain_size == 0xA00
        assert header.ticket_size == 0x350
        assert header.tmd_size == 0xB34
        assert header.meta_size == 0x3AC0
        assert header.content_size == 0x100000
        assert header.content_index == content_index

    def test_create_with_invalid_header_size_raises_error(self):
        """Test creating header with invalid header_size raises ValueError."""
        with pytest.raises(ValueError, match="header_size must be 0x2020"):
            CIAHeader(
                header_size=0x1000,  # Invalid
                type_=0,
                version=0,
                cert_chain_size=0xA00,
                ticket_size=0x350,
                tmd_size=0xB34,
                meta_size=0x3AC0,
                content_size=0x100000,
                content_index=bytes(0x2000),
            )

    def test_create_with_negative_cert_chain_size_raises_error(self):
        """Test creating header with negative cert_chain_size raises ValueError."""
        with pytest.raises(ValueError, match="cert_chain_size must be non-negative"):
            CIAHeader(
                header_size=0x2020,
                type_=0,
                version=0,
                cert_chain_size=-1,  # Invalid
                ticket_size=0x350,
                tmd_size=0xB34,
                meta_size=0x3AC0,
                content_size=0x100000,
                content_index=bytes(0x2000),
            )

    def test_create_with_wrong_content_index_length_raises_error(self):
        """Test creating header with wrong content_index length raises ValueError."""
        with pytest.raises(ValueError, match="content_index must be 0x2000 bytes"):
            CIAHeader(
                header_size=0x2020,
                type_=0,
                version=0,
                cert_chain_size=0xA00,
                ticket_size=0x350,
                tmd_size=0xB34,
                meta_size=0x3AC0,
                content_size=0x100000,
                content_index=bytes(0x100),  # Too short
            )

    def test_create_with_invalid_type_raises_error(self):
        """Test creating header with invalid type_ raises ValueError."""
        with pytest.raises(ValueError, match="type_ must be uint16"):
            CIAHeader(
                header_size=0x2020,
                type_=0x10000,  # Too large for uint16
                version=0,
                cert_chain_size=0xA00,
                ticket_size=0x350,
                tmd_size=0xB34,
                meta_size=0x3AC0,
                content_size=0x100000,
                content_index=bytes(0x2000),
            )

    def test_create_with_invalid_version_raises_error(self):
        """Test creating header with invalid version raises ValueError."""
        with pytest.raises(ValueError, match="version must be uint16"):
            CIAHeader(
                header_size=0x2020,
                type_=0,
                version=0x10000,  # Too large for uint16
                cert_chain_size=0xA00,
                ticket_size=0x350,
                tmd_size=0xB34,
                meta_size=0x3AC0,
                content_size=0x100000,
                content_index=bytes(0x2000),
            )

    def test_create_with_negative_ticket_size_raises_error(self):
        """Test creating header with negative ticket_size raises ValueError."""
        with pytest.raises(ValueError, match="ticket_size must be non-negative"):
            CIAHeader(
                header_size=0x2020,
                type_=0,
                version=0,
                cert_chain_size=0xA00,
                ticket_size=-1,  # Invalid
                tmd_size=0xB34,
                meta_size=0x3AC0,
                content_size=0x100000,
                content_index=bytes(0x2000),
            )

    def test_create_with_negative_tmd_size_raises_error(self):
        """Test creating header with negative tmd_size raises ValueError."""
        with pytest.raises(ValueError, match="tmd_size must be non-negative"):
            CIAHeader(
                header_size=0x2020,
                type_=0,
                version=0,
                cert_chain_size=0xA00,
                ticket_size=0x350,
                tmd_size=-1,  # Invalid
                meta_size=0x3AC0,
                content_size=0x100000,
                content_index=bytes(0x2000),
            )

    def test_create_with_negative_meta_size_raises_error(self):
        """Test creating header with negative meta_size raises ValueError."""
        with pytest.raises(ValueError, match="meta_size must be non-negative"):
            CIAHeader(
                header_size=0x2020,
                type_=0,
                version=0,
                cert_chain_size=0xA00,
                ticket_size=0x350,
                tmd_size=0xB34,
                meta_size=-1,  # Invalid
                content_size=0x100000,
                content_index=bytes(0x2000),
            )

    def test_create_with_negative_content_size_raises_error(self):
        """Test creating header with negative content_size raises ValueError."""
        with pytest.raises(ValueError, match="content_size must be non-negative"):
            CIAHeader(
                header_size=0x2020,
                type_=0,
                version=0,
                cert_chain_size=0xA00,
                ticket_size=0x350,
                tmd_size=0xB34,
                meta_size=0x3AC0,
                content_size=-1,  # Invalid
                content_index=bytes(0x2000),
            )

    def test_num_contents_property_with_no_contents(self):
        """Test num_contents property when no contents are set."""
        # Arrange - content_index with all zeros
        content_index = bytes(0x2000)
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

        # Act & Assert
        assert header.num_contents == 0

    def test_num_contents_property_with_one_content(self):
        """Test num_contents property with one content."""
        # Arrange - content_index with bit 7 set (content 0)
        content_index = bytes([0b10000000]) + bytes(0x1FFF)
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

        # Act & Assert
        assert header.num_contents == 1

    def test_num_contents_property_with_three_contents(self):
        """Test num_contents property with three contents."""
        # Arrange - content_index with bits 7, 6, 5 set (contents 0, 1, 2)
        content_index = bytes([0b11100000]) + bytes(0x1FFF)
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

        # Act & Assert
        assert header.num_contents == 3

    def test_has_multiple_contents_property_with_single_content(self):
        """Test has_multiple_contents returns False with single content."""
        # Arrange
        content_index = bytes([0b10000000]) + bytes(0x1FFF)
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

        # Act & Assert
        assert header.has_multiple_contents is False

    def test_has_multiple_contents_property_with_multiple_contents(self):
        """Test has_multiple_contents returns True with multiple contents."""
        # Arrange
        content_index = bytes([0b11000000]) + bytes(0x1FFF)
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

        # Act & Assert
        assert header.has_multiple_contents is True

    def test_cert_chain_offset_property(self):
        """Test cert_chain_offset property."""
        # Arrange
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

        # Act & Assert
        assert header.cert_chain_offset == 0x2020

    def test_ticket_offset_property(self):
        """Test ticket_offset property."""
        # Arrange
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
        ticket_offset = header.ticket_offset

        # Assert
        # Cert chain offset (0x2020) + cert chain size (0xA00) = 0x2A20
        # Aligned to 64 bytes: 0x2A40
        assert ticket_offset == 0x2A40

    def test_tmd_offset_property(self):
        """Test tmd_offset property."""
        # Arrange
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
        tmd_offset = header.tmd_offset

        # Assert
        # Ticket offset (0x2A40) + ticket size (0x350) = 0x2D90
        # Aligned to 64 bytes: 0x2DC0
        assert tmd_offset == 0x2DC0

    def test_content_offset_property(self):
        """Test content_offset property."""
        # Arrange
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
        content_offset = header.content_offset

        # Assert
        # TMD offset (0x2DC0) + TMD size (0xB34) = 0x38F4
        # Aligned to 64 bytes: 0x3900
        assert content_offset == 0x3900

    def test_meta_offset_property(self):
        """Test meta_offset property."""
        # Arrange
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
        meta_offset = header.meta_offset

        # Assert
        # Content offset (0x3900) + content size (0x100000) = 0x103900
        # Aligned to 64 bytes: 0x103900 (already aligned)
        assert meta_offset == 0x103900

    def test_from_bytes_with_valid_data(self):
        """Test creating header from binary data."""
        # Arrange - create minimal valid CIA header
        data = bytearray(0x2020)

        # Pack header fields
        struct.pack_into("<I", data, 0x00, 0x2020)  # header_size
        struct.pack_into("<H", data, 0x04, 0)  # type_
        struct.pack_into("<H", data, 0x06, 0)  # version
        struct.pack_into("<I", data, 0x08, 0xA00)  # cert_chain_size
        struct.pack_into("<I", data, 0x0C, 0x350)  # ticket_size
        struct.pack_into("<I", data, 0x10, 0xB34)  # tmd_size
        struct.pack_into("<I", data, 0x14, 0x3AC0)  # meta_size
        struct.pack_into("<Q", data, 0x18, 0x100000)  # content_size
        # content_index is already all zeros

        # Act
        header = CIAHeader.from_bytes(bytes(data))

        # Assert
        assert header.header_size == 0x2020
        assert header.type_ == 0
        assert header.version == 0
        assert header.cert_chain_size == 0xA00
        assert header.ticket_size == 0x350
        assert header.tmd_size == 0xB34
        assert header.meta_size == 0x3AC0
        assert header.content_size == 0x100000
        assert len(header.content_index) == 0x2000

    def test_from_bytes_with_short_data_raises_error(self):
        """Test from_bytes with insufficient data raises ValueError."""
        # Arrange
        data = bytes(0x100)  # Too short

        # Act & Assert
        with pytest.raises(ValueError, match="Data too short"):
            CIAHeader.from_bytes(data)

    @pytest.mark.parametrize(
        "header_size,type_,version,cert_size,ticket_size,tmd_size,meta_size,content_size",
        [
            (0x2020, 0, 0, 0xA00, 0x350, 0xB34, 0x3AC0, 0),  # Zero content size
            (0x2020, 1, 0, 0xA00, 0x350, 0xB34, 0x3AC0, 0x100000),  # Different type
            (0x2020, 0, 1, 0xA00, 0x350, 0xB34, 0x3AC0, 0x100000),  # Different version
            (0x2020, 0, 0, 0xB00, 0x350, 0xB34, 0x3AC0, 0x100000),  # Different cert size
            (0x2020, 0, 0, 0xA00, 0x350, 0xB64, 0x3AC0, 0x100000),  # TMD with 2 contents
            (0x2020, 0, 0, 0xA00, 0x350, 0xB94, 0x3AC0, 0x100000),  # TMD with 3 contents
        ],
    )
    def test_from_bytes_with_various_values(
        self,
        header_size,
        type_,
        version,
        cert_size,
        ticket_size,
        tmd_size,
        meta_size,
        content_size,
    ):
        """Test from_bytes with various valid values."""
        # Arrange
        data = bytearray(0x2020)
        struct.pack_into("<I", data, 0x00, header_size)
        struct.pack_into("<H", data, 0x04, type_)
        struct.pack_into("<H", data, 0x06, version)
        struct.pack_into("<I", data, 0x08, cert_size)
        struct.pack_into("<I", data, 0x0C, ticket_size)
        struct.pack_into("<I", data, 0x10, tmd_size)
        struct.pack_into("<I", data, 0x14, meta_size)
        struct.pack_into("<Q", data, 0x18, content_size)

        # Act
        header = CIAHeader.from_bytes(bytes(data))

        # Assert
        assert header.header_size == header_size
        assert header.type_ == type_
        assert header.version == version
        assert header.cert_chain_size == cert_size
        assert header.ticket_size == ticket_size
        assert header.tmd_size == tmd_size
        assert header.meta_size == meta_size
        assert header.content_size == content_size


class TestCIAContent:
    """Tests for CIAContent model."""

    def test_create_with_valid_data(self):
        """Test creating content with valid data."""
        # Arrange
        content_id = 0
        index = 0
        content_type = 0x0001  # Encrypted
        size = 0x100000
        hash_value = bytes(32)

        # Act
        content = CIAContent(
            content_id=content_id,
            index=index,
            content_type=content_type,
            size=size,
            hash=hash_value,
        )

        # Assert
        assert content.content_id == 0
        assert content.index == 0
        assert content.content_type == 0x0001
        assert content.size == 0x100000
        assert content.hash == hash_value

    def test_create_with_negative_size_raises_error(self):
        """Test creating content with negative size raises ValueError."""
        with pytest.raises(ValueError, match="size must be non-negative"):
            CIAContent(
                content_id=0,
                index=0,
                content_type=0,
                size=-1,  # Invalid
                hash=bytes(32),
            )

    def test_create_with_wrong_hash_length_raises_error(self):
        """Test creating content with wrong hash length raises ValueError."""
        with pytest.raises(ValueError, match="hash must be 32 bytes"):
            CIAContent(
                content_id=0,
                index=0,
                content_type=0,
                size=0x100000,
                hash=bytes(16),  # Too short
            )

    def test_create_with_invalid_content_id_raises_error(self):
        """Test creating content with invalid content_id raises ValueError."""
        with pytest.raises(ValueError, match="content_id must be uint32"):
            CIAContent(
                content_id=0x100000000,  # Too large for uint32
                index=0,
                content_type=0,
                size=0x100000,
                hash=bytes(32),
            )

    def test_create_with_invalid_index_raises_error(self):
        """Test creating content with invalid index raises ValueError."""
        with pytest.raises(ValueError, match="index must be uint16"):
            CIAContent(
                content_id=0,
                index=0x10000,  # Too large for uint16
                content_type=0,
                size=0x100000,
                hash=bytes(32),
            )

    def test_create_with_invalid_content_type_raises_error(self):
        """Test creating content with invalid content_type raises ValueError."""
        with pytest.raises(ValueError, match="content_type must be uint16"):
            CIAContent(
                content_id=0,
                index=0,
                content_type=0x10000,  # Too large for uint16
                size=0x100000,
                hash=bytes(32),
            )

    def test_is_encrypted_property_with_encrypted_content(self):
        """Test is_encrypted returns True for encrypted content."""
        # Arrange
        content = CIAContent(
            content_id=0,
            index=0,
            content_type=0x0001,  # Bit 0 set = encrypted
            size=0x100000,
            hash=bytes(32),
        )

        # Act & Assert
        assert content.is_encrypted is True

    def test_is_encrypted_property_with_unencrypted_content(self):
        """Test is_encrypted returns False for unencrypted content."""
        # Arrange
        content = CIAContent(
            content_id=0,
            index=0,
            content_type=0x0000,  # Bit 0 clear = not encrypted
            size=0x100000,
            hash=bytes(32),
        )

        # Act & Assert
        assert content.is_encrypted is False

    def test_is_optional_property_with_optional_content(self):
        """Test is_optional returns True for optional content."""
        # Arrange
        content = CIAContent(
            content_id=0,
            index=0,
            content_type=0x4000,  # Bit 14 set = optional
            size=0x100000,
            hash=bytes(32),
        )

        # Act & Assert
        assert content.is_optional is True

    def test_is_optional_property_with_required_content(self):
        """Test is_optional returns False for required content."""
        # Arrange
        content = CIAContent(
            content_id=0,
            index=0,
            content_type=0x0000,  # Bit 14 clear = required
            size=0x100000,
            hash=bytes(32),
        )

        # Act & Assert
        assert content.is_optional is False

    def test_is_shared_property_with_shared_content(self):
        """Test is_shared returns True for shared content."""
        # Arrange
        content = CIAContent(
            content_id=0,
            index=0,
            content_type=0x8000,  # Bit 15 set = shared
            size=0x100000,
            hash=bytes(32),
        )

        # Act & Assert
        assert content.is_shared is True

    def test_is_shared_property_with_non_shared_content(self):
        """Test is_shared returns False for non-shared content."""
        # Arrange
        content = CIAContent(
            content_id=0,
            index=0,
            content_type=0x0000,  # Bit 15 clear = not shared
            size=0x100000,
            hash=bytes(32),
        )

        # Act & Assert
        assert content.is_shared is False

    def test_from_bytes_with_valid_data(self):
        """Test creating content from binary data."""
        # Arrange - create minimal valid content record
        data = bytearray(0x30)

        # Pack content fields (big-endian for content records)
        struct.pack_into(">I", data, 0x00, 0)  # content_id
        struct.pack_into(">H", data, 0x04, 0)  # index
        struct.pack_into(">H", data, 0x06, 0x0001)  # content_type (encrypted)
        struct.pack_into(">Q", data, 0x08, 0x100000)  # size
        # hash is already all zeros (0x10-0x30)

        # Act
        content = CIAContent.from_bytes(bytes(data))

        # Assert
        assert content.content_id == 0
        assert content.index == 0
        assert content.content_type == 0x0001
        assert content.size == 0x100000
        assert len(content.hash) == 32

    def test_from_bytes_with_short_data_raises_error(self):
        """Test from_bytes with insufficient data raises ValueError."""
        # Arrange
        data = bytes(0x20)  # Too short

        # Act & Assert
        with pytest.raises(ValueError, match="Data too short"):
            CIAContent.from_bytes(data)

    @pytest.mark.parametrize(
        "content_id,index,content_type,size",
        [
            (0, 0, 0x0000, 0x100000),  # Game executable
            (1, 1, 0x0001, 0x50000),  # Manual (encrypted, index 1)
            (2, 2, 0x0001, 0x30000),  # DLP child (encrypted, index 2)
            (0xFFFFFFFF, 0xFFFF, 0xFFFF, 0xFFFFFFFFFFFFFFFF),  # Maximum values
        ],
    )
    def test_from_bytes_with_various_values(self, content_id, index, content_type, size):
        """Test from_bytes with various valid values."""
        # Arrange
        data = bytearray(0x30)
        struct.pack_into(">I", data, 0x00, content_id)
        struct.pack_into(">H", data, 0x04, index)
        struct.pack_into(">H", data, 0x06, content_type)
        struct.pack_into(">Q", data, 0x08, size)
        # Set a sample hash
        data[0x10:0x30] = bytes(range(32))

        # Act
        content = CIAContent.from_bytes(bytes(data))

        # Assert
        assert content.content_id == content_id
        assert content.index == index
        assert content.content_type == content_type
        assert content.size == size
        assert content.hash == bytes(range(32))

    @pytest.mark.parametrize(
        "content_type,is_encrypted,is_optional,is_shared",
        [
            (0x0000, False, False, False),  # No flags set
            (0x0001, True, False, False),  # Only encrypted
            (0x4000, False, True, False),  # Only optional
            (0x8000, False, False, True),  # Only shared
            (0x4001, True, True, False),  # Encrypted + optional
            (0x8001, True, False, True),  # Encrypted + shared
            (0xC000, False, True, True),  # Optional + shared
            (0xC001, True, True, True),  # All flags set
        ],
    )
    def test_content_type_flag_combinations(
        self, content_type, is_encrypted, is_optional, is_shared
    ):
        """Test various content_type flag combinations."""
        # Arrange
        content = CIAContent(
            content_id=0,
            index=0,
            content_type=content_type,
            size=0x100000,
            hash=bytes(32),
        )

        # Act & Assert
        assert content.is_encrypted == is_encrypted
        assert content.is_optional == is_optional
        assert content.is_shared == is_shared
