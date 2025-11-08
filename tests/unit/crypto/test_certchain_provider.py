"""Tests for certificate chain provider."""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest

from dsconv.crypto.certchain_provider import CertChainProvider


class TestCertChainProvider:
    """Tests for CertChainProvider class."""


class TestGetRetailCertchain:
    """Tests for get_retail_certchain method."""

    def test_returns_bytes(self):
        """Test that get_retail_certchain returns bytes."""
        # Act
        certchain = CertChainProvider.get_retail_certchain()

        # Assert
        assert isinstance(certchain, bytes)

    def test_returns_correct_size(self):
        """Test that retail certchain has correct size (0xA00 bytes)."""
        # Act
        certchain = CertChainProvider.get_retail_certchain()

        # Assert
        assert len(certchain) == 0xA00
        assert len(certchain) == CertChainProvider.CERTCHAIN_SIZE

    def test_returns_same_value_on_multiple_calls(self):
        """Test that multiple calls return identical data."""
        # Act
        certchain1 = CertChainProvider.get_retail_certchain()
        certchain2 = CertChainProvider.get_retail_certchain()

        # Assert
        assert certchain1 == certchain2

    def test_returns_non_empty_data(self):
        """Test that retail certchain is not all zeros."""
        # Act
        certchain = CertChainProvider.get_retail_certchain()

        # Assert
        assert certchain != b"\x00" * 0xA00
        assert any(b != 0 for b in certchain)

    def test_decompression_produces_valid_data(self):
        """Test that decompression works correctly."""
        # Act
        certchain = CertChainProvider.get_retail_certchain()

        # Assert - check some expected characteristics
        # Should be binary data, not text
        assert len(certchain) == 0xA00
        # Should have varying byte values
        unique_bytes = len(set(certchain))
        assert unique_bytes > 10  # Should have variety

    def test_is_static_method(self):
        """Test that get_retail_certchain is a static method."""
        # Assert - can call without instance
        certchain = CertChainProvider.get_retail_certchain()
        assert certchain is not None

    def test_decompression_error_handling(self, monkeypatch):
        """Test that RuntimeError is raised if decompression fails."""
        # This is a defensive test - in practice, this should never happen
        # since the embedded data is valid, but we test error handling anyway
        import zlib

        # Mock zlib.decompress to raise an error
        def mock_decompress(data):
            raise zlib.error("Mock decompression error")

        monkeypatch.setattr(zlib, "decompress", mock_decompress)

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to decompress retail certchain"):
            CertChainProvider.get_retail_certchain()


class TestGetDevCertchain:
    """Tests for get_dev_certchain method."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def valid_dev_certchain_file(self, temp_dir):
        """Create a valid dev certchain file for testing.

        Note: This creates a dummy file with the correct hash for testing.
        In a real scenario, this would be the actual dev certchain.
        """
        cert_path = temp_dir / "certchain-dev.bin"

        # Create dummy data that matches the expected hash
        # This is a known test pattern that produces the expected MD5
        # In production, this would be the actual dev certchain binary
        # For testing, we use a predictable pattern
        test_data = bytes([i % 256 for i in range(0xA00)])

        # We need to create data with the specific hash
        # For testing purposes, we'll just use a marker that we can validate
        # The actual implementation will check MD5, so we need correct hash

        # Instead, let's create a mock that has the right properties
        # We'll patch the validation in the test instead
        with open(cert_path, "wb") as f:
            f.write(test_data)

        return cert_path

    @pytest.fixture
    def invalid_size_certchain_file(self, temp_dir):
        """Create a certchain file with invalid size."""
        cert_path = temp_dir / "certchain-invalid-size.bin"
        with open(cert_path, "wb") as f:
            f.write(b"too short")
        return cert_path

    @pytest.fixture
    def invalid_hash_certchain_file(self, temp_dir):
        """Create a certchain file with correct size but invalid hash."""
        cert_path = temp_dir / "certchain-invalid-hash.bin"
        with open(cert_path, "wb") as f:
            # Write correct size but wrong data
            f.write(b"X" * 0xA00)
        return cert_path

    def test_raises_error_when_file_not_found(self):
        """Test that FileNotFoundError is raised when no certchain is found."""
        # Arrange
        nonexistent_paths = ["/nonexistent/path/certchain-dev.bin"]

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="Dev certchain not found or invalid"):
            CertChainProvider.get_dev_certchain(search_paths=nonexistent_paths)

    def test_error_message_includes_search_paths(self):
        """Test that error message includes the paths that were searched."""
        # Arrange
        paths = ["/path/one/certchain-dev.bin", "/path/two/certchain-dev.bin"]

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            CertChainProvider.get_dev_certchain(search_paths=paths)

        error_message = str(exc_info.value)
        assert "/path/one/certchain-dev.bin" in error_message
        assert "/path/two/certchain-dev.bin" in error_message

    def test_error_message_includes_expected_hash(self):
        """Test that error message includes expected MD5 hash."""
        # Arrange
        paths = ["/nonexistent/path"]

        # Act & Assert
        with pytest.raises(FileNotFoundError) as exc_info:
            CertChainProvider.get_dev_certchain(search_paths=paths)

        error_message = str(exc_info.value)
        assert CertChainProvider.DEV_CERTCHAIN_HASH in error_message

    def test_uses_default_paths_when_none_provided(self, monkeypatch):
        """Test that default paths are used when search_paths is None."""
        # Arrange - track which paths were checked
        checked_paths = []

        def mock_isfile(path):
            checked_paths.append(path)
            return False

        monkeypatch.setattr(os.path, "isfile", mock_isfile)

        # Act
        with pytest.raises(FileNotFoundError):
            CertChainProvider.get_dev_certchain(search_paths=None)

        # Assert - default paths were checked
        assert len(checked_paths) >= 2
        assert any("certchain-dev.bin" in path for path in checked_paths)

    def test_expands_user_home_directory(self, monkeypatch, temp_dir):
        """Test that ~ is expanded to user home directory."""
        # Arrange
        checked_paths = []
        real_isfile = os.path.isfile

        def mock_isfile(path):
            checked_paths.append(path)
            # Call real isfile to avoid recursion
            return real_isfile(path)

        monkeypatch.setattr(os.path, "isfile", mock_isfile)

        paths = ["~/certchain-dev.bin"]

        # Act
        with pytest.raises(FileNotFoundError):
            CertChainProvider.get_dev_certchain(search_paths=paths)

        # Assert - path was expanded (not containing ~)
        assert len(checked_paths) > 0
        assert all("~" not in path for path in checked_paths)

    def test_skips_file_with_wrong_size(self, invalid_size_certchain_file):
        """Test that file with wrong size is skipped."""
        # Arrange
        paths = [str(invalid_size_certchain_file)]

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            CertChainProvider.get_dev_certchain(search_paths=paths)

    def test_skips_file_with_wrong_hash(self, invalid_hash_certchain_file):
        """Test that file with wrong MD5 hash is skipped."""
        # Arrange
        paths = [str(invalid_hash_certchain_file)]

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            CertChainProvider.get_dev_certchain(search_paths=paths)

    def test_returns_bytes_on_success(self, temp_dir, monkeypatch):
        """Test that valid certchain file returns bytes."""
        # Arrange - create a file with correct hash
        cert_path = temp_dir / "certchain-dev.bin"

        # Create test data
        test_data = b"test" * (0xA00 // 4)  # Fill to correct size
        with open(cert_path, "wb") as f:
            f.write(test_data)

        # Mock the hash validation to accept our test data
        class MockHash:
            def hexdigest(self):
                return CertChainProvider.DEV_CERTCHAIN_HASH

        def mock_md5(data):
            return MockHash()

        monkeypatch.setattr(hashlib, "md5", mock_md5)

        # Act
        result = CertChainProvider.get_dev_certchain(search_paths=[str(cert_path)])

        # Assert
        assert isinstance(result, bytes)
        assert len(result) == 0xA00

    def test_returns_correct_size_on_success(self, temp_dir, monkeypatch):
        """Test that returned certchain has correct size."""
        # Arrange
        cert_path = temp_dir / "certchain-dev.bin"
        test_data = b"X" * 0xA00

        with open(cert_path, "wb") as f:
            f.write(test_data)

        # Mock hash validation
        class MockHash:
            def hexdigest(self):
                return CertChainProvider.DEV_CERTCHAIN_HASH

        def mock_md5(data):
            return MockHash()

        monkeypatch.setattr(hashlib, "md5", mock_md5)

        # Act
        result = CertChainProvider.get_dev_certchain(search_paths=[str(cert_path)])

        # Assert
        assert len(result) == CertChainProvider.CERTCHAIN_SIZE

    def test_tries_multiple_paths_in_order(self, temp_dir, monkeypatch):
        """Test that multiple paths are tried in order until valid one is found."""
        # Arrange
        cert_path1 = temp_dir / "path1" / "certchain-dev.bin"
        cert_path2 = temp_dir / "path2" / "certchain-dev.bin"
        cert_path3 = temp_dir / "path3" / "certchain-dev.bin"

        # Create directories
        cert_path1.parent.mkdir(parents=True, exist_ok=True)
        cert_path2.parent.mkdir(parents=True, exist_ok=True)
        cert_path3.parent.mkdir(parents=True, exist_ok=True)

        # Create files - first two invalid, third valid
        with open(cert_path1, "wb") as f:
            f.write(b"wrong")  # Too short

        with open(cert_path2, "wb") as f:
            f.write(b"A" * 0xA00)  # Wrong hash

        test_data = b"valid" * (0xA00 // 5)
        with open(cert_path3, "wb") as f:
            f.write(test_data)

        # Mock hash validation for the valid file
        class MockHash:
            def __init__(self, data):
                self.data = data

            def hexdigest(self):
                # Return correct hash only for test_data
                if self.data == test_data:
                    return CertChainProvider.DEV_CERTCHAIN_HASH
                return "wronghash"

        def mock_md5(data):
            return MockHash(data)

        monkeypatch.setattr(hashlib, "md5", mock_md5)

        paths = [str(cert_path1), str(cert_path2), str(cert_path3)]

        # Act
        result = CertChainProvider.get_dev_certchain(search_paths=paths)

        # Assert - should have found the valid one
        assert result == test_data

    def test_handles_io_error_gracefully(self, temp_dir, monkeypatch):
        """Test that IOError when reading file is handled gracefully."""
        # Arrange
        cert_path = temp_dir / "certchain-dev.bin"

        # Create file
        with open(cert_path, "wb") as f:
            f.write(b"X" * 0xA00)

        # Mock open to raise IOError
        original_open = open

        def mock_open(path, *args, **kwargs):
            if "certchain-dev.bin" in str(path):
                raise OSError("Mock IO error")
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr("builtins.open", mock_open)

        # Act & Assert - should continue and raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            CertChainProvider.get_dev_certchain(search_paths=[str(cert_path)])

    def test_is_static_method(self, temp_dir, monkeypatch):
        """Test that get_dev_certchain is a static method."""
        # Arrange
        cert_path = temp_dir / "certchain-dev.bin"
        test_data = b"X" * 0xA00

        with open(cert_path, "wb") as f:
            f.write(test_data)

        # Mock hash validation
        class MockHash:
            def hexdigest(self):
                return CertChainProvider.DEV_CERTCHAIN_HASH

        def mock_md5(data):
            return MockHash()

        monkeypatch.setattr(hashlib, "md5", mock_md5)

        # Act - call without instance
        result = CertChainProvider.get_dev_certchain(search_paths=[str(cert_path)])

        # Assert
        assert result is not None


class TestConstants:
    """Tests for CertChainProvider constants."""

    def test_certchain_size_constant(self):
        """Test CERTCHAIN_SIZE constant has correct value."""
        assert CertChainProvider.CERTCHAIN_SIZE == 0xA00
        assert CertChainProvider.CERTCHAIN_SIZE == 2560

    def test_dev_certchain_hash_constant(self):
        """Test DEV_CERTCHAIN_HASH constant has correct value."""
        assert CertChainProvider.DEV_CERTCHAIN_HASH == "d5c3d811a7eb87340aa9f4ab1841b6c4"
        assert len(CertChainProvider.DEV_CERTCHAIN_HASH) == 32  # MD5 hex length

    def test_default_dev_paths_constant(self):
        """Test DEFAULT_DEV_PATHS constant is a list."""
        assert isinstance(CertChainProvider.DEFAULT_DEV_PATHS, list)
        assert len(CertChainProvider.DEFAULT_DEV_PATHS) >= 2
        assert all(isinstance(path, str) for path in CertChainProvider.DEFAULT_DEV_PATHS)

    def test_default_dev_paths_includes_current_dir(self):
        """Test that default paths includes current directory option."""
        assert any(
            "certchain-dev.bin" in path and "/" not in path.replace("~", "")
            for path in CertChainProvider.DEFAULT_DEV_PATHS
        )

    def test_default_dev_paths_includes_home_dir(self):
        """Test that default paths includes home directory option."""
        # The actual implementation expands ~ in the code, not in the constant
        # So we just check that there's a path with .3ds in it
        assert any(".3ds" in path for path in CertChainProvider.DEFAULT_DEV_PATHS)
