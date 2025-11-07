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

    # positional arguments
    parser.add_argument("game", nargs="+", help="Game file to convert to CIA")

    # if no arguments are provided, display help message
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    return parser.parse_args()


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


# Note: print_v() and v() depend on global args and will be tested via mocking
# They are defined in the main 3dsconv.py module
