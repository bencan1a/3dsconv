"""Tests for NCCH header models."""

import struct

import pytest

from dsconv.models.ncch import NCCHHeader


class TestNCCHHeader:
    """Tests for NCCHHeader model."""

    def test_create_with_valid_data(self):
        """Test creating header with valid data."""
        # Arrange
        signature = bytes(0x100)
        magic = b"NCCH"
        content_size = 0x1000
        partition_id = bytes(8)
        maker_code = b"01"
        version = 0
        program_id = bytes(8)
        extheader_hash = bytes(0x20)
        extheader_size = 0x400
        flags = bytes(8)
        exefs_offset = 0x1000
        exefs_size = 0x200

        # Act
        header = NCCHHeader(
            signature=signature,
            magic=magic,
            content_size=content_size,
            partition_id=partition_id,
            maker_code=maker_code,
            version=version,
            program_id=program_id,
            extheader_hash=extheader_hash,
            extheader_size=extheader_size,
            flags=flags,
            exefs_offset=exefs_offset,
            exefs_size=exefs_size,
        )

        # Assert
        assert header.magic == b"NCCH"
        assert header.content_size == 0x1000
        assert header.partition_id == partition_id
        assert header.maker_code == maker_code
        assert header.version == 0
        assert header.program_id == program_id
        assert header.extheader_hash == extheader_hash
        assert header.extheader_size == 0x400
        assert header.flags == flags
        assert header.exefs_offset == 0x1000
        assert header.exefs_size == 0x200

    def test_create_with_invalid_magic_raises_error(self):
        """Test creating header with invalid magic raises ValueError."""
        with pytest.raises(ValueError, match="Invalid NCCH magic"):
            NCCHHeader(
                signature=bytes(0x100),
                magic=b"XXXX",  # Invalid
                content_size=0x1000,
                partition_id=bytes(8),
                maker_code=b"01",
                version=0,
                program_id=bytes(8),
                extheader_hash=bytes(0x20),
                extheader_size=0x400,
                flags=bytes(8),
                exefs_offset=0x1000,
                exefs_size=0x200,
            )

    def test_create_with_wrong_magic_length_raises_error(self):
        """Test creating header with wrong magic length raises ValueError."""
        with pytest.raises(ValueError, match="magic must be 4 bytes"):
            NCCHHeader(
                signature=bytes(0x100),
                magic=b"NC",  # Too short
                content_size=0x1000,
                partition_id=bytes(8),
                maker_code=b"01",
                version=0,
                program_id=bytes(8),
                extheader_hash=bytes(0x20),
                extheader_size=0x400,
                flags=bytes(8),
                exefs_offset=0x1000,
                exefs_size=0x200,
            )

    def test_create_with_wrong_signature_length_raises_error(self):
        """Test creating header with wrong signature length raises ValueError."""
        with pytest.raises(ValueError, match="signature must be 0x100 bytes"):
            NCCHHeader(
                signature=bytes(0x50),  # Too short
                magic=b"NCCH",
                content_size=0x1000,
                partition_id=bytes(8),
                maker_code=b"01",
                version=0,
                program_id=bytes(8),
                extheader_hash=bytes(0x20),
                extheader_size=0x400,
                flags=bytes(8),
                exefs_offset=0x1000,
                exefs_size=0x200,
            )

    def test_create_with_wrong_partition_id_length_raises_error(self):
        """Test creating header with wrong partition_id length raises ValueError."""
        with pytest.raises(ValueError, match="partition_id must be 8 bytes"):
            NCCHHeader(
                signature=bytes(0x100),
                magic=b"NCCH",
                content_size=0x1000,
                partition_id=bytes(4),  # Too short
                maker_code=b"01",
                version=0,
                program_id=bytes(8),
                extheader_hash=bytes(0x20),
                extheader_size=0x400,
                flags=bytes(8),
                exefs_offset=0x1000,
                exefs_size=0x200,
            )

    def test_create_with_wrong_maker_code_length_raises_error(self):
        """Test creating header with wrong maker_code length raises ValueError."""
        with pytest.raises(ValueError, match="maker_code must be 2 bytes"):
            NCCHHeader(
                signature=bytes(0x100),
                magic=b"NCCH",
                content_size=0x1000,
                partition_id=bytes(8),
                maker_code=b"0",  # Too short
                version=0,
                program_id=bytes(8),
                extheader_hash=bytes(0x20),
                extheader_size=0x400,
                flags=bytes(8),
                exefs_offset=0x1000,
                exefs_size=0x200,
            )

    def test_create_with_wrong_program_id_length_raises_error(self):
        """Test creating header with wrong program_id length raises ValueError."""
        with pytest.raises(ValueError, match="program_id must be 8 bytes"):
            NCCHHeader(
                signature=bytes(0x100),
                magic=b"NCCH",
                content_size=0x1000,
                partition_id=bytes(8),
                maker_code=b"01",
                version=0,
                program_id=bytes(4),  # Too short
                extheader_hash=bytes(0x20),
                extheader_size=0x400,
                flags=bytes(8),
                exefs_offset=0x1000,
                exefs_size=0x200,
            )

    def test_create_with_wrong_extheader_hash_length_raises_error(self):
        """Test creating header with wrong extheader_hash length raises ValueError."""
        with pytest.raises(ValueError, match="extheader_hash must be 0x20 bytes"):
            NCCHHeader(
                signature=bytes(0x100),
                magic=b"NCCH",
                content_size=0x1000,
                partition_id=bytes(8),
                maker_code=b"01",
                version=0,
                program_id=bytes(8),
                extheader_hash=bytes(0x10),  # Too short
                extheader_size=0x400,
                flags=bytes(8),
                exefs_offset=0x1000,
                exefs_size=0x200,
            )

    def test_create_with_wrong_flags_length_raises_error(self):
        """Test creating header with wrong flags length raises ValueError."""
        with pytest.raises(ValueError, match="flags must be 8 bytes"):
            NCCHHeader(
                signature=bytes(0x100),
                magic=b"NCCH",
                content_size=0x1000,
                partition_id=bytes(8),
                maker_code=b"01",
                version=0,
                program_id=bytes(8),
                extheader_hash=bytes(0x20),
                extheader_size=0x400,
                flags=bytes(4),  # Too short
                exefs_offset=0x1000,
                exefs_size=0x200,
            )

    def test_is_encrypted_property_with_encrypted_content(self):
        """Test is_encrypted returns True for encrypted content."""
        # Arrange - flags with bit 2 = 0 (encrypted)
        flags = bytes(8)  # All zeros, bit 2 of byte 7 = 0

        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=flags,
            exefs_offset=0x1000,
            exefs_size=0x200,
        )

        # Act & Assert
        assert header.is_encrypted is True

    def test_is_encrypted_property_with_decrypted_content(self):
        """Test is_encrypted returns False for decrypted content."""
        # Arrange - flags with bit 2 = 1 (decrypted)
        flags = bytes([0, 0, 0, 0, 0, 0, 0, 0x04])  # Byte 7 has bit 2 set

        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=flags,
            exefs_offset=0x1000,
            exefs_size=0x200,
        )

        # Act & Assert
        assert header.is_encrypted is False

    def test_uses_zerokey_property_with_zerokey_encryption(self):
        """Test uses_zerokey property with zero-key encryption."""
        # Arrange - flags with bit 0 = 1 (zerokey)
        flags = bytes([0, 0, 0, 0, 0, 0, 0, 0x01])  # Byte 7 has bit 0 set

        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=flags,
            exefs_offset=0x1000,
            exefs_size=0x200,
        )

        # Act & Assert
        assert header.uses_zerokey is True

    def test_uses_zerokey_property_without_zerokey_encryption(self):
        """Test uses_zerokey property without zero-key encryption."""
        # Arrange - flags with bit 0 = 0 (not zerokey)
        flags = bytes(8)  # All zeros

        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=flags,
            exefs_offset=0x1000,
            exefs_size=0x200,
        )

        # Act & Assert
        assert header.uses_zerokey is False

    def test_size_bytes_property(self):
        """Test size_bytes property."""
        # Arrange
        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x10,  # 0x10 media units
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=bytes(8),
            exefs_offset=0x1000,
            exefs_size=0x200,
        )

        # Act & Assert
        # 0x10 * 0x200 = 0x2000
        assert header.size_bytes == 0x2000

    def test_title_id_property(self):
        """Test title_id property returns program_id."""
        # Arrange
        program_id = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=program_id,
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=bytes(8),
            exefs_offset=0x1000,
            exefs_size=0x200,
        )

        # Act & Assert
        assert header.title_id == program_id

    def test_from_bytes_with_valid_data(self):
        """Test creating header from binary data."""
        # Arrange - create minimal valid NCCH header
        data = bytearray(0x200)

        # Signature (0x000-0x100)
        data[0x000:0x100] = bytes(0x100)

        # Magic (0x100-0x104)
        data[0x100:0x104] = b"NCCH"

        # Content size (0x104-0x108, little-endian)
        data[0x104:0x108] = struct.pack("<I", 0x1000)

        # Partition ID (0x108-0x110)
        data[0x108:0x110] = b"\x01\x02\x03\x04\x05\x06\x07\x08"

        # Maker code (0x110-0x112)
        data[0x110:0x112] = b"01"

        # Version (0x112-0x114, little-endian)
        data[0x112:0x114] = struct.pack("<H", 2)

        # Program ID (0x118-0x120)
        data[0x118:0x120] = b"\x10\x20\x30\x40\x50\x60\x70\x80"

        # Extended header hash (0x160-0x180)
        data[0x160:0x180] = bytes(0x20)

        # Extended header size (0x180-0x184, little-endian)
        data[0x180:0x184] = struct.pack("<I", 0x400)

        # Flags (0x188-0x190)
        data[0x188:0x190] = bytes(8)
        data[0x18F] = 0x04  # Decrypted flag

        # ExeFS offset (0x1A0-0x1A4, little-endian)
        data[0x1A0:0x1A4] = struct.pack("<I", 0x2000)

        # ExeFS size (0x1A4-0x1A8, little-endian)
        data[0x1A4:0x1A8] = struct.pack("<I", 0x300)

        # Act
        header = NCCHHeader.from_bytes(bytes(data))

        # Assert
        assert header.magic == b"NCCH"
        assert header.content_size == 0x1000
        assert header.partition_id == b"\x01\x02\x03\x04\x05\x06\x07\x08"
        assert header.maker_code == b"01"
        assert header.version == 2
        assert header.program_id == b"\x10\x20\x30\x40\x50\x60\x70\x80"
        assert len(header.extheader_hash) == 0x20
        assert header.extheader_size == 0x400
        assert header.flags[7] == 0x04
        assert header.exefs_offset == 0x2000
        assert header.exefs_size == 0x300

    def test_from_bytes_with_short_data_raises_error(self):
        """Test from_bytes with insufficient data raises ValueError."""
        # Arrange
        data = bytes(0x100)  # Too short (need 0x200)

        # Act & Assert
        with pytest.raises(ValueError, match="Data too short"):
            NCCHHeader.from_bytes(data)

    @pytest.mark.parametrize(
        "flags,is_encrypted,uses_zerokey",
        [
            (bytes([0, 0, 0, 0, 0, 0, 0, 0x00]), True, False),  # Encrypted, not zerokey
            (bytes([0, 0, 0, 0, 0, 0, 0, 0x01]), True, True),  # Encrypted with zerokey
            (bytes([0, 0, 0, 0, 0, 0, 0, 0x04]), False, False),  # Decrypted
            (bytes([0, 0, 0, 0, 0, 0, 0, 0x05]), False, True),  # Decrypted (zerokey flag set)
        ],
    )
    def test_encryption_flag_combinations(self, flags, is_encrypted, uses_zerokey):
        """Test various encryption flag combinations."""
        # Arrange
        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=flags,
            exefs_offset=0x1000,
            exefs_size=0x200,
        )

        # Act & Assert
        assert header.is_encrypted == is_encrypted
        assert header.uses_zerokey == uses_zerokey

    @pytest.mark.parametrize(
        "content_size,expected_bytes",
        [
            (0, 0),
            (1, 0x200),
            (10, 0x1400),
            (0x10, 0x2000),
            (0x100, 0x20000),
            (0x1000, 0x200000),
        ],
    )
    def test_size_bytes_with_various_sizes(self, content_size, expected_bytes):
        """Test size_bytes with various content sizes."""
        # Arrange
        header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=content_size,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=bytes(8),
            exefs_offset=0x1000,
            exefs_size=0x200,
        )

        # Act & Assert
        assert header.size_bytes == expected_bytes

    def test_from_bytes_roundtrip(self):
        """Test that from_bytes correctly parses a header created from data."""
        # Arrange - create complete valid NCCH header data
        data = bytearray(0x200)

        # Fill with test data
        data[0x000:0x100] = bytes(0x100)  # Signature
        data[0x100:0x104] = b"NCCH"  # Magic
        data[0x104:0x108] = struct.pack("<I", 0x5000)  # Content size
        data[0x108:0x110] = b"PARTITIO"  # Partition ID
        data[0x110:0x112] = b"MK"  # Maker code
        data[0x112:0x114] = struct.pack("<H", 5)  # Version
        data[0x118:0x120] = b"TITLEID!"  # Program ID
        data[0x160:0x180] = b"H" * 0x20  # ExtHeader hash
        data[0x180:0x184] = struct.pack("<I", 0x800)  # ExtHeader size
        data[0x188:0x190] = b"\x00\x01\x02\x03\x04\x05\x06\x07"  # Flags
        data[0x1A0:0x1A4] = struct.pack("<I", 0x3000)  # ExeFS offset
        data[0x1A4:0x1A8] = struct.pack("<I", 0x4000)  # ExeFS size

        # Act
        header = NCCHHeader.from_bytes(bytes(data))

        # Assert - verify all fields were parsed correctly
        assert header.signature == bytes(0x100)
        assert header.magic == b"NCCH"
        assert header.content_size == 0x5000
        assert header.partition_id == b"PARTITIO"
        assert header.maker_code == b"MK"
        assert header.version == 5
        assert header.program_id == b"TITLEID!"
        assert header.extheader_hash == b"H" * 0x20
        assert header.extheader_size == 0x800
        assert header.flags == b"\x00\x01\x02\x03\x04\x05\x06\x07"
        assert header.exefs_offset == 0x3000
        assert header.exefs_size == 0x4000
