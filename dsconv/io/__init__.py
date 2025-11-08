"""I/O operations for reading and writing 3DS file formats.

This package provides abstractions for reading and writing binary files
used in Nintendo 3DS software, including NCSD containers, NCCH content,
ExeFS filesystems, and CIA archives.
"""

from .binary_reader import BinaryReader
from .exefs_reader import ExeFSFile, ExeFSReader

__all__ = ["BinaryReader", "ExeFSFile", "ExeFSReader"]
