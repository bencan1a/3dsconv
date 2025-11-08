"""Main conversion service orchestrating CCI to CIA conversion.

This module provides the ConversionService class which orchestrates the entire
workflow of converting Nintendo 3DS CCI (CTR Cart Image) files to CIA
(CTR Importable Archive) format.

The service follows clean architecture principles with dependency injection
for all components, making it highly testable and maintainable.
"""

import hashlib
import struct
from typing import TYPE_CHECKING

from dsconv.crypto.decryption_service import DecryptionService
from dsconv.io.cia_writer import CIAWriter
from dsconv.io.exefs_reader import ExeFSReader
from dsconv.io.ncch_reader import NCCHReader
from dsconv.io.ncsd_reader import NCSDReader
from dsconv.models.encryption import EncryptionContext, EncryptionType
from dsconv.models.ncch import NCCHHeader
from dsconv.models.ncsd import NCSDContainer, NCSDPartition
from dsconv.services.conversion_config import ConversionConfig
from dsconv.services.progress_reporter import IProgressReporter
from dsconv.validation.hash_validator import HashValidator

if TYPE_CHECKING:
    pass


class ConversionService:
    """Main service orchestrating CCI to CIA conversion.

    This service coordinates the entire conversion workflow, using injected
    dependencies for all I/O, cryptography, validation, and progress reporting.
    It implements a clear multi-stage workflow:

    1. Read and validate CCI structure
    2. Analyze encryption and derive keys
    3. Read and validate extended header
    4. Extract icon from ExeFS
    5. Write CIA file with all content

    All dependencies are injected via the constructor, following the
    dependency inversion principle. This makes the service highly testable
    by allowing mock implementations for testing.

    Attributes:
        ncsd_reader: Reader for NCSD container structure
        ncch_reader: Reader for NCCH headers and content
        exefs_reader: Reader for ExeFS filesystem
        cia_writer: Writer for CIA file output
        decryption_service: Service for decrypting encrypted content (optional)
        hash_validator: Service for validating SHA-256 hashes
        progress_reporter: Interface for reporting progress to user

    Example:
        >>> service = ConversionService(
        ...     ncsd_reader=ncsd_reader,
        ...     ncch_reader=ncch_reader,
        ...     exefs_reader=exefs_reader,
        ...     cia_writer=cia_writer,
        ...     decryption_service=decryption_service,
        ...     hash_validator=hash_validator,
        ...     progress_reporter=progress_reporter
        ... )
        >>> service.convert(config)
    """

    def __init__(
        self,
        ncsd_reader: NCSDReader,
        ncch_reader: NCCHReader,
        exefs_reader: ExeFSReader,
        cia_writer: CIAWriter,
        decryption_service: DecryptionService | None,
        hash_validator: HashValidator,
        progress_reporter: IProgressReporter,
    ):
        """Initialize ConversionService with all dependencies.

        Args:
            ncsd_reader: Reader for NCSD container structure
            ncch_reader: Reader for NCCH headers and content
            exefs_reader: Reader for ExeFS filesystem
            cia_writer: Writer for CIA file output
            decryption_service: Optional service for decrypting encrypted content.
                               Required for encrypted ROMs, None for decrypted ROMs.
            hash_validator: Service for validating SHA-256 hashes
            progress_reporter: Interface for reporting conversion progress
        """
        self.ncsd_reader = ncsd_reader
        self.ncch_reader = ncch_reader
        self.exefs_reader = exefs_reader
        self.cia_writer = cia_writer
        self.decryption_service = decryption_service
        self.hash_validator = hash_validator
        self.progress_reporter = progress_reporter

    def convert(self, config: ConversionConfig) -> None:
        """Execute conversion from CCI to CIA.

        This is the main entry point for the conversion workflow. It orchestrates
        all stages of the conversion process, from reading the input CCI file
        to writing the output CIA file.

        The conversion follows these stages:
        1. Read and validate CCI structure
        2. Determine encryption type and derive keys if needed
        3. Read and validate extended header
        4. Extract icon from ExeFS
        5. Build and write CIA file

        Args:
            config: ConversionConfig object with all conversion parameters

        Raises:
            ValueError: If CCI file is invalid or encryption keys are missing
            FileNotFoundError: If input file doesn't exist
            IOError: If there are file I/O errors during conversion
        """
        # Stage 1: Read and validate CCI structure
        self.progress_reporter.report_stage("Reading CCI structure")
        container = self.ncsd_reader.read_container()

        # Get the game partition (first partition)
        game_partition = container.get_game_partition()
        if game_partition is None:
            raise ValueError("No game partition found in CCI file")

        # Calculate game partition offset in bytes (partition offsets are in media units)
        game_cxi_offset = game_partition.offset * 0x200

        # Stage 2: Read NCCH header and determine encryption
        self.progress_reporter.report_stage("Analyzing encryption")
        ncch_header = self.ncch_reader.read_header(offset=game_cxi_offset)
        encryption_ctx = self._determine_encryption(
            ncch_header, container.title_id, config, game_cxi_offset
        )

        # Read KeyY if needed for encryption
        key_y = None
        if encryption_ctx.needs_decryption and not encryption_ctx.is_zerokey:
            key_y = self.ncch_reader.read_key_y(game_cxi_offset)

        # Stage 3: Read and validate extended header
        self.progress_reporter.report_stage("Verifying ExtHeader")
        extheader, extheader_hash = self._read_and_validate_extheader(
            game_cxi_offset, ncch_header, encryption_ctx, key_y, config
        )

        # Stage 4: Extract icon from ExeFS
        self.progress_reporter.report_stage("Getting SMDH")
        icon = self._extract_icon(game_cxi_offset, ncch_header, encryption_ctx, key_y)

        # Stage 5: Write CIA
        self.progress_reporter.report_stage("Writing CIA")
        self._write_cia(
            container, game_partition, ncch_header, extheader, extheader_hash, icon, encryption_ctx
        )

    def _determine_encryption(
        self,
        ncch_header: NCCHHeader,
        title_id: bytes,
        config: ConversionConfig,
        partition_offset: int,
    ) -> EncryptionContext:
        """Determine encryption type and setup encryption context.

        Analyzes the NCCH header encryption flags to determine the encryption
        type. If encryption is used and not ignored, stores the title ID
        for later use in decryption.

        Note: The normal key is not derived here because the DecryptionService
        derives it on-the-fly during decryption. We only need to track the
        encryption type and title ID.

        Args:
            ncch_header: NCCH header containing encryption flags
            title_id: Title ID for key derivation
            config: Conversion configuration
            partition_offset: Offset to the NCCH partition (needed to read KeyY)

        Returns:
            EncryptionContext with encryption type and title ID

        Raises:
            ValueError: If ROM is encrypted but no decryption service available
        """
        # Check if encryption is ignored by config
        if config.ignore_encryption:
            return EncryptionContext(
                encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=title_id
            )

        # Check if content is already decrypted
        if not ncch_header.is_encrypted:
            return EncryptionContext(
                encryption_type=EncryptionType.DECRYPTED, normal_key=None, title_id=title_id
            )

        # Content is encrypted - check if we have decryption support
        if self.decryption_service is None:
            raise ValueError(
                "ROM is encrypted but no decryption service available. "
                "Ensure pyaes is installed and valid keys (prod.keys or boot9) are provided."
            )

        # Determine encryption type (zerokey vs original NCCH)
        if ncch_header.uses_zerokey:
            # Zero-key encryption uses a key of all zeros
            return EncryptionContext(
                encryption_type=EncryptionType.ZEROKEY, normal_key=bytes(16), title_id=title_id
            )
        else:
            # Original NCCH encryption
            # KeyY is stored in the first 16 bytes of the NCCH signature
            # We'll use the decryption service to derive the key during decryption
            return EncryptionContext(
                encryption_type=EncryptionType.ORIGINAL_NCCH, normal_key=None, title_id=title_id
            )

    def _read_and_validate_extheader(
        self,
        game_cxi_offset: int,
        ncch_header: NCCHHeader,
        encryption_ctx: EncryptionContext,
        key_y: bytes | None,
        config: ConversionConfig,
    ) -> tuple[bytes, bytes]:
        """Read extended header and validate its hash.

        Reads the extended header from the NCCH, decrypting it if necessary.
        Validates the hash against the expected hash stored in the NCCH header.
        Patches the extended header to mark it as an SD title.

        Args:
            game_cxi_offset: Offset to game CXI partition in bytes
            ncch_header: NCCH header containing hash
            encryption_ctx: Encryption context with encryption type
            key_y: KeyY for decryption (None if not needed)
            config: Conversion configuration

        Returns:
            Tuple of (patched_extheader, new_extheader_hash)

        Raises:
            ValueError: If extended header hash validation fails
        """
        # Read extended header (0x400 bytes at offset +0x200 from NCCH)
        extheader = self.ncch_reader.read_extheader(
            offset=game_cxi_offset + 0x200,
            size=0x400,
            decrypt=encryption_ctx.needs_decryption,
            decryption_service=self.decryption_service if encryption_ctx.needs_decryption else None,
            key_y=key_y if encryption_ctx.needs_decryption else None,
            title_id=encryption_ctx.title_id if encryption_ctx.needs_decryption else None,
        )

        # Validate extended header hash
        expected_hash = ncch_header.extheader_hash

        if not self.hash_validator.validate_extheader_hash(extheader, expected_hash):
            if not config.ignore_bad_hashes:
                raise ValueError(
                    "Extended header hash validation failed. "
                    "The file may be corrupt or incorrectly decrypted. "
                    "Use --ignore-bad-hashes to convert anyway."
                )

        # Patch extended header to make it an SD title
        # Set bit 1 of byte 0x0D (System Info flags)
        extheader_list = list(extheader)
        extheader_list[0x0D] |= 2
        extheader = bytes(extheader_list)

        # Compute new hash after patching
        new_extheader_hash = hashlib.sha256(extheader).digest()

        # Re-encrypt extended header if it was encrypted
        # Use the DecryptionService's decrypt method to re-encrypt
        # (AES-CTR mode: encryption and decryption are the same operation)
        if encryption_ctx.needs_decryption and self.decryption_service and key_y:
            extheader = self.decryption_service.decrypt_extheader(
                extheader, key_y, encryption_ctx.title_id
            )

        return extheader, new_extheader_hash

    def _extract_icon(
        self,
        game_cxi_offset: int,
        ncch_header: NCCHHeader,
        encryption_ctx: EncryptionContext,
        key_y: bytes | None,
    ) -> bytes:
        """Extract SMDH icon from ExeFS.

        Reads the ExeFS filesystem and extracts the icon file (SMDH).
        The icon is required for CIA files.

        Args:
            game_cxi_offset: Offset to game CXI partition in bytes
            ncch_header: NCCH header containing ExeFS offset
            encryption_ctx: Encryption context with encryption type
            key_y: KeyY for decryption (None if not needed)

        Returns:
            Icon data as bytes (0x36C0 bytes)

        Raises:
            ValueError: If icon file is not found in ExeFS
        """
        # Get ExeFS offset from NCCH header (stored in media units)
        exefs_offset = game_cxi_offset + (ncch_header.exefs_offset * 0x200)

        # Read raw header data
        header_data = self.ncch_reader.reader.read_at(exefs_offset, 0x200)

        # Decrypt header if needed
        if encryption_ctx.needs_decryption and self.decryption_service and key_y:
            header_data = self.decryption_service.decrypt_exefs(
                header_data, key_y, encryption_ctx.title_id, offset_in_blocks=0
            )

        # Parse file headers manually (simplified version)
        file_headers = []
        for i in range(10):
            header_offset = i * 0x10
            header_entry = header_data[header_offset : header_offset + 0x10]

            # Extract name (8 bytes, null-padded ASCII)
            name_bytes = header_entry[0:8]
            name = name_bytes.rstrip(b"\x00").decode("ascii", errors="ignore")

            if not name:
                continue

            # Extract offset and size (little-endian uint32)
            (file_offset, file_size) = struct.unpack("<II", header_entry[8:16])

            from dsconv.io.exefs_reader import ExeFSFile

            file_headers.append(ExeFSFile(name=name, offset=file_offset, size=file_size))

        # Find the icon file
        icon_file = None
        for file_header in file_headers:
            if file_header.name == "icon":
                icon_file = file_header
                break

        if icon_file is None:
            raise ValueError("Icon file not found in ExeFS")

        # Read icon data
        # Icon is at exefs_offset + 0x200 (header size) + icon_file.offset
        data_section_start = exefs_offset + 0x200
        icon_absolute_offset = data_section_start + icon_file.offset
        icon = self.ncch_reader.reader.read_at(icon_absolute_offset, icon_file.size)

        # Decrypt icon if needed
        if encryption_ctx.needs_decryption and self.decryption_service and key_y:
            # Calculate offset in blocks for icon
            # offset_in_blocks = (icon_file.offset / 16) + 0x20 (for 0x200 byte header)
            offset_in_blocks = (icon_file.offset // 16) + 0x20
            icon = self.decryption_service.decrypt_exefs(
                icon, key_y, encryption_ctx.title_id, offset_in_blocks=offset_in_blocks
            )

        return icon

    def _write_cia(
        self,
        container: NCSDContainer,
        game_partition: NCSDPartition,
        ncch_header: NCCHHeader,
        extheader: bytes,
        extheader_hash: bytes,
        icon: bytes,
        encryption_ctx: EncryptionContext,
    ) -> None:
        """Write CIA file with all content.

        Builds the complete CIA file structure including header, certificate chain,
        ticket, TMD, and content sections.

        Args:
            container: NCSD container with partition info
            game_partition: Game executable partition
            ncch_header: NCCH header for game partition
            extheader: Patched and optionally re-encrypted extended header
            extheader_hash: Hash of patched extended header
            icon: Icon data from ExeFS
            encryption_ctx: Encryption context
        """
        # TODO: Implement CIA writing
        # This will be implemented by calling methods on cia_writer
        # and coordinating with other readers to copy content sections
        pass
