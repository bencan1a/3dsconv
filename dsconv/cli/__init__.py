"""CLI layer for 3dsconv.

This package contains CLI-specific components that bridge between the
command-line interface (argparse) and the domain layer (ConversionConfig).
"""

from .config_mapper import CLIConfigMapper
from .main import main

__all__ = ["CLIConfigMapper", "main"]
