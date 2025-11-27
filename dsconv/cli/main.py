"""Refactored CLI implementation using modular architecture."""

import sys

from dsconv.cli.config_mapper import CLIConfigMapper
from dsconv.services.service_factory import ServiceFactory
from dsconv.utils import discover_cci_files, parse_args


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

        except Exception as e:
            print(f"Error converting {game_file}: {e}")
            continue

    print(f"Done converting {processed_files} out of {total_files} files.")


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
