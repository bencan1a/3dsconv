"""Tests for encryption state models."""

import pytest

from dsconv.models.encryption import EncryptionContext, EncryptionType


class TestEncryptionType:
    """Tests for EncryptionType enum."""

    def test_enum_has_three_values(self):
        """Test that EncryptionType enum has exactly three values."""
        # Arrange & Act
        values = list(EncryptionType)

        # Assert
        assert len(values) == 3

    def test_decrypted_value(self):
        """Test DECRYPTED enum value."""
        # Act & Assert
        assert EncryptionType.DECRYPTED.value == "decrypted"

    def test_zerokey_value(self):
        """Test ZEROKEY enum value."""
        # Act & Assert
        assert EncryptionType.ZEROKEY.value == "zerokey"

    def test_original_ncch_value(self):
        """Test ORIGINAL_NCCH enum value."""
        # Act & Assert
        assert EncryptionType.ORIGINAL_NCCH.value == "original_ncch"

    def test_enum_members_are_unique(self):
        """Test that all enum members have unique values."""
        # Arrange
        values = [member.value for member in EncryptionType]

        # Act & Assert
        assert len(values) == len(set(values))

    def test_can_compare_enum_members(self):
        """Test that enum members can be compared."""
        # Act & Assert
        assert EncryptionType.DECRYPTED == EncryptionType.DECRYPTED
        assert EncryptionType.DECRYPTED != EncryptionType.ZEROKEY
        assert EncryptionType.ZEROKEY != EncryptionType.ORIGINAL_NCCH


class TestEncryptionContext:
    """Tests for EncryptionContext dataclass."""

    def test_create_with_valid_data_decrypted(self):
        """Test creating context with valid decrypted data."""
        # Arrange
        encryption_type = EncryptionType.DECRYPTED
        normal_key = None
        title_id = b"\x00" * 8

        # Act
        ctx = EncryptionContext(
            encryption_type=encryption_type, normal_key=normal_key, title_id=title_id
        )

        # Assert
        assert ctx.encryption_type == EncryptionType.DECRYPTED
        assert ctx.normal_key is None
        assert ctx.title_id == title_id

    def test_create_with_valid_data_zerokey(self):
        """Test creating context with valid zero-key data."""
        # Arrange
        encryption_type = EncryptionType.ZEROKEY
        normal_key = bytes(16)  # 16 bytes of zeros
        title_id = b"\x01\x02\x03\x04\x05\x06\x07\x08"

        # Act
        ctx = EncryptionContext(
            encryption_type=encryption_type, normal_key=normal_key, title_id=title_id
        )

        # Assert
        assert ctx.encryption_type == EncryptionType.ZEROKEY
        assert ctx.normal_key == normal_key
        assert ctx.title_id == title_id

    def test_create_with_valid_data_original_ncch(self):
        """Test creating context with valid original NCCH data."""
        # Arrange
        encryption_type = EncryptionType.ORIGINAL_NCCH
        normal_key = b"\xff" * 16
        title_id = b"\xaa" * 8

        # Act
        ctx = EncryptionContext(
            encryption_type=encryption_type, normal_key=normal_key, title_id=title_id
        )

        # Assert
        assert ctx.encryption_type == EncryptionType.ORIGINAL_NCCH
        assert ctx.normal_key == normal_key
        assert ctx.title_id == title_id

    def test_create_with_wrong_title_id_length_raises_error(self):
        """Test creating context with wrong title_id length raises ValueError."""
        # Arrange
        encryption_type = EncryptionType.DECRYPTED
        normal_key = None
        title_id = b"\x00" * 4  # Too short

        # Act & Assert
        with pytest.raises(ValueError, match="title_id must be 8 bytes"):
            EncryptionContext(
                encryption_type=encryption_type, normal_key=normal_key, title_id=title_id
            )

    def test_create_with_empty_title_id_raises_error(self):
        """Test creating context with empty title_id raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="title_id must be 8 bytes"):
            EncryptionContext(
                encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=b""
            )

    def test_create_with_too_long_title_id_raises_error(self):
        """Test creating context with too long title_id raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="title_id must be 8 bytes"):
            EncryptionContext(
                encryption_type=EncryptionType.DECRYPTED,
                normal_key=None,
                title_id=b"\x00" * 16,  # Too long
            )

    def test_create_with_wrong_normal_key_length_raises_error(self):
        """Test creating context with wrong normal_key length raises ValueError."""
        # Arrange
        encryption_type = EncryptionType.ORIGINAL_NCCH
        normal_key = b"\xff" * 8  # Too short
        title_id = b"\x00" * 8

        # Act & Assert
        with pytest.raises(ValueError, match="normal_key must be 16 bytes"):
            EncryptionContext(
                encryption_type=encryption_type, normal_key=normal_key, title_id=title_id
            )

    def test_create_with_too_long_normal_key_raises_error(self):
        """Test creating context with too long normal_key raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="normal_key must be 16 bytes"):
            EncryptionContext(
                encryption_type=EncryptionType.ORIGINAL_NCCH,
                normal_key=b"\xff" * 32,  # Too long
                title_id=b"\x00" * 8,
            )

    def test_create_with_invalid_encryption_type_raises_error(self):
        """Test creating context with invalid encryption_type raises TypeError."""
        # Arrange
        invalid_type = "decrypted"  # String instead of enum
        normal_key = None
        title_id = b"\x00" * 8

        # Act & Assert
        with pytest.raises(TypeError, match="encryption_type must be EncryptionType enum"):
            EncryptionContext(
                encryption_type=invalid_type, normal_key=normal_key, title_id=title_id
            )

    def test_create_with_none_encryption_type_raises_error(self):
        """Test creating context with None encryption_type raises TypeError."""
        # Act & Assert
        with pytest.raises(TypeError, match="encryption_type must be EncryptionType enum"):
            EncryptionContext(encryption_type=None, normal_key=None, title_id=b"\x00" * 8)

    def test_needs_decryption_property_with_decrypted(self):
        """Test needs_decryption returns False for DECRYPTED."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=b"\x00" * 8
        )

        # Act & Assert
        assert ctx.needs_decryption is False

    def test_needs_decryption_property_with_zerokey(self):
        """Test needs_decryption returns True for ZEROKEY."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ZEROKEY, normal_key=bytes(16), title_id=b"\x00" * 8
        )

        # Act & Assert
        assert ctx.needs_decryption is True

    def test_needs_decryption_property_with_original_ncch(self):
        """Test needs_decryption returns True for ORIGINAL_NCCH."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ORIGINAL_NCCH,
            normal_key=b"\xff" * 16,
            title_id=b"\x00" * 8,
        )

        # Act & Assert
        assert ctx.needs_decryption is True

    def test_is_decrypted_property_with_decrypted(self):
        """Test is_decrypted returns True for DECRYPTED."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=b"\x00" * 8
        )

        # Act & Assert
        assert ctx.is_decrypted is True

    def test_is_decrypted_property_with_zerokey(self):
        """Test is_decrypted returns False for ZEROKEY."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ZEROKEY, normal_key=bytes(16), title_id=b"\x00" * 8
        )

        # Act & Assert
        assert ctx.is_decrypted is False

    def test_is_decrypted_property_with_original_ncch(self):
        """Test is_decrypted returns False for ORIGINAL_NCCH."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ORIGINAL_NCCH,
            normal_key=b"\xff" * 16,
            title_id=b"\x00" * 8,
        )

        # Act & Assert
        assert ctx.is_decrypted is False

    def test_is_zerokey_property_with_zerokey(self):
        """Test is_zerokey returns True for ZEROKEY."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ZEROKEY, normal_key=bytes(16), title_id=b"\x00" * 8
        )

        # Act & Assert
        assert ctx.is_zerokey is True

    def test_is_zerokey_property_with_decrypted(self):
        """Test is_zerokey returns False for DECRYPTED."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=b"\x00" * 8
        )

        # Act & Assert
        assert ctx.is_zerokey is False

    def test_is_zerokey_property_with_original_ncch(self):
        """Test is_zerokey returns False for ORIGINAL_NCCH."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ORIGINAL_NCCH,
            normal_key=b"\xff" * 16,
            title_id=b"\x00" * 8,
        )

        # Act & Assert
        assert ctx.is_zerokey is False

    def test_is_original_ncch_property_with_original_ncch(self):
        """Test is_original_ncch returns True for ORIGINAL_NCCH."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ORIGINAL_NCCH,
            normal_key=b"\xff" * 16,
            title_id=b"\x00" * 8,
        )

        # Act & Assert
        assert ctx.is_original_ncch is True

    def test_is_original_ncch_property_with_decrypted(self):
        """Test is_original_ncch returns False for DECRYPTED."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=b"\x00" * 8
        )

        # Act & Assert
        assert ctx.is_original_ncch is False

    def test_is_original_ncch_property_with_zerokey(self):
        """Test is_original_ncch returns False for ZEROKEY."""
        # Arrange
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ZEROKEY, normal_key=bytes(16), title_id=b"\x00" * 8
        )

        # Act & Assert
        assert ctx.is_original_ncch is False

    @pytest.mark.parametrize(
        "encryption_type,needs_decryption",
        [
            (EncryptionType.DECRYPTED, False),
            (EncryptionType.ZEROKEY, True),
            (EncryptionType.ORIGINAL_NCCH, True),
        ],
    )
    def test_needs_decryption_for_all_types(self, encryption_type, needs_decryption):
        """Test needs_decryption property for all encryption types."""
        # Arrange
        normal_key = b"\xff" * 16 if encryption_type != EncryptionType.DECRYPTED else None
        ctx = EncryptionContext(
            encryption_type=encryption_type, normal_key=normal_key, title_id=b"\x00" * 8
        )

        # Act & Assert
        assert ctx.needs_decryption == needs_decryption

    @pytest.mark.parametrize(
        "title_id",
        [
            b"\x00" * 8,
            b"\xff" * 8,
            b"\x01\x02\x03\x04\x05\x06\x07\x08",
            b"\xaa\xbb\xcc\xdd\xee\xff\x00\x11",
        ],
    )
    def test_create_with_various_valid_title_ids(self, title_id):
        """Test creating context with various valid title IDs."""
        # Act
        ctx = EncryptionContext(
            encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=title_id
        )

        # Assert
        assert ctx.title_id == title_id

    @pytest.mark.parametrize(
        "normal_key",
        [
            b"\x00" * 16,
            b"\xff" * 16,
            b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10",
        ],
    )
    def test_create_with_various_valid_normal_keys(self, normal_key):
        """Test creating context with various valid normal keys."""
        # Act
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ORIGINAL_NCCH,
            normal_key=normal_key,
            title_id=b"\x00" * 8,
        )

        # Assert
        assert ctx.normal_key == normal_key

    def test_normal_key_can_be_none_for_decrypted(self):
        """Test that normal_key can be None for DECRYPTED type."""
        # Act
        ctx = EncryptionContext(
            encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=b"\x00" * 8
        )

        # Assert
        assert ctx.normal_key is None
        assert ctx.encryption_type == EncryptionType.DECRYPTED

    def test_normal_key_can_be_none_for_zerokey(self):
        """Test that normal_key can be None for ZEROKEY type (key derived later)."""
        # Act
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ZEROKEY, normal_key=None, title_id=b"\x00" * 8
        )

        # Assert
        assert ctx.normal_key is None
        assert ctx.encryption_type == EncryptionType.ZEROKEY

    def test_normal_key_can_be_none_for_original_ncch(self):
        """Test that normal_key can be None for ORIGINAL_NCCH (key derived later)."""
        # Act
        ctx = EncryptionContext(
            encryption_type=EncryptionType.ORIGINAL_NCCH, normal_key=None, title_id=b"\x00" * 8
        )

        # Assert
        assert ctx.normal_key is None
        assert ctx.encryption_type == EncryptionType.ORIGINAL_NCCH
