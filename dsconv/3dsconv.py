#!/usr/bin/env python3
"""
Compatibility shim for old imports.

This module redirects to the refactored implementation for backward compatibility.
The original monolithic code has been moved to dsconv/legacy.py.

New code should use:
    python -m dsconv (refactored)
or
    python -m dsconv --legacy (original)
"""

# Import necessary functions from refactored implementation  
from dsconv.utils import parse_args  # noqa: F401

# Don't import legacy here as it runs module-level code
# from dsconv import legacy  # noqa: F401

def main():
    """Compatibility main - delegates to refactored CLI."""
    from dsconv.cli.main import main as refactored_main
    refactored_main()
