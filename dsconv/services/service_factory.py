"""Factory for creating conversion services with all dependencies.

This module provides the ServiceFactory class which creates fully configured
ConversionService instances with all required dependencies properly wired together.
This follows the dependency injection pattern and centralizes the complex
object graph construction.
"""

import os

from dsconv.crypto.certchain_provider import CertChainProvider
from dsconv.crypto.decryption_service import DecryptionService
from dsconv.crypto.key_derivation import KeyDerivationService
from dsconv.io.binary_reader import BinaryReader
from dsconv.io.binary_writer import BinaryWriter
from dsconv.io.cia_writer import CIAWriter
from dsconv.io.exefs_reader import ExeFSReader
from dsconv.io.ncch_reader import NCCHReader
from dsconv.io.ncsd_reader import NCSDReader
from dsconv.services.conversion_config import ConversionConfig
from dsconv.services.conversion_service import ConversionService
from dsconv.services.progress_reporter import ConsoleProgressReporter, IProgressReporter
from dsconv.validation.hash_validator import HashValidator


class ServiceFactory:
    """Factory for creating conversion services with dependencies.

    This factory is responsible for creating ConversionService instances
    with all required dependencies properly configured and injected. It
    handles:
    - Opening input/output files
    - Creating readers and writers
    - Setting up crypto services if keys are available
    - Configuring validation and progress reporting

    Example:
        >>> service = ServiceFactory.create_conversion_service(
        ...     "game.cci",
        ...     "game.cia",
        ...     config
        ... )
        >>> service.convert(config)
    """

    @staticmethod
    def create_conversion_service(
        input_file: str,
        output_file: str,
        config: ConversionConfig,
    ) -> ConversionService:
        """Create fully configured conversion service.

        This method creates and wires together all the dependencies needed
        for a complete CCI to CIA conversion:
        - Binary readers and writers
        - Format-specific readers (NCSD, NCCH, ExeFS)
        - CIA writer
        - Crypto services (if keys are available)
        - Hash validator
        - Progress reporter

        Args:
            input_file: Path to input CCI file
            output_file: Path to output CIA file
            config: ConversionConfig with all conversion parameters

        Returns:
            Fully configured ConversionService ready for conversion

        Raises:
            FileNotFoundError: If input file doesn't exist
            IOError: If files cannot be opened
        """
        # Validate input file exists
        if not os.path.isfile(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # Create output directory if needed
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Open files
        input_handle = open(input_file, "rb")
        output_handle = open(output_file, "wb")

        # Create readers
        binary_reader = BinaryReader(input_handle)
        ncsd_reader = NCSDReader(binary_reader)
        ncch_reader = NCCHReader(binary_reader)
        exefs_reader = ExeFSReader(binary_reader)

        # Create writers
        binary_writer = BinaryWriter(output_handle)

        # Load certificate chain using CertChainProvider
        if config.dev_keys:
            certchain = CertChainProvider.get_dev_certchain()
        else:
            certchain = CertChainProvider.get_retail_certchain()

        cia_writer = CIAWriter(binary_writer, certchain, config.dev_keys)

        # Create crypto services if key provider is available
        decryption_service = None
        if config.key_provider:
            try:
                from dsconv.crypto.aes_adapter import PyAESAdapter

                orig_key = config.key_provider.get_original_ncch_key()
                key_derivation = KeyDerivationService(orig_key)

                # Create AES cipher factory
                def aes_cipher_factory(key: bytes, counter_value: int):
                    """Factory for creating AES-CTR ciphers."""
                    return PyAESAdapter(key, counter_value)

                decryption_service = DecryptionService(key_derivation, aes_cipher_factory)
            except Exception as e:
                # If key loading fails, continue without decryption
                # (will fail later if encrypted content is encountered)
                if config.verbose:
                    print(f"Warning: Could not load encryption keys: {e}")

        # Create validator
        hash_validator = HashValidator(config.ignore_bad_hashes)

        # Create progress reporter
        progress_reporter: IProgressReporter = ConsoleProgressReporter(config.verbose)

        return ConversionService(
            ncsd_reader=ncsd_reader,
            ncch_reader=ncch_reader,
            exefs_reader=exefs_reader,
            cia_writer=cia_writer,
            decryption_service=decryption_service,
            hash_validator=hash_validator,
            progress_reporter=progress_reporter,
        )
