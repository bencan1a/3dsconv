"""I/O operations for 3dsconv."""

from .binary_reader import BinaryReader
from .ncch_reader import NCCHReader

__all__ = ["BinaryReader", "NCCHReader"]
from .ncsd_reader import NCSDReader

__all__ = ["BinaryReader", "NCSDReader"]
