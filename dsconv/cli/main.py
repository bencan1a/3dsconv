"""Refactored CLI implementation using modular architecture."""


from dsconv.cli.config_mapper import CLIConfigMapper
from dsconv.services.service_factory import ServiceFactory
from dsconv.utils import parse_args


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

    # Process each game file
    total_files = len(args.game)
    processed_files = 0

    for game_file in args.game:
        try:
            # Map CLI args to domain configuration
            config = CLIConfigMapper.map_to_conversion_config(args, game_file)

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


if __name__ == "__main__":
    main()
