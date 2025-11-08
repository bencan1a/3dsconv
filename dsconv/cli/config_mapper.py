"""CLI Configuration Mapper for 3dsconv.

This module maps CLI arguments from argparse to domain configuration objects.
It handles key provider auto-detection and output file path determination.
"""

import argparse
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dsconv.crypto.key_provider import IKeyProvider

from dsconv.services.conversion_config import ConversionConfig


class CLIConfigMapper:
    """Maps CLI arguments to domain configuration.

    This class provides static methods to convert argparse.Namespace objects
    (from parse_args()) into ConversionConfig domain objects. It handles:
    - Key provider selection and auto-detection
    - Output file path determination
    - Mapping of all CLI flags to config fields
    """

    @staticmethod
    def map_to_conversion_config(
        args: argparse.Namespace, input_file: str | None = None
    ) -> ConversionConfig:
        """Convert CLI args to conversion configuration.

        Args:
            args: Parsed command-line arguments from parse_args()
            input_file: Optional specific input file to use. If None, uses args.game[0]

        Returns:
            ConversionConfig object with all settings from CLI

        Raises:
            IndexError: If args.game is empty and input_file is None
        """
        # Determine input file
        if input_file is None:
            if not args.game or len(args.game) == 0:
                raise IndexError("No input file specified")
            input_file = args.game[0]

        # Type narrowing: input_file is guaranteed to be str at this point
        assert input_file is not None

        # Determine output file path
        output_file = CLIConfigMapper._determine_output_path(input_file, args.output)

        # Create appropriate key provider
        key_provider = CLIConfigMapper._create_key_provider(args)

        return ConversionConfig(
            input_file=input_file,
            output_file=output_file,
            key_provider=key_provider,
            ignore_bad_hashes=args.ignore_bad_hashes,
            ignore_encryption=args.ignore_encryption,
            dev_keys=args.dev_keys,
            verbose=args.verbose,
        )

    @staticmethod
    def _create_key_provider(args: argparse.Namespace) -> "IKeyProvider | None":
        """Create appropriate key provider based on args.

        Priority order:
        1. Use --prod-keys if specified
        2. Use --boot9 if specified
        3. Auto-detect from common locations

        Args:
            args: Parsed command-line arguments

        Returns:
            Appropriate key provider or None if no keys are available/needed
        """
        # Lazy import to reduce initial module loading time
        from dsconv.crypto.key_provider import Boot9KeyProvider, ProdKeysKeyProvider
        
        # Priority 1: Explicit prod.keys path
        if hasattr(args, "prod_keys") and args.prod_keys:
            # Check if file exists before creating provider
            if os.path.isfile(args.prod_keys):
                return ProdKeysKeyProvider(args.prod_keys)

        # Priority 2: Explicit boot9 path
        if hasattr(args, "boot9") and args.boot9:
            # Check if file exists before creating provider
            if os.path.isfile(args.boot9):
                return Boot9KeyProvider(args.boot9, args.dev_keys)

        # Priority 3: Auto-detect
        return CLIConfigMapper._auto_detect_key_provider(args.dev_keys)

    @staticmethod
    def _auto_detect_key_provider(dev_keys: bool = False) -> "IKeyProvider | None":
        """Auto-detect available key source from common locations.

        Args:
            dev_keys: If True, look for development keys; if False, look for retail keys

        Returns:
            Appropriate key provider or None if no keys found

        Search order:
        1. prod.keys in current directory
        2. prod.keys in ~/.3ds/
        3. boot9.bin in current directory
        4. boot9_prot.bin in current directory
        5. boot9.bin in ~/.3ds/
        6. boot9_prot.bin in ~/.3ds/
        """
        # Lazy import to reduce initial module loading time
        from dsconv.crypto.key_provider import Boot9KeyProvider, ProdKeysKeyProvider
        
        # Try prod.keys locations first
        prod_keys_paths = [
            "prod.keys",
            os.path.expanduser("~/.3ds/prod.keys"),
        ]

        for path in prod_keys_paths:
            if os.path.isfile(path):
                try:
                    return ProdKeysKeyProvider(path)
                except Exception:
                    # If this prod.keys file is invalid, try next location
                    continue

        # Try boot9 locations
        boot9_paths = [
            "boot9.bin",
            "boot9_prot.bin",
            os.path.expanduser("~/.3ds/boot9.bin"),
            os.path.expanduser("~/.3ds/boot9_prot.bin"),
        ]

        for path in boot9_paths:
            if os.path.isfile(path):
                try:
                    return Boot9KeyProvider(path, dev_keys)
                except Exception:
                    # If this boot9 file is invalid, try next location
                    continue

        # No valid key source found
        return None

    @staticmethod
    def _determine_output_path(input_file: str, output_dir: str) -> str:
        """Determine output CIA file path.

        Args:
            input_file: Path to input CCI file
            output_dir: Output directory (empty string means current directory)

        Returns:
            Full path to output CIA file
        """
        # Get the base filename without extension
        rom_name = os.path.basename(os.path.splitext(input_file)[0])

        # Create output filename with .cia extension
        output_filename = rom_name + ".cia"

        # Determine output directory
        if output_dir:
            # Use specified output directory
            return os.path.join(output_dir, output_filename)
        else:
            # Use current directory
            return output_filename
