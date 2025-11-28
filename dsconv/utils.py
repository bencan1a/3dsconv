"""
Testable utilities extracted from 3dsconv.

This module contains pure or near-pure functions that can be tested independently
without triggering the main script execution.
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


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

    # CXI extraction via ctrtool
    parser.add_argument(
        "--to-cxi",
        action="store_true",
        help="Extract CXI from converted CIA files using ctrtool. "
        "Requires ctrtool to be installed and available in PATH.",
    )

    parser.add_argument(
        "--ctrtool-path",
        metavar="path-to-ctrtool",
        default=os.environ.get("CTRTOOL_PATH"),
        help="Path to ctrtool executable. If not specified, searches PATH.",
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
        List of absolute paths to CCI files found, sorted alphabetically.
        Example: ['/path/to/game1.cci', '/path/to/game2.3ds']

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


def find_ctrtool(custom_path: str | None = None) -> str | None:
    """
    Find the ctrtool executable.

    Searches for ctrtool in the following order:
    1. Custom path if provided
    2. CTRTOOL_PATH environment variable
    3. Bundled ctrtool in package (dsconv/bin/)
    4. System PATH

    On Windows, looks for ctrtool.exe. On Linux/macOS, looks for ctrtool.

    Args:
        custom_path: Optional custom path to ctrtool

    Returns:
        Path to ctrtool executable if found, None otherwise
    """
    # Determine the executable name based on platform
    if platform.system() == "Windows":
        exe_names = ["ctrtool.exe", "ctrtool"]
    else:
        exe_names = ["ctrtool", "ctrtool.exe"]

    # Check custom path first
    if custom_path:
        if os.path.isfile(custom_path):
            return custom_path
        # If custom path is a directory, look for ctrtool inside
        if os.path.isdir(custom_path):
            for exe_name in exe_names:
                full_path = os.path.join(custom_path, exe_name)
                if os.path.isfile(full_path):
                    return full_path
        return None

    # Check CTRTOOL_PATH environment variable
    env_path = os.environ.get("CTRTOOL_PATH")
    if env_path:
        if os.path.isfile(env_path):
            return env_path
        if os.path.isdir(env_path):
            for exe_name in exe_names:
                full_path = os.path.join(env_path, exe_name)
                if os.path.isfile(full_path):
                    return full_path

    # Check bundled ctrtool in package
    try:
        package_dir = os.path.dirname(os.path.abspath(__file__))
        bin_dir = os.path.join(package_dir, "bin")
        if os.path.isdir(bin_dir):
            for exe_name in exe_names:
                bundled_path = os.path.join(bin_dir, exe_name)
                if os.path.isfile(bundled_path):
                    return bundled_path
    except Exception:
        # If we can't determine package location, continue to PATH search
        pass

    # Search in system PATH
    for exe_name in exe_names:
        found = shutil.which(exe_name)
        if found:
            return found

    return None


def run_ctrtool_extract_contents(
    ctrtool_path: str, cia_path: str, output_dir: str | None = None
) -> tuple[bool, str]:
    """
    Run ctrtool to extract contents from a CIA file.

    Executes: ctrtool --contents=<output_dir> --intype=cia "<cia_path>"

    Args:
        ctrtool_path: Path to ctrtool executable
        cia_path: Path to the CIA file to extract
        output_dir: Directory to output contents to. If None, uses CIA's directory.

    Returns:
        Tuple of (success, message). success is True if extraction succeeded,
        message contains either success info or error details.
    """
    if not os.path.isfile(cia_path):
        return False, f"CIA file not found: {cia_path}"

    if not os.path.isfile(ctrtool_path):
        return False, f"ctrtool not found: {ctrtool_path}"

    # Default output directory to CIA's directory
    if output_dir is None:
        output_dir = os.path.dirname(cia_path) or "."

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Build the command
    # ctrtool outputs contents as "contents.XXXX.<ext>" where XXXX is the content index
    contents_prefix = os.path.join(output_dir, "contents")
    cmd = [
        ctrtool_path,
        f"--contents={contents_prefix}",
        "--intype=cia",
        cia_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return False, f"ctrtool failed: {error_msg}"

        return True, f"Contents extracted to {output_dir}"

    except subprocess.TimeoutExpired:
        return False, "ctrtool timed out after 120 seconds"
    except FileNotFoundError:
        return False, f"ctrtool executable not found: {ctrtool_path}"
    except OSError as e:
        return False, f"Failed to run ctrtool: {e}"


def rename_contents_to_cxi(cia_path: str, output_dir: str | None = None) -> tuple[bool, str]:
    """
    Rename contents.0000.* file to <basename>.cxi.

    After ctrtool extracts contents from a CIA, the main game content
    is typically in contents.0000.<ext>. This function renames it to
    match the original filename with a .cxi extension.

    Args:
        cia_path: Path to the original CIA file (used to determine output name)
        output_dir: Directory where contents were extracted. If None, uses CIA's directory.

    Returns:
        Tuple of (success, message). success is True if rename succeeded,
        message contains either the new CXI path or error details.
    """
    if output_dir is None:
        output_dir = os.path.dirname(cia_path) or "."

    # Look for contents.0000.* file using pathlib for cross-platform compatibility
    output_path = Path(output_dir)
    content_files = list(output_path.glob("contents.0000.*"))

    if not content_files:
        return False, f"No contents.0000.* file found in {output_dir}"

    # Use the first match (there should only be one)
    content_file = str(content_files[0])

    # Determine output CXI filename based on CIA filename
    cia_basename = os.path.splitext(os.path.basename(cia_path))[0]
    cxi_path = os.path.join(output_dir, f"{cia_basename}.cxi")

    try:
        # Remove existing CXI file if present
        if os.path.exists(cxi_path):
            os.remove(cxi_path)

        # Rename contents file to CXI
        os.rename(content_file, cxi_path)
        return True, cxi_path

    except OSError as e:
        return False, f"Failed to rename {content_file} to {cxi_path}: {e}"


def convert_cia_to_cxi(
    ctrtool_path: str, cia_path: str, output_dir: str | None = None, verbose: bool = False
) -> tuple[bool, str]:
    """
    Convert a CIA file to CXI using ctrtool.

    This is a high-level function that:
    1. Runs ctrtool to extract contents from the CIA
    2. Renames the extracted contents.0000.* file to <basename>.cxi

    Args:
        ctrtool_path: Path to ctrtool executable
        cia_path: Path to the CIA file to convert
        output_dir: Directory for output. If None, uses CIA's directory.
        verbose: If True, print progress messages

    Returns:
        Tuple of (success, message). success is True if conversion succeeded,
        message contains either the CXI path or error details.
    """
    if verbose:
        print(f"Extracting CXI from {cia_path}...")

    # Step 1: Extract contents
    success, msg = run_ctrtool_extract_contents(ctrtool_path, cia_path, output_dir)
    if not success:
        return False, msg

    # Step 2: Rename to CXI
    success, cxi_path = rename_contents_to_cxi(cia_path, output_dir)
    if not success:
        return False, cxi_path

    if verbose:
        print(f"Created CXI: {cxi_path}")

    return True, cxi_path


# Note: print_v() and v() depend on global args and will be tested via mocking
# They are defined in the main 3dsconv.py module
