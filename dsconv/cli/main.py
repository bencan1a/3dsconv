"""Refactored CLI implementation using modular architecture."""

import os
import sys

from dsconv.cli.config_mapper import CLIConfigMapper
from dsconv.services.service_factory import ServiceFactory
from dsconv.utils import (
    convert_cia_to_cxi,
    discover_cci_files,
    find_ctrtool,
    parse_args,
)


def main() -> None:
    """Main entry point for refactored 3dsconv CLI.

    This is the new modular implementation that replaces the original
    monolithic 3dsconv.py. It uses dependency injection, clean architecture,
    and separates concerns across models, crypto, I/O, and services layers.
    """
    # Parse arguments
    args = parse_args()

    # Handle deprecated options
    if hasattr(args, "use_deprecated") and args.use_deprecated:
        print(
            "Note: Deprecated options are being used. XORpads are no longer "
            "supported. See the README at https://github.com/ihaveamac/3dsconv "
            "for more details."
        )
        return

    # Check ctrtool availability early if --to-cxi is specified
    ctrtool_path = None
    if args.to_cxi:
        ctrtool_path = find_ctrtool(args.ctrtool_path)
        if not ctrtool_path:
            print(
                "Error: ctrtool not found. Please install ctrtool and ensure it is in your PATH, "
                "or specify its location with --ctrtool-path."
            )
            sys.exit(1)
        if args.verbose:
            print(f"Using ctrtool: {ctrtool_path}")

    # Determine the list of game files to process
    game_files, is_batch_mode = _get_game_files(args)

    if not game_files:
        if is_batch_mode:
            # In batch mode, empty folder is not an error - just a warning
            print("Done converting 0 out of 0 files.")
            return
        else:
            print(
                "Error: No input files specified. Use --batch <folder> or provide game file(s) as positional arguments."
            )
            sys.exit(1)

    # Process each game file
    total_files = len(game_files)
    processed_files = 0
    converted_cia_files = []  # Track successfully converted CIA files for CXI extraction

    for game_file in game_files:
        try:
            # Map CLI args to domain configuration
            # For batch mode, use batch folder as default output if no --output specified
            config = CLIConfigMapper.map_to_conversion_config(
                args, game_file, batch_folder=args.batch
            )

            # Ensure output file path is determined
            output_file = config.output_file

            # Create conversion service with all dependencies
            service = ServiceFactory.create_conversion_service(game_file, output_file, config)

            # Execute conversion
            service.convert(config)
            processed_files += 1
            converted_cia_files.append(output_file)

        except Exception as e:
            print(f"Error converting {game_file}: {e}")
            continue

    print(f"Done converting {processed_files} out of {total_files} files.")

    # Extract CXI from converted CIA files if --to-cxi was specified
    if args.to_cxi and converted_cia_files and ctrtool_path is not None:
        print("\nExtracting CXI files...")
        cxi_success = 0
        for cia_file in converted_cia_files:
            # Determine output directory for CXI extraction
            output_dir = None
            if args.output:
                output_dir = args.output
            else:
                output_dir = os.path.dirname(os.path.abspath(cia_file))
            success, msg = convert_cia_to_cxi(
                ctrtool_path, cia_file, output_dir=output_dir, verbose=args.verbose
            )
            if success:
                cxi_success += 1
            else:
                print(f"Error extracting CXI from {cia_file}: {msg}")
        print(f"Done extracting {cxi_success} out of {len(converted_cia_files)} CXI files.")


def _get_game_files(args) -> tuple[list[str], bool]:
    """Get the list of game files to process based on args.

    Args:
        args: Parsed command-line arguments

    Returns:
        Tuple of (list of game file paths, is_batch_mode flag)

    Raises:
        SystemExit: If batch folder doesn't exist or is not a directory
    """
    # Batch mode: discover files from folder
    if args.batch:
        try:
            cci_files = discover_cci_files(args.batch)
            if not cci_files:
                print(f"Warning: No CCI files found in batch folder: {args.batch}")
            return cci_files, True
        except (FileNotFoundError, NotADirectoryError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Normal mode: use provided game files
    return args.game, False


if __name__ == "__main__":
    main()
