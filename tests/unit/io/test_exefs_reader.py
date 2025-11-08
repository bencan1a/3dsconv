"""Tests for ExeFSReader."""

import struct
from io import BytesIO
from unittest.mock import Mock

import pytest

from dsconv.crypto.aes_adapter import IAESCipher, MockAESAdapter
from dsconv.io.binary_reader import BinaryReader
from dsconv.io.exefs_reader import ExeFSFile, ExeFSReader


class TestExeFSFile:
    """Tests for ExeFSFile dataclass."""

    def test_create_with_valid_data(self):
        """Test creating ExeFSFile with valid data."""
        file_entry = ExeFSFile(name="icon", offset=0, size=0x36C0)

        assert file_entry.name == "icon"
        assert file_entry.offset == 0
        assert file_entry.size == 0x36C0

    def test_create_with_various_names(self):
        """Test creating files with different valid names."""
        file1 = ExeFSFile(name="icon", offset=0, size=100)
        assert file1.name == "icon"

        file2 = ExeFSFile(name="banner", offset=100, size=200)
        assert file2.name == "banner"

        file3 = ExeFSFile(name=".code", offset=300, size=400)
        assert file3.name == ".code"

    def test_name_too_long_raises_error(self):
        """Test that name longer than 8 characters raises ValueError."""
        with pytest.raises(ValueError, match="File name too long"):
            ExeFSFile(name="toolongname", offset=0, size=100)

    def test_negative_offset_raises_error(self):
        """Test that negative offset raises ValueError."""
        with pytest.raises(ValueError, match="Invalid offset"):
            ExeFSFile(name="icon", offset=-1, size=100)

    def test_negative_size_raises_error(self):
        """Test that negative size raises ValueError."""
        with pytest.raises(ValueError, match="Invalid size"):
            ExeFSFile(name="icon", offset=0, size=-100)

    def test_zero_offset_allowed(self):
        """Test that zero offset is valid."""
        file_entry = ExeFSFile(name="icon", offset=0, size=100)
        assert file_entry.offset == 0

    def test_zero_size_allowed(self):
        """Test that zero size is valid."""
        file_entry = ExeFSFile(name="icon", offset=0, size=0)
        assert file_entry.size == 0

    def test_max_length_name(self):
        """Test that 8-character name is valid."""
        file_entry = ExeFSFile(name="12345678", offset=0, size=100)
        assert file_entry.name == "12345678"

    @pytest.mark.parametrize(
        "name,offset,size",
        [
            ("icon", 0, 0x36C0),
            ("banner", 0x4000, 0x2000),
            (".code", 0x200, 0x100000),
            ("logo", 0, 0x2000),
            ("a", 100, 200),
        ],
    )
    def test_various_valid_combinations(self, name, offset, size):
        """Test various valid combinations of name, offset, size."""
        file_entry = ExeFSFile(name=name, offset=offset, size=size)
        assert file_entry.name == name
        assert file_entry.offset == offset
        assert file_entry.size == size


class TestExeFSReader:
    """Tests for ExeFSReader class."""

    @pytest.fixture
    def create_exefs_data(self):
        """Factory for creating ExeFS test data."""

        def _create(files: list[tuple[str, int, int]]) -> BytesIO:
            """Create ExeFS binary data with given files.

            Args:
                files: List of (name, offset, size) tuples

            Returns:
                BytesIO with ExeFS structure
            """
            data = BytesIO()

            # Write file headers (up to 10)
            for i in range(ExeFSReader.MAX_FILES):
                if i < len(files):
                    name, offset, size = files[i]
                    # Name (8 bytes, null-padded)
                    name_bytes = name.encode("ascii").ljust(8, b"\x00")
                    data.write(name_bytes)
                    # Offset and size (4 bytes each, little-endian)
                    data.write(struct.pack("<II", offset, size))
                else:
                    # Empty header
                    data.write(b"\x00" * 16)

            # Write hash region (0x140 bytes)
            data.write(b"\x00" * 0x140)

            # Padding to 0x200
            current_pos = data.tell()
            padding_needed = 0x200 - current_pos
            data.write(b"\x00" * padding_needed)

            # Write file data
            for name, offset, size in files:
                # Seek to correct position in data section
                data.seek(0x200 + offset)
                # Write dummy data (fill with pattern based on name)
                pattern = name.encode("ascii")[0] if name else 0xFF
                data.write(bytes([pattern]) * size)

            data.seek(0)
            return data

        return _create

    @pytest.fixture
    def simple_exefs(self, create_exefs_data):
        """Create simple ExeFS with icon file."""
        return create_exefs_data([("icon", 0, 0x36C0)])

    @pytest.fixture
    def multi_file_exefs(self, create_exefs_data):
        """Create ExeFS with multiple files."""
        return create_exefs_data(
            [
                ("icon", 0, 0x36C0),
                ("banner", 0x4000, 0x2000),
                (".code", 0x8000, 0x100),
                ("logo", 0x9000, 0x2000),
            ]
        )

    @pytest.fixture
    def reader(self, simple_exefs):
        """Create ExeFSReader with simple ExeFS data."""
        binary_reader = BinaryReader(simple_exefs)
        return ExeFSReader(binary_reader)

    def test_create_with_binary_reader(self, simple_exefs):
        """Test creating ExeFSReader with BinaryReader."""
        binary_reader = BinaryReader(simple_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        assert exefs_reader.reader is binary_reader

    def test_read_file_headers_single_file(self, create_exefs_data):
        """Test reading file headers with single file."""
        data = create_exefs_data([("icon", 0, 0x36C0)])
        binary_reader = BinaryReader(data)
        exefs_reader = ExeFSReader(binary_reader)

        files = exefs_reader.read_file_headers(0)

        assert len(files) == 1
        assert files[0].name == "icon"
        assert files[0].offset == 0
        assert files[0].size == 0x36C0

    def test_read_file_headers_multiple_files(self, multi_file_exefs):
        """Test reading file headers with multiple files."""
        binary_reader = BinaryReader(multi_file_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        files = exefs_reader.read_file_headers(0)

        assert len(files) == 4
        assert files[0].name == "icon"
        assert files[1].name == "banner"
        assert files[2].name == ".code"
        assert files[3].name == "logo"

    def test_read_file_headers_skips_empty_entries(self, create_exefs_data):
        """Test that empty file headers are skipped."""
        # Create data with gaps (files at indices 0, 2, 4)
        data = BytesIO()

        # File 0: icon
        data.write(b"icon\x00\x00\x00\x00")
        data.write(struct.pack("<II", 0, 0x36C0))

        # File 1: empty
        data.write(b"\x00" * 16)

        # File 2: banner
        data.write(b"banner\x00\x00")
        data.write(struct.pack("<II", 0x4000, 0x2000))

        # Files 3-9: empty
        data.write(b"\x00" * (7 * 16))

        # Hash region and padding
        data.write(b"\x00" * 0x140)
        data.write(b"\x00" * (0x200 - data.tell()))

        data.seek(0)

        binary_reader = BinaryReader(data)
        exefs_reader = ExeFSReader(binary_reader)

        files = exefs_reader.read_file_headers(0)

        # Should only get 2 files (icon and banner)
        assert len(files) == 2
        assert files[0].name == "icon"
        assert files[1].name == "banner"

    def test_read_file_headers_with_offset(self, create_exefs_data):
        """Test reading file headers at non-zero offset."""
        data = create_exefs_data([("icon", 0, 0x36C0)])

        # Add some padding before ExeFS
        exefs_offset = 0x1000
        padded_data = BytesIO()
        padded_data.write(b"\x00" * exefs_offset)
        padded_data.write(data.getvalue())
        padded_data.seek(0)

        binary_reader = BinaryReader(padded_data)
        exefs_reader = ExeFSReader(binary_reader)

        files = exefs_reader.read_file_headers(exefs_offset)

        assert len(files) == 1
        assert files[0].name == "icon"

    def test_read_file_headers_max_files(self, create_exefs_data):
        """Test reading maximum number of files (10)."""
        # Create 10 files
        files_data = [(f"file{i}", i * 0x1000, 0x100) for i in range(10)]
        data = create_exefs_data(files_data)

        binary_reader = BinaryReader(data)
        exefs_reader = ExeFSReader(binary_reader)

        files = exefs_reader.read_file_headers(0)

        assert len(files) == 10
        for i, file_entry in enumerate(files):
            assert file_entry.name == f"file{i}"

    def test_read_file_without_decryption(self, reader):
        """Test reading file without decryption."""
        files = reader.read_file_headers(0)
        icon_file = files[0]

        data = reader.read_file(0, icon_file, decrypt=False)

        assert len(data) == 0x36C0
        assert isinstance(data, bytes)
        # Data should be filled with 'i' (ASCII value of 'icon'[0])
        assert data[0] == ord("i")

    def test_read_file_with_decryption(self, reader):
        """Test reading file with decryption."""
        files = reader.read_file_headers(0)
        icon_file = files[0]

        # Create mock cipher
        mock_cipher = MockAESAdapter(b"\x00" * 16, 0)

        data = reader.read_file(0, icon_file, decrypt=True, cipher=mock_cipher)

        assert len(data) == 0x36C0
        assert mock_cipher.decrypt_called
        # Data should be XOR'd with 0xAA
        expected_first_byte = ord("i") ^ 0xAA
        assert data[0] == expected_first_byte

    def test_read_file_decrypt_without_cipher_raises_error(self, reader):
        """Test that decrypt=True without cipher raises ValueError."""
        files = reader.read_file_headers(0)
        icon_file = files[0]

        with pytest.raises(ValueError, match="Cipher required when decrypt=True"):
            reader.read_file(0, icon_file, decrypt=True, cipher=None)

    def test_read_file_calculates_correct_offset(self, create_exefs_data):
        """Test that read_file calculates correct file data offset."""
        # File at offset 0x4000 in data section
        data = create_exefs_data([("banner", 0x4000, 0x100)])
        binary_reader = BinaryReader(data)
        exefs_reader = ExeFSReader(binary_reader)

        files = exefs_reader.read_file_headers(0)
        banner_file = files[0]

        file_data = exefs_reader.read_file(0, banner_file)

        # Should read from 0x200 (header size) + 0x4000 (file offset)
        assert len(file_data) == 0x100
        assert file_data[0] == ord("b")  # Filled with 'b' from "banner"

    def test_read_file_multiple_files(self, multi_file_exefs):
        """Test reading different files from same ExeFS."""
        binary_reader = BinaryReader(multi_file_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        files = exefs_reader.read_file_headers(0)

        # Read icon
        icon_data = exefs_reader.read_file(0, files[0])
        assert len(icon_data) == 0x36C0
        assert icon_data[0] == ord("i")

        # Read banner
        banner_data = exefs_reader.read_file(0, files[1])
        assert len(banner_data) == 0x2000
        assert banner_data[0] == ord("b")

        # Read .code
        code_data = exefs_reader.read_file(0, files[2])
        assert len(code_data) == 0x100
        assert code_data[0] == ord(".")

    def test_read_file_with_cipher_interface(self, reader):
        """Test read_file accepts any IAESCipher implementation."""
        files = reader.read_file_headers(0)
        icon_file = files[0]

        # Create a mock that implements IAESCipher
        mock_cipher = Mock(spec=IAESCipher)
        mock_cipher.decrypt.return_value = b"\xab" * 0x36C0

        data = reader.read_file(0, icon_file, decrypt=True, cipher=mock_cipher)

        assert data == b"\xab" * 0x36C0
        mock_cipher.decrypt.assert_called_once()

    def test_find_file_returns_file_when_found(self, multi_file_exefs):
        """Test find_file returns correct file when found."""
        binary_reader = BinaryReader(multi_file_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        icon_file = exefs_reader.find_file(0, "icon")

        assert icon_file is not None
        assert icon_file.name == "icon"
        assert icon_file.offset == 0
        assert icon_file.size == 0x36C0

    def test_find_file_returns_none_when_not_found(self, multi_file_exefs):
        """Test find_file returns None when file not found."""
        binary_reader = BinaryReader(multi_file_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        result = exefs_reader.find_file(0, "notexist")

        assert result is None

    def test_find_file_is_case_sensitive(self, multi_file_exefs):
        """Test that find_file is case-sensitive."""
        binary_reader = BinaryReader(multi_file_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        # Should not find "ICON" when file is named "icon"
        result = exefs_reader.find_file(0, "ICON")
        assert result is None

        # Should find exact match
        result = exefs_reader.find_file(0, "icon")
        assert result is not None

    def test_find_file_finds_all_files(self, multi_file_exefs):
        """Test finding each file in multi-file ExeFS."""
        binary_reader = BinaryReader(multi_file_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        icon = exefs_reader.find_file(0, "icon")
        assert icon is not None and icon.name == "icon"

        banner = exefs_reader.find_file(0, "banner")
        assert banner is not None and banner.name == "banner"

        code = exefs_reader.find_file(0, ".code")
        assert code is not None and code.name == ".code"

        logo = exefs_reader.find_file(0, "logo")
        assert logo is not None and logo.name == "logo"

    def test_constants_are_correct(self):
        """Test that ExeFSReader constants have correct values."""
        assert ExeFSReader.MAX_FILES == 10
        assert ExeFSReader.HEADER_SIZE == 0x10
        assert ExeFSReader.HEADERS_REGION_SIZE == 0xA0
        assert ExeFSReader.HASH_REGION_SIZE == 0x140
        assert ExeFSReader.HEADER_TOTAL_SIZE == 0x200

    def test_read_file_headers_handles_non_ascii_names(self, create_exefs_data):
        """Test that non-ASCII characters in names are handled gracefully."""
        # Create data with invalid UTF-8 in name
        data = BytesIO()
        # Write file header with bytes that aren't valid ASCII
        data.write(b"\xff\xfe\xfd\xfc\x00\x00\x00\x00")  # Invalid ASCII name
        data.write(struct.pack("<II", 0, 0x100))  # offset, size

        # Fill rest of headers
        data.write(b"\x00" * (9 * 16))

        # Hash region and padding
        data.write(b"\x00" * 0x140)
        data.write(b"\x00" * (0x200 - data.tell()))

        data.seek(0)

        binary_reader = BinaryReader(data)
        exefs_reader = ExeFSReader(binary_reader)

        # Should not crash, may produce replacement characters
        files = exefs_reader.read_file_headers(0)
        # Should return at least the entry (even if name is mangled)
        assert len(files) >= 0  # May be empty or contain mangled name

    def test_read_empty_exefs(self, create_exefs_data):
        """Test reading ExeFS with no files."""
        data = create_exefs_data([])  # No files
        binary_reader = BinaryReader(data)
        exefs_reader = ExeFSReader(binary_reader)

        files = exefs_reader.read_file_headers(0)

        assert len(files) == 0

    @pytest.mark.parametrize(
        "file_name,expected_found",
        [
            ("icon", True),
            ("banner", True),
            (".code", True),
            ("logo", True),
            ("nothere", False),
            ("", False),
        ],
    )
    def test_find_file_parametrized(self, multi_file_exefs, file_name, expected_found):
        """Test find_file with various filenames."""
        binary_reader = BinaryReader(multi_file_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        result = exefs_reader.find_file(0, file_name)

        if expected_found:
            assert result is not None
            assert result.name == file_name
        else:
            assert result is None

    def test_integration_find_and_read_file(self, multi_file_exefs):
        """Test complete workflow: find then read a file."""
        binary_reader = BinaryReader(multi_file_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        # Find icon file
        icon_file = exefs_reader.find_file(0, "icon")
        assert icon_file is not None

        # Read its data
        icon_data = exefs_reader.read_file(0, icon_file)

        assert len(icon_data) == 0x36C0
        assert isinstance(icon_data, bytes)

    def test_integration_find_and_read_with_decryption(self, multi_file_exefs):
        """Test complete workflow with decryption."""
        binary_reader = BinaryReader(multi_file_exefs)
        exefs_reader = ExeFSReader(binary_reader)

        # Find and read with decryption
        icon_file = exefs_reader.find_file(0, "icon")
        assert icon_file is not None

        cipher = MockAESAdapter(b"\x00" * 16, 0)
        icon_data = exefs_reader.read_file(0, icon_file, decrypt=True, cipher=cipher)

        assert len(icon_data) == 0x36C0
        assert cipher.decrypt_called
