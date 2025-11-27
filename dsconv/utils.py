"""
Testable utilities extracted from 3dsconv.

This module contains pure or near-pure functions that can be tested independently
without triggering the main script execution.
"""

import argparse
import os
import sys


def parse_args() -> argparse.Namespace:
    """Parses and returns the command-line arguments"""

    parser = argparse.ArgumentParser(
        prog="3dsconv.py", description="Convert Nintendo 3DS CCI (.3ds/.cci) to CIA"
    )

    parser.add_argument(
        "-o",
        "--output",
        metavar="output-directory",
        default="",
        help="Save converted files in specified directory (default: current directory)",
    )

    parser.add_argument(
        "-b",
        "--boot9",
        metavar="path-to-boot9",
        default=os.environ.get("BOOT9_PATH"),
        help="Path to dump of ARM9 bootROM, protected or full",
    )

    parser.add_argument(
        "-p",
        "--prod-keys",
        metavar="path-to-prod-keys",
        default=os.environ.get("PROD_KEYS_PATH"),
        help="Path to prod.keys file containing encryption keys",
    )

    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing converted files"
    )

    parser.add_argument(
        "--ignore-bad-hashes",
        action="store_true",
        help="Ignore invalid hashes and CCI files and convert anyway",
    )

    parser.add_argument(
        "--ignore-encryption",
        action="store_true",
        help="Ignore the encryption header value, assume the ROM as unencrypted",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Print more information")

    parser.add_argument("--dev-keys", action="store_true", help="Use developer-unit keys")

    # Batch mode argument
    parser.add_argument(
        "--batch",
        metavar="folder-path",
        default=None,
        help="Batch mode: convert all CCI files in the specified folder. "
        "Output defaults to input folder unless --output is specified.",
    )

    # deprecated arguments; we want to print out a message on this
    # in the future we can probably use an `action` to handle this.
    parser.add_argument(
        "--gen-ncchinfo",
        "--gen-ncch-all",
        "--xorpads",
        dest="use_deprecated",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    # arguments kept for backwards compatibility
    parser.add_argument(
        "--no-convert", "--noconvert", default=argparse.SUPPRESS, help=argparse.SUPPRESS
    )

    # positional arguments - nargs="*" allows batch mode (--batch) to work without game files
    parser.add_argument("game", nargs="*", help="Game file(s) to convert to CIA")

    # if no arguments are provided, display help message
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


def discover_cci_files(folder_path: str) -> list[str]:
    """
    Discover all CCI files in a folder.

    Finds all files with .cci or .3ds extension (case-insensitive) in the
    specified folder. Does not search subdirectories.

    Args:
        folder_path: Path to the folder to search

    Returns:
        List of full paths to CCI files found, sorted alphabetically

    Raises:
        FileNotFoundError: If the folder does not exist
        NotADirectoryError: If the path exists but is not a directory
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Batch folder not found: {folder_path}")

    if not os.path.isdir(folder_path):
        raise NotADirectoryError(f"Batch path is not a directory: {folder_path}")

    cci_extensions = {".cci", ".3ds"}
    cci_files = []

    for filename in os.listdir(folder_path):
        # Check extension case-insensitively
        _, ext = os.path.splitext(filename)
        if ext.lower() in cci_extensions:
            full_path = os.path.join(folder_path, filename)
            # Only include regular files, not directories
            if os.path.isfile(full_path):
                cci_files.append(full_path)

    # Sort for consistent ordering
    return sorted(cci_files)


def rol(val, r_bits, max_bits):
    """
    Rotate left operation.

    Used from http://www.falatic.com/index.php/108/python-and-bitwise-rotation
    Converted to def because pycodestyle complained.

    Args:
        val: Value to rotate
        r_bits: Number of bits to rotate
        max_bits: Maximum number of bits (bit width)

    Returns:
        Rotated value
    """
    return (val << (r_bits % max_bits)) & (2**max_bits - 1) | (
        (val & (2**max_bits - 1)) >> (max_bits - (r_bits % max_bits))
    )


def error(*msg):
    """
    Print error message with 'Error:' prefix.

    Args:
        *msg: Message parts to print
    """
    print("Error:", *msg)


def show_progress(val, maxval):
    """
    Show a progress bar.

    Args:
        val: Current progress value
        maxval: Maximum value (100% completion)
    """
    minval = min(val, maxval)
    sys.stdout.write(f"\r  {(minval / maxval) * 100:>5.1f}% {minval:>10} / {maxval}")
    sys.stdout.flush()


def parse_prod_keys(prod_keys_path: str) -> dict[str, str]:
    """
    Parse a prod.keys file and extract key-value pairs.

    The prod.keys file format is simple:
    - Lines starting with # are comments
    - Empty lines are ignored
    - Key-value pairs are in the format: key=value
    - Values are hexadecimal strings without 0x prefix

    Args:
        prod_keys_path: Path to the prod.keys file

    Returns:
        Dictionary mapping key names to their hexadecimal values

    Raises:
        FileNotFoundError: If the prod.keys file doesn't exist
        ValueError: If the file contains invalid key-value pairs
    """
    if not os.path.isfile(prod_keys_path):
        raise FileNotFoundError(f"prod.keys file not found: {prod_keys_path}")

    keys = {}
    with open(prod_keys_path) as f:
        for line_num, line in enumerate(f, start=1):
            # Strip whitespace and skip empty lines and comments
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Parse key=value pairs
            if "=" not in line:
                raise ValueError(
                    f"Invalid format in prod.keys at line {line_num}: expected 'key=value'"
                )

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Validate that value is a valid hex string
            if not value:
                raise ValueError(f"Empty value for key '{key}' at line {line_num}")

            try:
                int(value, 16)
            except ValueError as e:
                raise ValueError(
                    f"Invalid hexadecimal value for key '{key}' at line {line_num}: {value}"
                ) from e

            keys[key] = value

    return keys


def get_slot0x2c_key_from_prod_keys(prod_keys_path: str) -> int:
    """
    Extract the slot 0x2C key from a prod.keys file.

    Args:
        prod_keys_path: Path to the prod.keys file

    Returns:
        The slot 0x2C key as an integer

    Raises:
        FileNotFoundError: If the prod.keys file doesn't exist
        ValueError: If the file is invalid or doesn't contain the required key
        KeyError: If slot0x2CKey is not found in the file
    """
    keys = parse_prod_keys(prod_keys_path)

    if "slot0x2CKey" not in keys:
        raise KeyError("slot0x2CKey not found in prod.keys file")

    key_hex = keys["slot0x2CKey"]

    # Convert hex string to integer
    key_int = int(key_hex, 16)

    return key_int


# Note: print_v() and v() depend on global args and will be tested via mocking
# They are defined in the main 3dsconv.py module
