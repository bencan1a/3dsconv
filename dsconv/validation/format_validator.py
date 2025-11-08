"""Format validation service for file structures."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dsconv.models import NCSDPartition


class FormatValidator:
    """Validates file format structures.

    This service provides static methods for validating magic bytes and
    structural integrity of Nintendo 3DS file formats (NCSD, NCCH).

    All methods are static and have no side effects, making them easy to
    test and use throughout the application.
    """

    @staticmethod
    def validate_ncsd_magic(magic: bytes) -> None:
        """Validate NCSD magic bytes.

        Validates that the provided magic bytes match the expected NCSD
        format magic value 'NCSD'. The NCSD format is used for CCI files
        (3DS game cards).

        Args:
            magic: The magic bytes to validate (should be 4 bytes)

        Raises:
            ValueError: If magic bytes don't match b'NCSD'

        Example:
            >>> FormatValidator.validate_ncsd_magic(b'NCSD')  # OK
            >>> FormatValidator.validate_ncsd_magic(b'XXXX')  # Raises ValueError
        """
        if magic != b"NCSD":
            raise ValueError("Invalid NCSD magic, not a CCI file")

    @staticmethod
    def validate_ncch_magic(magic: bytes) -> None:
        """Validate NCCH magic bytes.

        Validates that the provided magic bytes match the expected NCCH
        format magic value 'NCCH'. The NCCH format is used for partitions
        within CCI files and for CIA content.

        Args:
            magic: The magic bytes to validate (should be 4 bytes)

        Raises:
            ValueError: If magic bytes don't match b'NCCH'

        Example:
            >>> FormatValidator.validate_ncch_magic(b'NCCH')  # OK
            >>> FormatValidator.validate_ncch_magic(b'XXXX')  # Raises ValueError
        """
        if magic != b"NCCH":
            raise ValueError("Invalid NCCH magic, not a valid partition")

    @staticmethod
    def validate_partition_exists(partition: "NCSDPartition | None") -> None:
        """Validate that required partition exists.

        Validates that a partition object is not None, ensuring that
        required partitions (typically the game executable partition)
        are present in the NCSD container.

        Args:
            partition: The partition to validate (or None)

        Raises:
            ValueError: If partition is None

        Example:
            >>> partition = NCSDPartition(offset=0, size=100, partition_type='game')
            >>> FormatValidator.validate_partition_exists(partition)  # OK
            >>> FormatValidator.validate_partition_exists(None)  # Raises ValueError
        """
        if partition is None:
            raise ValueError("Required partition not found")
