"""Tests for AES cipher adapters."""

import pytest

from dsconv.crypto.aes_adapter import IAESCipher, MockAESAdapter, PyAESAdapter


class TestIAESCipher:
    """Tests for IAESCipher interface."""

    def test_is_abstract_base_class(self):
        """Test that IAESCipher cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IAESCipher()  # type: ignore[abstract]

    def test_has_decrypt_abstract_method(self):
        """Test that decrypt method is abstract."""
        assert hasattr(IAESCipher, "decrypt")
        assert getattr(IAESCipher.decrypt, "__isabstractmethod__", False)

    def test_has_encrypt_abstract_method(self):
        """Test that encrypt method is abstract."""
        assert hasattr(IAESCipher, "encrypt")
        assert getattr(IAESCipher.encrypt, "__isabstractmethod__", False)


class TestPyAESAdapter:
    """Tests for PyAESAdapter implementation."""

    @pytest.fixture
    def valid_key(self):
        """Provide a valid 16-byte AES key."""
        return b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f"

    @pytest.fixture
    def counter_value(self):
        """Provide a counter value for CTR mode."""
        return 0x12345678

    @pytest.fixture
    def adapter(self, valid_key, counter_value):
        """Create a PyAESAdapter instance."""
        return PyAESAdapter(valid_key, counter_value)

    def test_create_with_valid_key(self, valid_key, counter_value):
        """Test creating adapter with valid 16-byte key succeeds."""
        adapter = PyAESAdapter(valid_key, counter_value)
        assert adapter.key == valid_key
        assert adapter.counter_value == counter_value

    def test_create_with_short_key_raises_error(self, counter_value):
        """Test creating adapter with key shorter than 16 bytes raises ValueError."""
        short_key = b"\x00" * 15  # Only 15 bytes
        with pytest.raises(ValueError, match="AES key must be exactly 16 bytes"):
            PyAESAdapter(short_key, counter_value)

    def test_create_with_long_key_raises_error(self, counter_value):
        """Test creating adapter with key longer than 16 bytes raises ValueError."""
        long_key = b"\x00" * 17  # 17 bytes
        with pytest.raises(ValueError, match="AES key must be exactly 16 bytes"):
            PyAESAdapter(long_key, counter_value)

    def test_implements_iaescipher_interface(self, adapter):
        """Test that PyAESAdapter implements IAESCipher."""
        assert isinstance(adapter, IAESCipher)

    def test_decrypt_empty_data_returns_empty_bytes(self, adapter):
        """Test decrypting empty data returns empty bytes."""
        result = adapter.decrypt(b"")
        assert result == b""

    def test_encrypt_empty_data_returns_empty_bytes(self, adapter):
        """Test encrypting empty data returns empty bytes."""
        result = adapter.encrypt(b"")
        assert result == b""

    def test_decrypt_returns_bytes(self, adapter):
        """Test that decrypt returns bytes."""
        encrypted_data = b"test encrypted data"
        result = adapter.decrypt(encrypted_data)
        assert isinstance(result, bytes)

    def test_encrypt_returns_bytes(self, adapter):
        """Test that encrypt returns bytes."""
        plain_data = b"test plain data"
        result = adapter.encrypt(plain_data)
        assert isinstance(result, bytes)

    def test_encrypt_then_decrypt_returns_original_data(self, valid_key, counter_value):
        """Test that encrypting then decrypting returns original data."""
        # CTR mode encryption and decryption are the same operation
        # So we need to use the same counter for both
        original_data = b"Hello, Nintendo 3DS!"

        # Encrypt
        encrypt_adapter = PyAESAdapter(valid_key, counter_value)
        encrypted = encrypt_adapter.encrypt(original_data)

        # Decrypt with same key and counter
        decrypt_adapter = PyAESAdapter(valid_key, counter_value)
        decrypted = decrypt_adapter.decrypt(encrypted)

        assert decrypted == original_data

    def test_decrypt_then_encrypt_returns_original_data(self, valid_key, counter_value):
        """Test that decrypting then encrypting returns original data (CTR symmetry)."""
        # In CTR mode, encryption and decryption are the same operation
        original_data = b"3DS Game Data"

        # Decrypt (which is actually encryption in CTR)
        decrypt_adapter = PyAESAdapter(valid_key, counter_value)
        decrypted = decrypt_adapter.decrypt(original_data)

        # Encrypt with same key and counter
        encrypt_adapter = PyAESAdapter(valid_key, counter_value)
        encrypted = encrypt_adapter.encrypt(decrypted)

        assert encrypted == original_data

    def test_encrypt_produces_different_output_than_input(self, adapter):
        """Test that encryption changes the data."""
        plain_data = b"Nintendo 3DS content"
        encrypted = adapter.encrypt(plain_data)

        # Encrypted data should be different from plain data
        # (unless we're very unlucky with a specific key/counter combination)
        assert encrypted != plain_data

    def test_same_data_encrypted_with_different_counters_produces_different_output(
        self, valid_key
    ):
        """Test that same data with different counters produces different ciphertext."""
        plain_data = b"Test data for CTR mode"

        adapter1 = PyAESAdapter(valid_key, counter_value=0)
        encrypted1 = adapter1.encrypt(plain_data)

        adapter2 = PyAESAdapter(valid_key, counter_value=1000)
        encrypted2 = adapter2.encrypt(plain_data)

        assert encrypted1 != encrypted2

    def test_encrypt_preserves_data_length(self, adapter):
        """Test that CTR mode encryption preserves data length."""
        plain_data = b"A" * 100
        encrypted = adapter.encrypt(plain_data)
        assert len(encrypted) == len(plain_data)

    def test_decrypt_preserves_data_length(self, adapter):
        """Test that CTR mode decryption preserves data length."""
        encrypted_data = b"B" * 100
        decrypted = adapter.decrypt(encrypted_data)
        assert len(decrypted) == len(encrypted_data)

    @pytest.mark.parametrize(
        "data_size",
        [1, 16, 32, 64, 128, 256, 512, 1024],
    )
    def test_encrypt_decrypt_various_sizes(self, valid_key, counter_value, data_size):
        """Test encryption/decryption with various data sizes."""
        plain_data = bytes(range(256)) * (data_size // 256 + 1)
        plain_data = plain_data[:data_size]

        # Encrypt
        encrypt_adapter = PyAESAdapter(valid_key, counter_value)
        encrypted = encrypt_adapter.encrypt(plain_data)

        # Decrypt
        decrypt_adapter = PyAESAdapter(valid_key, counter_value)
        decrypted = decrypt_adapter.decrypt(encrypted)

        assert decrypted == plain_data
        assert len(encrypted) == data_size

    def test_multiple_decrypt_operations_with_same_adapter(self, adapter):
        """Test that multiple decrypt operations work correctly."""
        data1 = b"First data block"
        data2 = b"Second data block"

        result1 = adapter.decrypt(data1)
        result2 = adapter.decrypt(data2)

        # Results should be different
        assert result1 != result2
        # Each should be the correct length
        assert len(result1) == len(data1)
        assert len(result2) == len(data2)

    def test_multiple_encrypt_operations_with_same_adapter(self, adapter):
        """Test that multiple encrypt operations work correctly."""
        data1 = b"First plain block"
        data2 = b"Second plain block"

        result1 = adapter.encrypt(data1)
        result2 = adapter.encrypt(data2)

        # Results should be different
        assert result1 != result2
        # Each should be the correct length
        assert len(result1) == len(data1)
        assert len(result2) == len(data2)


class TestMockAESAdapter:
    """Tests for MockAESAdapter implementation."""

    @pytest.fixture
    def mock_key(self):
        """Provide a mock key."""
        return b"\xff" * 16

    @pytest.fixture
    def mock_counter(self):
        """Provide a mock counter value."""
        return 0xABCDEF

    @pytest.fixture
    def mock_adapter(self, mock_key, mock_counter):
        """Create a MockAESAdapter instance."""
        return MockAESAdapter(mock_key, mock_counter)

    def test_create_with_key_and_counter(self, mock_key, mock_counter):
        """Test creating mock adapter stores key and counter."""
        adapter = MockAESAdapter(mock_key, mock_counter)
        assert adapter.key == mock_key
        assert adapter.counter_value == mock_counter

    def test_implements_iaescipher_interface(self, mock_adapter):
        """Test that MockAESAdapter implements IAESCipher."""
        assert isinstance(mock_adapter, IAESCipher)

    def test_decrypt_empty_data_returns_empty_bytes(self, mock_adapter):
        """Test decrypting empty data returns empty bytes."""
        result = mock_adapter.decrypt(b"")
        assert result == b""

    def test_encrypt_empty_data_returns_empty_bytes(self, mock_adapter):
        """Test encrypting empty data returns empty bytes."""
        result = mock_adapter.encrypt(b"")
        assert result == b""

    def test_decrypt_tracks_call_state(self, mock_adapter):
        """Test that decrypt operation sets tracking flags."""
        assert mock_adapter.decrypt_called is False

        data = b"test data"
        mock_adapter.decrypt(data)

        assert mock_adapter.decrypt_called is True
        assert mock_adapter.last_decrypt_input == data

    def test_encrypt_tracks_call_state(self, mock_adapter):
        """Test that encrypt operation sets tracking flags."""
        assert mock_adapter.encrypt_called is False

        data = b"test data"
        mock_adapter.encrypt(data)

        assert mock_adapter.encrypt_called is True
        assert mock_adapter.last_encrypt_input == data

    def test_decrypt_returns_xor_result(self, mock_adapter):
        """Test that decrypt XORs data with 0xAA."""
        data = b"\x00\x55\xAA\xFF"
        expected = bytes(b ^ 0xAA for b in data)

        result = mock_adapter.decrypt(data)

        assert result == expected

    def test_encrypt_returns_xor_result(self, mock_adapter):
        """Test that encrypt XORs data with 0xAA."""
        data = b"\x00\x55\xAA\xFF"
        expected = bytes(b ^ 0xAA for b in data)

        result = mock_adapter.encrypt(data)

        assert result == expected

    def test_encrypt_decrypt_symmetry(self, mock_adapter):
        """Test that encrypt and decrypt are symmetric operations."""
        original_data = b"Symmetric test data"

        encrypted = mock_adapter.encrypt(original_data)
        # Create new adapter with same key/counter for symmetry
        mock_adapter2 = MockAESAdapter(mock_adapter.key, mock_adapter.counter_value)
        decrypted = mock_adapter2.decrypt(encrypted)

        assert decrypted == original_data

    def test_decrypt_encrypt_symmetry(self, mock_adapter):
        """Test that decrypt and encrypt are symmetric operations."""
        original_data = b"Another symmetric test"

        decrypted = mock_adapter.decrypt(original_data)
        # Create new adapter with same key/counter for symmetry
        mock_adapter2 = MockAESAdapter(mock_adapter.key, mock_adapter.counter_value)
        encrypted = mock_adapter2.encrypt(decrypted)

        assert encrypted == original_data

    def test_preserves_data_length(self, mock_adapter):
        """Test that operations preserve data length."""
        data = b"X" * 100

        encrypted = mock_adapter.encrypt(data)
        assert len(encrypted) == len(data)

        decrypted = mock_adapter.decrypt(data)
        assert len(decrypted) == len(data)

    def test_tracking_state_resets_between_operations(self, mock_adapter):
        """Test that tracking state is updated for each operation."""
        data1 = b"First operation"
        data2 = b"Second operation"

        mock_adapter.decrypt(data1)
        assert mock_adapter.last_decrypt_input == data1

        mock_adapter.decrypt(data2)
        assert mock_adapter.last_decrypt_input == data2

    @pytest.mark.parametrize(
        "input_byte,expected_byte",
        [
            (0x00, 0xAA),
            (0xAA, 0x00),
            (0xFF, 0x55),
            (0x55, 0xFF),
        ],
    )
    def test_xor_operation_correctness(
        self, mock_adapter, input_byte, expected_byte
    ):
        """Test XOR operation with specific byte values."""
        data = bytes([input_byte])
        result = mock_adapter.encrypt(data)
        assert result[0] == expected_byte


class TestAdapterComparison:
    """Tests comparing PyAESAdapter and MockAESAdapter behaviors."""

    @pytest.fixture
    def test_key(self):
        """Provide a test key."""
        return b"0123456789ABCDEF"

    @pytest.fixture
    def test_counter(self):
        """Provide a test counter."""
        return 12345

    def test_both_implement_same_interface(self, test_key, test_counter):
        """Test that both adapters implement IAESCipher."""
        pyaes_adapter = PyAESAdapter(test_key, test_counter)
        mock_adapter = MockAESAdapter(test_key, test_counter)

        assert isinstance(pyaes_adapter, IAESCipher)
        assert isinstance(mock_adapter, IAESCipher)

    def test_both_preserve_data_length(self, test_key, test_counter):
        """Test that both adapters preserve data length."""
        data = b"Test data 123"

        pyaes_adapter = PyAESAdapter(test_key, test_counter)
        mock_adapter = MockAESAdapter(test_key, test_counter)

        assert len(pyaes_adapter.encrypt(data)) == len(data)
        assert len(mock_adapter.encrypt(data)) == len(data)
        assert len(pyaes_adapter.decrypt(data)) == len(data)
        assert len(mock_adapter.decrypt(data)) == len(data)

    def test_both_handle_empty_data(self, test_key, test_counter):
        """Test that both adapters handle empty data correctly."""
        pyaes_adapter = PyAESAdapter(test_key, test_counter)
        mock_adapter = MockAESAdapter(test_key, test_counter)

        assert pyaes_adapter.encrypt(b"") == b""
        assert mock_adapter.encrypt(b"") == b""
        assert pyaes_adapter.decrypt(b"") == b""
        assert mock_adapter.decrypt(b"") == b""

    def test_both_are_substitutable(self, test_key, test_counter):
        """Test that adapters can be used interchangeably via interface."""

        def encrypt_with_adapter(adapter: IAESCipher, data: bytes) -> bytes:
            """Helper function that uses any IAESCipher implementation."""
            return adapter.encrypt(data)

        data = b"Substitution test"

        pyaes_adapter = PyAESAdapter(test_key, test_counter)
        mock_adapter = MockAESAdapter(test_key, test_counter)

        # Both should work with the same function
        pyaes_result = encrypt_with_adapter(pyaes_adapter, data)
        mock_result = encrypt_with_adapter(mock_adapter, data)

        # Results will be different, but both should be valid
        assert isinstance(pyaes_result, bytes)
        assert isinstance(mock_result, bytes)
        assert len(pyaes_result) == len(data)
        assert len(mock_result) == len(data)
