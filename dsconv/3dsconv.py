#!/usr/bin/env python3
"""
Compatibility shim for old imports.

This module redirects to the legacy implementation for backward compatibility.
New code should use dsconv.cli.main or dsconv.legacy directly.
"""

import warnings

warnings.warn(
    "Importing from dsconv.3dsconv is deprecated. "
    "Use 'python -m dsconv' (refactored) or 'python -m dsconv --legacy' (original).",
    DeprecationWarning,
    stacklevel=2,
)

# Redirect to legacy for backward compatibility
from dsconv.legacy import *  # noqa: F401, F403, E402
