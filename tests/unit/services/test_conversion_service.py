"""Tests for ConversionService orchestration."""

from unittest.mock import Mock

import pytest

from dsconv.crypto.decryption_service import DecryptionService
from dsconv.io.cia_writer import CIAWriter
from dsconv.io.exefs_reader import ExeFSReader
from dsconv.io.ncch_reader import NCCHReader
from dsconv.io.ncsd_reader import NCSDReader
from dsconv.models.encryption import EncryptionContext, EncryptionType
from dsconv.models.ncch import NCCHHeader
from dsconv.models.ncsd import NCSDContainer, NCSDPartition
from dsconv.services.conversion_config import ConversionConfig
from dsconv.services.conversion_service import ConversionService
from dsconv.services.progress_reporter import MockProgressReporter
from dsconv.validation.hash_validator import HashValidator


class TestConversionServiceInit:
    """Tests for ConversionService initialization."""

    @pytest.fixture
    def mock_ncsd_reader(self):
        """Create mock NCSD reader."""
        return Mock(spec=NCSDReader)

    @pytest.fixture
    def mock_ncch_reader(self):
        """Create mock NCCH reader."""
        return Mock(spec=NCCHReader)

    @pytest.fixture
    def mock_exefs_reader(self):
        """Create mock ExeFS reader."""
        return Mock(spec=ExeFSReader)

    @pytest.fixture
    def mock_cia_writer(self):
        """Create mock CIA writer."""
        return Mock(spec=CIAWriter)

    @pytest.fixture
    def mock_decryption_service(self):
        """Create mock decryption service."""
        return Mock(spec=DecryptionService)

    @pytest.fixture
    def mock_hash_validator(self):
        """Create mock hash validator."""
        return Mock(spec=HashValidator)

    @pytest.fixture
    def mock_progress_reporter(self):
        """Create mock progress reporter."""
        return MockProgressReporter()

    @pytest.fixture
    def service(
        self,
        mock_ncsd_reader,
        mock_ncch_reader,
        mock_exefs_reader,
        mock_cia_writer,
        mock_decryption_service,
        mock_hash_validator,
        mock_progress_reporter,
    ):
        """Create ConversionService with all mocked dependencies."""
        return ConversionService(
            ncsd_reader=mock_ncsd_reader,
            ncch_reader=mock_ncch_reader,
            exefs_reader=mock_exefs_reader,
            cia_writer=mock_cia_writer,
            decryption_service=mock_decryption_service,
            hash_validator=mock_hash_validator,
            progress_reporter=mock_progress_reporter,
        )

    def test_create_with_all_dependencies(self, service):
        """Test creating service with all dependencies."""
        assert service is not None
        assert isinstance(service, ConversionService)

    def test_stores_ncsd_reader(self, service, mock_ncsd_reader):
        """Test that service stores NCSD reader."""
        assert service.ncsd_reader is mock_ncsd_reader

    def test_stores_ncch_reader(self, service, mock_ncch_reader):
        """Test that service stores NCCH reader."""
        assert service.ncch_reader is mock_ncch_reader

    def test_stores_exefs_reader(self, service, mock_exefs_reader):
        """Test that service stores ExeFS reader."""
        assert service.exefs_reader is mock_exefs_reader

    def test_stores_cia_writer(self, service, mock_cia_writer):
        """Test that service stores CIA writer."""
        assert service.cia_writer is mock_cia_writer

    def test_stores_decryption_service(self, service, mock_decryption_service):
        """Test that service stores decryption service."""
        assert service.decryption_service is mock_decryption_service

    def test_stores_hash_validator(self, service, mock_hash_validator):
        """Test that service stores hash validator."""
        assert service.hash_validator is mock_hash_validator

    def test_stores_progress_reporter(self, service, mock_progress_reporter):
        """Test that service stores progress reporter."""
        assert service.progress_reporter is mock_progress_reporter

    def test_create_with_none_decryption_service(
        self,
        mock_ncsd_reader,
        mock_ncch_reader,
        mock_exefs_reader,
        mock_cia_writer,
        mock_hash_validator,
        mock_progress_reporter,
    ):
        """Test creating service with None decryption service (for decrypted ROMs)."""
        service = ConversionService(
            ncsd_reader=mock_ncsd_reader,
            ncch_reader=mock_ncch_reader,
            exefs_reader=mock_exefs_reader,
            cia_writer=mock_cia_writer,
            decryption_service=None,
            hash_validator=mock_hash_validator,
            progress_reporter=mock_progress_reporter,
        )
        assert service.decryption_service is None


class TestDetermineEncryption:
    """Tests for _determine_encryption method."""

    @pytest.fixture
    def service(self):
        """Create minimal service for testing encryption determination."""
        return ConversionService(
            ncsd_reader=Mock(),
            ncch_reader=Mock(),
            exefs_reader=Mock(),
            cia_writer=Mock(),
            decryption_service=Mock(spec=DecryptionService),
            hash_validator=Mock(),
            progress_reporter=MockProgressReporter(),
        )

    @pytest.fixture
    def decrypted_header(self):
        """Create NCCH header for decrypted content."""
        return NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=b"\x00" * 7 + b"\x04",  # Bit 2 set = decrypted
            exefs_offset=0x10,
            exefs_size=0x10,
        )

    @pytest.fixture
    def encrypted_header(self):
        """Create NCCH header for encrypted content."""
        return NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=b"\x00" * 8,  # Bit 2 clear = encrypted
            exefs_offset=0x10,
            exefs_size=0x10,
        )

    @pytest.fixture
    def zerokey_header(self):
        """Create NCCH header for zero-key encrypted content."""
        return NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=b"\x00" * 7 + b"\x01",  # Bit 0 set = zerokey
            exefs_offset=0x10,
            exefs_size=0x10,
        )

    @pytest.fixture
    def config(self):
        """Create basic conversion config."""
        return ConversionConfig(
            input_file="test.cci",
            output_file="test.cia",
            key_provider=None,
            ignore_bad_hashes=False,
            ignore_encryption=False,
            dev_keys=False,
            verbose=False,
        )

    def test_decrypted_content_returns_decrypted_type(self, service, decrypted_header, config):
        """Test that decrypted content is identified correctly."""
        title_id = bytes(8)
        ctx = service._determine_encryption(decrypted_header, title_id, config, 0)

        assert ctx.encryption_type == EncryptionType.DECRYPTED
        assert ctx.normal_key is None
        assert ctx.title_id == title_id

    def test_ignore_encryption_returns_decrypted_type(self, service, encrypted_header):
        """Test that ignore_encryption config returns DECRYPTED type."""
        config = ConversionConfig(
            input_file="test.cci",
            output_file="test.cia",
            key_provider=None,
            ignore_encryption=True,
        )
        title_id = bytes(8)
        ctx = service._determine_encryption(encrypted_header, title_id, config, 0)

        assert ctx.encryption_type == EncryptionType.DECRYPTED
        assert ctx.normal_key is None

    def test_zerokey_content_returns_zerokey_type(self, service, zerokey_header, config):
        """Test that zero-key encrypted content is identified correctly."""
        title_id = bytes(8)
        ctx = service._determine_encryption(zerokey_header, title_id, config, 0)

        assert ctx.encryption_type == EncryptionType.ZEROKEY
        assert ctx.normal_key == bytes(16)  # All zeros
        assert ctx.title_id == title_id

    def test_encrypted_without_decryption_service_raises_error(self, encrypted_header, config):
        """Test that encrypted content without decryption service raises error."""
        service = ConversionService(
            ncsd_reader=Mock(),
            ncch_reader=Mock(),
            exefs_reader=Mock(),
            cia_writer=Mock(),
            decryption_service=None,  # No decryption service
            hash_validator=Mock(),
            progress_reporter=MockProgressReporter(),
        )

        with pytest.raises(ValueError, match="ROM is encrypted but no decryption service"):
            service._determine_encryption(encrypted_header, bytes(8), config, 0)

    def test_original_ncch_encryption_returns_correct_type(self, service, encrypted_header, config):
        """Test that original NCCH encryption is identified correctly."""
        title_id = bytes(8)
        ctx = service._determine_encryption(encrypted_header, title_id, config, 0)

        assert ctx.encryption_type == EncryptionType.ORIGINAL_NCCH
        assert ctx.normal_key is None  # Not derived in _determine_encryption
        assert ctx.title_id == title_id


class TestReadAndValidateExtheaderEncrypted:
    """Tests for _read_and_validate_extheader with encrypted content."""

    @pytest.fixture
    def service(self):
        """Create service with mocked decryption service."""
        mock_ncch_reader = Mock(spec=NCCHReader)
        mock_hash_validator = Mock(spec=HashValidator)
        mock_decryption_service = Mock(spec=DecryptionService)

        return ConversionService(
            ncsd_reader=Mock(),
            ncch_reader=mock_ncch_reader,
            exefs_reader=Mock(),
            cia_writer=Mock(),
            decryption_service=mock_decryption_service,
            hash_validator=mock_hash_validator,
            progress_reporter=MockProgressReporter(),
        )

    @pytest.fixture
    def ncch_header(self):
        """Create NCCH header with extheader hash."""
        import hashlib

        extheader_data = b"test_extheader_data" + bytes(0x400 - 19)
        extheader_hash = hashlib.sha256(extheader_data).digest()

        return NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=extheader_hash,
            extheader_size=0x400,
            flags=b"\x00" * 8,  # Encrypted
            exefs_offset=0x10,
            exefs_size=0x10,
        )

    @pytest.fixture
    def encrypted_ctx(self):
        """Create encrypted encryption context."""
        return EncryptionContext(
            encryption_type=EncryptionType.ORIGINAL_NCCH,
            normal_key=bytes(16),
            title_id=bytes(8),
        )

    @pytest.fixture
    def config(self):
        """Create basic config."""
        return ConversionConfig(
            input_file="test.cci",
            output_file="test.cia",
            key_provider=None,
            ignore_bad_hashes=False,
        )

    def test_re_encrypts_extheader_after_patching(
        self, service, ncch_header, encrypted_ctx, config
    ):
        """Test that extheader is re-encrypted after patching when originally encrypted."""
        extheader_data = bytes(0x400)
        service.ncch_reader.read_extheader.return_value = extheader_data
        service.hash_validator.validate_extheader_hash.return_value = True

        # Mock re-encryption
        re_encrypted = b"re_encrypted_data" + bytes(0x400 - 17)
        service.decryption_service.decrypt_extheader.return_value = re_encrypted

        key_y = bytes(16)
        patched_extheader, new_hash = service._read_and_validate_extheader(
            0x4000, ncch_header, encrypted_ctx, key_y, config
        )

        # Verify re-encryption was called
        service.decryption_service.decrypt_extheader.assert_called_once()
        # Result should be the re-encrypted data
        assert patched_extheader == re_encrypted


class TestExtractIconEncrypted:
    """Tests for _extract_icon with encrypted content."""

    @pytest.fixture
    def service(self):
        """Create service with mocked decryption service."""
        mock_ncch_reader = Mock(spec=NCCHReader)
        mock_ncch_reader.reader = Mock()
        mock_decryption_service = Mock(spec=DecryptionService)

        return ConversionService(
            ncsd_reader=Mock(),
            ncch_reader=mock_ncch_reader,
            exefs_reader=Mock(),
            cia_writer=Mock(),
            decryption_service=mock_decryption_service,
            hash_validator=Mock(),
            progress_reporter=MockProgressReporter(),
        )

    @pytest.fixture
    def ncch_header(self):
        """Create NCCH header with ExeFS offset."""
        return NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=b"\x00" * 8,  # Encrypted
            exefs_offset=0x10,
            exefs_size=0x10,
        )

    @pytest.fixture
    def encrypted_ctx(self):
        """Create encrypted encryption context."""
        return EncryptionContext(
            encryption_type=EncryptionType.ORIGINAL_NCCH,
            normal_key=bytes(16),
            title_id=bytes(8),
        )

    def test_decrypts_exefs_header_when_encrypted(self, service, ncch_header, encrypted_ctx):
        """Test that ExeFS header is decrypted when content is encrypted."""
        # Create mock encrypted header data
        encrypted_header = b"encrypted_header" + bytes(0x200 - 16)

        # Create decrypted header with icon file
        header_data = bytearray(0x200)
        header_data[0:8] = b"icon\x00\x00\x00\x00"
        header_data[8:12] = (0).to_bytes(4, "little")
        header_data[12:16] = (0x36C0).to_bytes(4, "little")

        # Mock the decrypt call
        service.decryption_service.decrypt_exefs.side_effect = [
            bytes(header_data),  # Decrypted header
            b"I" * 0x36C0,  # Decrypted icon
        ]

        # Mock the read calls
        icon_data = b"encrypted_icon" + b"X" * (0x36C0 - 14)
        service.ncch_reader.reader.read_at.side_effect = [encrypted_header, icon_data]

        key_y = bytes(16)
        service._extract_icon(0x4000, ncch_header, encrypted_ctx, key_y)

        # Verify decryption was called for header and icon
        assert service.decryption_service.decrypt_exefs.call_count == 2

        # First call should be for header with offset_in_blocks=0
        first_call = service.decryption_service.decrypt_exefs.call_args_list[0]
        assert first_call[1]["offset_in_blocks"] == 0

    def test_decrypts_icon_at_correct_offset(self, service, ncch_header, encrypted_ctx):
        """Test that icon is decrypted at correct offset when encrypted."""
        # Create mock header with icon at offset 0x1000
        header_data = bytearray(0x200)
        header_data[0:8] = b"icon\x00\x00\x00\x00"
        header_data[8:12] = (0x1000).to_bytes(4, "little")  # Icon at offset 0x1000
        header_data[12:16] = (0x36C0).to_bytes(4, "little")

        encrypted_icon = b"encrypted_icon" + b"X" * (0x36C0 - 14)
        decrypted_icon = b"I" * 0x36C0

        service.decryption_service.decrypt_exefs.side_effect = [
            bytes(header_data),  # Decrypted header
            decrypted_icon,  # Decrypted icon
        ]

        service.ncch_reader.reader.read_at.side_effect = [
            bytes(header_data),  # Header read
            encrypted_icon,  # Icon read
        ]

        key_y = bytes(16)
        icon = service._extract_icon(0x4000, ncch_header, encrypted_ctx, key_y)

        # Verify icon decryption was called with correct offset
        # offset_in_blocks = (0x1000 / 16) + 0x20 = 0x100 + 0x20 = 0x120
        second_call = service.decryption_service.decrypt_exefs.call_args_list[1]
        assert second_call[1]["offset_in_blocks"] == 0x120

        assert icon == decrypted_icon


class TestConvertWithEncryptedContent:
    """Tests for convert method with encrypted content."""

    @pytest.fixture
    def service(self):
        """Create service with all mocked dependencies including decryption."""
        cia_writer = Mock(spec=CIAWriter)
        cia_writer.dev_mode = False  # Add dev_mode attribute
        cia_writer.cert_chain = b"mock_cert_chain"  # Add cert_chain attribute
        cia_writer.writer = Mock()  # Add writer attribute with file
        cia_writer.writer.file = Mock()
        cia_writer.writer.file.tell = Mock(return_value=0)  # Make tell() return an integer
        return ConversionService(
            ncsd_reader=Mock(spec=NCSDReader),
            ncch_reader=Mock(spec=NCCHReader),
            exefs_reader=Mock(spec=ExeFSReader),
            cia_writer=cia_writer,
            decryption_service=Mock(spec=DecryptionService),
            hash_validator=Mock(spec=HashValidator),
            progress_reporter=MockProgressReporter(),
        )

    @pytest.fixture
    def config(self):
        """Create basic config."""
        return ConversionConfig(input_file="test.cci", output_file="test.cia", key_provider=None)

    @pytest.fixture
    def mock_container(self):
        """Create mock NCSD container."""
        return NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[
                NCSDPartition(offset=0x10, size=0x1000, partition_type="game"),
            ],
        )

    def test_reads_key_y_for_encrypted_content(self, service, config, mock_container):
        """Test that KeyY is read for encrypted (non-zerokey) content."""
        service.ncsd_reader.read_container.return_value = mock_container

        # Encrypted header
        ncch_header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=b"\x00" * 8,  # Encrypted (not decrypted, not zerokey)
            exefs_offset=0x10,
            exefs_size=0x10,
        )
        service.ncch_reader.read_header.return_value = ncch_header
        service.ncch_reader.read_key_y.return_value = bytes(16)
        service.ncch_reader.reader = Mock()

        # Mock other methods
        extheader_data = bytes(0x400)
        service.ncch_reader.read_extheader.return_value = extheader_data
        service.hash_validator.validate_extheader_hash.return_value = True
        service.decryption_service.decrypt_extheader.return_value = extheader_data
        service.decryption_service.decrypt_exefs.return_value = bytes(0x200)

        # Mock icon extraction
        header_data = bytearray(0x200)
        header_data[0:8] = b"icon\x00\x00\x00\x00"
        header_data[8:12] = (0).to_bytes(4, "little")
        header_data[12:16] = (0x36C0).to_bytes(4, "little")
        service.decryption_service.decrypt_exefs.side_effect = [
            bytes(header_data),
            b"I" * 0x36C0,
        ]
        service.ncch_reader.reader.read_at.side_effect = [bytes(0x200), b"I" * 0x36C0]

        # Call convert
        service.convert(config)

        # Verify KeyY was read
        service.ncch_reader.read_key_y.assert_called_once()


class TestReadAndValidateExtheader:
    """Tests for _read_and_validate_extheader method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies."""
        mock_ncch_reader = Mock(spec=NCCHReader)
        mock_hash_validator = Mock(spec=HashValidator)

        return ConversionService(
            ncsd_reader=Mock(),
            ncch_reader=mock_ncch_reader,
            exefs_reader=Mock(),
            cia_writer=Mock(),
            decryption_service=Mock(spec=DecryptionService),
            hash_validator=mock_hash_validator,
            progress_reporter=MockProgressReporter(),
        )

    @pytest.fixture
    def ncch_header(self):
        """Create NCCH header with extheader hash."""
        import hashlib

        extheader_data = b"test_extheader_data" + bytes(0x400 - 19)
        extheader_hash = hashlib.sha256(extheader_data).digest()

        return NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=extheader_hash,
            extheader_size=0x400,
            flags=b"\x00" * 8,
            exefs_offset=0x10,
            exefs_size=0x10,
        )

    @pytest.fixture
    def decrypted_ctx(self):
        """Create decrypted encryption context."""
        return EncryptionContext(
            encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=bytes(8)
        )

    @pytest.fixture
    def config(self):
        """Create basic config."""
        return ConversionConfig(
            input_file="test.cci",
            output_file="test.cia",
            key_provider=None,
            ignore_bad_hashes=False,
        )

    def test_reads_extheader_at_correct_offset(self, service, ncch_header, decrypted_ctx, config):
        """Test that extheader is read at correct offset (+0x200 from partition)."""
        game_cxi_offset = 0x4000
        extheader_data = b"test_extheader_data" + bytes(0x400 - 19)

        service.ncch_reader.read_extheader.return_value = extheader_data
        service.hash_validator.validate_extheader_hash.return_value = True

        service._read_and_validate_extheader(
            game_cxi_offset, ncch_header, decrypted_ctx, None, config
        )

        service.ncch_reader.read_extheader.assert_called_once()
        call_kwargs = service.ncch_reader.read_extheader.call_args[1]
        assert call_kwargs["offset"] == game_cxi_offset + 0x200
        assert call_kwargs["size"] == 0x400

    def test_decrypted_content_does_not_decrypt(self, service, ncch_header, decrypted_ctx, config):
        """Test that decrypted content is not decrypted again."""
        extheader_data = b"test_extheader_data" + bytes(0x400 - 19)
        service.ncch_reader.read_extheader.return_value = extheader_data
        service.hash_validator.validate_extheader_hash.return_value = True

        service._read_and_validate_extheader(0x4000, ncch_header, decrypted_ctx, None, config)

        call_kwargs = service.ncch_reader.read_extheader.call_args[1]
        assert call_kwargs["decrypt"] is False

    def test_validates_extheader_hash(self, service, ncch_header, decrypted_ctx, config):
        """Test that extheader hash is validated."""
        extheader_data = b"test_extheader_data" + bytes(0x400 - 19)
        service.ncch_reader.read_extheader.return_value = extheader_data
        service.hash_validator.validate_extheader_hash.return_value = True

        service._read_and_validate_extheader(0x4000, ncch_header, decrypted_ctx, None, config)

        service.hash_validator.validate_extheader_hash.assert_called_once_with(
            extheader_data, ncch_header.extheader_hash
        )

    def test_hash_validation_failure_raises_error(self, service, ncch_header, decrypted_ctx):
        """Test that hash validation failure raises ValueError."""
        extheader_data = b"test_extheader_data" + bytes(0x400 - 19)
        service.ncch_reader.read_extheader.return_value = extheader_data
        service.hash_validator.validate_extheader_hash.return_value = False

        config = ConversionConfig(
            input_file="test.cci",
            output_file="test.cia",
            key_provider=None,
            ignore_bad_hashes=False,  # Don't ignore hash failures
        )

        with pytest.raises(ValueError, match="Extended header hash validation failed"):
            service._read_and_validate_extheader(0x4000, ncch_header, decrypted_ctx, None, config)

    def test_ignore_bad_hashes_allows_invalid_hash(self, service, ncch_header, decrypted_ctx):
        """Test that ignore_bad_hashes config allows invalid hash."""
        extheader_data = b"test_extheader_data" + bytes(0x400 - 19)
        service.ncch_reader.read_extheader.return_value = extheader_data
        service.hash_validator.validate_extheader_hash.return_value = False

        config = ConversionConfig(
            input_file="test.cci",
            output_file="test.cia",
            key_provider=None,
            ignore_bad_hashes=True,  # Ignore hash failures
        )

        # Should not raise
        result = service._read_and_validate_extheader(
            0x4000, ncch_header, decrypted_ctx, None, config
        )
        assert result is not None

    def test_patches_extheader_for_sd_title(self, service, ncch_header, decrypted_ctx, config):
        """Test that extheader is patched to mark as SD title."""
        extheader_data = bytearray(0x400)
        extheader_data[0x0D] = 0x00  # System info flags
        service.ncch_reader.read_extheader.return_value = bytes(extheader_data)
        service.hash_validator.validate_extheader_hash.return_value = True

        patched_extheader, new_hash = service._read_and_validate_extheader(
            0x4000, ncch_header, decrypted_ctx, None, config
        )

        # Check that bit 1 was set in byte 0x0D
        assert patched_extheader[0x0D] & 0x02

    def test_returns_new_hash_after_patching(self, service, ncch_header, decrypted_ctx, config):
        """Test that method returns new hash after patching."""
        import hashlib

        extheader_data = bytearray(0x400)
        service.ncch_reader.read_extheader.return_value = bytes(extheader_data)
        service.hash_validator.validate_extheader_hash.return_value = True

        patched_extheader, new_hash = service._read_and_validate_extheader(
            0x4000, ncch_header, decrypted_ctx, None, config
        )

        # Compute expected hash
        expected_hash = hashlib.sha256(patched_extheader).digest()
        assert new_hash == expected_hash


class TestExtractIcon:
    """Tests for _extract_icon method."""

    @pytest.fixture
    def service(self):
        """Create service with mocked dependencies."""
        mock_ncch_reader = Mock(spec=NCCHReader)
        mock_ncch_reader.reader = Mock()

        return ConversionService(
            ncsd_reader=Mock(),
            ncch_reader=mock_ncch_reader,
            exefs_reader=Mock(),
            cia_writer=Mock(),
            decryption_service=Mock(spec=DecryptionService),
            hash_validator=Mock(),
            progress_reporter=MockProgressReporter(),
        )

    @pytest.fixture
    def ncch_header(self):
        """Create NCCH header with ExeFS offset."""
        return NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=b"\x00" * 8,
            exefs_offset=0x10,  # ExeFS at +0x2000 from partition start
            exefs_size=0x10,
        )

    @pytest.fixture
    def decrypted_ctx(self):
        """Create decrypted encryption context."""
        return EncryptionContext(
            encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=bytes(8)
        )

    def test_calculates_exefs_offset_correctly(self, service, ncch_header, decrypted_ctx):
        """Test that ExeFS offset is calculated correctly."""
        game_cxi_offset = 0x4000
        # ExeFS offset = game_cxi_offset + (exefs_offset_mu * 0x200)
        # = 0x4000 + (0x10 * 0x200) = 0x4000 + 0x2000 = 0x6000
        expected_exefs_offset = 0x6000

        # Create mock header data with icon file entry
        header_data = bytearray(0x200)
        # First file entry: "icon" at offset 0
        header_data[0:8] = b"icon\x00\x00\x00\x00"
        header_data[8:12] = (0).to_bytes(4, "little")  # offset
        header_data[12:16] = (0x36C0).to_bytes(4, "little")  # size

        service.ncch_reader.reader.read_at.return_value = bytes(header_data)

        # Need to make icon data available too
        icon_data = b"I" * 0x36C0
        service.ncch_reader.reader.read_at.side_effect = [bytes(header_data), icon_data]

        service._extract_icon(game_cxi_offset, ncch_header, decrypted_ctx, None)

        # Verify that header was read at correct offset
        calls = service.ncch_reader.reader.read_at.call_args_list
        assert calls[0][0][0] == expected_exefs_offset

    def test_finds_icon_file_in_exefs(self, service, ncch_header, decrypted_ctx):
        """Test that icon file is found in ExeFS."""
        # Create mock header data with icon file entry
        header_data = bytearray(0x200)
        # First file entry: "icon" at offset 0x1000
        header_data[0:8] = b"icon\x00\x00\x00\x00"
        header_data[8:12] = (0x1000).to_bytes(4, "little")  # offset
        header_data[12:16] = (0x36C0).to_bytes(4, "little")  # size

        icon_data = b"I" * 0x36C0
        service.ncch_reader.reader.read_at.side_effect = [bytes(header_data), icon_data]

        icon = service._extract_icon(0x4000, ncch_header, decrypted_ctx, None)

        assert len(icon) == 0x36C0
        assert icon == icon_data

    def test_raises_error_if_icon_not_found(self, service, ncch_header, decrypted_ctx):
        """Test that ValueError is raised if icon is not found."""
        # Create mock header data without icon file
        header_data = bytearray(0x200)
        # First file entry: "code" (not icon)
        header_data[0:8] = b"code\x00\x00\x00\x00"
        header_data[8:12] = (0).to_bytes(4, "little")
        header_data[12:16] = (0x1000).to_bytes(4, "little")

        service.ncch_reader.reader.read_at.return_value = bytes(header_data)

        with pytest.raises(ValueError, match="Icon file not found in ExeFS"):
            service._extract_icon(0x4000, ncch_header, decrypted_ctx, None)


class TestConvert:
    """Tests for the main convert method."""

    @pytest.fixture
    def service(self):
        """Create service with all mocked dependencies."""
        cia_writer = Mock(spec=CIAWriter)
        cia_writer.dev_mode = False  # Add dev_mode attribute
        cia_writer.cert_chain = b"mock_cert_chain"  # Add cert_chain attribute
        cia_writer.writer = Mock()  # Add writer attribute with file
        cia_writer.writer.file = Mock()
        cia_writer.writer.file.tell = Mock(return_value=0)  # Make tell() return an integer
        return ConversionService(
            ncsd_reader=Mock(spec=NCSDReader),
            ncch_reader=Mock(spec=NCCHReader),
            exefs_reader=Mock(spec=ExeFSReader),
            cia_writer=cia_writer,
            decryption_service=Mock(spec=DecryptionService),
            hash_validator=Mock(spec=HashValidator),
            progress_reporter=MockProgressReporter(),
        )

    @pytest.fixture
    def config(self):
        """Create basic config."""
        return ConversionConfig(input_file="test.cci", output_file="test.cia", key_provider=None)

    @pytest.fixture
    def mock_container(self):
        """Create mock NCSD container."""
        return NCSDContainer(
            magic=b"NCSD",
            title_id=bytes(8),
            partitions=[
                NCSDPartition(offset=0x10, size=0x1000, partition_type="game"),
            ],
        )

    def test_reports_progress_stages(self, service, config, mock_container):
        """Test that progress stages are reported correctly."""
        # Setup mocks
        service.ncsd_reader.read_container.return_value = mock_container

        ncch_header = NCCHHeader(
            signature=bytes(0x100),
            magic=b"NCCH",
            content_size=0x1000,
            partition_id=bytes(8),
            maker_code=b"01",
            version=0,
            program_id=bytes(8),
            extheader_hash=bytes(0x20),
            extheader_size=0x400,
            flags=b"\x00" * 7 + b"\x04",  # Decrypted
            exefs_offset=0x10,
            exefs_size=0x10,
        )
        service.ncch_reader.read_header.return_value = ncch_header
        service.ncch_reader.reader = Mock()

        # Mock other methods to avoid errors
        extheader_data = bytes(0x400)
        service.ncch_reader.read_extheader.return_value = extheader_data
        service.hash_validator.validate_extheader_hash.return_value = True

        # Mock icon extraction
        header_data = bytearray(0x200)
        header_data[0:8] = b"icon\x00\x00\x00\x00"
        header_data[8:12] = (0).to_bytes(4, "little")
        header_data[12:16] = (0x36C0).to_bytes(4, "little")
        icon_data = b"I" * 0x36C0
        service.ncch_reader.reader.read_at.side_effect = [bytes(header_data), icon_data]

        # Call convert
        service.convert(config)

        # Check that all stages were reported
        reporter = service.progress_reporter
        assert len(reporter.stages) == 5
        assert "Reading CCI structure" in reporter.stages
        assert "Analyzing encryption" in reporter.stages
        assert "Verifying ExtHeader" in reporter.stages
        assert "Getting SMDH" in reporter.stages
        assert "Writing CIA" in reporter.stages

    def test_raises_error_if_no_game_partition(self, service, config):
        """Test that ValueError is raised if no game partition found."""
        # Container with no partitions
        container = NCSDContainer(magic=b"NCSD", title_id=bytes(8), partitions=[])
        service.ncsd_reader.read_container.return_value = container

        with pytest.raises(ValueError, match="No game partition found"):
            service.convert(config)
