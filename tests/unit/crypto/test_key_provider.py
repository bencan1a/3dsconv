"""Tests for key provider service."""

import hashlib
import os

import pytest

from dsconv.crypto import (
    Boot9KeyProvider,
    InvalidKeyFileError,
    KeyNotFoundError,
    MockKeyProvider,
    ProdKeysKeyProvider,
)


class TestProdKeysKeyProvider:
    """Tests for ProdKeysKeyProvider."""

    def test_init_with_valid_file(self, tmp_path):
        """Test initialization with a valid prod.keys file."""
        # Arrange
        prod_keys = tmp_path / "prod.keys"
        prod_keys.write_text("slot0x2CKey=1234567890ABCDEF1234567890ABCDEF\n")

        # Act
        provider = ProdKeysKeyProvider(str(prod_keys))

        # Assert
        assert provider.prod_keys_path == str(prod_keys)

    def test_init_with_nonexistent_file_raises_error(self):
        """Test initialization with nonexistent file raises FileNotFoundError."""
        # Arrange
        nonexistent_path = "/nonexistent/path/prod.keys"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="prod.keys file not found"):
            ProdKeysKeyProvider(nonexistent_path)

    def test_get_original_ncch_key_success(self, tmp_path):
        """Test successful key extraction from prod.keys."""
        # Arrange
        prod_keys = tmp_path / "prod.keys"
        test_key_hex = "1234567890ABCDEF1234567890ABCDEF"
        prod_keys.write_text(f"slot0x2CKey={test_key_hex}\n")
        provider = ProdKeysKeyProvider(str(prod_keys))

        # Act
        key = provider.get_original_ncch_key()

        # Assert
        expected_key = int(test_key_hex, 16)
        assert key == expected_key

    def test_get_original_ncch_key_with_multiple_keys(self, tmp_path):
        """Test extracting key from file with multiple keys."""
        # Arrange
        prod_keys = tmp_path / "prod.keys"
        prod_keys.write_text(
            "# Comment\n"
            "someOtherKey=AAAA\n"
            "slot0x2CKey=FEDCBA0987654321FEDCBA0987654321\n"
            "anotherKey=BBBB\n"
        )
        provider = ProdKeysKeyProvider(str(prod_keys))

        # Act
        key = provider.get_original_ncch_key()

        # Assert
        expected_key = int("FEDCBA0987654321FEDCBA0987654321", 16)
        assert key == expected_key

    def test_get_original_ncch_key_missing_key_raises_error(self, tmp_path):
        """Test that missing slot0x2CKey raises KeyNotFoundError."""
        # Arrange
        prod_keys = tmp_path / "prod.keys"
        prod_keys.write_text("someOtherKey=1234\n")
        provider = ProdKeysKeyProvider(str(prod_keys))

        # Act & Assert
        with pytest.raises(KeyNotFoundError, match="slot0x2CKey not found"):
            provider.get_original_ncch_key()

    def test_get_original_ncch_key_with_invalid_file_raises_error(self, tmp_path):
        """Test that invalid prod.keys file raises InvalidKeyFileError."""
        # Arrange
        prod_keys = tmp_path / "prod.keys"
        prod_keys.write_text("invalid format no equals\n")
        provider = ProdKeysKeyProvider(str(prod_keys))

        # Act & Assert
        with pytest.raises(InvalidKeyFileError, match="Invalid prod.keys file"):
            provider.get_original_ncch_key()

    def test_get_original_ncch_key_with_empty_value_raises_error(self, tmp_path):
        """Test that empty key value raises InvalidKeyFileError."""
        # Arrange
        prod_keys = tmp_path / "prod.keys"
        prod_keys.write_text("slot0x2CKey=\n")
        provider = ProdKeysKeyProvider(str(prod_keys))

        # Act & Assert
        with pytest.raises(InvalidKeyFileError, match="Invalid prod.keys file"):
            provider.get_original_ncch_key()

    def test_get_original_ncch_key_with_invalid_hex_raises_error(self, tmp_path):
        """Test that invalid hex value raises InvalidKeyFileError."""
        # Arrange
        prod_keys = tmp_path / "prod.keys"
        prod_keys.write_text("slot0x2CKey=NOTVALIDHEX\n")
        provider = ProdKeysKeyProvider(str(prod_keys))

        # Act & Assert
        with pytest.raises(InvalidKeyFileError, match="Invalid prod.keys file"):
            provider.get_original_ncch_key()


class TestBoot9KeyProvider:
    """Tests for Boot9KeyProvider."""

    # Test-specific hashes (not the real retail/dev hashes)
    # These match the MD5 hashes of our test keys
    TEST_RETAIL_HASH = "4ae71336e44bf9bf79d2752e234818a5"  # MD5 of 16 zero bytes
    TEST_DEV_HASH = "40559ee2113ce2a79abfd73dc5480949"  # MD5 of "1" + 15 zero bytes

    def create_boot9_file(self, path, file_size, dev_keys=False):
        """Helper to create a mock boot9 file with valid key.

        Args:
            path: Path where to create the file
            file_size: Size of the file (0x8000 for protected, 0x10000 for full)
            dev_keys: If True, create dev keys; if False, create retail keys
        """
        # Create a file of the right size filled with zeros
        with open(path, "wb") as f:
            f.write(bytes(file_size))

        # Calculate offset for the key
        keys_offset = Boot9KeyProvider.KEY_OFFSET_BASE
        if file_size == 0x10000:
            keys_offset += Boot9KeyProvider.FULL_DUMP_OFFSET
        if dev_keys:
            keys_offset += Boot9KeyProvider.DEV_KEYS_OFFSET

        # Create a test key (16 bytes)
        if dev_keys:
            key_bytes = b"1" + bytes(15)  # MD5: c4ca4238a0b923820dcc509a6f75849b
        else:
            key_bytes = bytes(16)  # MD5: d41d8cd98f00b204e9800998ecf8427e

        # Write the key at the correct offset
        with open(path, "r+b") as f:
            f.seek(keys_offset)
            f.write(key_bytes)

    def test_init_with_valid_file(self, tmp_path):
        """Test initialization with a valid boot9 file."""
        # Arrange
        boot9_file = tmp_path / "boot9.bin"
        self.create_boot9_file(boot9_file, 0x8000, dev_keys=False)

        # Act
        provider = Boot9KeyProvider(str(boot9_file), dev_keys=False)

        # Assert
        assert provider.boot9_path == str(boot9_file)
        assert provider.dev_keys is False

    def test_init_with_nonexistent_file_raises_error(self):
        """Test initialization with nonexistent file raises FileNotFoundError."""
        # Arrange
        nonexistent_path = "/nonexistent/path/boot9.bin"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="boot9 file not found"):
            Boot9KeyProvider(nonexistent_path)

    def test_init_with_dev_keys_flag(self, tmp_path):
        """Test initialization with dev_keys flag."""
        # Arrange
        boot9_file = tmp_path / "boot9.bin"
        self.create_boot9_file(boot9_file, 0x8000, dev_keys=True)

        # Act
        provider = Boot9KeyProvider(str(boot9_file), dev_keys=True)

        # Assert
        assert provider.dev_keys is True

    def test_get_original_ncch_key_from_protected_dump_retail(self, tmp_path, monkeypatch):
        """Test extracting retail key from protected boot9 dump."""
        # Arrange - patch the hash constant for testing
        monkeypatch.setattr(Boot9KeyProvider, "RETAIL_KEY_HASH", self.TEST_RETAIL_HASH)

        boot9_file = tmp_path / "boot9_prot.bin"
        self.create_boot9_file(boot9_file, 0x8000, dev_keys=False)
        provider = Boot9KeyProvider(str(boot9_file), dev_keys=False)

        # Act
        key = provider.get_original_ncch_key()

        # Assert
        assert isinstance(key, int)
        # Verify it's the correct key by checking it matches what we wrote
        expected_key = int.from_bytes(bytes(16), byteorder="big")
        assert key == expected_key

    def test_get_original_ncch_key_from_full_dump_retail(self, tmp_path, monkeypatch):
        """Test extracting retail key from full boot9 dump."""
        # Arrange - patch the hash constant for testing
        monkeypatch.setattr(Boot9KeyProvider, "RETAIL_KEY_HASH", self.TEST_RETAIL_HASH)

        boot9_file = tmp_path / "boot9.bin"
        self.create_boot9_file(boot9_file, 0x10000, dev_keys=False)
        provider = Boot9KeyProvider(str(boot9_file), dev_keys=False)

        # Act
        key = provider.get_original_ncch_key()

        # Assert
        assert isinstance(key, int)
        expected_key = int.from_bytes(bytes(16), byteorder="big")
        assert key == expected_key

    def test_get_original_ncch_key_from_protected_dump_dev(self, tmp_path, monkeypatch):
        """Test extracting dev key from protected boot9 dump."""
        # Arrange - patch the hash constant for testing
        monkeypatch.setattr(Boot9KeyProvider, "DEV_KEY_HASH", self.TEST_DEV_HASH)

        boot9_file = tmp_path / "boot9_prot.bin"
        self.create_boot9_file(boot9_file, 0x8000, dev_keys=True)
        provider = Boot9KeyProvider(str(boot9_file), dev_keys=True)

        # Act
        key = provider.get_original_ncch_key()

        # Assert
        assert isinstance(key, int)
        expected_key = int.from_bytes(b"1" + bytes(15), byteorder="big")
        assert key == expected_key

    def test_get_original_ncch_key_from_full_dump_dev(self, tmp_path, monkeypatch):
        """Test extracting dev key from full boot9 dump."""
        # Arrange - patch the hash constant for testing
        monkeypatch.setattr(Boot9KeyProvider, "DEV_KEY_HASH", self.TEST_DEV_HASH)

        boot9_file = tmp_path / "boot9.bin"
        self.create_boot9_file(boot9_file, 0x10000, dev_keys=True)
        provider = Boot9KeyProvider(str(boot9_file), dev_keys=True)

        # Act
        key = provider.get_original_ncch_key()

        # Assert
        assert isinstance(key, int)
        expected_key = int.from_bytes(b"1" + bytes(15), byteorder="big")
        assert key == expected_key

    def test_get_original_ncch_key_with_invalid_hash_raises_error(self, tmp_path):
        """Test that invalid key hash raises InvalidKeyFileError."""
        # Arrange
        boot9_file = tmp_path / "boot9.bin"
        # Create file with wrong key
        with open(boot9_file, "wb") as f:
            f.write(bytes(0x8000))
            f.seek(Boot9KeyProvider.KEY_OFFSET_BASE)
            f.write(bytes(16))  # All zeros won't match the hash

        provider = Boot9KeyProvider(str(boot9_file), dev_keys=False)

        # Act & Assert
        with pytest.raises(InvalidKeyFileError, match="Invalid retail key in boot9 file"):
            provider.get_original_ncch_key()

    def test_get_original_ncch_key_with_wrong_dev_key_raises_error(self, tmp_path, monkeypatch):
        """Test that wrong dev key raises InvalidKeyFileError."""
        # Arrange - patch hashes for testing
        monkeypatch.setattr(Boot9KeyProvider, "RETAIL_KEY_HASH", self.TEST_RETAIL_HASH)
        monkeypatch.setattr(Boot9KeyProvider, "DEV_KEY_HASH", self.TEST_DEV_HASH)

        boot9_file = tmp_path / "boot9.bin"
        # Create file with retail key but try to read as dev
        self.create_boot9_file(boot9_file, 0x8000, dev_keys=False)
        provider = Boot9KeyProvider(str(boot9_file), dev_keys=True)  # Wrong flag

        # Act & Assert
        with pytest.raises(InvalidKeyFileError, match="Invalid development key"):
            provider.get_original_ncch_key()

    def test_get_original_ncch_key_with_truncated_file_raises_error(self, tmp_path):
        """Test that truncated boot9 file raises InvalidKeyFileError."""
        # Arrange
        boot9_file = tmp_path / "boot9.bin"
        with open(boot9_file, "wb") as f:
            f.write(bytes(0x100))  # Too short

        provider = Boot9KeyProvider(str(boot9_file), dev_keys=False)

        # Act & Assert
        with pytest.raises(InvalidKeyFileError, match="boot9 file too short"):
            provider.get_original_ncch_key()

    def test_get_original_ncch_key_with_unreadable_file_raises_error(self, tmp_path, monkeypatch):
        """Test that unreadable boot9 file raises InvalidKeyFileError."""
        # Arrange - patch hash for testing
        monkeypatch.setattr(Boot9KeyProvider, "RETAIL_KEY_HASH", self.TEST_RETAIL_HASH)

        boot9_file = tmp_path / "boot9.bin"
        self.create_boot9_file(boot9_file, 0x8000, dev_keys=False)

        # Mock open to raise PermissionError
        original_open = open

        def mock_open(file, mode="r", *args, **kwargs):
            # Check if the file being opened is our boot9 file
            # Handle both string paths and Path objects
            if str(file) == str(boot9_file):
                raise PermissionError("Mock permission error")
            return original_open(file, mode, *args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        provider = Boot9KeyProvider(str(boot9_file), dev_keys=False)

        # Act & Assert
        with pytest.raises(InvalidKeyFileError, match="Failed to read boot9 file"):
            provider.get_original_ncch_key()

    def test_get_original_ncch_key_with_getsize_error_raises_error(self, tmp_path, monkeypatch):
        """Test that OSError when getting file size raises InvalidKeyFileError."""
        # Arrange
        boot9_file = tmp_path / "boot9.bin"
        self.create_boot9_file(boot9_file, 0x8000, dev_keys=False)
        provider = Boot9KeyProvider(str(boot9_file), dev_keys=False)

        # Mock os.path.getsize to raise OSError
        def mock_getsize(path):
            raise OSError("Mock error getting file size")

        monkeypatch.setattr(os.path, "getsize", mock_getsize)

        # Act & Assert
        with pytest.raises(InvalidKeyFileError, match="Cannot read boot9 file"):
            provider.get_original_ncch_key()

    @pytest.mark.parametrize(
        "file_size,dev_keys,expected_offset",
        [
            (0x8000, False, 0x59D0),  # Protected, retail
            (0x10000, False, 0x59D0 + 0x8000),  # Full, retail
            (0x8000, True, 0x59D0 + 0x400),  # Protected, dev
            (0x10000, True, 0x59D0 + 0x8000 + 0x400),  # Full, dev
        ],
    )
    def test_key_offset_calculation(
        self, tmp_path, monkeypatch, file_size, dev_keys, expected_offset
    ):
        """Test that key offset is calculated correctly for different scenarios."""
        # Arrange - patch hashes for testing
        monkeypatch.setattr(Boot9KeyProvider, "RETAIL_KEY_HASH", self.TEST_RETAIL_HASH)
        monkeypatch.setattr(Boot9KeyProvider, "DEV_KEY_HASH", self.TEST_DEV_HASH)

        boot9_file = tmp_path / "boot9.bin"
        self.create_boot9_file(boot9_file, file_size, dev_keys=dev_keys)

        # Read the key from the file at the expected offset to verify
        with open(boot9_file, "rb") as f:
            f.seek(expected_offset)
            key_at_offset = f.read(16)

        # Verify that the key at the calculated offset has the correct hash
        # MD5 is used here for test verification only, matching the production code's
        # use of MD5 for integrity checking of known encryption keys.
        key_hash = hashlib.md5(key_at_offset).hexdigest()  # codeql[py/weak-cryptographic-algorithm]
        expected_hash = self.TEST_DEV_HASH if dev_keys else self.TEST_RETAIL_HASH
        assert key_hash == expected_hash


class TestMockKeyProvider:
    """Tests for MockKeyProvider."""

    def test_init_with_default_value(self):
        """Test initialization with default key value."""
        # Act
        provider = MockKeyProvider()

        # Assert
        assert provider.key_value == 0x1234567890ABCDEF1234567890ABCDEF

    def test_init_with_custom_value(self):
        """Test initialization with custom key value."""
        # Arrange
        custom_key = 0xAAAABBBBCCCCDDDDEEEEFFFF00001111

        # Act
        provider = MockKeyProvider(custom_key)

        # Assert
        assert provider.key_value == custom_key

    def test_get_original_ncch_key_returns_configured_value(self):
        """Test that get_original_ncch_key returns the configured value."""
        # Arrange
        test_key = 0x11112222333344445555666677778888
        provider = MockKeyProvider(test_key)

        # Act
        key = provider.get_original_ncch_key()

        # Assert
        assert key == test_key

    def test_get_original_ncch_key_with_zero_value(self):
        """Test that mock provider can return zero key."""
        # Arrange
        provider = MockKeyProvider(0x0)

        # Act
        key = provider.get_original_ncch_key()

        # Assert
        assert key == 0

    def test_get_original_ncch_key_with_max_value(self):
        """Test that mock provider can return maximum 128-bit value."""
        # Arrange
        max_128bit = (2**128) - 1
        provider = MockKeyProvider(max_128bit)

        # Act
        key = provider.get_original_ncch_key()

        # Assert
        assert key == max_128bit


class TestKeyProviderInterface:
    """Tests for the IKeyProvider interface."""

    def test_all_providers_implement_interface(self):
        """Test that all provider classes implement the IKeyProvider interface."""
        from dsconv.crypto import IKeyProvider

        # All concrete providers should be subclasses of IKeyProvider
        assert issubclass(ProdKeysKeyProvider, IKeyProvider)
        assert issubclass(Boot9KeyProvider, IKeyProvider)
        assert issubclass(MockKeyProvider, IKeyProvider)

    def test_interface_enforces_get_original_ncch_key_method(self, tmp_path):
        """Test that all providers have get_original_ncch_key method."""
        # Arrange - create instances
        prod_keys = tmp_path / "prod.keys"
        prod_keys.write_text("slot0x2CKey=1234567890ABCDEF1234567890ABCDEF\n")

        providers = [
            ProdKeysKeyProvider(str(prod_keys)),
            MockKeyProvider(),
        ]

        # Act & Assert
        for provider in providers:
            assert hasattr(provider, "get_original_ncch_key")
            assert callable(provider.get_original_ncch_key)
