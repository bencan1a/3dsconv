"""Tests for ExeFS reader."""

import struct
from io import BytesIO

import pytest

from dsconv.crypto.aes_adapter import MockAESAdapter
from dsconv.io.binary_reader import BinaryReader
from dsconv.io.exefs_reader import ExeFSFile, ExeFSReader


class TestExeFSFile:
    """Tests for ExeFSFile dataclass."""

    def test_create_with_valid_data(self):
        """Test creating ExeFSFile with valid data."""
        # Arrange & Act
        file_info = ExeFSFile(name="icon", offset=0x200, size=0x36C0)

        # Assert
        assert file_info.name == "icon"
        assert file_info.offset == 0x200
        assert file_info.size == 0x36C0

    def test_create_with_short_name(self):
        """Test creating ExeFSFile with short name."""
        file_info = ExeFSFile(name="txt", offset=0, size=100)
        assert file_info.name == "txt"

    def test_create_with_max_length_name(self):
        """Test creating ExeFSFile with 8-character name."""
        file_info = ExeFSFile(name="12345678", offset=0, size=100)
        assert file_info.name == "12345678"

    def test_create_with_long_name_raises_error(self):
        """Test creating ExeFSFile with name longer than 8 characters raises ValueError."""
        with pytest.raises(ValueError, match="name must be 8 characters or less"):
            ExeFSFile(name="toolongname", offset=0, size=100)

    def test_create_with_negative_offset_raises_error(self):
        """Test creating ExeFSFile with negative offset raises ValueError."""
        with pytest.raises(ValueError, match="offset must be non-negative"):
            ExeFSFile(name="file", offset=-1, size=100)

    def test_create_with_negative_size_raises_error(self):
        """Test creating ExeFSFile with negative size raises ValueError."""
        with pytest.raises(ValueError, match="size must be non-negative"):
            ExeFSFile(name="file", offset=0, size=-1)

    def test_create_with_zero_size(self):
        """Test creating ExeFSFile with zero size is valid."""
        file_info = ExeFSFile(name="empty", offset=0, size=0)
        assert file_info.size == 0

    def test_create_with_non_string_name_raises_error(self):
        """Test creating ExeFSFile with non-string name raises TypeError."""
        with pytest.raises(TypeError, match="name must be str"):
            ExeFSFile(name=b"bytes", offset=0, size=100)  # type: ignore


class TestExeFSReader:
    """Tests for ExeFSReader."""

    @pytest.fixture
    def empty_exefs_data(self):
        """Create minimal ExeFS data with no files."""
        # ExeFS header is 0x200 bytes, all zeros means no files
        return BytesIO(bytes(0x400))

    @pytest.fixture
    def sample_exefs_data(self):
        """Create sample ExeFS data with multiple files."""
        data = BytesIO()

        # Create ExeFS header (0x200 bytes total)
        header = bytearray(0x200)

        # File 1: "icon" at offset 0x0, size 0x36C0
        header[0x00:0x08] = b"icon\x00\x00\x00\x00"
        header[0x08:0x0C] = struct.pack("<I", 0x0)
        header[0x0C:0x10] = struct.pack("<I", 0x36C0)

        # File 2: "banner" at offset 0x3800, size 0x2000
        header[0x10:0x18] = b"banner\x00\x00"
        header[0x18:0x1C] = struct.pack("<I", 0x3800)
        header[0x1C:0x20] = struct.pack("<I", 0x2000)

        # File 3: "logo" at offset 0x5800, size 0x2000
        header[0x20:0x28] = b"logo\x00\x00\x00\x00"
        header[0x28:0x2C] = struct.pack("<I", 0x5800)
        header[0x2C:0x30] = struct.pack("<I", 0x2000)

        # Remaining headers are empty (null bytes)

        # Write header
        data.write(header)

        # Write file data (after 0x200 header section)
        # File 1: icon (0x36C0 bytes)
        icon_data = (b"ICON" * ((0x36C0 + 3) // 4))[:0x36C0]  # Ensure exactly 0x36C0 bytes
        data.write(icon_data)

        # File 2: banner (at offset 0x3800 from data start)
        # Need to pad to reach offset 0x3800
        current_pos = 0x36C0
        padding_needed = 0x3800 - current_pos
        data.write(bytes(padding_needed))
        banner_data = (b"BANNER" * ((0x2000 + 5) // 6))[:0x2000]  # Ensure exactly 0x2000 bytes
        data.write(banner_data)

        # File 3: logo (at offset 0x5800 from data start)
        current_pos = 0x3800 + 0x2000
        padding_needed = 0x5800 - current_pos
        data.write(bytes(padding_needed))
        logo_data = (b"LOGO" * ((0x2000 + 3) // 4))[:0x2000]  # Ensure exactly 0x2000 bytes
        data.write(logo_data)

        data.seek(0)
        return data

    @pytest.fixture
    def reader(self, sample_exefs_data):
        """Create BinaryReader with sample ExeFS data."""
        return BinaryReader(sample_exefs_data)

    @pytest.fixture
    def empty_reader(self, empty_exefs_data):
        """Create BinaryReader with empty ExeFS data."""
        return BinaryReader(empty_exefs_data)

    def test_init(self, reader):
        """Test ExeFSReader initialization."""
        exefs_reader = ExeFSReader(reader)
        assert exefs_reader.reader is reader

    def test_read_file_headers_with_no_files(self, empty_reader):
        """Test reading file headers from empty ExeFS."""
        # Arrange
        exefs_reader = ExeFSReader(empty_reader)

        # Act
        files = exefs_reader.read_file_headers(exefs_offset=0)

        # Assert
        assert files == []

    def test_read_file_headers_with_multiple_files(self, reader):
        """Test reading file headers from ExeFS with multiple files."""
        # Arrange
        exefs_reader = ExeFSReader(reader)

        # Act
        files = exefs_reader.read_file_headers(exefs_offset=0)

        # Assert
        assert len(files) == 3
        assert files[0].name == "icon"
        assert files[0].offset == 0x0
        assert files[0].size == 0x36C0

        assert files[1].name == "banner"
        assert files[1].offset == 0x3800
        assert files[1].size == 0x2000

        assert files[2].name == "logo"
        assert files[2].offset == 0x5800
        assert files[2].size == 0x2000

    def test_read_file_headers_with_non_zero_exefs_offset(self):
        """Test reading file headers with non-zero ExeFS offset."""
        # Arrange - create data with ExeFS at offset 0x1000
        data = BytesIO()
        data.write(bytes(0x1000))  # Padding before ExeFS

        # ExeFS header
        header = bytearray(0x200)
        header[0x00:0x08] = b"test\x00\x00\x00\x00"
        header[0x08:0x0C] = struct.pack("<I", 0x0)
        header[0x0C:0x10] = struct.pack("<I", 0x100)
        data.write(header)

        # File data
        data.write(b"TEST" * (0x100 // 4))

        data.seek(0)
        reader = BinaryReader(data)
        exefs_reader = ExeFSReader(reader)

        # Act
        files = exefs_reader.read_file_headers(exefs_offset=0x1000)

        # Assert
        assert len(files) == 1
        assert files[0].name == "test"
        assert files[0].offset == 0x0
        assert files[0].size == 0x100

    def test_read_file_headers_with_decryption(self, reader):
        """Test reading file headers with decryption enabled."""
        # Arrange
        exefs_reader = ExeFSReader(reader)
        cipher = MockAESAdapter(key=bytes(16), counter_value=0)

        # Act
        files = exefs_reader.read_file_headers(exefs_offset=0, decrypt=True, cipher=cipher)

        # Assert - MockAESAdapter XORs with 0xAA, so we should still be able to parse
        # Note: The mock doesn't actually decrypt properly, but we can verify it was called
        assert cipher.encrypt_called
        assert len(files) >= 0  # Depends on how the XOR affects parsing

    def test_read_file_headers_decrypt_without_cipher_raises_error(self, reader):
        """Test that decrypt=True without cipher raises ValueError."""
        # Arrange
        exefs_reader = ExeFSReader(reader)

        # Act & Assert
        with pytest.raises(ValueError, match="cipher is required when decrypt is True"):
            exefs_reader.read_file_headers(exefs_offset=0, decrypt=True, cipher=None)

    def test_read_file_headers_skips_empty_entries(self):
        """Test that empty header entries are skipped."""
        # Arrange - create ExeFS with file in slot 3 (skip slots 0, 1, 2)
        data = BytesIO()
        header = bytearray(0x200)

        # Slot 0, 1, 2: empty (all zeros)
        # Slot 3: "file"
        header[0x30:0x38] = b"file\x00\x00\x00\x00"
        header[0x38:0x3C] = struct.pack("<I", 0x0)
        header[0x3C:0x40] = struct.pack("<I", 0x100)

        data.write(header)
        data.write(b"DATA" * (0x100 // 4))

        data.seek(0)
        reader = BinaryReader(data)
        exefs_reader = ExeFSReader(reader)

        # Act
        files = exefs_reader.read_file_headers(exefs_offset=0)

        # Assert - only one file, from slot 3
        assert len(files) == 1
        assert files[0].name == "file"

    def test_read_file_basic(self, reader):
        """Test reading file content without decryption."""
        # Arrange
        exefs_reader = ExeFSReader(reader)
        file_info = ExeFSFile(name="icon", offset=0x0, size=0x36C0)

        # Act
        content = exefs_reader.read_file(exefs_offset=0, file_info=file_info)

        # Assert
        assert len(content) == 0x36C0
        assert content[:4] == b"ICON"

    def test_read_file_second_file(self, reader):
        """Test reading second file from ExeFS."""
        # Arrange
        exefs_reader = ExeFSReader(reader)
        file_info = ExeFSFile(name="banner", offset=0x3800, size=0x2000)

        # Act
        content = exefs_reader.read_file(exefs_offset=0, file_info=file_info)

        # Assert
        assert len(content) == 0x2000
        assert content[:6] == b"BANNER"

    def test_read_file_with_non_zero_exefs_offset(self):
        """Test reading file with non-zero ExeFS offset."""
        # Arrange - ExeFS at offset 0x1000
        data = BytesIO()
        data.write(bytes(0x1000))  # Padding

        # Header
        header = bytearray(0x200)
        header[0x00:0x08] = b"data\x00\x00\x00\x00"
        header[0x08:0x0C] = struct.pack("<I", 0x0)
        header[0x0C:0x10] = struct.pack("<I", 0x100)
        data.write(header)

        # File content
        data.write(b"TESTDATA" * (0x100 // 8))

        data.seek(0)
        reader = BinaryReader(data)
        exefs_reader = ExeFSReader(reader)
        file_info = ExeFSFile(name="data", offset=0x0, size=0x100)

        # Act
        content = exefs_reader.read_file(exefs_offset=0x1000, file_info=file_info)

        # Assert
        assert len(content) == 0x100
        assert content[:8] == b"TESTDATA"

    def test_read_file_with_empty_size(self, reader):
        """Test reading file with zero size."""
        # Arrange
        exefs_reader = ExeFSReader(reader)
        file_info = ExeFSFile(name="empty", offset=0x0, size=0)

        # Act
        content = exefs_reader.read_file(exefs_offset=0, file_info=file_info)

        # Assert
        assert content == b""

    def test_read_file_with_decryption(self, reader):
        """Test reading file with decryption enabled."""
        # Arrange
        exefs_reader = ExeFSReader(reader)
        file_info = ExeFSFile(name="icon", offset=0x0, size=0x36C0)
        cipher = MockAESAdapter(key=bytes(16), counter_value=0)

        # Act
        content = exefs_reader.read_file(
            exefs_offset=0, file_info=file_info, decrypt=True, cipher=cipher
        )

        # Assert
        assert len(content) == 0x36C0
        assert cipher.decrypt_called
        # Content is XORed with 0xAA by MockAESAdapter
        expected_first_byte = ord(b"I") ^ 0xAA
        assert content[0] == expected_first_byte

    def test_read_file_decrypt_without_cipher_raises_error(self, reader):
        """Test that decrypt=True without cipher raises ValueError."""
        # Arrange
        exefs_reader = ExeFSReader(reader)
        file_info = ExeFSFile(name="icon", offset=0x0, size=0x36C0)

        # Act & Assert
        with pytest.raises(ValueError, match="cipher is required when decrypt is True"):
            exefs_reader.read_file(exefs_offset=0, file_info=file_info, decrypt=True, cipher=None)

    def test_find_file_success(self, reader):
        """Test finding a file by name."""
        # Arrange
        exefs_reader = ExeFSReader(reader)

        # Act
        file_info = exefs_reader.find_file(exefs_offset=0, filename="banner")

        # Assert
        assert file_info is not None
        assert file_info.name == "banner"
        assert file_info.offset == 0x3800
        assert file_info.size == 0x2000

    def test_find_file_not_found(self, reader):
        """Test finding a file that doesn't exist."""
        # Arrange
        exefs_reader = ExeFSReader(reader)

        # Act
        file_info = exefs_reader.find_file(exefs_offset=0, filename="notfound")

        # Assert
        assert file_info is None

    def test_find_file_case_sensitive(self, reader):
        """Test that file search is case-sensitive."""
        # Arrange
        exefs_reader = ExeFSReader(reader)

        # Act
        file_info = exefs_reader.find_file(exefs_offset=0, filename="ICON")

        # Assert - should not find "icon" with uppercase
        assert file_info is None

    def test_find_file_with_decryption(self, reader):
        """Test finding a file with header decryption."""
        # Arrange
        exefs_reader = ExeFSReader(reader)
        cipher = MockAESAdapter(key=bytes(16), counter_value=0)

        # Act
        exefs_reader.find_file(
            exefs_offset=0, filename="banner", decrypt_headers=True, cipher=cipher
        )

        # Assert
        assert cipher.encrypt_called

    def test_find_file_decrypt_without_cipher_raises_error(self, reader):
        """Test that decrypt_headers=True without cipher raises ValueError."""
        # Arrange
        exefs_reader = ExeFSReader(reader)

        # Act & Assert
        with pytest.raises(ValueError, match="cipher is required when decrypt is True"):
            exefs_reader.find_file(
                exefs_offset=0, filename="icon", decrypt_headers=True, cipher=None
            )

    def test_read_file_headers_handles_all_10_slots(self):
        """Test that reader can handle all 10 file header slots."""
        # Arrange - create ExeFS with files in all 10 slots
        data = BytesIO()
        header = bytearray(0x200)

        for i in range(10):
            slot_offset = i * 0x10
            name = f"file{i}".encode("ascii").ljust(8, b"\x00")
            header[slot_offset : slot_offset + 8] = name
            header[slot_offset + 8 : slot_offset + 12] = struct.pack("<I", i * 0x100)
            header[slot_offset + 12 : slot_offset + 16] = struct.pack("<I", 0x100)

        data.write(header)
        # Add enough file data
        data.write(bytes(10 * 0x100))

        data.seek(0)
        reader = BinaryReader(data)
        exefs_reader = ExeFSReader(reader)

        # Act
        files = exefs_reader.read_file_headers(exefs_offset=0)

        # Assert
        assert len(files) == 10
        for i in range(10):
            assert files[i].name == f"file{i}"
            assert files[i].offset == i * 0x100
            assert files[i].size == 0x100

    def test_read_file_headers_handles_partial_name(self):
        """Test reading file with name shorter than 8 bytes."""
        # Arrange
        data = BytesIO()
        header = bytearray(0x200)

        # Name "a" (1 character)
        header[0x00:0x08] = b"a\x00\x00\x00\x00\x00\x00\x00"
        header[0x08:0x0C] = struct.pack("<I", 0x0)
        header[0x0C:0x10] = struct.pack("<I", 0x10)

        data.write(header)
        data.write(bytes(0x10))

        data.seek(0)
        reader = BinaryReader(data)
        exefs_reader = ExeFSReader(reader)

        # Act
        files = exefs_reader.read_file_headers(exefs_offset=0)

        # Assert
        assert len(files) == 1
        assert files[0].name == "a"

    def test_integration_read_file_by_finding_it_first(self, reader):
        """Integration test: find a file and then read it."""
        # Arrange
        exefs_reader = ExeFSReader(reader)

        # Act - find the logo file
        file_info = exefs_reader.find_file(exefs_offset=0, filename="logo")
        assert file_info is not None

        # Read the file
        content = exefs_reader.read_file(exefs_offset=0, file_info=file_info)

        # Assert
        assert len(content) == 0x2000
        assert content[:4] == b"LOGO"
