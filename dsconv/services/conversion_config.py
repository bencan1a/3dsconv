"""
Conversion configuration for 3dsconv.

This module defines the configuration dataclass for CCI to CIA conversion.
It encapsulates all conversion parameters and provides validation.
"""

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dsconv.crypto.key_provider import IKeyProvider


@dataclass
class ConversionConfig:
    """Configuration for CCI to CIA conversion.

    This dataclass encapsulates all parameters needed for converting a
    Nintendo 3DS CCI file to CIA format. It includes input/output paths,
    encryption settings, and various conversion options.

    Attributes:
        input_file: Path to the input CCI file
        output_file: Path for the output CIA file
        key_provider: Optional key provider for encryption/decryption operations
        ignore_bad_hashes: If True, ignore hash validation failures
        ignore_encryption: If True, ignore encryption status and convert anyway
        dev_keys: If True, use development keys instead of retail keys
        verbose: If True, enable verbose output during conversion
    """

    input_file: str
    output_file: str
    key_provider: "IKeyProvider | None"
    ignore_bad_hashes: bool = False
    ignore_encryption: bool = False
    dev_keys: bool = False
    verbose: bool = False

    def validate(self) -> None:
        """Validate the configuration.

        Checks that the input file exists and is accessible.

        Raises:
            FileNotFoundError: If the input file does not exist
        """
        if not os.path.isfile(self.input_file):
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
