"""I/O operations for 3dsconv.

This module provides utilities for reading and writing binary file formats
used in Nintendo 3DS content, including CCI, NCCH, and CIA formats.
"""

from dsconv.io.binary_reader import BinaryReader
from dsconv.io.ncch_reader import NCCHReader

__all__ = ["BinaryReader", "NCCHReader"]
