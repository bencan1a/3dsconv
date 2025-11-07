"""Domain models for 3dsconv."""

from .ncch import NCCHHeader
from .ncsd import NCSDContainer, NCSDPartition

__all__ = ["NCCHHeader", "NCSDContainer", "NCSDPartition"]
