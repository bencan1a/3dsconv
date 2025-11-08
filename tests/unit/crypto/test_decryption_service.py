"""Tests for DecryptionService."""

import pytest

from dsconv.crypto import DecryptionService, IAESCipher, KeyDerivationService


class TestDecryptionService:
    """Tests for DecryptionService class."""

    @pytest.fixture
    def mock_key_derivation(self):
        """Create a mock KeyDerivationService.

        Returns a KeyDerivationService that derives keys by simply
        returning the KeyY value reversed (for testing purposes).
        """

        class MockKeyDerivation:
            """Mock key derivation for testing."""

            def derive_normal_key(self, key_y: bytes) -> bytes:
                """Return reversed KeyY as the derived key."""
                return key_y[::-1]

        return MockKeyDerivation()

    @pytest.fixture
    def mock_cipher_factory(self):
        """Create a mock AES cipher factory.

        Returns a factory that creates mock ciphers that track their
        parameters and perform simple XOR operations for testing.
        """

        class MockCipher(IAESCipher):
            """Mock cipher that tracks calls and performs XOR."""

            def __init__(self, key: bytes, counter_value: int):
                self.key = key
                self.counter_value = counter_value
                self.decrypt_called = False
                self.encrypt_called = False
                self.last_decrypt_input = b""
                self.last_encrypt_input = b""

            def decrypt(self, data: bytes) -> bytes:
                """Mock decrypt using XOR with 0xAA."""
                self.decrypt_called = True
                self.last_decrypt_input = data
                if not data:
                    return b""
                return bytes(b ^ 0xAA for b in data)

            def encrypt(self, data: bytes) -> bytes:
                """Mock encrypt using XOR with 0xAA."""
                self.encrypt_called = True
                self.last_encrypt_input = data
                if not data:
                    return b""
                return bytes(b ^ 0xAA for b in data)

        # Create a list to track all created ciphers
        created_ciphers = []

        def factory(key: bytes, counter_value: int) -> MockCipher:
            cipher = MockCipher(key, counter_value)
            created_ciphers.append(cipher)
            return cipher

        # Attach the list to the factory for test access
        factory.created_ciphers = created_ciphers  # type: ignore[attr-defined]
        return factory

    @pytest.fixture
    def service(self, mock_key_derivation, mock_cipher_factory):
        """Create a DecryptionService with mock dependencies."""
        return DecryptionService(mock_key_derivation, mock_cipher_factory)

    def test_init_stores_dependencies(self, mock_key_derivation, mock_cipher_factory):
        """Test that __init__ stores the provided dependencies."""
        service = DecryptionService(mock_key_derivation, mock_cipher_factory)

        assert service.key_derivation is mock_key_derivation
        assert service.aes_cipher_factory is mock_cipher_factory

    def test_decrypt_extheader_with_valid_inputs(self, service, mock_cipher_factory):
        """Test decrypt_extheader with valid inputs."""
        # Arrange
        encrypted_data = b"encrypted_extheader_data_here" + bytes(0x400 - 29)
        key_y = b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff"
        title_id = b"\x01\x02\x03\x04\x05\x06\x07\x08"

        # Act
        result = service.decrypt_extheader(encrypted_data, key_y, title_id)

        # Assert
        # Should have created exactly one cipher
        assert len(mock_cipher_factory.created_ciphers) == 1

        cipher = mock_cipher_factory.created_ciphers[0]

        # Verify the cipher was created with correct parameters
        # Key should be the reversed key_y (from our mock key derivation)
        assert cipher.key == key_y[::-1]

        # Counter should be: title_id || 0x01 || 0x00...00 (7 bytes)
        expected_counter_bytes = title_id + b"\x01" + bytes(7)
        expected_counter = int.from_bytes(expected_counter_bytes, byteorder="big")
        assert cipher.counter_value == expected_counter

        # Verify decrypt was called
        assert cipher.decrypt_called is True
        assert cipher.last_decrypt_input == encrypted_data

        # Result should be XOR'd data (from our mock cipher)
        expected_result = bytes(b ^ 0xAA for b in encrypted_data)
        assert result == expected_result

    def test_decrypt_extheader_with_empty_data(self, service, mock_cipher_factory):
        """Test decrypt_extheader with empty encrypted data."""
        # Arrange
        encrypted_data = b""
        key_y = b"\x00" * 16
        title_id = b"\x00" * 8

        # Act
        result = service.decrypt_extheader(encrypted_data, key_y, title_id)

        # Assert
        assert result == b""

    def test_decrypt_extheader_with_short_key_y_raises_error(self, service):
        """Test decrypt_extheader with invalid key_y length raises ValueError."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 15  # Too short
        title_id = b"\x00" * 8

        # Act & Assert
        with pytest.raises(ValueError, match="key_y must be 16 bytes"):
            service.decrypt_extheader(encrypted_data, key_y, title_id)

    def test_decrypt_extheader_with_long_key_y_raises_error(self, service):
        """Test decrypt_extheader with invalid key_y length raises ValueError."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 17  # Too long
        title_id = b"\x00" * 8

        # Act & Assert
        with pytest.raises(ValueError, match="key_y must be 16 bytes"):
            service.decrypt_extheader(encrypted_data, key_y, title_id)

    def test_decrypt_extheader_with_short_title_id_raises_error(self, service):
        """Test decrypt_extheader with invalid title_id length raises ValueError."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 16
        title_id = b"\x00" * 7  # Too short

        # Act & Assert
        with pytest.raises(ValueError, match="title_id must be 8 bytes"):
            service.decrypt_extheader(encrypted_data, key_y, title_id)

    def test_decrypt_extheader_with_long_title_id_raises_error(self, service):
        """Test decrypt_extheader with invalid title_id length raises ValueError."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 16
        title_id = b"\x00" * 9  # Too long

        # Act & Assert
        with pytest.raises(ValueError, match="title_id must be 8 bytes"):
            service.decrypt_extheader(encrypted_data, key_y, title_id)

    def test_decrypt_extheader_counter_calculation(self, service, mock_cipher_factory):
        """Test that decrypt_extheader calculates the counter correctly."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 16
        # Use a specific title ID to verify counter calculation
        title_id = b"\xff\xee\xdd\xcc\xbb\xaa\x99\x88"

        # Act
        service.decrypt_extheader(encrypted_data, key_y, title_id)

        # Assert
        cipher = mock_cipher_factory.created_ciphers[0]

        # Expected counter: title_id || 0x01 || 0x00...00 (7 bytes)
        expected_counter_bytes = title_id + b"\x01" + bytes(7)
        expected_counter = int.from_bytes(expected_counter_bytes, byteorder="big")

        assert cipher.counter_value == expected_counter

        # Verify the counter value is what we expect
        # 0xFFEEDDCCBBAA9988 0100000000000000 in big-endian
        assert expected_counter == 0xFFEEDDCCBBAA99880100000000000000

    def test_decrypt_exefs_with_valid_inputs_zero_offset(self, service, mock_cipher_factory):
        """Test decrypt_exefs with valid inputs and zero offset."""
        # Arrange
        encrypted_data = b"encrypted_exefs_data"
        key_y = b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc\xdd\xee\xff"
        title_id = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        offset_in_blocks = 0

        # Act
        result = service.decrypt_exefs(encrypted_data, key_y, title_id, offset_in_blocks)

        # Assert
        assert len(mock_cipher_factory.created_ciphers) == 1

        cipher = mock_cipher_factory.created_ciphers[0]

        # Key should be the reversed key_y
        assert cipher.key == key_y[::-1]

        # Counter should be: title_id || 0x02 || 0x00...00 (7 bytes) + offset
        expected_counter_bytes = title_id + b"\x02" + bytes(7)
        expected_counter = int.from_bytes(expected_counter_bytes, byteorder="big")
        expected_counter += offset_in_blocks
        assert cipher.counter_value == expected_counter

        # Verify decrypt was called
        assert cipher.decrypt_called is True
        assert cipher.last_decrypt_input == encrypted_data

        # Result should be XOR'd data
        expected_result = bytes(b ^ 0xAA for b in encrypted_data)
        assert result == expected_result

    def test_decrypt_exefs_with_nonzero_offset(self, service, mock_cipher_factory):
        """Test decrypt_exefs with non-zero offset."""
        # Arrange
        encrypted_data = b"icon_data"
        key_y = b"\x00" * 16
        title_id = b"\x00" * 8
        offset_in_blocks = 0x120  # Typical offset for icon file

        # Act
        service.decrypt_exefs(encrypted_data, key_y, title_id, offset_in_blocks)

        # Assert
        cipher = mock_cipher_factory.created_ciphers[0]

        # Counter should include the offset
        expected_counter_bytes = title_id + b"\x02" + bytes(7)
        base_counter = int.from_bytes(expected_counter_bytes, byteorder="big")
        expected_counter = base_counter + offset_in_blocks

        assert cipher.counter_value == expected_counter

    def test_decrypt_exefs_counter_calculation(self, service, mock_cipher_factory):
        """Test that decrypt_exefs calculates the counter correctly."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 16
        title_id = b"\xff\xee\xdd\xcc\xbb\xaa\x99\x88"
        offset_in_blocks = 0x20  # Header offset

        # Act
        service.decrypt_exefs(encrypted_data, key_y, title_id, offset_in_blocks)

        # Assert
        cipher = mock_cipher_factory.created_ciphers[0]

        # Expected counter: title_id || 0x02 || 0x00...00 (7 bytes) + offset
        expected_counter_bytes = title_id + b"\x02" + bytes(7)
        base_counter = int.from_bytes(expected_counter_bytes, byteorder="big")
        expected_counter = base_counter + offset_in_blocks

        assert cipher.counter_value == expected_counter

        # Verify the counter value
        # 0xFFEEDDCCBBAA9988 0200000000000000 + 0x20 in big-endian
        assert expected_counter == 0xFFEEDDCCBBAA99880200000000000020

    def test_decrypt_exefs_with_default_offset(self, service, mock_cipher_factory):
        """Test decrypt_exefs uses offset 0 by default."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 16
        title_id = b"\x00" * 8

        # Act - don't provide offset parameter
        service.decrypt_exefs(encrypted_data, key_y, title_id)

        # Assert
        cipher = mock_cipher_factory.created_ciphers[0]

        # Counter should have no offset added (offset = 0)
        expected_counter_bytes = title_id + b"\x02" + bytes(7)
        expected_counter = int.from_bytes(expected_counter_bytes, byteorder="big")

        assert cipher.counter_value == expected_counter

    def test_decrypt_exefs_with_empty_data(self, service, mock_cipher_factory):
        """Test decrypt_exefs with empty encrypted data."""
        # Arrange
        encrypted_data = b""
        key_y = b"\x00" * 16
        title_id = b"\x00" * 8

        # Act
        result = service.decrypt_exefs(encrypted_data, key_y, title_id)

        # Assert
        assert result == b""

    def test_decrypt_exefs_with_short_key_y_raises_error(self, service):
        """Test decrypt_exefs with invalid key_y length raises ValueError."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 15  # Too short
        title_id = b"\x00" * 8

        # Act & Assert
        with pytest.raises(ValueError, match="key_y must be 16 bytes"):
            service.decrypt_exefs(encrypted_data, key_y, title_id)

    def test_decrypt_exefs_with_long_key_y_raises_error(self, service):
        """Test decrypt_exefs with invalid key_y length raises ValueError."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 17  # Too long
        title_id = b"\x00" * 8

        # Act & Assert
        with pytest.raises(ValueError, match="key_y must be 16 bytes"):
            service.decrypt_exefs(encrypted_data, key_y, title_id)

    def test_decrypt_exefs_with_short_title_id_raises_error(self, service):
        """Test decrypt_exefs with invalid title_id length raises ValueError."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 16
        title_id = b"\x00" * 7  # Too short

        # Act & Assert
        with pytest.raises(ValueError, match="title_id must be 8 bytes"):
            service.decrypt_exefs(encrypted_data, key_y, title_id)

    def test_decrypt_exefs_with_long_title_id_raises_error(self, service):
        """Test decrypt_exefs with invalid title_id length raises ValueError."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 16
        title_id = b"\x00" * 9  # Too long

        # Act & Assert
        with pytest.raises(ValueError, match="title_id must be 8 bytes"):
            service.decrypt_exefs(encrypted_data, key_y, title_id)

    def test_decrypt_extheader_uses_key_derivation_service(self, mock_cipher_factory):
        """Test that decrypt_extheader uses the key derivation service."""
        # Arrange
        key_derivation = KeyDerivationService(original_ncch_key=0x12345678)
        service = DecryptionService(key_derivation, mock_cipher_factory)

        encrypted_data = b"test"
        key_y = b"\x00" * 16
        title_id = b"\x00" * 8

        # Act
        service.decrypt_extheader(encrypted_data, key_y, title_id)

        # Assert
        cipher = mock_cipher_factory.created_ciphers[0]

        # The key should be derived using the actual key derivation service
        # (not our mock that just reverses it)
        expected_key = key_derivation.derive_normal_key(key_y)
        assert cipher.key == expected_key

    def test_decrypt_exefs_uses_key_derivation_service(self, mock_cipher_factory):
        """Test that decrypt_exefs uses the key derivation service."""
        # Arrange
        key_derivation = KeyDerivationService(original_ncch_key=0x12345678)
        service = DecryptionService(key_derivation, mock_cipher_factory)

        encrypted_data = b"test"
        key_y = b"\x00" * 16
        title_id = b"\x00" * 8

        # Act
        service.decrypt_exefs(encrypted_data, key_y, title_id)

        # Assert
        cipher = mock_cipher_factory.created_ciphers[0]

        # The key should be derived using the actual key derivation service
        expected_key = key_derivation.derive_normal_key(key_y)
        assert cipher.key == expected_key

    @pytest.mark.parametrize(
        "title_id,expected_extheader_suffix,expected_exefs_suffix",
        [
            (
                b"\x00\x00\x00\x00\x00\x00\x00\x00",
                0x0100000000000000,
                0x0200000000000000,
            ),
            (
                b"\xff\xff\xff\xff\xff\xff\xff\xff",
                0xFFFFFFFFFFFFFFFF0100000000000000,
                0xFFFFFFFFFFFFFFFF0200000000000000,
            ),
            (
                b"\x01\x23\x45\x67\x89\xab\xcd\xef",
                0x0123456789ABCDEF0100000000000000,
                0x0123456789ABCDEF0200000000000000,
            ),
        ],
    )
    def test_counter_values_for_different_title_ids(
        self,
        service,
        mock_cipher_factory,
        title_id,
        expected_extheader_suffix,
        expected_exefs_suffix,
    ):
        """Test counter calculation with various title IDs."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 16

        # Test extheader counter
        service.decrypt_extheader(encrypted_data, key_y, title_id)
        extheader_cipher = mock_cipher_factory.created_ciphers[0]
        assert extheader_cipher.counter_value == expected_extheader_suffix

        # Clear created ciphers
        mock_cipher_factory.created_ciphers.clear()

        # Test exefs counter (with offset 0)
        service.decrypt_exefs(encrypted_data, key_y, title_id, 0)
        exefs_cipher = mock_cipher_factory.created_ciphers[0]
        assert exefs_cipher.counter_value == expected_exefs_suffix

    def test_different_methods_use_different_counter_types(self, service, mock_cipher_factory):
        """Test that extheader and exefs use different counter type bytes."""
        # Arrange
        encrypted_data = b"test"
        key_y = b"\x00" * 16
        title_id = b"\x00" * 8

        # Act
        service.decrypt_extheader(encrypted_data, key_y, title_id)
        extheader_cipher = mock_cipher_factory.created_ciphers[0]

        mock_cipher_factory.created_ciphers.clear()

        service.decrypt_exefs(encrypted_data, key_y, title_id, 0)
        exefs_cipher = mock_cipher_factory.created_ciphers[0]

        # Assert - counters should differ by 0x01 vs 0x02
        # ExtHeader: 0x00...00 || 0x01 || 0x00...00
        # ExeFS:     0x00...00 || 0x02 || 0x00...00
        assert extheader_cipher.counter_value == 0x0100000000000000
        assert exefs_cipher.counter_value == 0x0200000000000000
